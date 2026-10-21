
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.agents.coder import CoderAgent, CodeChange
from app.agents.qa import QAAgent
from app.agents.reviewer import CodeReviewer, ReviewReport
from app.model_router import ModelRouter
from app.tools.registry import create_filesystem_registry


SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


@dataclass
class ReviewFixReport:
    status: str
    cycles: int = 0
    review: ReviewReport | None = None
    qa_passed: bool = False
    messages: list[str] = field(default_factory=list)
    pending_changes: list[CodeChange] = field(default_factory=list)


class ReviewFixLoop:
    def __init__(
        self,
        workspace: str | Path,
        model_router: ModelRouter,
        max_cycles: int = 3,
        min_severity: str = "high",
        write_progress: Callable[[str, str], None] | None = None,
    ) -> None:
        if max_cycles < 1:
            raise ValueError("max_cycles must be at least 1.")

        min_severity = min_severity.strip().lower()

        if min_severity not in SEVERITY_ORDER:
            raise ValueError(
                "min_severity must be one of: "
                "critical, high, medium, low, info."
            )

        self.workspace = Path(workspace).resolve()
        self.model_router = model_router
        self.max_cycles = max_cycles
        self.min_severity = min_severity
        self.min_severity_rank = SEVERITY_ORDER[min_severity]

        self.registry = create_filesystem_registry(
            self.workspace,
            write_progress=write_progress,
        )
        self.reviewer = CodeReviewer(model_router)
        self.coder = CoderAgent(model_router)
        self.qa = QAAgent(self.workspace)

    def _validate_files(self, relative_paths: list[str]) -> list[str]:
        if not relative_paths:
            raise ValueError("Select at least one file.")

        if len(set(relative_paths)) != len(relative_paths):
            raise ValueError("Duplicate file paths are not allowed.")

        validated = []

        for relative_path in relative_paths:
            path = Path(relative_path)

            if path.is_absolute():
                raise ValueError("Only relative file paths are allowed.")

            resolved = (self.workspace / path).resolve()

            if not resolved.is_relative_to(self.workspace):
                raise ValueError(
                    f"Outside-workspace path rejected: {relative_path}"
                )

            if not resolved.is_file():
                raise ValueError(f"File does not exist: {relative_path}")

            validated.append(
                resolved.relative_to(self.workspace).as_posix()
            )

        return validated

    def _read_file(self, relative_path: str) -> str:
        result = self.registry.execute(
            "read_file",
            {"relative_path": relative_path},
        )

        if not result["ok"]:
            raise ValueError(
                f"Could not read {relative_path}: {result['error']}"
            )

        return result["result"]

    def _write_file(self, relative_path: str, content: str) -> None:
        result = self.registry.execute(
            "write_file",
            {
                "relative_path": relative_path,
                "content": content,
            },
        )

        if not result["ok"]:
            raise ValueError(
                f"Could not write {relative_path}: {result['error']}"
            )

    def _actionable_findings(self, review: ReviewReport):
        actionable = []

        for finding in review.findings:
            severity = finding.severity.strip().lower()
            severity_rank = SEVERITY_ORDER.get(severity)

            if (
                severity_rank is not None
                and severity_rank <= self.min_severity_rank
            ):
                actionable.append(finding)

        return actionable

    def run(
        self,
        relative_paths: list[str],
        approve_change: Callable[[CodeChange], bool] | None = None,
    ) -> ReviewFixReport:
        selected = self._validate_files(relative_paths)

        python_files = [
            path for path in selected
            if Path(path).suffix.lower() == ".py"
        ]

        messages: list[str] = []
        latest_review = None
        latest_qa_passed = False

        for cycle in range(self.max_cycles + 1):
            code_context = "\n\n".join(
                f"File: {path}\n```\n{self._read_file(path)}\n```"
                for path in selected
            )

            latest_review = self.reviewer.review(code_context)
            actionable_findings = self._actionable_findings(
                latest_review
            )

            if python_files:
                qa_report = self.qa.run_checks(python_files)
                latest_qa_passed = qa_report.passed

                messages.extend(
                    f"QA [{check.name}]: "
                    f"{'PASS' if check.passed else 'FAIL'}"
                    + (f" — {check.error}" if check.error else "")
                    for check in qa_report.checks
                )
            else:
                latest_qa_passed = True
                messages.append("QA skipped: no selected Python files.")

            if not actionable_findings and latest_qa_passed:
                return ReviewFixReport(
                    status="passed",
                    cycles=cycle,
                    review=latest_review,
                    qa_passed=latest_qa_passed,
                    messages=messages,
                )

            if cycle == self.max_cycles:
                break

            proposed_changes: list[CodeChange] = []
            failed_qa = not latest_qa_passed

            for path in selected:
                matching = [
                    finding for finding in actionable_findings
                    if not finding.file or finding.file == path
                ]

                if not matching and not (
                    failed_qa and path in python_files
                ):
                    continue

                feedback_parts = [
                    (
                        f"[{finding.severity.upper()}] "
                        f"{finding.category}: {finding.message}\n"
                        f"Recommendation: {finding.recommendation}"
                    )
                    for finding in matching
                ]

                if failed_qa and path in python_files:
                    feedback_parts.append(
                        "Python syntax QA failed. Fix syntax errors "
                        "while preserving unrelated functionality."
                    )

                change = self.coder.propose_fix(
                    file_path=path,
                    current_content=self._read_file(path),
                    review_feedback="\n\n".join(feedback_parts),
                )

                if change.file != path:
                    raise ValueError(
                        f"Coder target mismatch: expected {path}, "
                        f"received {change.file}"
                    )

                proposed_changes.append(change)

            if not proposed_changes:
                messages.append("No applicable fixes were generated.")
                break

            pending_changes: list[CodeChange] = []

            for change in proposed_changes:
                if approve_change is None or not approve_change(change):
                    pending_changes.append(change)
                    messages.append(
                        f"Change awaiting approval: {change.file}"
                    )
                    continue

                self._write_file(change.file, change.content)
                messages.append(
                    f"Applied approved change to {change.file}: "
                    f"{change.explanation}"
                )

            if pending_changes:
                return ReviewFixReport(
                    status="awaiting_approval",
                    cycles=cycle,
                    review=latest_review,
                    qa_passed=latest_qa_passed,
                    messages=messages,
                    pending_changes=pending_changes,
                )

        return ReviewFixReport(
            status="limit_reached",
            cycles=self.max_cycles,
            review=latest_review,
            qa_passed=latest_qa_passed,
            messages=messages,
        )

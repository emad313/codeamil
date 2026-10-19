
from pathlib import Path

from app.verification.checks import (
    CheckResult,
    VerificationReport,
    check_python_syntax,
)


class QAAgent:
    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    def run_checks(
        self,
        python_files: list[str],
    ) -> VerificationReport:
        result: CheckResult = check_python_syntax(
            self.workspace,
            python_files,
        )

        return VerificationReport(checks=[result])


import argparse
import difflib

from app.config import load_settings, validate_active_provider
from app.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CodeAmil Agent - General-Purpose AI Coding Agent"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="The task you want CodeAmil Agent to perform",
    )
    parser.add_argument(
        "--review-fix",
        nargs="+",
        metavar="FILE",
        help="Review selected files and propose or apply approved fixes",
    )

    args = parser.parse_args()

    try:
        settings = load_settings()
        validate_active_provider(settings)
    except ValueError as exc:
        parser.exit(1, f"Configuration error: {exc}\n")

    orchestrator = Orchestrator(settings)

    if args.review_fix:
        print(f"Workspace: {orchestrator.workspace}")
        print("Selected files:")
        for file_path in args.review_fix:
            print(f"  - {file_path}")

        def approve_change(change) -> bool:
            print(f"\nProposed change: {change.file}")
            print(f"Explanation: {change.explanation}")

            try:
                original = (
                    orchestrator.workspace / change.file
                ).read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                print(f"Could not preview the change: {exc}")
                return False

            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                change.content.splitlines(keepends=True),
                fromfile=f"a/{change.file}",
                tofile=f"b/{change.file}",
            )

            preview = "".join(diff)

            if not preview:
                print("No content differences detected.")
                return False

            print("\n--- Proposed Diff ---")
            print(
                preview,
                end="" if preview.endswith("\n") else "\n",
            )
            print("--- End Diff ---")

            answer = input(
                "\nApply this change? [y/N]: "
            ).strip().lower()

            return answer == "y"

        try:
            report = orchestrator.run_review_fix(
                args.review_fix,
                approve_change=approve_change,
            )
        except (ValueError, OSError) as exc:
            parser.exit(1, f"Review-fix error: {exc}\n")

        print(f"\nStatus: {report.status}")
        print(f"Cycles: {report.cycles}")
        print(f"QA passed: {report.qa_passed}")

        if report.review:
            print(f"\nReview summary: {report.review.summary}")

            for finding in report.review.findings:
                location = (
                    f" ({finding.file}:{finding.line})"
                    if finding.file and finding.line
                    else f" ({finding.file})"
                    if finding.file
                    else ""
                )

                print(
                    f"- [{finding.severity.upper()}] "
                    f"{finding.category}{location}: "
                    f"{finding.message}"
                )

                if finding.recommendation:
                    print(
                        f"  Recommendation: "
                        f"{finding.recommendation}"
                    )

        for message in report.messages:
            print(f"- {message}")

        if report.pending_changes:
            print("\nChanges awaiting approval:")

            for change in report.pending_changes:
                print(
                    f"- {change.file}: {change.explanation}"
                )

        return

    task = args.task or input(
        "Enter your coding task: "
    ).strip()

    if not task:
        parser.error("A task is required.")

    state = orchestrator.run_task(task)

    print(f"\nStatus: {state.status}")
    print(f"Iterations: {state.iteration}")

    if state.result:
        print("\n--- CodeAmil Agent Response ---\n")
        print(state.result)

    if state.error:
        print(f"\nError: {state.error}")


if __name__ == "__main__":
    main()

import argparse
import difflib
import getpass
import json
import os
from pathlib import Path

from dotenv import dotenv_values

from app.config import load_settings, validate_active_provider
from app.orchestrator import Orchestrator



def configure_user_settings() -> None:
    """Interactively configure CodeAmil for the current user."""
    config_path = Path.home() / ".codeamil" / ".env"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {
        key: value
        for key, value in dotenv_values(config_path).items()
        if value is not None
    }

    print("Configure CodeAmil")
    print(f"Settings file: {config_path}")
    print("Providers: gemini, openai, openrouter")

    current_provider = existing.get("MODEL_PROVIDER", "gemini")
    provider = input(
        f"Provider [{current_provider}]: "
    ).strip().lower() or current_provider

    if provider not in {"gemini", "openai", "openrouter"}:
        print("Unsupported provider. Choose gemini, openai, or openrouter.")
        return

    default_models = {
        "gemini": "gemini-3.6-flash",
        "openai": "gpt-4.1-mini",
        "openrouter": "openrouter/free",
    }

    current_model = existing.get("MODEL_ID", default_models[provider])
    model = input(f"Model ID [{current_model}]: ").strip() or current_model

    key_names = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    selected_key = key_names[provider]

    print(f"Enter the API key for {provider}. Leave blank to keep the saved key.")
    api_key = getpass.getpass("API key: ").strip()

    existing["MODEL_PROVIDER"] = provider
    existing["MODEL_ID"] = model

    if api_key:
        existing[selected_key] = api_key

    existing.setdefault("MAX_AGENT_ITERATIONS", "12")
    existing.setdefault("MAX_REVIEW_FIX_CYCLES", "3")
    existing.setdefault("REQUIRE_APPROVAL_FOR_COMMANDS", "true")
    existing.setdefault("REVIEW_FIX_MIN_SEVERITY", "high")

    config_path.write_text(
        "".join(
            f"{key}={json.dumps(value)}\n"
            for key, value in existing.items()
        ),
        encoding="utf-8",
    )

    if os.name != "nt":
        config_path.chmod(0o600)

    if not existing.get(selected_key):
        print(f"Configuration saved, but {selected_key} is still missing.")
        return

    print("Configuration saved successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CodeAmil Agent - General-Purpose AI Coding Agent"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="CodeAmil 0.1.0",
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

    if args.task == "config" and not args.review_fix:
        configure_user_settings()
        return

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

    def approve_command(command: list[str]) -> bool:
        print("\nCommand requires your approval:")
        print(f"  {' '.join(command)}")

        answer = input("Execute this command? [y/N]: ").strip().lower()
        return answer == "y"


    state = orchestrator.run_task(
        task,
        approve_command=approve_command,
    )

    print(f"\nStatus: {state.status}")
    print(f"Iterations: {state.iteration}")

    if state.result:
        print("\n--- CodeAmil Agent Response ---\n")
        print(state.result)

    if state.error:
        print(f"\nError: {state.error}")


if __name__ == "__main__":
    main()

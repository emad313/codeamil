
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.config import load_settings
from app.orchestrator import Orchestrator


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        with patch("app.orchestrator.ModelRouter"):
            orchestrator = Orchestrator(
                settings=load_settings(),
                workspace=workspace,
            )

        executor = orchestrator.command_executor

        # An unclassified command must not run without approval.
        result = executor.execute(["python", "--version"])
        assert result["ok"] is False
        assert "approval" in result["error"].lower()
        print("PASS: command without approval is rejected")

        # A denied approval must prevent execution.
        with patch("app.tools.execution.subprocess.run") as run:
            result = executor.execute(
                ["python", "--version"],
                approve=lambda command: False,
            )
            assert result["ok"] is False
            run.assert_not_called()
        print("PASS: rejected approval prevents execution")

        # An approved command can execute.
        with patch("app.tools.execution.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "Python test\n"
            run.return_value.stderr = ""

            result = executor.execute(
                ["python", "--version"],
                approve=lambda command: True,
            )

            assert result["ok"] is True
            run.assert_called_once()
        print("PASS: approved command executes")

        # Shell launch attempts remain blocked even if approval is granted.
        with patch("app.tools.execution.subprocess.run") as run:
            result = executor.execute(
                ["bash", "-c", "echo unsafe"],
                approve=lambda command: True,
            )
            assert result["ok"] is False
            run.assert_not_called()
        print("PASS: shell launch is blocked")

    print("All orchestrator command approval tests passed.")


if __name__ == "__main__":
    main()

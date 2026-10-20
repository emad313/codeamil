
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.config import load_settings
from app.orchestrator import Orchestrator


import os
from unittest.mock import patch


def load_settings_with_approval(enabled: bool):
    home = Path(os.environ.get("USERPROFILE", r"C:\Users\emad"))

    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "MODEL_PROVIDER": "gemini",
        "MODEL_ID": "test-model",
        "REQUIRE_APPROVAL_FOR_COMMANDS": str(enabled).lower(),
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch("pathlib.Path.home", return_value=home),
    ):
        return load_settings()


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        for approval_setting in (True, False):
            with patch("app.orchestrator.ModelRouter"):
                orchestrator = Orchestrator(
                    settings=load_settings_with_approval(
                        approval_setting
                    ),
                    workspace=workspace,
                )

            assert (
                orchestrator.command_executor.require_approval
                is approval_setting
            )

        print("PASS: orchestrator passes approval setting to executor")

        # Existing approval behavior remains enabled by default.
        with patch("app.orchestrator.ModelRouter"):
            orchestrator = Orchestrator(
                settings=load_settings_with_approval(True),
                workspace=workspace,
            )

        executor = orchestrator.command_executor

        result = executor.execute(["python", "--version"])
        assert result["ok"] is False
        assert "approval" in result["error"].lower()
        print("PASS: command without approval is rejected")

        with patch("app.tools.execution.subprocess.run") as run:
            result = executor.execute(
                ["python", "--version"],
                approve=lambda command: False,
            )
            assert result["ok"] is False
            run.assert_not_called()
        print("PASS: rejected approval prevents execution")

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

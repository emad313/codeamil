import sys
import tempfile
from pathlib import Path

from app.tools.execution import CommandExecutor


def test_command_requires_approval():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)
        result = executor.execute([sys.executable, "--version"])

        assert not result["ok"]
        assert "approval" in result["error"].lower()
        print("PASS: command without approval is rejected")


def test_rejected_approval_prevents_execution():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)
        marker = Path(temp) / "marker.txt"

        result = executor.execute(
            [
                sys.executable,
                "-c",
                f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')",
            ],
            approve=lambda command: False,
        )

        assert not result["ok"]
        assert not marker.exists()
        print("PASS: rejected approval prevents execution")


def test_approved_command_executes():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)

        result = executor.execute(
            [sys.executable, "-c", "print('approved')"],
            approve=lambda command: True,
        )

        assert result["ok"]
        assert "approved" in result["stdout"]
        print("PASS: approved command executes")


def test_shell_launch_is_blocked():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)
        result = executor.execute(["bash", "-c", "echo unsafe"])

        assert not result["ok"]
        assert "prohibited" in result["error"].lower()
        print("PASS: shell launch is blocked")


if __name__ == "__main__":
    test_command_requires_approval()
    test_rejected_approval_prevents_execution()
    test_approved_command_executes()
    test_shell_launch_is_blocked()
    print("All command execution tests passed.")

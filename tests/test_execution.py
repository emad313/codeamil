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


def test_missing_executable_is_rejected():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)

        result = executor.execute(
            ["codeamil-executable-that-does-not-exist-92841"],
            approve=lambda command: True,
        )

        assert not result["ok"]
        assert "FileNotFoundError" in result["error"]
        print("PASS: missing executable is rejected")


def test_executable_path_is_not_rewritten():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp)

        result = executor.execute(
            [sys.executable, "--version"],
            approve=lambda command: True,
        )

        assert result["ok"]
        assert sys.executable in result["stdout"] or (
            sys.version.split()[0] in result["stdout"]
        )
        print("PASS: explicit executable path runs correctly")



def test_command_executes_when_approval_disabled():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp, require_approval=False)

        result = executor.execute(
            [sys.executable, "-c", "print('no approval required')"]
        )

        assert result["ok"]
        assert "no approval required" in result["stdout"]
        print("PASS: command executes when approval is disabled")


def test_shell_stays_blocked_when_approval_disabled():
    with tempfile.TemporaryDirectory() as temp:
        executor = CommandExecutor(temp, require_approval=False)

        result = executor.execute(["bash", "-c", "echo unsafe"])

        assert not result["ok"]
        assert "prohibited" in result["error"].lower()
        print("PASS: shell remains blocked when approval is disabled")



if __name__ == "__main__":
    test_command_requires_approval()
    test_rejected_approval_prevents_execution()
    test_approved_command_executes()
    test_shell_launch_is_blocked()
    test_missing_executable_is_rejected()
    test_executable_path_is_not_rewritten()
    test_command_executes_when_approval_disabled()
    test_shell_stays_blocked_when_approval_disabled()
    print("All command execution tests passed.")

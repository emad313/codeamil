from pathlib import Path

from app.safety.command_policy import CommandPolicy


def test_read_only_command_needs_no_approval():
    policy = CommandPolicy()

    decision = policy.evaluate(
        ["git", "status"],
        Path.cwd(),
    )

    assert decision.allowed
    assert not decision.requires_approval
    print("PASS: read-only command needs no approval")


def test_unknown_command_requires_approval():
    policy = CommandPolicy()

    decision = policy.evaluate(
        ["python", "-m", "pytest"],
        Path.cwd(),
    )

    assert decision.allowed
    assert decision.requires_approval
    print("PASS: unclassified command requires approval")


def test_shell_execution_is_blocked():
    policy = CommandPolicy()

    for command in (
        ["bash", "-c", "echo unsafe"],
        ["powershell", "-Command", "Write-Output unsafe"],
        ["cmd.exe", "/c", "echo unsafe"],
    ):
        decision = policy.evaluate(command, Path.cwd())

        assert not decision.allowed
        assert not decision.requires_approval

    print("PASS: shell launch attempts are blocked")


def test_shell_paths_are_blocked():
    policy = CommandPolicy()

    for command in (
        ["/bin/bash", "-c", "echo unsafe"],
        [r"C:\Windows\System32\cmd.exe", "/c", "echo unsafe"],
        [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
         "-Command", "Write-Output unsafe"],
    ):
        decision = policy.evaluate(command, Path.cwd())

        assert not decision.allowed
        assert not decision.requires_approval

    print("PASS: shell executable paths are blocked")

def test_invalid_commands_are_rejected():
    policy = CommandPolicy()

    for command in ([], "", ["git", ""]):
        decision = policy.evaluate(command, Path.cwd())
        assert not decision.allowed

    print("PASS: invalid commands are rejected")


def test_read_only_classification_requires_exact_match():
    policy = CommandPolicy()

    decision = policy.evaluate(
        ["git", "status", "--short"],
        Path.cwd(),
    )

    assert decision.allowed
    assert decision.requires_approval
    print("PASS: unclassified command variants require approval")


if __name__ == "__main__":
    test_read_only_command_needs_no_approval()
    test_unknown_command_requires_approval()
    test_shell_execution_is_blocked()
    test_shell_paths_are_blocked()
    test_invalid_commands_are_rejected()
    test_read_only_classification_requires_exact_match()
    print("All command policy tests passed.")

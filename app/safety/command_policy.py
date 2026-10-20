
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CommandDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class CommandPolicy:
    """Classify commands before they reach the execution layer."""

    READ_ONLY_COMMANDS = {
        ("git", "status"),
        ("git", "diff"),
        ("git", "log"),
        ("git", "show"),
        ("git", "branch", "--show-current"),
    }

    SHELL_EXECUTABLES = {
        "sh",
        "bash",
        "zsh",
        "cmd",
        "cmd.exe",
        "powershell",
        "powershell.exe",
        "pwsh",
        "pwsh.exe",
    }

    def evaluate(
        self,
        command: Sequence[str],
        workspace: str | Path,
    ) -> CommandDecision:
        """Evaluate a command without executing it."""

        if (
            isinstance(command, (str, bytes))
            or not isinstance(command, (list, tuple))
            or not command
        ):
            return CommandDecision(
                allowed=False,
                requires_approval=False,
                reason="Command must be a non-empty argument list.",
            )

        if not all(
            isinstance(arg, str) and arg.strip()
            for arg in command
        ):
            return CommandDecision(
                allowed=False,
                requires_approval=False,
                reason="Every command argument must be a non-empty string.",
            )

        executable = command[0].replace("\\", "/").rsplit("/", 1)[-1].lower()

        if executable in self.SHELL_EXECUTABLES:
            return CommandDecision(
                allowed=False,
                requires_approval=False,
                reason="Launching a shell through this tool is prohibited.",
            )

        normalized = tuple(
            arg.strip().lower() for arg in command
        )

        if normalized in self.READ_ONLY_COMMANDS:
            return CommandDecision(
                allowed=True,
                requires_approval=False,
                reason="Recognized read-only command.",
            )

        return CommandDecision(
            allowed=True,
            requires_approval=True,
            reason="Explicit approval is required for this command.",
        )


import subprocess
from pathlib import Path
from typing import Callable, Sequence

from app.safety.command_policy import CommandPolicy


ApprovalCallback = Callable[[Sequence[str]], bool]


class CommandExecutor:
    def __init__(
        self,
        workspace: str | Path,
        policy: CommandPolicy | None = None,
        timeout: int = 30,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.policy = policy or CommandPolicy()

        if timeout < 1:
            raise ValueError("timeout must be at least 1 second.")

        self.timeout = timeout

        if not self.workspace.is_dir():
            raise ValueError("Workspace must be an existing directory.")

    def execute(
        self,
        command: Sequence[str],
        approve: ApprovalCallback | None = None,
    ) -> dict[str, object]:
        decision = self.policy.evaluate(command, self.workspace)

        if not decision.allowed:
            return {
                "ok": False,
                "error": decision.reason,
            }

        if decision.requires_approval:
            if approve is None:
                return {
                    "ok": False,
                    "error": "Explicit approval is required.",
                }

            try:
                approved = approve(command)
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"Approval failed: {type(exc).__name__}: {exc}",
                }

            if approved is not True:
                return {
                    "ok": False,
                    "error": "Command was not approved.",
                }

        try:
            result = subprocess.run(
                list(command),
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "error": f"Command timed out after {self.timeout} seconds.",
            }
        except OSError as exc:
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


import subprocess
import queue
import threading
import time
from pathlib import Path
from typing import Callable, Sequence

from app.safety.command_policy import CommandPolicy


ApprovalCallback = Callable[[Sequence[str]], bool]
OutputCallback = Callable[[str], None]
CommandStartedCallback = Callable[[Sequence[str]], None]
CommandFinishedCallback = Callable[[Sequence[str], dict[str, object]], None]


class CommandExecutor:
    def __init__(
        self,
        workspace: str | Path,
        policy: CommandPolicy | None = None,
        timeout: int = 600,
        require_approval: bool = True,
        output_callback: OutputCallback | None = None,
        command_started: CommandStartedCallback | None = None,
        command_finished: CommandFinishedCallback | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.policy = policy or CommandPolicy()
        self.require_approval = require_approval
        self.output_callback = output_callback
        self.command_started = command_started
        self.command_finished = command_finished

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

        needs_approval = (
            decision.requires_approval and self.require_approval
        )

        if needs_approval:
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
            process = subprocess.Popen(
                list(command),
                cwd=self.workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=False,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
                    else 0
                ),
            )
        except OSError as exc:
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        output_queue: queue.Queue[str | None] = queue.Queue()

        def read_output() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                output_queue.put(line)
            output_queue.put(None)

        reader = threading.Thread(
            target=read_output,
            name="codeamil-command-output",
            daemon=True,
        )
        reader.start()
        if self.command_started is not None:
            self.command_started(command)

        def finish(result: dict[str, object]) -> dict[str, object]:
            if self.command_finished is not None:
                self.command_finished(command, result)
            return result

        output_parts: list[str] = []
        deadline = time.monotonic() + self.timeout
        output_closed = False

        while not output_closed:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._terminate_process_tree(process)
                reader.join(timeout=1)
                return finish({
                    "ok": False,
                    "error": (
                        f"Command timed out after {self.timeout} seconds."
                    ),
                    "stdout": "".join(output_parts),
                    "stderr": "",
                })

            try:
                output = output_queue.get(timeout=min(remaining, 0.1))
            except queue.Empty:
                continue

            if output is None:
                output_closed = True
                continue

            output_parts.append(output)
            if self.output_callback is not None:
                self.output_callback(output)

        returncode = process.wait(timeout=max(remaining, 0))
        stdout = "".join(output_parts)

        return finish({
            "ok": returncode == 0,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": "",
        })

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return

        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            process.kill()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

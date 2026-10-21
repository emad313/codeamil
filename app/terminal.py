import sys
import threading
from typing import Sequence, TextIO


class TerminalAnimation:
    """Display a non-intrusive spinner while CodeAmil is working."""

    FRAMES = ("|", "/", "-", "\\")
    COLORS = {
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "magenta": "\033[35m",
        "dim": "\033[2m",
        "bold": "\033[1m",
    }
    RESET = "\033[0m"

    def __init__(
        self,
        message: str = "CodeAmil is working",
        stream: TextIO | None = None,
        enabled: bool | None = None,
        interval: float = 0.12,
        color: bool | None = None,
    ) -> None:
        self.stream = stream or sys.stderr
        self.message = message
        self.enabled = (
            self.stream.isatty() if enabled is None else enabled
        )
        self.color_enabled = (
            self.stream.isatty() if color is None else color
        )
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._active = False
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self.enabled or self._active:
            return

        self._stop.clear()
        self._active = True
        self._write("\033[?25l")
        self._thread = threading.Thread(
            target=self._run,
            name="codeamil-terminal-animation",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._active:
            return

        self._stop.set()
        if self._thread is not threading.current_thread():
            self._thread.join(timeout=max(self.interval * 4, 0.5))
        self._thread = None
        self._active = False
        self._clear()
        self._write("\033[?25h")

    def pause(self) -> None:
        self.stop()

    def resume(self) -> None:
        self.start()

    def show_file_write(self, relative_path: str, content: str) -> None:
        """Show each line immediately before a file is written."""
        self.pause()
        try:
            lines = content.splitlines(keepends=True)
            print(
                self.paint(
                    f"\nWriting {relative_path} ({len(lines)} lines):",
                    "cyan",
                )
            )

            if not lines:
                print("  (empty file)")

            for line_number, line in enumerate(lines, start=1):
                displayed = line.rstrip("\r\n")
                print(
                    self.paint(
                        f"  {line_number:>4} | ",
                        "dim",
                    )
                    + displayed,
                    flush=True,
                )

            print(
                self.paint(f"Writing {relative_path} now...", "green"),
                flush=True,
            )
        finally:
            self.resume()

    def show_command_output(self, output: str) -> None:
        print(output, end="", flush=True)

    def show_command_started(self, command: Sequence[str]) -> None:
        self.pause()
        print(
            self.paint(
                "\nRunning command (CodeAmil will continue after it finishes):",
                "yellow",
            ),
            flush=True,
        )
        print(self.paint(f"  {' '.join(command)}", "bold"), flush=True)
        print(self.paint("Command output:", "dim"), flush=True)

    def show_command_finished(
        self,
        command: Sequence[str],
        result: dict[str, object],
    ) -> None:
        returncode = result.get("returncode")
        if result.get("ok") is True:
            print(
                self.paint(
                    f"\nCommand finished successfully (exit code {returncode}).",
                    "green",
                ),
                flush=True,
            )
        else:
            error = result.get("error")
            detail = f": {error}" if error else ""
            print(
                self.paint(
                    f"\nCommand finished unsuccessfully{detail}",
                    "red",
                ),
                flush=True,
            )
        self.resume()

    def paint(self, value: str, color: str) -> str:
        """Apply a named ANSI color when terminal color is enabled."""
        if not self.color_enabled:
            return value

        code = self.COLORS.get(color)
        if code is None:
            raise ValueError(f"Unknown terminal color: {color}")

        return f"{code}{value}{self.RESET}"

    def __enter__(self) -> "TerminalAnimation":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def _run(self) -> None:
        frame_index = 0
        while not self._stop.is_set():
            self._write(
                f"\r{self.message} "
                f"{self.FRAMES[frame_index % len(self.FRAMES)]}"
            )
            frame_index += 1
            self._stop.wait(self.interval)

    def _clear(self) -> None:
        self._write("\r" + (" " * (len(self.message) + 2)) + "\r")

    def _write(self, value: str) -> None:
        with self._lock:
            self.stream.write(value)
            self.stream.flush()

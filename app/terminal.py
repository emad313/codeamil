import sys
import threading
from typing import TextIO


class TerminalAnimation:
    """Display a non-intrusive spinner while CodeAmil is working."""

    FRAMES = ("|", "/", "-", "\\")

    def __init__(
        self,
        message: str = "CodeAmil is working",
        stream: TextIO | None = None,
        enabled: bool | None = None,
        interval: float = 0.12,
    ) -> None:
        self.stream = stream or sys.stderr
        self.message = message
        self.enabled = (
            self.stream.isatty() if enabled is None else enabled
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
            print(f"\nWriting {relative_path} ({len(lines)} lines):")

            if not lines:
                print("  (empty file)")

            for line_number, line in enumerate(lines, start=1):
                displayed = line.rstrip("\r\n")
                print(f"  {line_number:>4} | {displayed}", flush=True)

            print(f"Writing {relative_path} now...", flush=True)
        finally:
            self.resume()

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

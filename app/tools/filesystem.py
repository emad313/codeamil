
from pathlib import Path


class WorkspaceFileSystem:
    """Safely inspect and edit files within one project workspace."""

    IGNORED_DIRS = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
    }

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

        if not self.workspace.is_dir():
            raise ValueError(
                f"Workspace directory does not exist: {self.workspace}"
            )

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a path and reject paths outside the workspace."""
        path = (self.workspace / relative_path).resolve()

        if not path.is_relative_to(self.workspace):
            raise PermissionError(
                "Access denied: path is outside the workspace."
            )

        return path

    def list_files(
        self,
        relative_path: str = ".",
        max_files: int = 200,
    ) -> list[str]:
        directory = self._resolve_path(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        results: list[str] = []

        for path in sorted(directory.rglob("*")):
            if any(part in self.IGNORED_DIRS for part in path.parts):
                continue

            if path.is_file():
                results.append(
                    path.relative_to(self.workspace).as_posix()
                )

                if len(results) >= max_files:
                    break

        return results

    def read_file(self, relative_path: str) -> str:
        path = self._resolve_path(relative_path)

        if not path.is_file():
            raise FileNotFoundError(relative_path)

        return path.read_text(encoding="utf-8")

    def search_text(
        self,
        query: str,
        relative_path: str = ".",
        max_results: int = 100,
    ) -> list[dict[str, str | int]]:
        if not query:
            raise ValueError("Search query cannot be empty.")

        directory = self._resolve_path(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        results: list[dict[str, str | int]] = []

        for path in sorted(directory.rglob("*")):
            if any(part in self.IGNORED_DIRS for part in path.parts):
                continue

            if not path.is_file():
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(
                content.splitlines(), start=1
            ):
                if query.casefold() in line.casefold():
                    results.append({
                        "file": path.relative_to(
                            self.workspace
                        ).as_posix(),
                        "line": line_number,
                        "text": line.strip(),
                    })

                    if len(results) >= max_results:
                        return results

        return results

    def write_file(
        self,
        relative_path: str,
        content: str,
    ) -> str:
        path = self._resolve_path(relative_path)

        if path.exists() and not path.is_file():
            raise IsADirectoryError(relative_path)

        path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve again after creating parent directories.
        path = self._resolve_path(relative_path)

        if path.exists() and not path.is_file():
            raise IsADirectoryError(relative_path)

        path.write_text(content, encoding="utf-8")

        return path.relative_to(self.workspace).as_posix()

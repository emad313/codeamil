
import os
from pathlib import Path
from typing import Callable

from app.tools.search import WorkspaceSearch


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

    def __init__(
        self,
        workspace: str | Path,
        write_progress: Callable[[str, str], None] | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.write_progress = write_progress

        if not self.workspace.is_dir():
            raise ValueError(
                f"Workspace directory does not exist: {self.workspace}"
            )
        self.search = WorkspaceSearch(self.workspace, self.IGNORED_DIRS)

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a path and reject paths outside the workspace."""
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("A non-empty relative path is required.")

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
        if not isinstance(max_files, int) or isinstance(max_files, bool):
            raise ValueError("max_files must be an integer.")

        if max_files < 1:
            raise ValueError("max_files must be at least 1.")

        directory = self._resolve_path(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        results: list[str] = []

        for current, directories, filenames in os.walk(
            directory, topdown=True, followlinks=False
        ):
            current_path = Path(current)
            directories[:] = sorted(
                name for name in directories
                if name not in self.IGNORED_DIRS
                and not (current_path / name).is_symlink()
            )

            for filename in sorted(filenames):
                path = current_path / filename
                if path.is_symlink() or any(
                    part in self.IGNORED_DIRS for part in path.parts
                ):
                    continue

                results.append(path.relative_to(self.workspace).as_posix())
                if len(results) >= max_files:
                    return results

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

        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise ValueError("max_results must be an integer.")

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        directory = self._resolve_path(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        return self.search.text(query, relative_path, max_results)

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

        if self.write_progress is not None:
            self.write_progress(
                path.relative_to(self.workspace).as_posix(),
                content,
            )

        path.write_text(content, encoding="utf-8")

        return path.relative_to(self.workspace).as_posix()

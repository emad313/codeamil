import fnmatch
import os
from pathlib import Path
from typing import TypedDict


class TextMatch(TypedDict):
    file: str
    line: int
    text: str


class WorkspaceSearch:
    """Search text and file names without leaving a project workspace."""

    def __init__(self, workspace: str | Path, ignored_dirs: set[str]) -> None:
        self.workspace = Path(workspace).resolve()
        self.ignored_dirs = ignored_dirs

    def _directory(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("A non-empty relative path is required.")

        directory = (self.workspace / relative_path).resolve()
        if not directory.is_relative_to(self.workspace):
            raise PermissionError(
                "Access denied: path is outside the workspace."
            )
        if not directory.is_dir():
            raise NotADirectoryError(str(directory))
        return directory

    def _files(self, directory: Path):
        for current, directories, filenames in os.walk(
            directory, topdown=True, followlinks=False
        ):
            current_path = Path(current)
            directories[:] = sorted(
                name for name in directories
                if name not in self.ignored_dirs
                and not (current_path / name).is_symlink()
            )
            for filename in sorted(filenames):
                path = current_path / filename
                if path.is_symlink() or any(
                    part in self.ignored_dirs for part in path.parts
                ):
                    continue
                yield path

    def text(
        self,
        query: str,
        relative_path: str = ".",
        max_results: int = 100,
    ) -> list[TextMatch]:
        if not isinstance(query, str) or not query:
            raise ValueError("Search query cannot be empty.")
        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise ValueError("max_results must be an integer.")
        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        results: list[TextMatch] = []
        for path in self._files(self._directory(relative_path)):
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(content.splitlines(), start=1):
                if query.casefold() not in line.casefold():
                    continue
                results.append({
                    "file": path.relative_to(self.workspace).as_posix(),
                    "line": line_number,
                    "text": line.strip(),
                })
                if len(results) >= max_results:
                    return results
        return results

    def files(
        self,
        pattern: str,
        relative_path: str = ".",
        max_results: int = 100,
    ) -> list[str]:
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("File pattern cannot be empty.")
        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise ValueError("max_results must be an integer.")
        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        results: list[str] = []
        for path in self._files(self._directory(relative_path)):
            relative = path.relative_to(self.workspace).as_posix()
            if fnmatch.fnmatchcase(path.name, pattern) or fnmatch.fnmatchcase(
                relative, pattern
            ):
                results.append(relative)
                if len(results) >= max_results:
                    return results
        return results

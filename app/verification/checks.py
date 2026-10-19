
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str = ""
    error: str = ""


@dataclass
class VerificationReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(
            check.passed for check in self.checks
        )


def check_python_syntax(
    workspace: str | Path,
    relative_paths: list[str],
) -> CheckResult:
    """Compile selected Python files without executing them."""
    root = Path(workspace).resolve()

    if not relative_paths:
        return CheckResult(
            name="Python syntax",
            passed=False,
            error="No Python files were supplied.",
        )

    files: list[Path] = []

    for relative_path in relative_paths:
        path = (root / relative_path).resolve()

        if not path.is_relative_to(root):
            return CheckResult(
                name="Python syntax",
                passed=False,
                error=f"Outside-workspace path rejected: {relative_path}",
            )

        if not path.is_file() or path.suffix != ".py":
            return CheckResult(
                name="Python syntax",
                passed=False,
                error=f"Not a Python file: {relative_path}",
            )

        files.append(path)

    try:
        result = subprocess.run(
            [
                __import__("sys").executable,
                "-m",
                "py_compile",
                *[str(path) for path in files],
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="Python syntax",
            passed=False,
            error="Python syntax check timed out after 30 seconds.",
        )
    except OSError as exc:
        return CheckResult(
            name="Python syntax",
            passed=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    return CheckResult(
        name="Python syntax",
        passed=result.returncode == 0,
        output=result.stdout.strip(),
        error=result.stderr.strip(),
    )

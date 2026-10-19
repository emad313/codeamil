
from pathlib import Path
from tempfile import TemporaryDirectory

from app.verification.checks import check_python_syntax


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        # Valid Python should pass.
        (workspace / "valid.py").write_text(
            "def greet():\n    return 'hello'\n",
            encoding="utf-8",
        )
        result = check_python_syntax(workspace, ["valid.py"])
        assert result.passed, result.error
        print("PASS: valid Python syntax accepted")

        # Invalid Python should fail.
        (workspace / "invalid.py").write_text(
            "def broken(:\n    pass\n",
            encoding="utf-8",
        )
        result = check_python_syntax(workspace, ["invalid.py"])
        assert not result.passed
        assert result.error
        print("PASS: invalid Python syntax rejected")

        # Paths outside the workspace must be rejected.
        result = check_python_syntax(workspace, ["../outside.py"])
        assert not result.passed
        assert "Outside-workspace" in result.error
        print("PASS: outside-workspace path rejected")

        # Empty input must fail clearly.
        result = check_python_syntax(workspace, [])
        assert not result.passed
        print("PASS: empty file list rejected")

    print("All verification checks passed.")


if __name__ == "__main__":
    main()

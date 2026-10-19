from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import load_settings
from app.orchestrator import Orchestrator


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        (workspace / "valid.py").write_text(
            "def greet():\n    return 'Hello'\n",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(
            settings=load_settings(),
            workspace=workspace,
        )

        report = orchestrator.run_qa(["valid.py"])

        assert report.passed
        assert len(report.checks) == 1
        print("PASS: orchestrator QA accepts valid Python")

        (workspace / "invalid.py").write_text(
            "def broken(:\n    pass\n",
            encoding="utf-8",
        )

        report = orchestrator.run_qa(["invalid.py"])

        assert not report.passed
        print("PASS: orchestrator QA detects syntax errors")

        report = orchestrator.run_qa(["../outside.py"])

        assert not report.passed
        assert "Outside-workspace" in report.checks[0].error
        print("PASS: orchestrator QA rejects outside-workspace paths")

    print("All orchestrator QA tests passed.")


if __name__ == "__main__":
    main()

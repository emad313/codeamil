
from pathlib import Path
from tempfile import TemporaryDirectory

from app.agents.qa import QAAgent


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)

        (workspace / "valid.py").write_text(
            "def greet():\n    return 'Hello'\n",
            encoding="utf-8",
        )

        agent = QAAgent(workspace)
        report = agent.run_checks(["valid.py"])

        assert report.passed
        assert len(report.checks) == 1
        assert report.checks[0].name == "Python syntax"
        print("PASS: QA agent accepts valid Python")

        (workspace / "invalid.py").write_text(
            "def broken(:\n    pass\n",
            encoding="utf-8",
        )

        report = agent.run_checks(["invalid.py"])

        assert not report.passed
        assert report.checks[0].error
        print("PASS: QA agent detects syntax errors")

        report = agent.run_checks(["../outside.py"])

        assert not report.passed
        assert "Outside-workspace" in report.checks[0].error
        print("PASS: QA agent rejects outside-workspace paths")

    print("All QA agent tests passed.")


if __name__ == "__main__":
    main()

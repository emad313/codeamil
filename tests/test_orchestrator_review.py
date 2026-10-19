
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.config import load_settings
from app.orchestrator import Orchestrator


class MockResponse:
    content = json.dumps({
        "summary": "One issue found.",
        "findings": [
            {
                "severity": "medium",
                "category": "bug",
                "message": "The function has no input validation.",
                "file": "example.py",
                "line": 1,
                "recommendation": "Validate the input.",
            }
        ],
    })


class MockModelRouter:
    def generate(self, messages):
        assert "example.py" in messages[1]["content"]
        assert "def greet" in messages[1]["content"]
        return MockResponse()


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        (workspace / "example.py").write_text(
            "def greet(name):\n    return 'Hello ' + name\n",
            encoding="utf-8",
        )

        with patch(
            "app.orchestrator.ModelRouter",
            return_value=MockModelRouter(),
        ):
            orchestrator = Orchestrator(
                settings=load_settings(),
                workspace=workspace,
            )

        report = orchestrator.review_files(["example.py"])

        assert report.summary == "One issue found."
        assert len(report.findings) == 1
        assert report.findings[0].severity == "medium"

        try:
            orchestrator.review_files(["../outside.py"])
        except ValueError:
            pass
        else:
            raise AssertionError("Outside-workspace review was accepted.")

        print("PASS: workspace file reviewed")
        print("PASS: review report returned")
        print("PASS: outside-workspace path rejected")
        print("All orchestrator review tests passed.")


if __name__ == "__main__":
    main()

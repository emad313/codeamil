
from types import SimpleNamespace

from app.agents.reviewer import CodeReviewer


class MockModelRouter:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, messages: list[dict[str, str]]) -> SimpleNamespace:
        return SimpleNamespace(content=self.response)


def main() -> None:
    router = MockModelRouter(
        """
        {
          "summary": "One security issue found.",
          "findings": [
            {
              "severity": "high",
              "category": "security",
              "message": "User input is used without validation.",
              "file": "app/example.py",
              "line": 12,
              "recommendation": "Validate and sanitize user input."
            }
          ]
        }
        """
    )

    reviewer = CodeReviewer(router)
    report = reviewer.review("12: execute_query(user_input)")

    assert report.summary == "One security issue found."
    assert len(report.findings) == 1
    assert report.findings[0].severity == "high"
    assert report.findings[0].file == "app/example.py"
    assert report.findings[0].line == 12
    assert report.passed is False

    empty_router = MockModelRouter(
        '{"summary": "No issues found.", "findings": []}'
    )
    empty_report = CodeReviewer(empty_router).review(
        "def greet(): return 'hello'"
    )

    assert empty_report.passed is True
    assert empty_report.findings == []

    print("PASS: review findings parsed")
    print("PASS: high-severity issue fails review")
    print("PASS: clean review passes")
    print("All reviewer tests passed.")


if __name__ == "__main__":
    main()

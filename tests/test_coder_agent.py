
import json
from types import SimpleNamespace

from app.agents.coder import CoderAgent


class MockModelRouter:
    def __init__(self, content: str) -> None:
        self.content = content

    def generate(self, messages):
        return SimpleNamespace(content=self.content)


def main() -> None:
    response = json.dumps({
        "file": "example.py",
        "content": "def add(a, b):\n    return a + b\n",
        "explanation": "Implemented the missing addition logic.",
    })

    agent = CoderAgent(MockModelRouter(response))

    change = agent.propose_fix(
        file_path="example.py",
        current_content="def add(a, b):\n    pass\n",
        review_feedback="The function does not return a result.",
    )

    assert change.file == "example.py"
    assert "return a + b" in change.content
    assert change.explanation
    print("PASS: proposed code change parsed")

    wrong_target = json.dumps({
        "file": "../outside.py",
        "content": "print('unexpected')",
        "explanation": "Wrong target.",
    })

    agent = CoderAgent(MockModelRouter(wrong_target))

    try:
        agent.propose_fix(
            file_path="example.py",
            current_content="",
            review_feedback="Fix the file.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Mismatched target file was accepted.")

    print("PASS: mismatched target rejected")

    agent = CoderAgent(MockModelRouter("not valid JSON"))

    try:
        agent.propose_fix(
            file_path="example.py",
            current_content="",
            review_feedback="Fix the file.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid JSON was accepted.")

    print("PASS: invalid model response rejected")
    print("All coder agent tests passed.")


if __name__ == "__main__":
    main()

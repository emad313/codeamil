
import tempfile
from pathlib import Path

from app.agents.coder import CodeChange
from app.agents.reviewer import ReviewFinding, ReviewReport
from app.config import load_settings
from app.orchestrator import Orchestrator



class MockReviewer:
    def review(self, code_context):
        if "return a - b" in code_context:
            return ReviewReport(
                summary="A high-severity issue was found.",
                findings=[
                    ReviewFinding(
                        severity="high",
                        category="bug",
                        message="The function returns the wrong result.",
                        file="example.py",
                        line=2,
                        recommendation="Correct the return expression.",
                    )
                ],
            )

        return ReviewReport(
            summary="No critical or high-severity issues found.",
            findings=[],
        )



class MockCoder:
    def propose_fix(self, **kwargs):
        return CodeChange(
            file="example.py",
            content="def add(a, b):\n    return a + b\n",
            explanation="Corrected the addition function.",
        )


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        target = root / "example.py"
        original = "def add(a, b):\n    return a - b\n"
        target.write_text(original)

        orchestrator = Orchestrator(
            load_settings(),
            workspace=root,
        )

        # Replace both model-dependent agents with mocks.
        from app.agents.review_fix_loop import ReviewFixLoop

        loop = ReviewFixLoop(
            workspace=root,
            model_router=orchestrator.model_router,
            max_cycles=2,
        )
        loop.reviewer = MockReviewer()
        loop.coder = MockCoder()

        # Reject the proposed change.
        rejected = loop.run(
            ["example.py"],
            approve_change=lambda change: False,
        )

        assert rejected.status == "awaiting_approval"
        assert target.read_text() == original
        assert len(rejected.pending_changes) == 1
        print("PASS: rejected change leaves file unchanged")

        # Approve the proposed change.
        approved = loop.run(
            ["example.py"],
            approve_change=lambda change: True,
        )

        assert target.read_text() == (
            "def add(a, b):\n    return a + b\n"
        )
        assert approved.status == "passed"
        print("PASS: approved change is written and verified")

    print("All review-fix approval tests passed.")


if __name__ == "__main__":
    main()

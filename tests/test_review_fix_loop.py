
import tempfile
from pathlib import Path
from types import SimpleNamespace

from app.agents.coder import CodeChange
from app.agents.review_fix_loop import ReviewFixLoop
from app.agents.reviewer import ReviewFinding, ReviewReport
from app.verification.checks import CheckResult, VerificationReport


class MockReviewer:
    def __init__(self, report):
        self.report = report
        self.calls = 0

    def review(self, code_context):
        self.calls += 1
        return self.report


class MockCoder:
    def __init__(self, change):
        self.change = change
        self.calls = 0

    def propose_fix(self, **kwargs):
        self.calls += 1
        return self.change


class MockQA:
    def __init__(self, passed=True):
        self.passed = passed

    def run_checks(self, python_files):
        return VerificationReport(checks=[
            CheckResult(
                name="Mock QA",
                passed=self.passed,
                error="" if self.passed else "Mock failure",
            )
        ])


def failing_review():
    return ReviewReport(
        summary="A critical issue was found.",
        findings=[
            ReviewFinding(
                severity="high",
                category="bug",
                message="The function needs a fix.",
                file="example.py",
                recommendation="Return the correct result.",
            )
        ],
    )


def passing_review():
    return ReviewReport(
        summary="No critical or high-severity issues found.",
        findings=[],
    )


def make_loop(directory, review, change, qa_passed=True, max_cycles=2):
    loop = ReviewFixLoop(
        workspace=directory,
        model_router=object(),
        max_cycles=max_cycles,
    )
    loop.reviewer = MockReviewer(review)
    loop.coder = MockCoder(change)
    loop.qa = MockQA(qa_passed)
    return loop


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        target = root / "example.py"
        target.write_text("def add(a, b):\n    return a + b\n")

        # 1. Passing review and QA should finish without changes.
        loop = make_loop(
            root,
            passing_review(),
            CodeChange("example.py", "unused", "unused"),
        )
        report = loop.run(["example.py"])

        assert report.status == "passed"
        assert report.qa_passed
        assert report.cycles == 0
        assert loop.coder.calls == 0
        print("PASS: clean review and QA finish immediately")

        # 2. Without explicit approval, changes must remain pending.
        original = target.read_text()
        loop = make_loop(
            root,
            failing_review(),
            CodeChange(
                "example.py",
                "def add(a, b):\n    return a - b\n",
                "Proposed change",
            ),
        )
        report = loop.run(["example.py"])

        assert report.status == "awaiting_approval"
        assert len(report.pending_changes) == 1
        assert target.read_text() == original
        print("PASS: unapproved changes are not written")

        # 3. A mismatched target must be rejected.
        loop = make_loop(
            root,
            failing_review(),
            CodeChange(
                "../outside.py",
                "print('unexpected')",
                "Wrong target",
            ),
        )

        try:
            loop.run(
                ["example.py"],
                approve_change=lambda change: True,
            )
        except ValueError as exc:
            assert "target mismatch" in str(exc).lower()
        else:
            raise AssertionError("Mismatched target was accepted.")

        assert target.read_text() == original
        print("PASS: mismatched target rejected")

        # 4. The fix loop must respect its configured cycle limit.
        loop = make_loop(
            root,
            failing_review(),
            CodeChange(
                "example.py",
                original,
                "No effective change",
            ),
            max_cycles=2,
        )
        report = loop.run(
            ["example.py"],
            approve_change=lambda change: True,
        )

        assert report.status == "limit_reached"
        assert report.cycles == 2
        assert loop.coder.calls == 2
        assert loop.reviewer.calls == 3
        print("PASS: review-fix cycle limit enforced")

        # 5. Reject workspace traversal.
        try:
            loop.run(["../outside.py"])
        except ValueError:
            pass
        else:
            raise AssertionError("Outside-workspace path was accepted.")

        print("PASS: outside-workspace file rejected")

    print("All review-fix loop tests passed.")


if __name__ == "__main__":
    main()

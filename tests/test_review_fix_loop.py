
import tempfile
from pathlib import Path

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

    def propose_fix(self, file_path, current_content, review_feedback):
        self.calls += 1
        return self.change



class MockQA:
    def __init__(self, passed=True):
        self.passed = passed

    def run_checks(self, relative_paths):
        check = CheckResult(
            name="mock_check",
            passed=self.passed,
            error="" if self.passed else "Mock check failed",
        )
        return VerificationReport(checks=[check])



def make_finding(severity="high"):
    return ReviewFinding(
        file="example.py",
        severity=severity,
        category="test",
        message=f"{severity} test finding",
        recommendation="Fix the test finding",
    )


def failing_review():
    return ReviewReport(
        summary="High-severity issue found",
        findings=[make_finding("high")],
    )


def medium_review():
    return ReviewReport(
        summary="Medium-severity issue found",
        findings=[make_finding("medium")],
    )


def critical_review():
    return ReviewReport(
        summary="Critical issue found",
        findings=[make_finding("critical")],
    )


def passing_review():
    return ReviewReport(
        summary="No issues found",
        findings=[],
    )


def make_loop(
    directory,
    review,
    change=None,
    qa_passed=True,
    max_cycles=2,
    min_severity="high",
):
    loop = ReviewFixLoop(
        workspace=directory,
        model_router=None,
        max_cycles=max_cycles,
        min_severity=min_severity,
    )
    loop.reviewer = MockReviewer(review)
    loop.coder = MockCoder(
        change or CodeChange(
            file="example.py",
            content="print('fixed')\n",
            explanation="Mock fix",
        )
    )
    loop.qa = MockQA(qa_passed)
    return loop


def test_clean_review_finishes_immediately():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        loop = make_loop(directory, passing_review())
        report = loop.run(["example.py"])

        assert report.status == "passed"
        assert report.cycles == 0
        assert loop.coder.calls == 0
        print("PASS: clean review and QA finish immediately")


def test_unapproved_changes_are_not_written():
    with tempfile.TemporaryDirectory() as directory:
        file_path = Path(directory, "example.py")
        original = "print('original')\n"
        file_path.write_text(original, encoding="utf-8")

        loop = make_loop(directory, failing_review())
        report = loop.run(["example.py"])

        assert report.status == "awaiting_approval"
        assert file_path.read_text(encoding="utf-8") == original
        assert len(report.pending_changes) == 1
        print("PASS: unapproved changes are not written")


def test_mismatched_target_rejected():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        bad_change = CodeChange(
            file="../outside.py",
            content="malicious change",
            explanation="Invalid target",
        )
        loop = make_loop(
            directory,
            failing_review(),
            change=bad_change,
        )

        try:
            loop.run(["example.py"], approve_change=lambda change: True)
        except ValueError as exc:
            assert "target mismatch" in str(exc).lower()
        else:
            raise AssertionError("Expected target mismatch rejection")

        print("PASS: mismatched target rejected")


def test_cycle_limit_enforced():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        loop = make_loop(
            directory,
            failing_review(),
            max_cycles=1,
        )
        report = loop.run(
            ["example.py"],
            approve_change=lambda change: True,
        )

        assert report.status == "limit_reached"
        assert report.cycles == 1
        print("PASS: review-fix cycle limit enforced")


def test_outside_workspace_file_rejected():
    with tempfile.TemporaryDirectory() as directory:
        loop = make_loop(directory, passing_review())

        try:
            loop.run(["../outside.py"])
        except ValueError:
            pass
        else:
            raise AssertionError("Expected outside-workspace rejection")

        print("PASS: outside-workspace file rejected")


def test_medium_findings_ignored_at_high_threshold():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        loop = make_loop(
            directory,
            medium_review(),
            min_severity="high",
        )
        report = loop.run(["example.py"])

        assert report.status == "passed"
        assert loop.coder.calls == 0
        print("PASS: medium findings ignored at high threshold")


def test_medium_findings_trigger_proposal_at_medium_threshold():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        loop = make_loop(
            directory,
            medium_review(),
            min_severity="medium",
        )
        report = loop.run(["example.py"])

        assert report.status == "awaiting_approval"
        assert loop.coder.calls == 1
        assert len(report.pending_changes) == 1
        print("PASS: medium findings trigger proposal at medium threshold")


def test_critical_findings_trigger_proposal_at_critical_threshold():
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "example.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        loop = make_loop(
            directory,
            critical_review(),
            min_severity="critical",
        )
        report = loop.run(["example.py"])

        assert report.status == "awaiting_approval"
        assert loop.coder.calls == 1
        print("PASS: critical findings trigger proposal at critical threshold")


def test_invalid_severity_threshold_rejected():
    with tempfile.TemporaryDirectory() as directory:
        try:
            make_loop(
                directory,
                passing_review(),
                min_severity="urgent",
            )
        except ValueError as exc:
            assert "min_severity" in str(exc)
        else:
            raise AssertionError("Expected invalid threshold rejection")

        print("PASS: invalid severity threshold rejected")


def run_all_tests():
    test_clean_review_finishes_immediately()
    test_unapproved_changes_are_not_written()
    test_mismatched_target_rejected()
    test_cycle_limit_enforced()
    test_outside_workspace_file_rejected()
    test_medium_findings_ignored_at_high_threshold()
    test_medium_findings_trigger_proposal_at_medium_threshold()
    test_critical_findings_trigger_proposal_at_critical_threshold()
    test_invalid_severity_threshold_rejected()
    print("All review-fix loop tests passed.")


if __name__ == "__main__":
    run_all_tests()

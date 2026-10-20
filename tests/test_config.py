import os
from unittest.mock import patch

from app.config import load_settings


def load_with_env(**overrides):
    env = {
        "MODEL_PROVIDER": "gemini",
        "MODEL_ID": "test-model",
        "REVIEW_FIX_MIN_SEVERITY": "high",
    }
    env.update(overrides)

    with patch.dict(os.environ, env, clear=True):
        return load_settings()


def test_default_severity_is_high():
    settings = load_with_env()
    assert settings.review_fix_min_severity == "high"
    print("PASS: default severity is high")


def test_valid_severity_values():
    for severity in ("critical", "high", "medium", "low", "info"):
        settings = load_with_env(
            REVIEW_FIX_MIN_SEVERITY=severity
        )
        assert settings.review_fix_min_severity == severity

    print("PASS: all valid severity values accepted")


def test_severity_is_normalized():
    settings = load_with_env(
        REVIEW_FIX_MIN_SEVERITY="  MEDIUM  "
    )
    assert settings.review_fix_min_severity == "medium"
    print("PASS: severity is normalized")


def test_invalid_severity_rejected():
    try:
        load_with_env(REVIEW_FIX_MIN_SEVERITY="urgent")
    except ValueError as exc:
        assert "REVIEW_FIX_MIN_SEVERITY" in str(exc)
    else:
        raise AssertionError("Invalid severity was accepted")

    print("PASS: invalid severity rejected")


def test_missing_model_id_rejected():
    try:
        load_with_env(MODEL_ID="")
    except ValueError as exc:
        assert "MODEL_ID" in str(exc)
    else:
        raise AssertionError("Missing MODEL_ID was accepted")

    print("PASS: missing MODEL_ID rejected")


def test_command_approval_defaults_to_enabled():
    settings = load_with_env()
    assert settings.require_approval_for_commands is True
    print("PASS: command approval defaults to enabled")


def test_command_approval_can_be_disabled():
    settings = load_with_env(REQUIRE_APPROVAL_FOR_COMMANDS="false")
    assert settings.require_approval_for_commands is False
    print("PASS: command approval can be disabled")


def test_command_approval_is_case_insensitive():
    settings = load_with_env(REQUIRE_APPROVAL_FOR_COMMANDS=" TRUE ")
    assert settings.require_approval_for_commands is True
    print("PASS: command approval setting accepts normalized true")


def test_file_change_approval_defaults_to_enabled():
    settings = load_with_env()
    assert settings.require_approval_for_file_changes is True
    print("PASS: file change approval defaults to enabled")


def test_invalid_command_approval_rejected():
    try:
        load_with_env(REQUIRE_APPROVAL_FOR_COMMANDS="sometimes")
    except ValueError as exc:
        assert "REQUIRE_APPROVAL_FOR_COMMANDS" in str(exc)
    else:
        raise AssertionError("Invalid command approval was accepted")


def test_invalid_file_change_approval_rejected():
    try:
        load_with_env(REQUIRE_APPROVAL_FOR_FILE_CHANGES="sometimes")
    except ValueError as exc:
        assert "REQUIRE_APPROVAL_FOR_FILE_CHANGES" in str(exc)
    else:
        raise AssertionError("Invalid file approval was accepted")



if __name__ == "__main__":
    test_default_severity_is_high()
    test_valid_severity_values()
    test_severity_is_normalized()
    test_invalid_severity_rejected()
    test_missing_model_id_rejected()
    test_command_approval_defaults_to_enabled()
    test_command_approval_can_be_disabled()
    test_command_approval_is_case_insensitive()
    test_file_change_approval_defaults_to_enabled()
    test_invalid_command_approval_rejected()
    test_invalid_file_change_approval_rejected()
    print("All configuration tests passed.")

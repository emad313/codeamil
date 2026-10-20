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


if __name__ == "__main__":
    test_default_severity_is_high()
    test_valid_severity_values()
    test_severity_is_normalized()
    test_invalid_severity_rejected()
    test_missing_model_id_rejected()
    print("All configuration tests passed.")

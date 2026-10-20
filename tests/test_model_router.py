from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.config import Settings
from app.model_router import ModelRouter
from app.providers.base import ModelResponse


def settings() -> Settings:
    return Settings(
        model_provider="openai",
        model_id="test-model",
        openai_api_key="secret-key",
        openrouter_api_key="",
        gemini_api_key="",
        max_agent_iterations=2,
        max_review_fix_cycles=1,
        require_approval_for_commands=True,
        require_approval_for_file_changes=True,
        review_fix_min_severity="high",
    )


def test_empty_provider_response_is_reported():
    with patch("app.model_router.OpenAIProvider") as provider_class:
        router = ModelRouter(settings())
        router.provider = SimpleNamespace(
            generate=lambda messages: ModelResponse(
                content="",
                provider="openai",
                model="test-model",
            )
        )

    with pytest.raises(RuntimeError, match="empty response"):
        router.generate([])


def test_provider_error_redacts_configured_key():
    with patch("app.model_router.OpenAIProvider"):
        router = ModelRouter(settings())
        router.provider = SimpleNamespace(
            generate=lambda messages: (_ for _ in ()).throw(
                RuntimeError("request failed with secret-key")
            )
        )

    with pytest.raises(RuntimeError) as error:
        router.generate([])

    assert "secret-key" not in str(error.value)
    assert "[REDACTED]" in str(error.value)

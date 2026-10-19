
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model_provider: str
    model_id: str

    openai_api_key: str
    openrouter_api_key: str
    gemini_api_key: str

    max_agent_iterations: int
    max_review_fix_cycles: int
    require_approval_for_commands: bool
    review_fix_min_severity: str


def load_settings() -> Settings:
    provider = os.getenv("MODEL_PROVIDER", "gemini").strip().lower()

    supported_providers = {"openai", "openrouter", "gemini"}

    if provider not in supported_providers:
        raise ValueError(
            f"Unsupported MODEL_PROVIDER: {provider}"
        )

    model_id = os.getenv("MODEL_ID", "").strip()

    if not model_id:
        raise ValueError("MODEL_ID must be configured in .env")

    min_severity = os.getenv(
        "REVIEW_FIX_MIN_SEVERITY", "high"
    ).strip().lower()

    allowed_severities = {"critical", "high", "medium", "low", "info"}

    if min_severity not in allowed_severities:
        raise ValueError(
            "REVIEW_FIX_MIN_SEVERITY must be one of: "
            "critical, high, medium, low, info"
        )

    return Settings(
        model_provider=provider,
        model_id=model_id,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        max_agent_iterations=int(
            os.getenv("MAX_AGENT_ITERATIONS", "12")
        ),
        max_review_fix_cycles=int(
            os.getenv("MAX_REVIEW_FIX_CYCLES", "3")
        ),
        require_approval_for_commands=(
            os.getenv(
                "REQUIRE_APPROVAL_FOR_COMMANDS", "true"
            ).strip().lower() == "true"
        ),
        review_fix_min_severity=min_severity,
    )


def validate_active_provider(settings: Settings) -> None:
    key_by_provider = {
        "openai": settings.openai_api_key,
        "openrouter": settings.openrouter_api_key,
        "gemini": settings.gemini_api_key,
    }

    if not key_by_provider[settings.model_provider]:
        raise ValueError(
            f"Missing API key for {settings.model_provider}. "
            "Check your .env file."
        )

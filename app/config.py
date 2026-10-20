
import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


def load_environment() -> None:
    """Load global defaults and project overrides without replacing OS values."""
    user_env = Path.home() / ".codeamil" / ".env"
    project_env = Path.cwd() / ".env"

    original_environment = os.environ.copy()

    if user_env.is_file():
        load_dotenv(user_env, override=True)

    if project_env.is_file():
        load_dotenv(project_env, override=True)

    for key, value in original_environment.items():
        os.environ[key] = value


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
    load_environment()

    provider = os.getenv("MODEL_PROVIDER", "gemini").strip().lower()
    supported_providers = {"openai", "openrouter", "gemini"}

    if provider not in supported_providers:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")

    model_id = os.getenv("MODEL_ID", "").strip()
    if not model_id:
        raise ValueError("MODEL_ID must be configured. Run 'codeamil config'.")

    min_severity = os.getenv("REVIEW_FIX_MIN_SEVERITY", "high").strip().lower()
    allowed_severities = {"critical", "high", "medium", "low", "info"}

    if min_severity not in allowed_severities:
        raise ValueError(
            "REVIEW_FIX_MIN_SEVERITY must be one of: "
            "critical, high, medium, low, info"
        )

    try:
        max_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "12"))
        max_cycles = int(os.getenv("MAX_REVIEW_FIX_CYCLES", "3"))
    except ValueError as exc:
        raise ValueError(
            "MAX_AGENT_ITERATIONS and MAX_REVIEW_FIX_CYCLES must be integers."
        ) from exc

    if max_iterations < 1 or max_cycles < 1:
        raise ValueError("Iteration and review-fix limits must be at least 1.")

    return Settings(
        model_provider=provider,
        model_id=model_id,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        max_agent_iterations=max_iterations,
        max_review_fix_cycles=max_cycles,
        require_approval_for_commands=(
            os.getenv("REQUIRE_APPROVAL_FOR_COMMANDS", "true").strip().lower()
            in {"true", "1", "yes", "on"}
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
            "Run 'codeamil config' or set the corresponding environment variable."
        )

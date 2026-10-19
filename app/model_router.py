from app.config import Settings
from app.providers.base import ModelProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.gemini_provider import GeminiProvider
import time


class ModelRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        providers: dict[str, type] = {
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider,
        }

        provider_class = providers[settings.model_provider]
        self.provider: ModelProvider = provider_class(settings)

    def generate(self, messages: list[dict[str, str]]):
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                return self.provider.generate(messages)

            except Exception as exc:
                error_text = str(exc).upper()

                retryable = any(
                    marker in error_text
                    for marker in (
                        "429",
                        "500",
                        "502",
                        "503",
                        "504",
                        "UNAVAILABLE",
                        "RESOURCE_EXHAUSTED",
                        "TIMEOUT",
                        "TIMED OUT",
                    )
                )

                if not retryable or attempt == max_attempts:
                    raise RuntimeError(
                        f"Model request failed "
                        f"(provider={self.settings.model_provider}, "
                        f"model={self.settings.model_id}): "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc

                delay = 2 ** attempt
                print(
                    f"Temporary provider error. Retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_attempts})..."
                )
                time.sleep(delay)

        raise RuntimeError("Model request failed after retries.")
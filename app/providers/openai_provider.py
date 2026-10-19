from openai import OpenAI

from app.config import Settings
from app.providers.base import ModelResponse


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=60.0,
            max_retries=2,
        )

    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        response = self.client.chat.completions.create(
            model=self.settings.model_id,
            messages=messages,
        )

        choice = response.choices[0]
        usage = response.usage

        return ModelResponse(
            content=choice.message.content or "",
            provider="openai",
            model=response.model,
            usage={
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason,
        )

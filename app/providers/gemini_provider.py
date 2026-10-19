from google import genai
from google.genai import types

from app.config import Settings
from app.providers.base import ModelResponse


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
            timeout=30000,
            ),
        )

    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        system_parts = [
            message["content"]
            for message in messages
            if message["role"] == "system"
        ]

        contents = [
            {
                "role": (
                    "model"
                    if message["role"] == "assistant"
                    else "user"
                ),
                "parts": [{"text": message["content"]}],
            }
            for message in messages
            if message["role"] in {"user", "assistant"}
        ]

        response = self.client.models.generate_content(
            model=self.settings.model_id,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="\n\n".join(system_parts)
                if system_parts else None,
            ),
        )

        metadata = response.usage_metadata

        return ModelResponse(
            content=response.text or "",
            provider="gemini",
            model=self.settings.model_id,
            usage={
                "input_tokens": (
                    metadata.prompt_token_count
                    if metadata else 0
                ),
                "output_tokens": (
                    metadata.candidates_token_count
                    if metadata else 0
                ),
                "total_tokens": (
                    metadata.total_token_count
                    if metadata else 0
                ),
            },
            finish_reason=(
                str(response.candidates[0].finish_reason)
                if response.candidates else None
            ),
        )

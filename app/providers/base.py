from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None


class ModelProvider(Protocol):
    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> ModelResponse:
        ...

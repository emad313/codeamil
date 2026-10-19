
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentAction:
    kind: str
    name: str = ""
    arguments: dict[str, Any] | None = None
    content: str = ""


def parse_model_action(response: str) -> AgentAction:
    """Parse the model's JSON response into a tool call or final answer."""

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The model response is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("The model response must be a JSON object.")

    if "final_answer" in data:
        answer = data["final_answer"]

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("final_answer must be a non-empty string.")

        return AgentAction(
            kind="final",
            content=answer.strip(),
        )

    if "tool_call" in data:
        call = data["tool_call"]

        if not isinstance(call, dict):
            raise ValueError("tool_call must be a JSON object.")

        name = call.get("name")
        arguments = call.get("arguments", {})

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool name must be a non-empty string.")

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        return AgentAction(
            kind="tool",
            name=name,
            arguments=arguments,
        )

    raise ValueError(
        "Expected either 'tool_call' or 'final_answer'."
    )

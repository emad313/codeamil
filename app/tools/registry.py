
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.tools.execution import CommandExecutor
from app.tools.filesystem import WorkspaceFileSystem


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool name must be a non-empty string.")

        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        if not callable(handler):
            raise ValueError("Tool handler must be callable.")

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return registered tool definitions."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        """Check a value against a supported JSON Schema type."""
        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)

        if expected_type == "number":
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        if expected_type == "boolean":
            return isinstance(value, bool)

        if expected_type == "array":
            return isinstance(value, list)

        if expected_type == "object":
            return isinstance(value, dict)

        if expected_type == "null":
            return value is None

        # Do not silently accept unsupported schema types.
        return False

    @classmethod
    def _validate_value(
        cls,
        value: Any,
        schema: dict[str, Any],
        argument_name: str,
    ) -> str | None:
        """Return a validation error, or None when the value is valid."""
        expected_type = schema.get("type")

        if isinstance(expected_type, str):
            if not cls._matches_type(value, expected_type):
                return (
                    f"Argument '{argument_name}' must be of type "
                    f"{expected_type}."
                )

        elif isinstance(expected_type, list):
            if not expected_type or not any(
                isinstance(item, str)
                and cls._matches_type(value, item)
                for item in expected_type
            ):
                return (
                    f"Argument '{argument_name}' does not match "
                    "any permitted type."
                )

        if "enum" in schema and value not in schema["enum"]:
            return (
                f"Argument '{argument_name}' must be one of "
                f"{schema['enum']}."
            )

        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                return (
                    f"Argument '{argument_name}' is shorter than "
                    "the minimum allowed length."
                )

            max_length = schema.get("maxLength")
            if max_length is not None and len(value) > max_length:
                return (
                    f"Argument '{argument_name}' exceeds the "
                    "maximum allowed length."
                )

        if isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                return (
                    f"Argument '{argument_name}' has too few items."
                )

            max_items = schema.get("maxItems")
            if max_items is not None and len(value) > max_items:
                return (
                    f"Argument '{argument_name}' has too many items."
                )

            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(value):
                    error = cls._validate_value(
                        item,
                        item_schema,
                        f"{argument_name}[{index}]",
                    )
                    if error:
                        return error

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")

            if minimum is not None and value < minimum:
                return (
                    f"Argument '{argument_name}' must be at least "
                    f"{minimum}."
                )

            if maximum is not None and value > maximum:
                return (
                    f"Argument '{argument_name}' must be at most "
                    f"{maximum}."
                )

        return None

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate arguments and execute a registered tool safely."""
        tool = self._tools.get(name)

        if tool is None:
            return {
                "ok": False,
                "error": f"Unknown tool: {name}",
            }

        if not isinstance(arguments, dict):
            return {
                "ok": False,
                "error": "Tool arguments must be an object.",
            }

        properties = tool.parameters.get("properties", {})
        required = tool.parameters.get("required", [])

        if not isinstance(properties, dict):
            return {
                "ok": False,
                "error": "Tool definition has invalid properties.",
            }

        if not isinstance(required, list):
            return {
                "ok": False,
                "error": "Tool definition has an invalid required list.",
            }

        if not all(isinstance(key, str) for key in arguments):
            return {
                "ok": False,
                "error": "All argument names must be strings.",
            }

        unknown = set(arguments) - set(properties)

        if unknown and tool.parameters.get("additionalProperties") is False:
            return {
                "ok": False,
                "error": f"Unexpected arguments: {sorted(unknown)}",
            }

        missing = set(required) - set(arguments)

        if missing:
            return {
                "ok": False,
                "error": f"Missing arguments: {sorted(missing)}",
            }

        for argument_name, value in arguments.items():
            schema = properties.get(argument_name)

            if not isinstance(schema, dict):
                continue

            error = self._validate_value(
                value,
                schema,
                argument_name,
            )

            if error:
                return {
                    "ok": False,
                    "error": error,
                }

        try:
            result = tool.handler(**arguments)

            # CommandExecutor already returns its own structured result.
            if name == "run_command" and isinstance(result, dict):
                return result

            return {
                "ok": True,
                "result": result,
            }

        except Exception as exc:
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }


def create_filesystem_registry(
    workspace: str | Path,
    command_executor: CommandExecutor | None = None,
    write_progress: Callable[[str, str], None] | None = None,
) -> ToolRegistry:
    """Create the filesystem registry with optional command execution."""
    fs = WorkspaceFileSystem(workspace, write_progress=write_progress)
    registry = ToolRegistry()

    registry.register(
        name="list_files",
        description="List files within the selected project directory.",
        parameters={
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
                "max_files": {"type": "integer"},
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=fs.list_files,
    )

    registry.register(
        name="read_file",
        description="Read a UTF-8 text file in the selected project.",
        parameters={
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
            },
            "required": ["relative_path"],
            "additionalProperties": False,
        },
        handler=fs.read_file,
    )

    registry.register(
        name="search_text",
        description="Search file contents within the selected project.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "relative_path": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        handler=fs.search_text,
    )

    registry.register(
        name="search_files",
        description="Find project files by name or relative path pattern.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "relative_path": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
        handler=fs.search.files,
    )

    registry.register(
        name="write_file",
        description="Create or overwrite a UTF-8 text file in the project.",
        parameters={
            "type": "object",
            "properties": {
                "relative_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["relative_path", "content"],
            "additionalProperties": False,
        },
        handler=fs.write_file,
    )

    if command_executor is not None:
        registry.register(
            name="run_command",
            description=(
                "Execute a command in the project workspace. "
                "Commands may require explicit user approval."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            handler=lambda command: command_executor.execute(command),
        )

    return registry


from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
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
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for future model integration."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
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

        unknown = set(arguments) - set(properties)
        if unknown:
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

        try:
            result = tool.handler(**arguments)
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
) -> ToolRegistry:
    fs = WorkspaceFileSystem(workspace)
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

    return registry

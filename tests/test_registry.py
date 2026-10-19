
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tools.filesystem import WorkspaceFileSystem
from app.tools.registry import ToolRegistry


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        fs = WorkspaceFileSystem(workspace)

        fs.write_file("hello.py", "print('Hello CodeAmil')\n")

        registry = ToolRegistry()

        registry.register(
            name="list_files",
            description="List files in the selected project directory.",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            },
            handler=fs.list_files,
        )

        registry.register(
            name="read_file",
            description="Read a text file from the selected project.",
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

        print("--- Available Tools ---")
        for tool in registry.list_tools():
            print(tool["name"])

        print("\n--- List Files ---")
        print(registry.execute("list_files", {}))

        print("\n--- Read File ---")
        print(
            registry.execute(
                "read_file",
                {"relative_path": "hello.py"},
            )
        )

        print("\n--- Unknown Tool Test ---")
        print(registry.execute("delete_everything", {}))

        print("\n--- Invalid Argument Test ---")
        print(
            registry.execute(
                "read_file",
                {"unexpected": "value"},
            )
        )


if __name__ == "__main__":
    main()

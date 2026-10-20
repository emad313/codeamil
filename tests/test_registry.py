
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tools.filesystem import WorkspaceFileSystem
from app.tools.registry import ToolRegistry


def test_argument_type_validation() -> None:
    registry = ToolRegistry()
    calls = []

    registry.register(
        name="example",
        description="Test argument validation.",
        parameters={
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["count", "labels"],
            "additionalProperties": False,
        },
        handler=lambda count, labels: calls.append((count, labels))
        or {"count": count, "labels": labels},
    )

    assert registry.execute(
        "example",
        {"count": "5", "labels": ["valid"]},
    )["ok"] is False

    assert registry.execute(
        "example",
        {"count": True, "labels": ["valid"]},
    )["ok"] is False

    assert registry.execute(
        "example",
        {"count": 5, "labels": [123]},
    )["ok"] is False

    assert registry.execute(
        "example",
        {"count": 5, "labels": []},
    )["ok"] is False

    assert registry.execute(
        "example",
        {"labels": ["valid"]},
    )["ok"] is False

    assert calls == []

    result = registry.execute(
        "example",
        {"count": 5, "labels": ["valid"]},
    )

    assert result == {
        "ok": True,
        "result": {"count": 5, "labels": ["valid"]},
    }
    assert calls == [(5, ["valid"])]

    print("PASS: invalid argument types are rejected")
    print("PASS: invalid array items and empty arrays are rejected")
    print("PASS: missing required arguments are rejected")
    print("PASS: invalid arguments never reach the handler")
    print("PASS: valid arguments execute successfully")


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
        unknown = registry.execute("delete_everything", {})
        print(unknown)
        assert unknown["ok"] is False

        print("\n--- Invalid Argument Test ---")
        invalid = registry.execute(
            "read_file",
            {"unexpected": "value"},
        )
        print(invalid)
        assert invalid["ok"] is False

    test_argument_type_validation()
    print("\nAll registry tests passed.")


if __name__ == "__main__":
    main()

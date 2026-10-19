
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tools.registry import create_filesystem_registry


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        registry = create_filesystem_registry(Path(temp_dir))

        print("Available tools:")
        for tool in registry.list_tools():
            print(f"- {tool['name']}")

        print("\nCreate file:")
        print(
            registry.execute(
                "write_file",
                {
                    "relative_path": "src/app.py",
                    "content": "print('Hello from CodeAmil')\n",
                },
            )
        )

        print("\nSearch file:")
        print(
            registry.execute(
                "search_text",
                {"query": "Hello"},
            )
        )

        print("\nAll registry integration tests completed.")


if __name__ == "__main__":
    main()

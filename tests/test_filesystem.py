
from pathlib import Path
from tempfile import TemporaryDirectory

from app.tools.filesystem import WorkspaceFileSystem


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        fs = WorkspaceFileSystem(workspace)

        # Create a file.
        fs.write_file(
            "src/example.py",
            "def greet():\n    return 'Hello, world!'\n",
        )

        # List files.
        print("\n--- Files ---")
        print(fs.list_files())

        # Read a file.
        print("\n--- File Content ---")
        print(fs.read_file("src/example.py"))

        # Search source code.
        print("\n--- Search Results ---")
        print(fs.search_text("greet"))

        # Verify workspace protection.
        print("\n--- Security Test ---")
        try:
            fs.read_file("../outside.txt")
        except PermissionError:
            print("PASS: outside-workspace access blocked")
        else:
            raise AssertionError(
                "Workspace protection failed."
            )

        try:
            fs.list_files(max_files=0)
        except ValueError:
            print("PASS: invalid file limits are rejected")
        else:
            raise AssertionError("Invalid file limit was accepted")

        print("\nAll filesystem tests passed.")


if __name__ == "__main__":
    main()

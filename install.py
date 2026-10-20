
import os
import site
import subprocess
import sys
import sysconfig
from pathlib import Path

REPO_URL = "git+https://github.com/emad313/codeamil.git"


def get_base_python() -> Path:
    """Use the base interpreter even when running inside a virtual environment."""
    return Path(getattr(sys, "_base_executable", sys.executable)).resolve()


def get_user_scripts(python: Path) -> Path:
    """Ask the selected interpreter for its user-level scripts directory."""
    result = subprocess.check_output(
        [
            str(python),
            "-c",
            (
                "import os, site, sysconfig; "
                "print(sysconfig.get_path('scripts', "
                "scheme='nt_user' if os.name == 'nt' else 'posix_user'))"
            ),
        ],
        text=True,
    ).strip()

    scripts = Path(result)
    if os.name == "nt" and scripts.name.lower() != "scripts":
        scripts = Path(site.getuserbase()) / "Scripts"

    return scripts


def install_codeamil(
    python: Path,
    scripts: Path,
    source: Path | None = None,
) -> None:
    """Install CodeAmil into the selected interpreter's user environment."""
    package_source = str(source) if source and (source / "pyproject.toml").is_file() else REPO_URL
    subprocess.check_call(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--user",
            "--upgrade",
            "--no-warn-script-location",
            package_source,
        ]
    )

    executable = "codeamil.exe" if os.name == "nt" else "codeamil"
    if not (scripts / executable).is_file():
        raise RuntimeError(
            f"Installation completed, but {scripts / executable} was not found."
        )


def configure_path(scripts: Path) -> None:
    """Add the user Scripts directory to PATH persistently."""
    entry = str(scripts.resolve())

    if os.name == "nt":
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            try:
                current, kind = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current, kind = "", winreg.REG_EXPAND_SZ

            entries = [part.strip() for part in current.split(";") if part.strip()]
            if not any(part.casefold() == entry.casefold() for part in entries):
                entries.append(entry)
                winreg.SetValueEx(key, "Path", 0, kind, ";".join(entries))

        print("User PATH updated. Restart your terminal to apply it.")
        return

    shell = Path(os.environ.get("SHELL", "")).name
    home = Path.home()

    if shell == "fish":
        profile = home / ".config" / "fish" / "config.fish"
        line = f"fish_add_path {entry!r}"
    elif shell == "zsh":
        profile = home / ".zshrc"
        line = f'export PATH="{entry}:$PATH"'
    else:
        profile = home / ".profile"
        line = f'export PATH="{entry}:$PATH"'

    profile.parent.mkdir(parents=True, exist_ok=True)
    content = profile.read_text(encoding="utf-8") if profile.exists() else ""

    if line not in content:
        with profile.open("a", encoding="utf-8") as file:
            file.write(f"\n# CodeAmil CLI\n{line}\n")

    print(f"PATH updated in {profile}. Restart your terminal to apply it.")


def main() -> None:
    python = get_base_python()
    scripts = get_user_scripts(python)
    source = Path(__file__).resolve().parent

    print(f"Installing CodeAmil for the current user using {python}...")
    install_codeamil(python, scripts, source=source)
    configure_path(scripts)

    print(f"Installation finished. Command directory: {scripts}")


if __name__ == "__main__":
    main()

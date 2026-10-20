# CodeAmil

CodeAmil is a Python-based AI coding agent that can inspect, modify, review, and verify code in your current project directory.

## Features

- Supports Gemini, OpenAI, and OpenRouter.
- Reads and edits project files using registered tools.
- Reviews code and proposes fixes.
- Runs supported verification checks.
- Requires approval for commands that need approval by default.
- Uses the current working directory as the project workspace.

## Requirements

- Python 3.10 or newer.
- Git.
- An API key for your selected model provider.

## Installation

### Requirements
- Python 3.10 or newer
- pip

### Windows, macOS, and Linux

Clone the repository and run the installer:

```bash
git clone https://github.com/emad313/codeamil.git
cd codeamil
python install.py
```

The installer installs CodeAmil for the current user and configures the command-line path where supported. Restart your terminal after installation.

Verify the installation:

```bash
codeamil --version
```

### Configure CodeAmil

Run the configuration command to set your AI provider, model, and API key:

```bash
codeamil config
```

### Use CodeAmil in any project

Navigate to the project directory you want CodeAmil to work in, then run:

```bash
cd /path/to/your/project
codeamil
```

CodeAmil uses your current working directory as the workspace.

## Configuration

Run the interactive configuration command:

```bash
codeamil config
```

Choose your provider and model, then enter your API key. Configuration is saved in `~/.codeamil/.env` under your user home directory.

You can also configure a project-specific `.env` file. Never commit API keys or other secrets.

## Usage

Navigate to any project directory before running CodeAmil:

```bash
cd /path/to/your-project
codeamil "Explain this project's structure"
codeamil "Fix the bug in the login flow"
codeamil "Add user authentication"
```

CodeAmil uses the current working directory as its workspace.

## Review and Fix

Review selected files and propose fixes:

```bash
codeamil --review-fix app/main.py app/config.py
```

Review proposed changes carefully before approving them.

## Useful Commands

```bash
codeamil --help
codeamil --version
codeamil config
```

## Development Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/emad313/codeamil.git
cd codeamil
python -m venv .venv
python -m pip install -e .
```

Activate the virtual environment before running development commands.

## Security

CodeAmil is a local coding agent, not a security sandbox. Commands you approve execute with the permissions of your operating-system account. Review commands and proposed file changes before approving them.

Keep API keys private, never commit `.env` files, and use version control to protect your work.

## License

See the repository's license file for licensing terms.

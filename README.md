# CodeAmil

CodeAmil is a local Python coding agent for inspecting, changing, reviewing,
debugging, and verifying real projects. It uses the directory from which
`codeamil` is started as the workspace, so it can be used from any project
directory on Windows, macOS, or Linux.

During model work and verification, an interactive terminal shows a small
spinner. It is disabled automatically when output is redirected or captured,
and pauses while CodeAmil waits for command or file-change approval.

## What it does

- Inspects project files and searches source text before acting.
- Plans multi-step work through a bounded model/tool loop.
- Creates and edits files through workspace-restricted tools.
- Runs project commands with `shell=False` and approval by default.
- Requires approval before model-proposed file changes by default.
- Reviews files and can propose approval-gated fixes.
- Runs deterministic Python syntax checks.
- Supports Gemini, OpenAI, and OpenRouter.
- Reports failed tools, provider errors, iteration limits, and verification
  results instead of claiming success.
- Redacts configured provider keys from surfaced provider errors.

CodeAmil is an assistant, not a complete operating-system sandbox. Approved
commands run with the permissions of your user account.

## Requirements

- Python 3.10 or newer
- pip
- An API key for the selected provider

## Installation

### Windows user installation

Clone the repository and run the installer from PowerShell:

```powershell
git clone https://github.com/emad313/codeamil.git
Set-Location codeamil
py install.py
```

The installer installs the checked-out project for the current user and adds
the user Scripts directory to PATH. Restart PowerShell after it finishes, then
verify:

```powershell
codeamil --version
```

For development, use an editable install instead:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If PowerShell blocks activation, run the commands through the venv directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\codeamil.exe --version
```

### macOS and Linux

```bash
git clone https://github.com/emad313/codeamil.git
cd codeamil
python3 install.py
```

## Configuration

Run the interactive setup:

```text
codeamil config
```

It writes user settings to `~/.codeamil/.env`. A project `.env` in the current
workspace can override user settings, while already-exported environment
variables take precedence over both.

Supported providers and typical settings:

| Provider | `MODEL_PROVIDER` | API key | Example model |
| --- | --- | --- | --- |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | `gemini-3.6-flash` |
| OpenAI | `openai` | `OPENAI_API_KEY` | `gpt-4.1-mini` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | `openrouter/free` |

You can copy [.env.example](./.env.example) to a project `.env`, but never
commit API keys. Relevant controls are:

```dotenv
MAX_AGENT_ITERATIONS=12
MAX_REVIEW_FIX_CYCLES=3
REQUIRE_APPROVAL_FOR_COMMANDS=true
REQUIRE_APPROVAL_FOR_FILE_CHANGES=true
REVIEW_FIX_MIN_SEVERITY=high
```

The approval settings accept `true`, `false`, `1`, `0`, `yes`, `no`, `on`, or
`off`. File-change approval should remain enabled unless the workspace is
already protected by another review workflow.

## Usage

Always start CodeAmil from the project it should work on:

```powershell
Set-Location C:\path\to\project
codeamil "Fix the login bug and run the relevant tests"
```

Without a task argument, CodeAmil prompts for one:

```text
codeamil
```

The agent can inspect files, search text, write approved changes, and run
approved commands. It stops at `MAX_AGENT_ITERATIONS` to prevent infinite
model/tool loops. It exits with a non-zero status when the task fails or
reaches the iteration limit.

The agent has two search tools:

- `search_text` finds case-insensitive text matches and reports file, line, and
  matching text.
- `search_files` finds files by name or relative path pattern, such as
  `*.py` or `src/*.py`.

## Review and verification commands

Review files without changing them:

```text
codeamil --review app/main.py app/config.py
```

Run Python syntax checks:

```text
codeamil --qa app/main.py app/config.py
```

Review selected files and propose fixes. Each proposed replacement is shown as
a diff and requires approval:

```text
codeamil --review-fix app/main.py app/config.py
```

Useful commands:

```text
codeamil --help
codeamil --version
codeamil config
```

## Workspace and safety limitations

- Tool paths must remain inside the selected workspace.
- Ignored directories include `.git`, virtual environments, `node_modules`,
  caches, and Python bytecode caches.
- Symlink traversal is skipped during listing and search.
- Commands are executed without a shell. Shell launchers such as `cmd`,
  PowerShell, `bash`, and `sh` are blocked.
- Read-only Git commands do not require approval; other commands do.
- File changes and review-fix changes are approval-gated by default.
- CodeAmil does not automatically infer every framework's test command.
  Ask it to inspect the project and run the relevant command, or run the
  project's normal checks yourself after reviewing its diff.

## Troubleshooting

### `Configuration error: MODEL_ID must be configured`

Run `codeamil config`, or set `MODEL_PROVIDER`, `MODEL_ID`, and the matching
API key in the environment.

### `Missing API key`

Confirm that the key name matches the selected provider. Environment variables
are not printed by CodeAmil.

### `codeamil` is not recognized on Windows

Restart the terminal after `install.py` updates PATH. If it still is not
available, use the Scripts path printed by the installer or install into an
activated virtual environment with `python -m pip install -e .`.

### The agent stops at an iteration limit

The model did not produce a final answer before the configured limit. Inspect
the tool results, increase `MAX_AGENT_ITERATIONS` modestly if appropriate, or
split the task into smaller requests.

### A command or file change was not executed

CodeAmil requires explicit approval by default. Re-run the task and approve
only commands and diffs you understand, or review
`REQUIRE_APPROVAL_FOR_COMMANDS` and `REQUIRE_APPROVAL_FOR_FILE_CHANGES`.

### Provider requests are slow or temporarily fail

Provider requests use bounded retries for common rate-limit, timeout, and
temporary server errors. After the retry limit, CodeAmil reports a failure and
does not claim that the task completed. Check the provider, model ID, API key,
and network connection before retrying.

### Review or QA exits with an error

Review and QA commands return a non-zero exit status when a file is missing,
outside the workspace, a provider request fails, or a verification check
fails. The error is printed to the terminal; no changes are applied by the
read-only review or QA commands.

## Development checks

From the repository root:

```powershell
python -m compileall -q app tests
python -m pytest -q
```

The test suite uses temporary workspaces and does not require an API call.

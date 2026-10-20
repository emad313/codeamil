
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import os

from app.config import load_settings
from app.orchestrator import Orchestrator


class FakeRouter:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate(self, messages):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(content=response)



def make_orchestrator(workspace, responses, max_iterations=4):
    home = Path(os.environ.get("USERPROFILE", r"C:\Users\emad"))

    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "MODEL_PROVIDER": "gemini",
        "MODEL_ID": "test-model",
        "MAX_AGENT_ITERATIONS": str(max_iterations),
        "REQUIRE_APPROVAL_FOR_COMMANDS": "true",
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch("pathlib.Path.home", return_value=home),
    ):
        settings = load_settings()

    with patch("app.orchestrator.ModelRouter"):
        orchestrator = Orchestrator(settings, workspace=workspace)

    orchestrator.model_router = FakeRouter(responses)
    return orchestrator



def main():
    with TemporaryDirectory() as temp:
        workspace = Path(temp)

        # A final answer completes a task.
        agent = make_orchestrator(
            workspace,
            ['{"final_answer":"Task completed."}'],
        )
        state = agent.run_task("Explain the project")
        assert state.status == "completed"
        assert state.result == "Task completed."
        assert state.iteration == 1
        print("PASS: final answer completes task")

        # Invalid JSON can be recovered from.
        agent = make_orchestrator(
            workspace,
            [
                "not valid JSON",
                '{"final_answer":"Recovered successfully."}',
            ],
        )
        state = agent.run_task("Explain the project")
        assert state.status == "completed"
        assert state.iteration == 2
        print("PASS: invalid model response is recoverable")

        # Model/provider exceptions become visible task failures.
        agent = make_orchestrator(
            workspace,
            [RuntimeError("simulated provider failure")],
        )
        state = agent.run_task("Explain the project")
        assert state.status == "failed"
        assert "simulated provider failure" in state.error
        print("PASS: provider failure is reported")

        # An agent that never finishes hits the iteration limit.
        agent = make_orchestrator(
            workspace,
            [
                '{"tool_call":{"name":"list_files","arguments":{"relative_path":"."}}}',
                '{"tool_call":{"name":"list_files","arguments":{"relative_path":"."}}}',
            ],
            max_iterations=2,
        )
        state = agent.run_task("Inspect the project")
        assert state.status == "limit_reached"
        assert state.iteration == 2
        print("PASS: iteration limit is enforced")

        # Empty tasks must not call the model.
        agent = make_orchestrator(workspace, [])
        state = agent.run_task("   ")
        assert state.status == "failed"
        assert "non-empty" in state.error
        print("PASS: empty tasks are rejected")

        # File changes are approval-gated before reaching the filesystem.
        agent = make_orchestrator(
            workspace,
            [
                (
                    '{"tool_call":{"name":"write_file","arguments":'
                    '{"relative_path":"created.txt","content":"safe"}}}'
                ),
                '{"final_answer":"Change was declined."}',
            ],
        )
        approvals = []
        state = agent.run_task(
            "Create a file",
            approve_file_change=lambda path, content, explanation: (
                approvals.append(path) or False
            ),
        )
        assert state.status == "completed"
        assert approvals == ["created.txt"]
        assert not (workspace / "created.txt").exists()
        print("PASS: file changes require explicit approval")

    print("All task-loop tests passed.")


if __name__ == "__main__":
    main()

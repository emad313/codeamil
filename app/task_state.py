from dataclasses import dataclass, field


@dataclass
class TaskState:
    task: str
    status: str = "pending"
    iteration: int = 0
    messages: list[dict[str, str]] = field(default_factory=list)
    result: str = ""
    error: str | None = None

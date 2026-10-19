
from app.agents.tool_protocol import parse_model_action


def main() -> None:
    tool_action = parse_model_action(
        """
        {
          "tool_call": {
            "name": "list_files",
            "arguments": {"relative_path": "."}
          }
        }
        """
    )

    assert tool_action.kind == "tool"
    assert tool_action.name == "list_files"
    assert tool_action.arguments == {"relative_path": "."}

    final_action = parse_model_action(
        '{"final_answer": "Task completed."}'
    )

    assert final_action.kind == "final"
    assert final_action.content == "Task completed."

    try:
        parse_model_action('{"tool_call": "invalid"}')
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid tool call was accepted.")

    print("PASS: tool request parsed")
    print("PASS: final answer parsed")
    print("PASS: invalid tool request rejected")
    print("All protocol tests passed.")


if __name__ == "__main__":
    main()

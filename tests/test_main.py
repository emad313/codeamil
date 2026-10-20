import sys
from pathlib import Path
from unittest.mock import patch

from app.main import main


def test_qa_does_not_require_provider_configuration(
    tmp_path: Path,
    capsys,
) -> None:
    target = tmp_path / "sample.py"
    target.write_text("value = 1\n", encoding="utf-8")

    with (
        patch("pathlib.Path.cwd", return_value=tmp_path),
        patch.object(sys, "argv", ["codeamil", "--qa", "sample.py"]),
    ):
        main()

    assert "[PASS] Python syntax" in capsys.readouterr().out

from __future__ import annotations

from pathlib import Path

from yidl_lifecycle.regenerate_lifecycle_base import main
from yidl_lifecycle.regenerate_lifecycle_base import render_lifecycle_base_source


def test_rendered_lifecycle_base_matches_committed_generated_file() -> None:
    project_root = Path(__file__).resolve().parents[1]
    generated_path = project_root / "src" / "yidl_lifecycle" / "_generated_lifecycle_base.py"

    assert render_lifecycle_base_source() == generated_path.read_text(encoding="utf-8")


def test_regenerate_lifecycle_base_check_command_succeeds(capsys) -> None:
    assert main([]) == 0

    captured = capsys.readouterr()
    assert "generated lifecycle base matches" in captured.out

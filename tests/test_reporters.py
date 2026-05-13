import json
from pathlib import Path

from git_health.reporters import render_json, render_text
from git_health.scanner import scan_repository


def test_render_json_contains_score_summary_and_checks(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## Install\n\npip install demo\n\n## Usage\n\ndemo run\n")
    (tmp_path / "LICENSE").write_text("MIT\n")

    payload = json.loads(render_json(scan_repository(tmp_path)))

    assert payload["root"] == str(tmp_path.resolve())
    assert isinstance(payload["score"], float)
    assert payload["summary"]["total"] == len(payload["checks"])
    assert payload["summary"]["failed"] >= 1
    assert {"id", "title", "category", "passed", "weight", "severity", "message", "recommendation"} <= set(
        payload["checks"][0]
    )


def test_render_text_remains_human_readable(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("demo\n")

    output = render_text(scan_repository(tmp_path))

    assert "Git Health Score:" in output
    assert "Recommended next steps:" in output

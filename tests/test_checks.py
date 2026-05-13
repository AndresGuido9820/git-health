from pathlib import Path

from git_health.scanner import calculate_score, scan_repository


def test_score_rewards_present_project_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## Install\n\npip install demo\n\n## Usage\n\ndemo run\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / "tests").mkdir()

    result = scan_repository(tmp_path)

    assert result.score > 0
    assert any(check.id == "readme" and check.passed for check in result.checks)
    assert any(check.id == "license" and check.passed for check in result.checks)
    assert any(check.id == "tests" and check.passed for check in result.checks)


def test_sensitive_files_reduce_health(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("demo\n")
    (tmp_path / ".env").write_text("TOKEN=secret\n")

    result = scan_repository(tmp_path)

    assert any(check.id == "sensitive-files" and not check.passed for check in result.checks)


def test_score_is_zero_without_rules() -> None:
    assert calculate_score(()) == 0.0

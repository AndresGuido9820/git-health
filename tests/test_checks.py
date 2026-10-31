from pathlib import Path

import pytest

from git_health.scanner import calculate_score, scan_repository


def test_score_rewards_present_project_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## Install\n\npip install demo\n\n## Usage\n\ndemo run\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_demo.py").write_text("def test_example(): pass\n")

    result = scan_repository(tmp_path)

    assert result.score > 0
    assert any(check.id == "readme" and check.passed for check in result.checks)
    assert any(check.id == "license" and check.passed for check in result.checks)
    assert any(check.id == "tests" and check.passed for check in result.checks)


def test_score_is_zero_without_rules() -> None:
    assert calculate_score(()) == 0.0


@pytest.mark.parametrize("location", ["", "docs", ".github"])
@pytest.mark.parametrize("name", ["pull_request_template.md", "PULL_REQUEST_TEMPLATE.md"])
def test_pr_template_in_supported_location(tmp_path: Path, location: str, name: str) -> None:
    template = tmp_path / location / name
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text("## Summary\n\n## Verification\n")

    result = scan_repository(tmp_path)

    assert next(check for check in result.checks if check.id == "pr-template").passed


@pytest.mark.parametrize("location", ["", "docs", ".github"])
@pytest.mark.parametrize("folder", ["PULL_REQUEST_TEMPLATE", "pull_request_template"])
def test_multiple_pr_templates(tmp_path: Path, location: str, folder: str) -> None:
    template = tmp_path / location / folder / "full.md"
    template.parent.mkdir(parents=True)
    template.write_text("## Summary\n\n## Verification\n")

    result = scan_repository(tmp_path)

    assert next(check for check in result.checks if check.id == "pr-template").passed


@pytest.mark.parametrize("contents", [None, "preview.png"])
def test_pr_template_directory_needs_a_direct_markdown_file(tmp_path: Path, contents: str | None) -> None:
    folder = tmp_path / ".github" / "PULL_REQUEST_TEMPLATE"
    folder.mkdir(parents=True)
    if contents is not None:
        path = folder / contents
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Not a direct Markdown template.\n")

    result = scan_repository(tmp_path)

    assert not next(check for check in result.checks if check.id == "pr-template").passed


def test_directory_with_default_template_name_is_not_a_template(tmp_path: Path) -> None:
    (tmp_path / "PULL_REQUEST_TEMPLATE.md").mkdir()

    result = scan_repository(tmp_path)

    assert not next(check for check in result.checks if check.id == "pr-template").passed


@pytest.mark.parametrize("filename", ["README.md", "README.rst", "README.txt"])
def test_readme_documentation_checks_support_each_format(tmp_path: Path, filename: str) -> None:
    (tmp_path / filename).write_text("Install\n pip install demo\nUsage\n demo run\n")

    result = scan_repository(tmp_path)

    checks = {check.id: check.passed for check in result.checks}
    assert checks["readme"]
    assert checks["install-docs"]
    assert checks["usage-docs"]


def test_readme_documentation_checks_do_not_pass_without_terms(tmp_path: Path) -> None:
    (tmp_path / "README.rst").write_text("A project description.\n")

    result = scan_repository(tmp_path)

    checks = {check.id: check.passed for check in result.checks}
    assert checks["readme"]
    assert not checks["install-docs"]
    assert not checks["usage-docs"]

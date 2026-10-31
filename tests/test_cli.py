import json
import os
import subprocess
import sys
from pathlib import Path


def cli(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "git_health.cli", "scan", str(path), "--format", "json", *args],
                          capture_output=True, text=True, check=False)


def test_deceptive_scaffold_fails_and_reports_evidence(tmp_path: Path) -> None:
    for name in ("LICENSE", "CONTRIBUTING.md", "SECURITY.md", ".gitignore", "PULL_REQUEST_TEMPLATE.md"):
        (tmp_path / name).touch()
    (tmp_path / "README.md").write_text("uninstall unused example\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/broken.yml").write_text("not: [valid\n")
    result = cli(tmp_path)
    data = json.loads(result.stdout)
    checks = {c["id"]: c for c in data["checks"]}
    assert result.returncode == 1 and data["score"] < 10 and not data["gate"]["passed"]
    for name in ("license", "tests", "install-docs", "usage-docs", "pr-template"):
        assert not checks[name]["passed"] and checks[name]["evidence"] is None
    assert checks["ci"]["passed"] and "not verified" in checks["ci"]["message"]
    assert checks["ci"]["evidence"] == ".github/workflows/broken.yml"


def test_gate_severity_and_threshold_are_independent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## Install\n\nsetup\n\n## Usage\n\nrun\n")
    default = cli(tmp_path, "--min-score", "0")
    relaxed = cli(tmp_path, "--min-score", "0", "--fail-on", "none")
    strict = cli(tmp_path, "--min-score", "10", "--fail-on", "none")
    assert default.returncode == 1 and "license" in json.loads(default.stdout)["gate"]["failed_checks"]
    assert relaxed.returncode == 0 and strict.returncode == 1


def test_input_errors_are_json(tmp_path: Path) -> None:
    for path, args in ((tmp_path / "missing", ()), (tmp_path, ("--min-score", "nan"))):
        result = cli(path, *args)
        assert result.returncode == 2 and json.loads(result.stdout)["error"]["message"]
        assert not result.stderr
    other = tmp_path / "not-git"
    other.mkdir()
    result = cli(other)
    assert result.returncode == 2 and "Git working tree root" in json.loads(result.stdout)["error"]["message"]


def test_symlink_candidates_are_ignored_and_large_files_error(tmp_path: Path) -> None:
    target = tmp_path / "outside"
    target.write_text("## Install\n\n## Usage\n")
    (tmp_path / "README.md").symlink_to(target)
    result = cli(tmp_path)
    checks = {c["id"]: c for c in json.loads(result.stdout)["checks"]}
    assert result.returncode == 1 and not checks["readme"]["passed"]
    (tmp_path / "README.md").unlink()
    (tmp_path / "README.md").write_bytes(b"a" * (1_048_576 + 1))
    result = cli(tmp_path)
    assert result.returncode == 2 and "exceeds" in json.loads(result.stdout)["error"]["message"]


def test_unreadable_readme_is_structured_error(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("hello")
    path.chmod(0)
    if os.access(path, os.R_OK):
        return  # Privileged test runners may bypass permission bits.
    try:
        result = cli(tmp_path)
        assert result.returncode == 2 and "Cannot read" in json.loads(result.stdout)["error"]["message"]
    finally:
        path.chmod(0o600)


def test_gate_recovery_after_adding_observed_signals(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Sample\n")
    assert cli(tmp_path).returncode == 1
    (tmp_path / "README.md").write_text("# Sample\n\n## Install\n\nsetup\n\n## Usage\n\nrun\n")
    (tmp_path / "LICENSE").write_text("License terms\n")
    (tmp_path / ".gitignore").write_text(".venv/\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text("def test_sample(): assert True\n")
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/test.yml").write_text("name: test\n")
    result = cli(tmp_path)
    data = json.loads(result.stdout)
    assert result.returncode == 0 and data["gate"]["passed"] and data["score"] >= 7
    assert "not verified" in next(c["message"] for c in data["checks"] if c["id"] == "ci")


def test_symlinked_candidate_directory_is_ignored(tmp_path: Path) -> None:
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "run.yml").write_text("name: test\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/workflows").symlink_to(outside, target_is_directory=True)
    result = cli(tmp_path)
    check = next(c for c in json.loads(result.stdout)["checks"] if c["id"] == "ci")
    assert result.returncode == 1 and not check["passed"]


def test_nested_test_files_are_discovered_without_following_symlinks(tmp_path: Path) -> None:
    nested = tmp_path / "tests" / "unit"
    nested.mkdir(parents=True)
    (nested / "test_example.py").write_text("def test_example(): pass\n")
    (nested / "cycle").symlink_to(tmp_path / "tests", target_is_directory=True)
    result = cli(tmp_path)
    check = next(c for c in json.loads(result.stdout)["checks"] if c["id"] == "tests")
    assert check["passed"] and check["evidence"] == "tests/unit/test_example.py"
    assert "execution and coverage not verified" in check["message"]
    (nested / "test_example.py").unlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "test_outside.py").write_text("def test_x(): pass\n")
    (nested / "linked").symlink_to(outside, target_is_directory=True)
    result = cli(tmp_path)
    check = next(c for c in json.loads(result.stdout)["checks"] if c["id"] == "tests")
    assert not check["passed"]


def test_usage_heading_variants_and_substrings(tmp_path: Path) -> None:
    for heading in ("Getting started", "Quick start", "Quickstart", "Start with a local clip"):
        (tmp_path / "README.md").write_text(f"# Project\n\n## {heading}\n\nexample\n")
        result = cli(tmp_path)
        check = next(c for c in json.loads(result.stdout)["checks"] if c["id"] == "usage-docs")
        assert check["passed"] and check["evidence"] == "README.md", heading
    for heading in ("Unused", "Uninstall", "Getting startedness", "Quick starter", "Start without setup"):
        (tmp_path / "README.md").write_text(f"## {heading}\n")
        result = cli(tmp_path)
        checks = {c["id"]: c for c in json.loads(result.stdout)["checks"]}
        assert not checks["usage-docs"]["passed"] and not checks["install-docs"]["passed"], heading


def test_recursive_discovery_depth_and_shared_read_limits(tmp_path: Path) -> None:
    deep = tmp_path / "tests"
    for _ in range(6):
        deep /= "nested"
    deep.mkdir(parents=True)
    result = cli(tmp_path)
    assert result.returncode == 2 and "depth" in json.loads(result.stdout)["error"]["message"]
    # Move the deeply nested directory out of the search roots before testing both roots' shared budget.
    (tmp_path / "tests").rename(tmp_path / "other")
    for root_name in ("test", "tests"):
        directory = tmp_path / root_name
        directory.mkdir()
        for i in range(51):
            (directory / f"test_{i:03}.py").touch()
    result = cli(tmp_path)
    assert result.returncode == 2 and "candidate reads" in json.loads(result.stdout)["error"]["message"]


def test_recursive_discovery_entry_limit(tmp_path: Path) -> None:
    directory = tmp_path / "tests" / "nested"
    directory.mkdir(parents=True)
    for i in range(2000):
        (directory / f"file_{i:04}").touch()
    result = cli(tmp_path)
    assert result.returncode == 2 and "entries" in json.loads(result.stdout)["error"]["message"]


def test_recursive_discovery_byte_budget(tmp_path: Path) -> None:
    directory = tmp_path / "tests"
    directory.mkdir()
    for i in range(5):
        (directory / f"test_{i}.py").write_bytes(b" " * 1_048_576)
    result = cli(tmp_path)
    assert result.returncode == 2 and "read limit" in json.loads(result.stdout)["error"]["message"]


def summary_cli(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "git_health.cli", "scan", str(path), "--format", "summary", *args],
                          capture_output=True, text=True, check=False)


def test_summary_shows_selected_gate_and_missing_signals(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("## Install\n\nsetup\n\n## Usage\n\nrun\n")
    result = summary_cli(tmp_path, "--min-score", "0")
    assert result.returncode == 1 and "Gate: FAIL" in result.stdout
    assert "Policy: min 0.0/10; fail: critical" in result.stdout
    assert "License file" in result.stdout and "Other missing:" in result.stdout
    assert str(tmp_path) not in result.stdout
    assert all(len(line) <= 40 for line in result.stdout.splitlines())
    relaxed = summary_cli(tmp_path, "--min-score", "0", "--fail-on", "none")
    assert relaxed.returncode == 0 and "Gate: PASS" in relaxed.stdout
    assert "License file" in relaxed.stdout and "fail: none" in relaxed.stdout
    precise = summary_cli(tmp_path, "--min-score", "6.9999999", "--fail-on", "none")
    assert "6.9999999/10" in precise.stdout
    assert all(len(line) <= 38 for line in precise.stdout.splitlines())
    threshold = summary_cli(tmp_path, "--min-score", "10", "--fail-on", "none")
    assert threshold.returncode == 1 and "Gate: FAIL" in threshold.stdout


def test_summary_scan_error_goes_to_stderr(tmp_path: Path) -> None:
    result = summary_cli(tmp_path / "missing")
    assert result.returncode == 2 and not result.stdout
    assert result.stderr.startswith("Error:")

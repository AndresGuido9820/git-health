from __future__ import annotations

import subprocess
from pathlib import Path

from git_health.fs import FileScanError
from git_health.models import CheckResult, ScanResult
from git_health.rules import Rule, default_rules


class ScanError(ValueError):
    pass


def calculate_score(checks: tuple[CheckResult, ...]) -> float:
    total = sum(check.weight for check in checks)
    return round(sum(check.weight for check in checks if check.passed) / total * 10, 1) if total else 0.0


def scan_repository(path: str | Path, rules: tuple[Rule, ...] | None = None) -> ScanResult:
    try:
        root = Path(path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ScanError(f"Not a directory: {root}")
        proc = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=10, check=False)
        if proc.returncode or not proc.stdout.strip() or Path(proc.stdout.strip()).resolve() != root:
            raise ScanError(f"Not a Git working tree root: {root}")
        checks = tuple(rule.evaluate(root) for rule in (default_rules() if rules is None else rules))
    except ScanError:
        raise
    except (OSError, RuntimeError, subprocess.SubprocessError, FileScanError) as exc:
        raise ScanError(str(exc)) from exc
    return ScanResult(root=str(root), score=calculate_score(checks), checks=checks)

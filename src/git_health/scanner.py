from __future__ import annotations

from pathlib import Path

from git_health.models import CheckResult, ScanResult
from git_health.rules import Rule, default_rules


class ScanError(ValueError):
    pass


def calculate_score(checks: tuple[CheckResult, ...]) -> float:
    total = sum(check.weight for check in checks)
    earned = sum(check.weight for check in checks if check.passed)
    if total == 0:
        return 0.0
    return round((earned / total) * 10, 1)


def scan_repository(path: str | Path, rules: tuple[Rule, ...] | None = None) -> ScanResult:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise ScanError(f"No existe {root}")
    if not root.is_dir():
        raise ScanError(f"{root} no es un directorio")

    active_rules = rules or default_rules()
    checks = tuple(rule.evaluate(root) for rule in active_rules)
    return ScanResult(root=str(root), score=calculate_score(checks), checks=checks)


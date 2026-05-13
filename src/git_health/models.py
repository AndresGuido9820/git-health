from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CheckResult:
    id: str
    title: str
    category: str
    passed: bool
    weight: int
    severity: Severity
    success_message: str
    recommendation: str


@dataclass(frozen=True)
class ScanResult:
    root: str
    score: float
    checks: tuple[CheckResult, ...]

    @property
    def failed_checks(self) -> tuple[CheckResult, ...]:
        return tuple(check for check in self.checks if not check.passed)


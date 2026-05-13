from __future__ import annotations

import json
from collections import defaultdict

from git_health.models import CheckResult, ScanResult


def _status(check: CheckResult) -> str:
    return "OK" if check.passed else "WARN"


def render_text(result: ScanResult) -> str:
    lines = [
        f"Git Health Score: {result.score}/10",
        f"Repo: {result.root}",
        "",
    ]

    by_category: dict[str, list[CheckResult]] = defaultdict(list)
    for check in result.checks:
        by_category[check.category].append(check)

    for category in sorted(by_category):
        lines.append(category.title())
        for check in by_category[category]:
            message = check.success_message if check.passed else check.recommendation
            lines.append(f"  {_status(check):4s} {check.title:26s} {message}")
        lines.append("")

    failed = sorted(result.failed_checks, key=lambda item: item.weight, reverse=True)
    if failed:
        lines.append("Recommended next steps:")
        for index, check in enumerate(failed, start=1):
            lines.append(f"{index}. {check.recommendation}")

    return "\n".join(lines).rstrip()


def render_json(result: ScanResult) -> str:
    payload = {
        "root": result.root,
        "score": result.score,
        "summary": {
            "total": len(result.checks),
            "passed": sum(1 for check in result.checks if check.passed),
            "failed": len(result.failed_checks),
        },
        "checks": [
            {
                "id": check.id,
                "title": check.title,
                "category": check.category,
                "passed": check.passed,
                "weight": check.weight,
                "severity": check.severity.value,
                "message": check.success_message if check.passed else check.recommendation,
                "recommendation": check.recommendation,
            }
            for check in result.checks
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)

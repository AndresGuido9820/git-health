from __future__ import annotations

import json
import textwrap
from collections import defaultdict
from typing import Any

from git_health.models import ScanResult, Severity


def render_text(result: ScanResult, gate: dict[str, Any] | None = None) -> str:
    lines = [f"Git Health Score: {result.score}/10 (checklist signals, not a quality rating)",
             f"Repository: {result.root}", ""]
    by_category: dict[str, list] = defaultdict(list)
    for check in result.checks:
        by_category[check.category].append(check)
    for category in sorted(by_category):
        lines.append(category.title())
        for check in by_category[category]:
            message = check.success_message if check.passed else check.recommendation
            evidence = f" [{check.evidence}]" if check.evidence else ""
            lines.append(f"  {'FOUND' if check.passed else 'MISSING':7s} {check.title}: {message}{evidence}")
        lines.append("")
    if result.failed_checks:
        lines.append("Recommended next steps:")
        for index, check in enumerate(sorted(result.failed_checks, key=lambda item: item.weight, reverse=True), 1):
            lines.append(f"{index}. {check.recommendation}")
    if gate is not None:
        lines.append(f"\nGate: {'PASS' if gate['passed'] else 'FAIL'} (minimum {gate['min_score']}/10; "
                     f"fail on {gate['fail_on']}; severity failures: {', '.join(gate['failed_checks']) or 'none'})")
    lines.append("Limits: Signals are not proof of working CI, test coverage, or security; use dedicated tools.")
    return "\n".join(lines)



def render_summary(result: ScanResult, gate: dict[str, Any]) -> str:
    """Show the actual gate and a bounded set of actionable missing signals."""
    critical = [c for c in result.failed_checks if c.severity == Severity.CRITICAL]
    warnings = sum(c.severity == Severity.WARNING for c in result.failed_checks)
    info = sum(c.severity == Severity.INFO for c in result.failed_checks)
    lines = ["Local checklist (not an audit)",
             f"Score: {result.score:g}/10  Gate: {'PASS' if gate['passed'] else 'FAIL'}",
             *textwrap.wrap(f"Policy: min {gate['min_score']!r}/10; fail: {gate['fail_on']}", width=38)]
    if critical:
        lines.append("Critical signals missing:")
        for check in critical[:3]:
            lines.extend(textwrap.wrap(check.title, width=38, initial_indent="- ", subsequent_indent="  "))
        if len(critical) > 3:
            lines.append(f"- +{len(critical) - 3} more critical")
    else:
        lines.append("Critical signals missing: 0")
    lines.append(f"Other missing: {warnings} warning, {info} info")
    lines.append("Details: use --format text or json")
    return "\n".join(lines)

def render_json(result: ScanResult, gate: dict[str, Any] | None = None) -> str:
    payload = {
        "root": result.root,
        "score": result.score,
        "summary": {"total": len(result.checks), "passed": len(result.checks) - len(result.failed_checks),
                    "failed": len(result.failed_checks)},
        "checks": [{"id": c.id, "title": c.title, "category": c.category, "passed": c.passed,
                    "weight": c.weight, "severity": c.severity.value,
                    "message": c.success_message if c.passed else c.recommendation,
                    "recommendation": c.recommendation, "evidence": c.evidence} for c in result.checks],
        "limits": "Local signals only; workflow syntax, execution, test coverage and security are not verified.",
    }
    if gate is not None:
        payload["gate"] = gate
    return json.dumps(payload, indent=2, ensure_ascii=False)

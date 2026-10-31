from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from git_health.fs import find_test_file, matching_file, nonempty, read_candidate
from git_health.models import CheckResult, Severity

README_FILES = ("README.md", "README.rst", "README.txt")
Predicate = Callable[[Path], str | None]


def readme_heading(root: Path, words: str) -> str | None:
    # Recognize a whole-word heading or line, rather than substrings such as uninstall.
    pattern = re.compile(rf"(?im)^[ \t]*(?:#{{1,6}}[ \t]+)?(?:{words})[ \t]*:?[ \t]*$")
    for name in README_FILES:
        text = read_candidate(root, root / name)
        if text and pattern.search(text):
            return name
    return None


def pr_template(root: Path) -> str | None:
    for directory in (".", "docs", ".github"):
        found = matching_file(root, directory, r"pull_request_template\.md")
        if found:
            return found
        found = matching_file(root, f"{directory}/PULL_REQUEST_TEMPLATE", r".+\.md")
        if found:
            return found
        found = matching_file(root, f"{directory}/pull_request_template", r".+\.md")
        if found:
            return found
    return None


def files(*names: str) -> Predicate:
    return lambda root: nonempty(root, names)


def directory_file(directory: str, pattern: str) -> Predicate:
    return lambda root: matching_file(root, directory, pattern)


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    category: str
    weight: int
    severity: Severity
    success_message: str
    recommendation: str
    predicate: Predicate

    def evaluate(self, root: Path) -> CheckResult:
        evidence = self.predicate(root)
        return CheckResult(self.id, self.title, self.category, bool(evidence), self.weight,
                           self.severity, self.success_message, self.recommendation, evidence)


def default_rules() -> tuple[Rule, ...]:
    critical, warning, info = Severity.CRITICAL, Severity.WARNING, Severity.INFO
    return (
        Rule("readme", "README", "documentation", 12, critical, "Nonempty README found.",
             "Add a nonempty README.md, README.rst, or README.txt.", files(*README_FILES)),
        Rule("license", "License file", "community", 10, critical, "Nonempty license file found; terms not verified.",
             "Add a license file with the terms for reuse.", files("LICENSE", "LICENSE.md", "COPYING")),
        Rule("contributing", "Contribution guide", "community", 8, warning,
             "Nonempty contribution guide found; content not verified.",
             "Add a CONTRIBUTING.md guide.", files("CONTRIBUTING.md", ".github/CONTRIBUTING.md")),
        Rule("pr-template", "Pull request template", "community", 6, warning, "Nonempty PR template found.",
             "Add a Markdown PR template at the root, docs/, or .github/.", pr_template),
        Rule("issue-templates", "Issue template", "community", 6, warning,
             "Nonempty GitHub issue template candidate found; content not verified.",
             "Add a Markdown or YAML issue template under .github/ISSUE_TEMPLATE/.",
             directory_file(".github/ISSUE_TEMPLATE", r".+\.(md|yml|yaml)")),
        Rule("ci", "Workflow file", "engineering", 12, critical,
             "Nonempty GitHub workflow candidate found; syntax and execution not verified.",
             "Add and verify a GitHub Actions workflow under .github/workflows/.",
             directory_file(".github/workflows", r".+\.ya?ml")),
        Rule("tests", "Test file", "engineering", 10, critical,
             "Nonempty test file candidate found; execution and coverage not verified.",
             "Add and run tests in test/ or tests/.",
             lambda root: find_test_file(root, r"(test_.+\.py|.+_test\.py|.+\.(test|spec)\.[cm]?[jt]sx?)")),
        Rule("gitignore", "Gitignore", "engineering", 5, warning, "Nonempty .gitignore found; patterns not verified.",
             "Add a .gitignore for local artifacts.", files(".gitignore")),
        Rule("security", "Security policy", "community", 5, warning,
             "Nonempty security policy file found; content not verified.",
             "Add SECURITY.md with a vulnerability reporting process.", files("SECURITY.md", ".github/SECURITY.md")),
        Rule("install-docs", "Installation heading", "documentation", 8, critical,
             "Installation heading found; instructions not verified.",
             "Add an Install or Installation heading to the README.",
             lambda root: readme_heading(root, "install|installation|instalacion")),
        Rule("usage-docs", "Usage heading", "documentation", 8, critical, "Usage heading found; examples not verified.",
             "Add a Usage, Example, Quickstart, or Getting started heading to the README.",
             lambda root: readme_heading(
                 root, r"usage|uso|example|examples|ejemplo|quick[ \t]*start|getting[ \t]+started|"
                 r"start[ \t]+with[ \t]+\S[^\n]*")),
        Rule("changelog", "Changelog", "maintenance", 3, info, "Nonempty changelog found; content not verified.",
             "Consider a changelog for release history.", files("CHANGELOG.md", "HISTORY.md", "RELEASES.md")),
    )

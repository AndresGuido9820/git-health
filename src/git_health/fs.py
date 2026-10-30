from __future__ import annotations

from pathlib import Path


def exists_any(root: Path, candidates: tuple[str, ...]) -> bool:
    return any((root / candidate).exists() for candidate in candidates)


def glob_any(root: Path, pattern: str) -> bool:
    return any(root.glob(pattern))


def has_pull_request_template(root: Path) -> bool:
    """Find Markdown templates in GitHub's root, docs and .github locations."""
    for parent in (root, root / "docs", root / ".github"):
        if not parent.is_dir():
            continue
        for entry in parent.iterdir():
            name = entry.name.casefold()
            if name == "pull_request_template.md" and entry.is_file():
                return True
            if (
                name == "pull_request_template"
                and entry.is_dir()
                and any(path.is_file() and path.suffix.casefold() == ".md" for path in entry.iterdir())
            ):
                return True
    return False


def file_contains(path: Path, terms: tuple[str, ...]) -> bool:
    if not path.exists() or not path.is_file():
        return False

    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(term.lower() in text for term in terms)


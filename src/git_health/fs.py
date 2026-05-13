from __future__ import annotations

from pathlib import Path


def exists_any(root: Path, candidates: tuple[str, ...]) -> bool:
    return any((root / candidate).exists() for candidate in candidates)


def glob_any(root: Path, pattern: str) -> bool:
    return any(root.glob(pattern))


def file_contains(path: Path, terms: tuple[str, ...]) -> bool:
    if not path.exists() or not path.is_file():
        return False

    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(term.lower() in text for term in terms)


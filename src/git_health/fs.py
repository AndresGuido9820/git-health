from __future__ import annotations

import os
import re
import stat
from pathlib import Path

MAX_FILE_BYTES = 1_048_576
MAX_DIRECTORY_ENTRIES = 2000
MAX_TEST_DEPTH = 5
MAX_TEST_ENTRIES = 2000
MAX_TEST_READS = 100
MAX_TEST_BYTES = 4_194_304


class FileScanError(ValueError):
    """A candidate could not be inspected safely."""


def safe_parts(root: Path, path: Path) -> bool:
    """Ignore symlinks in every component below the selected repository root."""
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise FileScanError(f"Cannot inspect {current}: {exc.strerror}") from exc
        if stat.S_ISLNK(mode):
            return False
    return True


def read_candidate(root: Path, path: Path, budget: list[int] | None = None) -> str | None:
    if not safe_parts(root, path):
        return None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            os.close(fd)
            return None
        with os.fdopen(fd, "rb") as file:
            limit = min(MAX_FILE_BYTES, budget[0]) if budget is not None else MAX_FILE_BYTES
            if info.st_size > limit:
                raise FileScanError(f"File exceeds read limit of {limit} bytes: {path}")
            data = file.read(limit + 1)
            if len(data) > limit:
                raise FileScanError(f"File exceeds read limit of {limit} bytes: {path}")
            if budget is not None:
                budget[0] -= len(data)
    except OSError as exc:
        raise FileScanError(f"Cannot read {path}: {exc.strerror}") from exc
    return data.decode("utf-8", errors="replace")


def nonempty(root: Path, paths: tuple[str, ...]) -> str | None:
    for name in paths:
        text = read_candidate(root, root / name)
        if text and text.strip():
            return name
    return None


def matching_file(root: Path, directory: str, pattern: str) -> str | None:
    parent = root / directory
    if not safe_parts(root, parent):
        return None
    try:
        if not parent.is_dir():
            return None
        with os.scandir(parent) as entries:
            names = []
            for entry in entries:
                names.append(entry.name)
                if len(names) > MAX_DIRECTORY_ENTRIES:
                    raise FileScanError(f"Too many entries in {parent} (limit {MAX_DIRECTORY_ENTRIES})")
    except OSError as exc:
        raise FileScanError(f"Cannot list {parent}: {exc.strerror}") from exc
    for name in sorted(names):
        if re.fullmatch(pattern, name, re.IGNORECASE):
            relative = str(Path(directory) / name)
            if nonempty(root, (relative,)):
                return relative
    return None


def find_test_file(root: Path, pattern: str) -> str | None:
    """Search both test roots with shared entry, depth, file and byte budgets."""
    entries_seen = 0
    reads = 0
    budget = [MAX_TEST_BYTES]
    pending = [(root / name, 0) for name in ("test", "tests")]
    while pending:
        directory, depth = pending.pop()
        if not safe_parts(root, directory):
            continue
        try:
            if not directory.is_dir():
                continue
            with os.scandir(directory) as entries:
                children = []
                for entry in entries:
                    entries_seen += 1
                    if entries_seen > MAX_TEST_ENTRIES:
                        raise FileScanError(f"Test discovery exceeds {MAX_TEST_ENTRIES} entries")
                    children.append(entry)
            for entry in sorted(children, key=lambda item: item.name):
                if entry.is_symlink():
                    continue
                path = directory / entry.name
                if entry.is_dir(follow_symlinks=False):
                    if depth >= MAX_TEST_DEPTH:
                        raise FileScanError(f"Test discovery exceeds depth {MAX_TEST_DEPTH}: {path}")
                    pending.append((path, depth + 1))
                elif re.fullmatch(pattern, entry.name, re.IGNORECASE) and entry.is_file(follow_symlinks=False):
                    reads += 1
                    if reads > MAX_TEST_READS:
                        raise FileScanError(f"Test discovery exceeds {MAX_TEST_READS} candidate reads")
                    text = read_candidate(root, path, budget)
                    if text and text.strip():
                        return str(path.relative_to(root))
        except OSError as exc:
            raise FileScanError(f"Cannot inspect {directory}: {exc.strerror}") from exc
    return None

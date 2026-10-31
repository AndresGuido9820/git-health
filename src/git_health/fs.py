from __future__ import annotations

import os
import re
import stat
from pathlib import Path

MAX_FILE_BYTES = 1_048_576
MAX_DIRECTORY_ENTRIES = 2000


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


def read_candidate(root: Path, path: Path) -> str | None:
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
            if info.st_size > MAX_FILE_BYTES:
                raise FileScanError(f"File exceeds {MAX_FILE_BYTES} bytes: {path}")
            data = file.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise FileScanError(f"File exceeds {MAX_FILE_BYTES} bytes: {path}")
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

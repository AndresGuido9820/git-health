from __future__ import annotations

import argparse

from git_health.reporters import render_text
from git_health.scanner import ScanError, scan_repository


def scan(path: str) -> int:
    try:
        result = scan_repository(path)
    except ScanError as exc:
        print(f"Error: {exc}")
        return 2

    print(render_text(result))
    return 0 if result.score >= 7 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-health",
        description="Audita la salud open source de un repositorio Git.",
    )
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Escanea un repositorio local")
    scan_parser.add_argument("path", nargs="?", default=".", help="Ruta del repositorio")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return scan(args.path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

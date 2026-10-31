from __future__ import annotations

import argparse
import json
import math
import sys

from git_health.reporters import render_json, render_summary, render_text
from git_health.scanner import ScanError, scan_repository


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "--format=json" in sys.argv or any(
            sys.argv[i:i + 2] == ["--format", "json"] for i in range(len(sys.argv))
        ):
            print(json.dumps({"error": {"code": "invalid_arguments", "message": message}}))
        else:
            print(f"Error: {message}", file=sys.stderr)
        raise SystemExit(2)


def score_value(value: str) -> float:
    try:
        score = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number from 0 to 10") from exc
    if not math.isfinite(score) or not 0 <= score <= 10:
        raise argparse.ArgumentTypeError("must be a number from 0 to 10")
    return score


def scan(path: str, output_format: str = "text", min_score: float = 7,
         fail_on: str = "critical") -> int:
    try:
        result = scan_repository(path)
    except ScanError as exc:
        if output_format == "json":
            print(json.dumps({"error": {"code": "scan_error", "message": str(exc)}}))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    levels = {"none": 0, "critical": 1, "warning": 2, "info": 3}
    failed = [c.id for c in result.failed_checks if levels[c.severity.value] <= levels[fail_on]]
    gate = {"min_score": min_score, "fail_on": fail_on, "failed_checks": failed,
            "passed": result.score >= min_score and not failed}
    renderers = {"json": render_json, "text": render_text, "summary": render_summary}
    print(renderers[output_format](result, gate))
    return 0 if gate["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(prog="git-health", description="Check local GitHub-oriented repository readiness signals.")
    subparsers = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    scan_parser = subparsers.add_parser("scan", help="Scan a Git working tree root")
    scan_parser.add_argument("path", nargs="?", default=".", help="Git working tree root (default: current directory)")
    scan_parser.add_argument("--format", choices=("text", "json", "summary"), default="text")
    scan_parser.add_argument("--min-score", type=score_value, default=7.0,
                             help="Minimum score from 0 to 10 (default: 7)")
    scan_parser.add_argument("--fail-on", choices=("critical", "warning", "info", "none"), default="critical",
                             help="Fail on missing signals at this severity or higher (default: critical)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return scan(args.path, args.format, args.min_score, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())

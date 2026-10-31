# git-health

A small local checklist for maintainers preparing a Git repository for contributors. It looks for a limited set of GitHub-oriented files and README headings, reports the paths it found, and can fail a CI job when selected signals are missing.

The score measures **only these checklist signals**. It does not establish software quality, working CI, test coverage, license validity, security, or contribution readiness. A workflow candidate is not parsed or run. This is not a secret scanner; use a dedicated secret scanner and review tracked files separately. The tool inspects the working tree, including untracked and ignored files, not the contents of a Git commit.

## Install

Requires Python 3.10+ and Git. From a clone of this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

From the root of a Git working tree:

```bash
git-health scan .
```

Missing signals include a suggested next step. Found signals include a path and say what remains unverified. For automation:

```bash
git-health scan . --format json --min-score 7 --fail-on critical
```

The JSON response contains `root`, `score`, `summary`, `checks`, `gate`, and `limits`. Each check has a `passed` boolean, severity, recommendation, and an `evidence` path or null. A passing check means a named signal was found, not that its contents are correct.

The default gate requires a score of at least 7 out of 10 **and** no missing critical signals. Change the threshold with `--min-score` (0–10) and the severity with `--fail-on critical|warning|info|none`. Severity includes higher severities: `warning` fails for missing warning or critical signals; `info` fails for any missing signal; `none` disables severity gating. Both conditions must pass. Exit codes are 0 for a passing gate, 1 for a failed gate, and 2 for invalid input or a scan error. With `--format json`, errors are JSON objects on stdout, for example `{"error":{"code":"scan_error","message":"..."}}`; text errors go to stderr.

For example, a missing README, license, test file, or GitHub workflow candidate fails the default gate. Add the relevant files, run your tests and workflow independently, then rerun the scan. A passing checklist does not prove those commands work. If a signal does not apply to your project, review the results and select an appropriate gate explicitly; there is no per-check exclusion yet.

## Scope and limits

- The path must be the root of a non-bare Git working tree; it may contain uncommitted files. GitHub issue/PR templates and workflows are recognized in the locations checked by this tool, not every hosting provider's conventions.
- Checks require nonempty regular files. Tests are recognized by common Python and JavaScript/TypeScript test filenames under `test/` or `tests/`, including nested directories; test contents and execution are not validated. Workflow and issue-template candidates are selected by extension and nonempty content, not syntax or behavior.
- README installation and usage checks recognize standalone headings/lines such as `Install`, `Installation`, `Usage`, `Example`, `Quickstart`, `Quick start`, `Getting started`, or `Start with …` in README.md, README.rst, or README.txt. They do not validate instructions or examples. Headings in other forms or languages may be missed.
- Candidate files and directory components that are symbolic links are ignored; the selected root itself is resolved. Each candidate read is limited to 1 MiB, and each inspected directory to 2,000 entries. Recursive test discovery shares limits across both roots: 2,000 entries, five directory levels below a test root, 100 candidate reads, and 4 MiB of candidate data. Discovery stops after finding a signal; hitting a limit or an unreadable candidate stops the scan with an error instead of silently passing. These precautions are not a security boundary against a concurrently changing hostile filesystem.
- Citation metadata is not scored; it is not applicable to every project. Scores and check IDs may change while this project is in alpha.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

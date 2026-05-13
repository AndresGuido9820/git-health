# Contributing

Thanks for helping improve `git-health`.

## Local setup

```bash
git clone https://github.com/AndresGuido9820/git-health.git
cd git-health
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development workflow

1. Create a focused branch:
   ```bash
   git checkout -b feat/my-change
   ```
2. Keep changes small and covered by tests.
3. Run checks before opening a pull request:
   ```bash
   ruff check .
   pytest
   ```
4. Open a pull request with context, verification steps, and screenshots or terminal output when useful.

## Good first contributions

- Add a new repository health rule.
- Improve rule recommendations.
- Add JSON output for automation.
- Add a `fix` command that generates missing templates.
- Add examples for Python, Node or notebook repositories.

## Code style

- Prefer small functions with explicit names.
- Keep CLI parsing separate from scanning logic.
- Add tests for every new rule or reporter.
- Avoid network calls in core scanning unless the feature is explicitly API-based.


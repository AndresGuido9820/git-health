# Security Policy

## Supported versions

`git-health` is currently pre-1.0. Security fixes will target the latest version on `main`.

## Reporting a vulnerability

Please do not open public issues for vulnerabilities.

Report security problems by contacting the maintainer directly through GitHub. Include:

- affected version or commit,
- reproduction steps,
- expected impact,
- suggested fix if available.

## Scope

In scope:

- unsafe file handling,
- accidental secret disclosure caused by the tool,
- command execution vulnerabilities.

Out of scope:

- findings in repositories scanned by `git-health`,
- false positives in heuristic rules,
- vulnerabilities in optional development dependencies.


# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in doraemon, please report it
**privately** to the maintainers (see `pyproject.toml` `[tool.poetry]` for
contact information) rather than opening a public issue.

## Known historical exposure

Versions up to and including **0.2.0** contained a hardcoded PostgreSQL
password (`zgt#1024`) and an internal IP address (`10.170.138.230`) in
`src/doraemon/database_utils/main.py`. These values were committed to git
history.

If you ever ran the database referenced by this code, you **must rotate the
PostgreSQL password externally** — removing the literal from `HEAD` does
**not** remove it from git history. Anyone who cloned the repository before
this fix still has the credential.

The hardcoded value has been replaced with environment-variable lookups in
later versions; see `src/doraemon/database_utils/main.py` for the current
config interface.

## Supported versions

Only the latest minor release is actively supported with security fixes.

## Dependency scanning

This repository runs `bandit` (and ruff/mypy) via **pre-commit** on every
commit and via GitHub Actions (`.github/workflows/ci.yml`) on every push and
pull request. Install the local hooks with `poetry run pre-commit install`.

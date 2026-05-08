# Security Policy

## Six-layer defense model

This repo is designed so that forking it cannot leak your data. Here's how:

### Layer 1 — Aggressive `.gitignore`
`.env`, `/local/`, root-level `*.csv` and `*.parquet`, `.mcp.json` are all excluded. If you accidentally create a file in one of these patterns, git won't stage it.

### Layer 2 — Pre-commit hooks (local)
[gitleaks](https://github.com/gitleaks/gitleaks) and [detect-secrets](https://github.com/Yelp/detect-secrets) are installed automatically on `git clone` via `.pre-commit-config.yaml`. They scan every commit for credentials, API keys, and PII before the commit lands.

Install them:
```bash
pip install pre-commit
pre-commit install
```

### Layer 3 — Server-side PR scans
GitHub Actions runs the same secret-scanning checks on every pull request. If you skipped local hooks, the CI scan catches it before merge.

### Layer 4 — Required `/local/` subfolder pattern
Every recipe directory has a `local/` subfolder (gitignored). Put your real API keys, real CSV exports, and test data there. The public recipe only contains synthetic fixtures. This makes accidental commits structurally hard.

### Layer 5 — Minimum-data MCP responses
The Chili Piper MCP returns minimum necessary data by default — fitness signals ("is this account a fit: yes/no") rather than full records. Other MCPs should follow the same pattern.

### Layer 6 — Human-layer education
Every first-time contributor completes the PR checklist in [`.community/pr-checklist.md`](.community/pr-checklist.md) before their PR is reviewed. The checklist explicitly confirms no real data, no credentials, synthetic examples only.

---

## Reporting a vulnerability

If you find a security issue in this repo (a recipe that leaks credentials, a hook bypass, an MCP that returns more data than it should), please report it privately:

**Email:** security@chilipiper.com  
**Do not** open a public GitHub issue for security vulnerabilities.

We aim to respond within 48 hours and patch within 7 days.

---

## Scope

This policy covers:
- Code in this repository
- The Chili Piper MCP server (`mcp-servers/chili-piper/`)
- Pre-commit and CI tooling

It does **not** cover Chili Piper's SaaS product. For product security, see [chilipiper.com/security](https://chilipiper.com/security).

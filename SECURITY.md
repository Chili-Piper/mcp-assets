# Security Policy

This repository contains **skills and GPT configurations only — no customer data**. Skills are instructions; your data stays in your Chili Piper account and is accessed live via the MCP using your own credentials. Several layers keep it that way:

### Layer 1 — Aggressive `.gitignore`
`.env`, `/local/`, root-level `*.csv` and `*.parquet`, and credential files are excluded so they can't be staged by accident.

### Layer 2 — Pre-commit hooks (local)
[gitleaks](https://github.com/gitleaks/gitleaks) and [detect-secrets](https://github.com/Yelp/detect-secrets) are configured in `.pre-commit-config.yaml`. They scan every commit for credentials, API keys, and PII before it lands.

Install them:
```bash
pip install pre-commit
pre-commit install
```

### Layer 3 — Server-side CI scans
GitHub Actions runs the same secret-scanning checks on every pull request and push to `main`. If you skip the local hooks, CI catches it before merge.

### Layer 4 — Minimum-data MCP responses
The Chili Piper MCP returns only what a skill asks for, and API keys can be scoped to the exact permissions a skill needs. See [`mcp-servers/chili-piper/README.md`](mcp-servers/chili-piper/README.md#api-permissions).

### Layer 5 — Credentials never in the repo
API keys go in environment variables or your OS keychain — never in a committed file. Use a gitignored `local/` folder for any real test data.

---

## Reporting a vulnerability

If you find a security issue in this repo (a skill that leaks credentials, a hook bypass, or an MCP response that returns more data than it should), please report it privately:

**Email:** security@chilipiper.com
**Do not** open a public GitHub issue for security vulnerabilities.

We aim to respond within 48 hours.

---

## Scope

This policy covers:
- Skills and GPT configurations in this repository
- The Chili Piper MCP setup guidance (`mcp-servers/chili-piper/`)
- Pre-commit and CI tooling

It does **not** cover Chili Piper's SaaS product. For product security, see [chilipiper.com/security](https://chilipiper.com/security).

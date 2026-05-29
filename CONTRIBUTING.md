# Contributing

These are Chili Piper's official skills, maintained by Chili Piper. We welcome bug reports, fixes, and new skill ideas from the community.

## Report a bug or request a skill

- **Something broken or returning wrong data?** Open a [skill bug report](https://github.com/Chili-Piper/mcp-assets/issues/new?template=skill-bug.yml).
- **Want a new skill or an improvement?** Open a [skill request](https://github.com/Chili-Piper/mcp-assets/issues/new?template=skill-request.yml).

## Submitting a change

1. Fork and branch.
2. Follow the structure in [`skills/README.md`](skills/README.md) — each skill is `skills/<slug>/SKILL.md` with a `references/` folder for deep dives.
3. If your change affects a skill that also ships as a ChatGPT GPT, update the paired `gpts/<slug>/` to the same `version`.
4. Run the checks locally:
   ```bash
   pip install pre-commit pyyaml
   pre-commit run --all-files
   python .github/scripts/validate_skill_frontmatter.py
   ```
5. Open a PR — the [skill PR template](.github/PULL_REQUEST_TEMPLATE/skill.md) checklist will guide you.

## Quality bar

- MCP tool names and response field names must match the **live** Chili Piper MCP schema.
- No real customer data, credentials, or API keys — ever. Synthetic examples only.
- Read-only vs. write behavior must be stated accurately in each skill's `writes_to`.
- Test read-only skills against a real tenant and log the result in [`docs/QA.md`](docs/QA.md).

Thanks for helping make these better. 🌶️

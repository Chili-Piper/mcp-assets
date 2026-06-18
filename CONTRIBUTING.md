# Contributing

These are Chili Piper's official skills, maintained by Chili Piper. We welcome bug reports, fixes, and new skill ideas from the community.

## Report a bug, request a skill, or float an idea

- **Something broken or returning wrong data?** Open a [skill bug report](https://github.com/Chili-Piper/mcp-assets/issues/new?template=skill-bug.yml).
- **Want a new skill or an improvement (concrete spec)?** Open a [skill request](https://github.com/Chili-Piper/mcp-assets/issues/new?template=skill-request.yml).
- **Have a rough idea you may not build yourself?** Open a [skill idea](https://github.com/Chili-Piper/mcp-assets/issues/new?template=skill-idea.yml).

## The skill idea inbox

Ideas live as **GitHub issues**, not as half-built files in the repo — so anyone can view them, comment, react with 👍, and pick one up when it's ready to build. Browse the inbox here: **[open skill ideas](https://github.com/Chili-Piper/mcp-assets/issues?q=is%3Aissue+label%3Askill-idea)**.

Both people and our automated `edge-api-skill-sync` routine file ideas into the same inbox. A maintainer triages each with a status label:

| Label | Meaning |
|-------|---------|
| `skill-idea` | It's a proposal to discuss, not yet committed work |
| `source:community` / `source:auto` | Submitted by a person vs. surfaced by the sync routine |
| `status:needs-api` | Blocked — needs a new or changed Edge API before it can be built |
| `status:ready-to-build` | The API exists; anyone is welcome to pick it up |
| `status:in-progress` | Someone is actively building it |
| `status:built` | Shipped — a skill now exists; the issue is closed and links the PR |
| `status:declined` | Not moving forward (out of scope, duplicate, or low value) |

When you build a `status:ready-to-build` idea, open a PR that closes its issue (`Closes #NN`) so the idea and the delivered skill stay linked.

## Submitting a change

1. Fork and branch.
2. Read [`docs/methodology.md`](docs/methodology.md) — the Interpreted-Context authoring standard every skill follows (layered loading, file budgets, the required SKILL.md shape) — and start from [`docs/SKILL.template.md`](docs/SKILL.template.md). Each skill is `skills/<slug>/SKILL.md` with a `references/` folder for deep detail; see [`skills/README.md`](skills/README.md) for the frontmatter schema.
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

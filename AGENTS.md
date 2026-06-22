# AGENTS.md — repo orientation

Layer-0 orientation for any agent working **in** this repo (authoring or reviewing
skills). If you're an agent *running* a skill, you don't need this — load the skill.

## What this repo is

Official, first-party **Skills** and **ChatGPT GPTs** for the Chili Piper MCP server.
Each skill teaches an agent to do one Chili Piper task correctly: which MCP tools to
call, in what order, and how to format the result. Skills are instructions only — this
repo holds **zero customer data**.

## Layout

| Path | What it is |
|------|-----------|
| `skills/<slug>/SKILL.md` | A skill: frontmatter contract + Process. The entry point. |
| `skills/<slug>/references/*.md` | Deep detail (API fields, output formats, procedures), loaded on demand. |
| `gpts/<slug>/` | The ChatGPT version of each skill — `GPT.md` + `openapi.yaml`. |
| `commands/*.md` | Thin slash-command wrappers that invoke a skill. |
| `mcp-servers/chili-piper/` | How to connect the Chili Piper MCP (API key / OAuth). |
| `docs/` | `methodology.md` (authoring standard), `QA.md` (maturity tracker), `org-deployment.md`. |
| `.github/scripts/` | CI checks: frontmatter+structure, GPT sync, packaging. |

## The one rule that governs structure

Skills follow **progressive disclosure** (Anthropic's Agent Skills convention): one job
per file, load only what the current step needs, canonical sources, plain-text. The full
standard — the loading stages, file budgets, and the required SKILL.md shape — is
[`docs/methodology.md`](docs/methodology.md). **Read it before adding or editing a
skill.** Start a new skill by copying [`docs/SKILL.template.md`](docs/SKILL.template.md).

## Hard constraints

- **No real data, credentials, or API keys — ever.** Synthetic examples only.
- **MCP tool and field names must match the live MCP**, not the tool's own (often wrong)
  blurb. Put the verified truth in a skill's `references/api-reference.md`.
- **`writes_to` must be accurate.** Read-only skills say so; write skills default to a
  dry run and checkpoint before mutating.
- **SKILL ↔ GPT parity.** A behavior change bumps both the SKILL.md and the paired
  GPT.md `version`; a pure structural refactor keeps the version.

## Before you commit

```bash
pip install pyyaml pre-commit
pre-commit run --all-files
python .github/scripts/validate_skill_frontmatter.py
python .github/scripts/check_gpt_sync.py
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contribution flow.

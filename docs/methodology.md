# Skill authoring methodology — progressive disclosure

This is the authoring standard for every skill in this repo. It is Anthropic's **Agent
Skills progressive-disclosure** model, made concrete for Chili Piper skills with a few
repo-specific rules (file budgets, a required `SKILL.md` shape). Other docs in the repo
link here rather than restating it.

> **Primary source.** Anthropic, *Agent Skills* —
> [platform.claude.com/docs/en/agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
>
> **Convergent framing we drew on.** The same "folder structure as agent architecture"
> idea is described independently as the Interpreted-Context Methodology
> ([RinDig/Interpreted-Context-Methdology](https://github.com/RinDig/Interpreted-Context-Methdology) —
> note the repo owner's spelling of the slug; and the preprint
> [arXiv:2603.16021](https://arxiv.org/pdf/2603.16021)). Useful vocabulary, but Anthropic's
> convention above is the authority for how these skills are built.

---

## Why progressive disclosure

A skill is context an agent loads to do one job. Progressive disclosure is the discipline
of being deliberate about what enters the context window and what stays on disk until it's
actually needed. The payoff for these skills is concrete — an agent spends ~2–8k tokens on
the right slice of a skill instead of ~30k on the whole thing, and a human can audit
exactly which files an agent will read, in what order.

## The principles

1. **Single responsibility.** One skill does one Chili Piper task. One reference file
   covers one topic (an API surface, an output format, one procedure).
2. **Plain-text interfaces.** Everything is Markdown a human can read and edit.
3. **Load only what the step needs.** The agent reads the cheapest layer that answers its
   current step and stops. Deep detail lives behind an explicit "load this when…".
4. **Glass-box.** Every artifact is inspectable; a reviewer can see precisely which files
   an agent will pull and in what order.
5. **Canonical sources, one-way dependencies.** Each fact lives in exactly one file;
   everything else links to it. If A references B, B must not reference A.

## The loading stages, mapped to this repo

Anthropic's model loads a skill in three stages; we add a repo-level orientation file on
top for *authors* working across skills.

| Stage | Anthropic model | In this repo |
|------|-----------------|--------------|
| (author orientation) | — | [`AGENTS.md`](../AGENTS.md) — what this repo is, the layout, the rules. ~1 screen. |
| Discovery | name + `description` only | A skill's frontmatter `description` — the one sentence an agent reads to decide *whether to load this skill at all*. |
| Activation | full `SKILL.md` | `skills/<slug>/SKILL.md` body — Inputs → Process → Outputs for this one task. |
| Execution | referenced files, as needed | `skills/<slug>/references/*.md` — API field names, output formats, deep procedures. Loaded **on demand** from a Process step. |

An agent should be able to route on the `description`, execute the happy path on
`SKILL.md`, and only drop to a reference when a step says so.

## Required SKILL.md shape

Copy [`SKILL.template.md`](SKILL.template.md). Every SKILL.md has, in order:

1. **Frontmatter** — the schema in [`../skills/README.md`](../skills/README.md). The
   `description` is the discovery line: one sentence, ≤ 280 characters. List every
   `references/` file in `references:` and nothing that isn't a file.
2. **Role line** — one or two sentences: who the agent is and the job.
3. **When to use** — the situations this skill is the right tool for.
4. **Inputs** — a table; mark each input required/optional with its default.
5. **Process** — numbered steps. This is the heart. Each step that needs deep detail
   ends in a **selective-routing pointer**: *"→ load `references/x.md` § Section."*
   Point at the *section*, not just the file — that is what keeps loading thin.
6. **Preflight audit** — a short checklist with unambiguous pass conditions the agent
   verifies *before* it writes output (and, for write skills, before it mutates data).
7. **Checkpoint** — the `human_decision_point`: where the agent must stop for a human.
   Write skills checkpoint **before** any mutation; read skills checkpoint on the
   recommendation.
8. **Data handling** — PII touched, storage (always ephemeral here), writes (yes/no).

## Selective section routing

Don't write "see `references/api-reference.md`." Write the step's pointer as
*"field names → `references/api-reference.md` § Critical field name differences."*
The agent loads one section, not the file. References therefore carry stable `##`
headings that Process steps can name. (Anthropic's guidance: for a reference over ~100
lines, include a table of contents at the top.)

## File budgets

Progressive disclosure works only if each file is small enough to load whole. Anthropic
suggests keeping a SKILL.md under ~500 lines and splitting longer files; we hold a tighter
repo budget so the entry point stays lean:

| File | Budget | Enforcement |
|------|--------|-------------|
| `references/*.md` | ≤ 200 lines | **hard** — CI fails |
| `SKILL.md` | ≤ 200 lines | warning — push detail into `references/` |
| frontmatter `description` | ≤ 280 chars | warning — it's a discovery line, not a summary |
| `AGENTS.md` | ≤ 80 lines | by convention |

When a SKILL.md outgrows its budget, the fix is always the same: move the deep detail
(API tables, output formats, long procedures) into a `references/*.md` and replace it
in the Process with a one-line selective-routing pointer.

## When a SKILL.md needs references

Split detail out the moment any of these is true: the body exceeds the budget; the same
facts (e.g. exact MCP field names) would otherwise be repeated; or a step's detail is
only needed on one branch. Reference candidates, in order of how often they're needed:
`api-reference.md` (field names, limits, gotchas — the canonical API truth for the
skill), `output-format.md` (the exact result layout), then one file per deep procedure
(e.g. `routing-trace.md`).

## Checks before you commit

```bash
pip install pyyaml
python .github/scripts/validate_skill_frontmatter.py   # frontmatter + structure
python .github/scripts/check_gpt_sync.py               # SKILL <-> GPT parity
```

A structural refactor that doesn't change behavior keeps the existing skill `version` (and
so needs no paired GPT edit). Bump a skill `version` only when behavior changes — and then
bump the paired `gpts/<slug>/GPT.md` to match. The **plugin** version
(`.claude-plugin/plugin.json` + `marketplace.json`) is separate: bump it whenever you want
installed clients to pull an update, since org distribution keys off it.

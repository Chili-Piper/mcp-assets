# Skill authoring methodology — Interpreted Context

This is the **canonical** standard for how every skill in this repo is written. It
adapts the **Interpreted Context Methodology (ICM)** — *folder structure as agent
architecture* — to Chili Piper skills. When anything elsewhere in the repo conflicts
with this file, this file wins; other docs link here rather than restating it.

> **Sources.** ICM, "Folder Structure as Agent Architecture"
> ([RinDig/Interpreted-Context-Methodology](https://github.com/RinDig/Interpreted-Context-Methdology));
> *Interpretable Context Methodology: Folder Structure as Agentic Architecture*
> ([arXiv:2603.16021](https://arxiv.org/pdf/2603.16021)).

---

## Why ICM here

A skill is context an agent loads to do one job correctly. ICM's claim is that the
**filesystem layout is the architecture**: scope each file to one job, load only what
the current step needs, and keep every artifact human-readable. The payoff for these
skills is concrete — an agent spends ~2–8k tokens on the right slice of a skill instead
of ~30k on the whole thing, and a human can audit exactly what the agent will read.

## The five principles

1. **Single responsibility.** One skill does one Chili Piper task. One reference file
   covers one topic (an API surface, an output format, one procedure).
2. **Plain-text interfaces.** Everything is Markdown a human can read and edit. No
   binary formats, no proprietary serialization.
3. **Layered context loading.** The agent reads the cheapest layer that answers its
   current step and stops. Deep detail lives behind an explicit "load this when…".
4. **Human-editable, glass-box outputs.** Every intermediate is inspectable; a reviewer
   can see precisely which files an agent will pull and in what order.
5. **Canonical sources, one-way dependencies.** Each fact lives in exactly one file;
   everything else links to it. If A references B, B must not reference A.

## The context layers, mapped to this repo

| Layer | ICM role | In this repo |
|------|----------|--------------|
| 0 | System orientation | [`AGENTS.md`](../AGENTS.md) — what this repo is, the layout, the rules. ~1 screen. |
| 1 | Task routing | A skill's frontmatter `description` — the one sentence an agent reads to decide *whether to load this skill at all*. |
| 2 | Stage contract | `skills/<slug>/SKILL.md` body — Inputs → Process → Outputs for this one task. |
| 3 | Reference material | `skills/<slug>/references/*.md` — API field names, output formats, deep procedures. Loaded **on demand** from a Process step. |
| 4 | Working artifacts | Live MCP responses and anything the run produces. Never committed. |

An agent should be able to route on layer 1, execute the happy path on layer 2, and
only drop to layer 3 when a step says so.

## Required SKILL.md shape

Copy [`SKILL.template.md`](SKILL.template.md). Every SKILL.md has, in order:

1. **Frontmatter** — the schema in [`../skills/README.md`](../skills/README.md). The
   `description` is the layer-1 router: one sentence, ≤ 280 characters. List every
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
headings that Process steps can name.

## File budgets

ICM keeps every file small enough to load whole. Enforced/recommended here:

| File | Budget | Enforcement |
|------|--------|-------------|
| `references/*.md` | ≤ 200 lines | **hard** — CI fails |
| `SKILL.md` | ≤ 200 lines | warning — push detail into `references/` |
| frontmatter `description` | ≤ 280 chars | warning — it's a router, not a summary |
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
python .github/scripts/validate_skill_frontmatter.py   # frontmatter + ICM structure
python .github/scripts/check_gpt_sync.py               # SKILL <-> GPT parity
```

A structural refactor that doesn't change behavior keeps the existing `version` (and so
needs no paired GPT edit). Bump `version` only when behavior changes — and then bump the
paired `gpts/<slug>/GPT.md` to match.

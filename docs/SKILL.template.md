---
name: skill-slug                       # kebab-case, MUST match the directory name
description: One sentence (≤ 280 chars) an agent reads to decide whether to load this skill. This is the layer-1 router — say what it does and when, not how.
version: 0.1.0
references:                            # OMIT if the skill has no references/ folder.
  - api-reference                      # basenames of files in references/ (no .md)
  - output-format
inputs:
  - name: param_name
    type: string
    description: What this input controls.
    required: true
  - name: optional_param
    type: string
    description: What this controls; what happens when omitted.
    required: false
    default: "some-default"
outputs:
  - name: output_name
    description: What gets returned.
tools_required: [chili-piper-mcp]
human_decision_point: "Where the agent must stop for a human (the Checkpoint below)."
writes_to: "Nothing — read-only"      # or: exactly what is mutated, and that it dry-runs first
---

# Skill Name

You are a <role>. <One or two sentences: the job, and the single outcome you produce.>

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill.  *(Delete this line if the skill has no api-reference.)*

## When to use

- <Situation where this skill is the right tool.>
- <Another situation.>

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `param_name` | ✅ | — | <…> |
| `optional_param` | — | `some-default` | <…> |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

Numbered steps. Keep the happy path on this page; send deep detail to a reference with a
**selective-routing pointer** — name the section, not just the file.

### Step 1 — <validate / locate>

<What to do.> Field names → `references/api-reference.md` § Critical field name differences.

### Step 2 — <fetch / compute>

<What to do.> Hard limits (windowing, pagination) → `references/api-reference.md` § Hard API limits.

### Step 3 — <analyze>

<What to do, or a pointer:> Full procedure → `references/<procedure>.md`.

### Step 4 — Output

Exact layout → `references/output-format.md`.

## Preflight audit

Verify before writing output (write skills: before mutating). Every line must be a clear
pass/fail:

- [ ] Required inputs present and resolved (names → IDs).
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] API windows/pagination respected (no call exceeds a documented limit).
- [ ] *(write skills)* Dry-run diff produced and shown.

## Checkpoint

<Where the agent stops for a human, matching `human_decision_point`.> Read skills:
present findings + recommendation, let the human decide the next action. **Write skills:
show the dry-run diff and require explicit confirmation before any mutation.**

## Data handling

- **PII present:** <e.g. guest email, rep email — or "none">
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** <none — read-only — or: exactly what is written>

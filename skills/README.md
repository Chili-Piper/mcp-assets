# Skills

Small, reusable Claude Code specialists — one technique each. Skills are the building blocks that recipes assemble into workflows.

A skill does one thing well. It can be dropped into a recipe with a single reference in `stack:`.

---

## How to use a skill

In Claude Code, invoke a skill command directly:

```
/inspect-meeting guest@example.com
/audit-routing "APAC Sales"
```

Or reference a skill in a recipe's `stack:` field — Claude Code will load it automatically when you `/run-recipe`.

To load a skill manually for an ad-hoc task:

```
Read skills/<skill-name>/SKILL.md
```

---

## Skill structure

Each skill lives in its own directory:

```
skills/
└── meeting-inspector/
    ├── SKILL.md           # overview, inputs/outputs, quick API table, step-by-step
    └── references/
        ├── api-reference.md      # full field names, status codes, known gotchas
        ├── routing-trace.md      # how to fetch and interpret routing traces
        ├── anomaly-detection.md  # anomaly table and severity definitions
        └── output-format.md      # exact output template
```

**`SKILL.md`** — the entry point. Frontmatter declares inputs, outputs, tools required, and which reference files exist. Contains the high-level steps and quick API table. Read this first.

**`references/`** — deep dives. Load only the reference files relevant to your current step. A skill's frontmatter lists available references under `references:`.

This two-tier structure lets agents load minimal context for quick answers and drill into reference docs only when needed — mirroring the pattern used by [AWS](https://github.com/aws/agent-toolkit-for-aws) and [Cloudflare](https://github.com/cloudflare/skills) skills repositories.

---

## Skill frontmatter schema

```yaml
---
name: skill-name                    # kebab-case, matches directory name
description: One sentence           # used by agents to decide whether to load this skill
version: 0.1.0
references:                         # list of basename files in references/
  - api-reference
  - output-format
inputs:
  - name: param_name
    type: string
    description: What this input controls
    required: true
outputs:
  - name: output_name
    description: What gets returned
tools_required: [chili-piper-mcp]   # MCP names the skill needs
human_decision_point: "When human must approve before continuing"
writes_to: "Where outputs go, or 'Nothing — read-only'"
---
```

---

## Skill index

### Analytics & diagnostics

| Skill | What it does |
|-------|-------------|
| [meeting-inspector](meeting-inspector/SKILL.md) | Deep-dives into a single meeting — routing path, rep assignment, outcome, anomalies |
| [no-show-analyzer](no-show-analyzer.md) | Analyzes no-show patterns and predicts/prevents recurrence |
| [routing-audit](routing-audit.md) | Audits all concierge routers for coverage gaps and stale rules |
| [availability-inspector](availability-inspector.md) | Diagnoses why a rep has no available slots |

### User & org operations

| Skill | What it does |
|-------|-------------|
| [user-details](user-details.md) | Fetches and summarizes a user's profile info |
| [user-meetings](user-meetings.md) | Gets a user's meeting history |
| [user-copy](user-copy.md) | Generates user-specific copy/personalization |
| [user-offboarding](user-offboarding.md) | Handles user offboarding workflows |
| [org-meeting](org-meeting.md) | Organizes multi-party meeting logistics |
| [concierge-debugger](concierge-debugger.md) | Debugs Chili Piper routing issues |

### Planned

- `score-account-nrr-fit` — score accounts on expansion potential, not just ICP
- `draft-outreach-email` — draft a personalized email from account + persona context
- `summarize-gong-call` — extract key moments, objections, next steps from a call transcript
- `enrich-account` — fill gaps in account data using Clay + LinkedIn signals

---

## Contributing a skill

1. Create `skills/<your-slug>/SKILL.md` using the frontmatter schema above
2. Add `references/*.md` for any deep-dive content (API details, output templates, decision tables)
3. Register the skill in this README's index
4. Reference the skill in at least one recipe's `stack:` field (or open a draft PR if the recipe is in-flight)

See [.community/CONTRIBUTING.md](../.community/CONTRIBUTING.md) for the full contribution guide.

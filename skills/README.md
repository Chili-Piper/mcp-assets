# Skills

Official Chili Piper Skills — small, reusable AI specialists that each do one Chili Piper task well, running against your account through the [Chili Piper MCP](../mcp-servers/chili-piper/README.md).

Each skill works in Claude Code (and other Claude Skills-compatible agents). The ChatGPT equivalents live in [`../gpts/`](../gpts/).

---

## How to use a skill

Install the plugin (`/plugin marketplace add Chili-Piper/mcp-assets` → `/plugin install chili-piper-skills@chili-piper-skills`) and invoke the bundled commands:

```
/inspect-meeting guest@example.com
/audit-routing "APAC Sales"
```

Or just describe what you want — the agent loads the matching skill automatically. To load one manually for an ad-hoc task:

```
Read skills/<skill-name>/SKILL.md
```

---

## Skill structure

Skills follow **progressive disclosure** (Anthropic's Agent Skills convention) — one job per file, with on-demand loading of deep detail. The full authoring standard (the principles, the loading stages, file budgets, and the required SKILL.md shape) is in [`../docs/methodology.md`](../docs/methodology.md); copy [`../docs/SKILL.template.md`](../docs/SKILL.template.md) to start a new skill.

Each skill lives in its own directory:

```
skills/
└── meeting-inspector/
    ├── SKILL.md           # overview, inputs/outputs, quick API table, step-by-step
    └── references/        # optional deep-dive docs, loaded on demand
        ├── api-reference.md
        ├── routing-trace.md
        ├── anomaly-detection.md
        └── output-format.md
```

**`SKILL.md`** — the entry point. Frontmatter declares `name`, `description`, `version`, inputs/outputs, `tools_required`, and `writes_to`. Read this first.

**`references/`** — deep dives loaded only when a step needs them, keeping context minimal.

---

## Skill frontmatter schema

```yaml
---
name: skill-name                    # kebab-case, matches directory name
description: One sentence           # used by agents to decide whether to load this skill
version: 0.1.0
references:                         # optional — basenames of files in references/
  - api-reference
inputs:
  - name: param_name
    type: string
    description: What this input controls
    required: true
outputs:
  - name: output_name
    description: What gets returned
tools_required: [chili-piper-mcp]   # MCP the skill needs
human_decision_point: "When a human must approve before continuing"
writes_to: "Where outputs go, or 'Nothing — read-only'"
---
```

---

## Maturity

Every skill carries a QA maturity level (tracked in [`../docs/QA.md`](../docs/QA.md)):

- **`draft`** — known issues or not yet verified against the live MCP.
- **`tested`** — static review complete; tool names, response field names, and limits verified against the live MCP. No known correctness bugs.
- **`verified`** — `tested` plus a successful end-to-end run against a real tenant.

---

## Skill index

### Analytics & diagnostics (read-only)

| Skill | What it does | Maturity |
|-------|-------------|:--------:|
| [meeting-inspector](meeting-inspector/SKILL.md) | Deep-dives a single meeting — routing path, rep assignment, outcome, anomalies | `verified` |
| [no-show-analyzer](no-show-analyzer/SKILL.md) | Analyzes no-show patterns by trigger, route, rep, or workspace | `verified` |
| [routing-audit](routing-audit/SKILL.md) | Audits all concierge routers for coverage gaps and stale rules | `verified` |
| [availability-inspector](availability-inspector/SKILL.md) | Diagnoses why a rep or team has no available slots | `verified` |
| [concierge-debugger](concierge-debugger/SKILL.md) | Traces why a specific lead didn't book | `verified` |
| [distro-debugger](distro-debugger/SKILL.md) | Debugs why a CRM record was routed (or not) through a distribution — rule stage by rule stage | `draft` |
| [chat-conversation-inspector](chat-conversation-inspector/SKILL.md) | Inspects Chat AI conversation logs — routing outcomes, transcripts, abandonment analysis | `draft` |
| [org-meeting](org-meeting/SKILL.md) | Org-wide (and single-tenant) meeting volume and health snapshot | `verified` |
| [distribution-analysis](distribution-analysis/SKILL.md) | Analyzes a round-robin distribution — meeting counts by rep, imbalance vs. weights, skew, cancellations | `verified` |

### User & org operations

| Skill | What it does | Maturity |
|-------|-------------|:--------:|
| [user-details](user-details/SKILL.md) | Full profile for any Chili Piper user | `verified` |
| [user-meetings](user-meetings/SKILL.md) | Rep-level meeting volume and health metrics | `verified` |
| [user-copy](user-copy/SKILL.md) | Copies a user's workspace/team memberships (and, optionally, licenses) to another user (writes) | `tested` |
| [user-offboarding](user-offboarding/SKILL.md) | Safely removes a departing rep, with an audit trail (writes/destructive) | `tested` |

### Configuration management (writes)

| Skill | What it does | Maturity |
|-------|-------------|:--------:|
| [meeting-type-management](meeting-type-management/SKILL.md) | Manages team meeting types and their email/SMS reminders — durations, invite text, limits (writes/destructive) | `draft` |
| [distro-router-configuration](distro-router-configuration/SKILL.md) | Manages Distro lead-routing routers — full lifecycle with async status polling (writes/destructive) | `draft` |
| [handoff-router-configuration](handoff-router-configuration/SKILL.md) | Manages Handoff routers — rep-to-rep routing rules; always-live writes (writes/destructive) | `draft` |

> ⚠️ `user-copy`, `user-offboarding`, and the configuration-management skills modify Chili Piper data. All default to `dry_run: true` and require explicit human confirmation before any write.

---

## Contributing a skill

1. Create `skills/<your-slug>/SKILL.md` using the frontmatter schema above.
2. Add `references/*.md` for any deep-dive content.
3. Register the skill in this index with its maturity status.
4. If a ChatGPT version applies, add the paired `../gpts/<your-slug>/` at the same `version`.
5. Run the checks locally:
   ```bash
   pip install pyyaml
   python ../.github/scripts/validate_skill_frontmatter.py
   ```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full guide.

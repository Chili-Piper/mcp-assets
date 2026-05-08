# Skills

Small, reusable Claude Code specialists — one technique each. Skills are the building blocks that recipes assemble into workflows.

A skill does one thing well. It can be dropped into a recipe with a single `<skill>` reference.

---

## How to use a skill

In Claude Code, invoke a skill with:

```
/skill-name [arguments]
```

Or reference it in a recipe's `stack` field and Claude Code will load it automatically when you run the recipe.

---

## Skill index

*No skills yet — [submit the first one](../.community/CONTRIBUTING.md).*

### Planned skills (from incoming recipes)
- `score-account-nrr-fit` — score accounts on expansion potential, not just ICP
- `draft-outreach-email` — draft a personalized email from account + persona context
- `summarize-gong-call` — extract key moments, objections, and next steps from a call transcript
- `enrich-account` — fill gaps in account data using Clay + LinkedIn signals

---

## Skill file structure

```markdown
---
name: skill-name
description: One sentence on what this skill does
inputs:
  - name: account_id
    type: string
    description: Salesforce account ID
outputs:
  - name: score
    type: number
    description: NRR fit score 0-100
tools_required: [salesforce-mcp, clay-mcp]
---

# Skill body (prompt + instructions for Claude Code)
```

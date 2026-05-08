# Agents

Multi-step AI workers that combine skills + MCPs to run a complete workflow autonomously — with defined human decision points.

An agent is not fully autonomous. Every agent in this repo declares when it pauses for human review.

---

## Agent index

*No agents yet — [submit the first one](../.community/CONTRIBUTING.md).*

### Planned agents (from incoming recipes)
- `weekly-campaign-audit` — reviews bottom-decile campaigns and surfaces optimization recommendations for demand-gen review
- `expansion-signal-monitor` — watches usage data + CRM signals and creates expansion tasks when thresholds are hit

---

## Agent file structure

```markdown
---
name: agent-name
description: One sentence on what this agent does
schedule: weekly | daily | on-trigger | manual
human_decision_points:
  - step: 3
    description: "Review flagged accounts before outreach is sent"
skills_used: [score-account-nrr-fit, draft-outreach-email]
mcps_used: [salesforce-mcp, chili-piper-mcp]
---

# Agent body (multi-step instructions for Claude Code)
```

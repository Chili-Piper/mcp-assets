---
description: Org-wide meeting volume and health snapshot — total booked, completed, no-show, and cancelled by workspace — for weekly or monthly executive reviews.
argument-hint: "[date-range] [group-by]"
allowed-tools: [Read]
---

# /org-meeting-report

Produce an org-wide meeting health snapshot using the `org-meeting` skill.

## Steps

1. Read `skills/org-meeting/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs (both optional):
   - `date-range` → `date_range` (`last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-7-days`). The skill paginates automatically across the API's 7-day-per-call limit.
   - `group-by` → `group_by` (`workspace` | `rep` | `status`; default `workspace`).
4. Execute the skill's steps in order.
5. Output the org summary, the breakdown by the selected dimension, and any flagged workspaces/reps with above-average no-show rates.
6. Ask: *"Want to share this with leadership, drill into a flagged workspace with `/analyze-no-shows`, or check a specific rep with `/user-meetings`?"*

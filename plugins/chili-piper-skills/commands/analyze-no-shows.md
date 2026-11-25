---
description: Analyzes Chili Piper meeting no-show patterns by trigger type, routing path, rep, or workspace to surface actionable optimization opportunities.
argument-hint: "[date-range] [workspace] [group-by] [threshold]"
allowed-tools: [Read]
---

# /analyze-no-shows

Surface no-show patterns and root-cause hypotheses using the `no-show-analyzer` skill.

## Steps

1. Read `skills/no-show-analyzer/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs (all optional):
   - `date-range` → `date_range` (`last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-30-days`). For trigger/route breakdowns, routing context (`concierge-logs`) caps at 30 days.
   - `workspace` → `workspace` (name or ID). Omit for org-wide.
   - `group-by` → `group_by` (`trigger` | `route` | `rep` | `workspace`; default `trigger`).
   - `threshold` → `flag_threshold` (no-show % above which a segment is flagged; default 30).
4. Execute the skill's steps in order.
5. Output the summary, the breakdown by the selected dimension, the flagged segments with hypotheses, and the recommended actions.
6. Ask: *"Which routing rule or confirmation-flow change do you want to test first?"*

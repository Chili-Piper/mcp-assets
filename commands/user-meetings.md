---
description: Shows all meetings assigned to a specific rep for a period — volume, statuses, and no-show rate — to surface rep-level pipeline health.
argument-hint: "<rep-email-or-name> [date-range] [workspace]"
allowed-tools: [Read]
---

# /user-meetings

Show a single rep's meeting health using the `user-meetings` skill.

## Steps

1. Read `skills/user-meetings/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `user` (email, name, or user ID of the rep). **Required** — if missing, ask: *"Which rep's meetings should I pull?"*
   - Optional `date-range` → `date_range` (`last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-30-days`). The skill paginates across the API's 7-day-per-call limit.
   - Optional `workspace` → `workspace` (name or ID). Omit for org-wide.
4. Execute the skill's steps in order.
5. Output the summary (volume, completion rate, no-show rate), the meeting list, and any anomaly flags.
6. Ask: *"Coaching conversation, territory/routing adjustment, or no action?"*

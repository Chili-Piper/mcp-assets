---
description: Checks why a rep or team is showing no available slots — diagnoses calendar connectivity, working hours, meeting limits, and distribution membership to find the specific blocker.
argument-hint: "<rep-email-or-name> [workspace] [lookahead-days]"
allowed-tools: [Read]
---

# /check-availability

Diagnose why a rep or team has no bookable slots using the `availability-inspector` skill.

## Steps

1. Read `skills/availability-inspector/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `user` (email, name, or user ID). **Required** — if missing, ask: *"Which rep should I check availability for?"*
   - Optional second argument → `workspace` (name or ID) to scope team/distribution lookup.
   - Optional `lookahead-days` → `lookahead_days` (default 14).
4. Execute the skill's steps in order.
5. Output the availability result, per-day slot breakdown, any per-rep failure reasons, the diagnosis, and the step-by-step fix.

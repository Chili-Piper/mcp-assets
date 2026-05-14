---
description: Inspect a single Chili Piper meeting — routing path, rep assignment, outcome, and anomalies — and get a recommended next action.
argument-hint: "<meeting-id or guest@email.com>"
allowed-tools: [Read]
---

# /inspect-meeting

Deep-dive into one meeting using the `meeting-inspector` skill.

## Steps

1. Read `skills/meeting-inspector/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Determine the input type from the argument:
   - Looks like a UUID or numeric ID → use as `meeting_id`
   - Contains `@` → use as `guest_email`
   - Neither → ask: *"Is that a meeting ID or a guest email address?"*
4. Load `skills/meeting-inspector/references/api-reference.md` before making any MCP calls — it contains critical field-name gotchas.
5. Execute the skill steps in order.
6. Output the full inspector report (summary, routing trace, anomalies, recommended action).

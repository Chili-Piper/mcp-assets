---
description: Debugs why a specific lead did not book — traces the concierge routing session, identifies the rule that fired (or why none did), and recommends a targeted fix.
argument-hint: "<guest@email.com> [router] [date-range]"
allowed-tools: [Read]
---

# /debug-concierge

Trace why a lead did not book using the `concierge-debugger` skill.

## Steps

1. Read `skills/concierge-debugger/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `guest_email`. **Required** — if missing, ask: *"What's the email of the lead who didn't book?"*
   - Optional second argument → `router` (name or slug). Omit to search all routers.
   - Optional `date-range` → `date_range` (`today`, `last-7-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-7-days`). Note `concierge-logs` caps at a 30-day window.
4. Execute the skill's steps in order.
5. Output the routing session, the plain-language diagnosis, and the specific router fix.
6. Ask: *"Want me to help draft the rule change, or rebook this lead manually?"*

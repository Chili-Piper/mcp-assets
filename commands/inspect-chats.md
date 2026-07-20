---
description: Inspects Chat AI conversation logs for a workspace — routing-outcome breakdowns (Routed/NotRouted/Abandoned), transcripts, and abandonment analysis.
argument-hint: "<workspace> [playbook-id] [date-range] [guest@email.com]"
allowed-tools: [Read]
---

# /inspect-chats

Analyze Chat AI conversation outcomes and transcripts using the `chat-conversation-inspector` skill.

## Steps

1. Read `skills/chat-conversation-inspector/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace`. **Required** — if missing, ask: *"Which workspace should I inspect?"*
   - A UUID argument → `playbook`. Omit to include all playbooks.
   - `date-range` → `date_range` (`today`, `last-7-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-7-days`). Note `chat-logs` caps each call at a 30-day window — longer ranges are chunked.
   - An email argument → `guest_email` (transcript drill-down for that guest).
4. Execute the skill's steps in order.
5. Output the outcome summary, per-playbook breakdown, any requested transcripts, and the abandonment findings with the recommendation.
6. Ask: *"Want me to drill into specific transcripts, or compare a different date range?"*

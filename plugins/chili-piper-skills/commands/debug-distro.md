---
description: Debugs why a CRM record was routed (or not routed) through a Chili Piper distribution — explains each rule stage and recommends a targeted fix.
argument-hint: "<log-id|salesforce-id|record-name> [router-id] [workspace] [date-range]"
allowed-tools: [Read]
---

# /debug-distro

Trace why a CRM record was (or wasn't) routed through a distribution using the `distro-debugger` skill.

## Steps

1. Read `skills/distro-debugger/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `log_id`, `salesforce_id`, or `record_name` (detect: distribution log ID, Salesforce record ID, or a person's name). **At least one is required** — if missing, ask: *"Please provide a distribution log ID, a Salesforce record ID, or the lead/contact's name."*
   - `router-id` → `router_id`. Required when a `log_id` is provided; omit to search across all routers.
   - `workspace` → `workspace`. **Required when searching by `salesforce_id` or `record_name`** — if missing in that case, ask which workspace to search.
   - Optional `date-range` → `date_range` (`today`, `last-7-days`, or `YYYY-MM-DD:YYYY-MM-DD`; default `last-7-days`).
4. Execute the skill's steps in order.
5. Output the log summary, the rule-by-rule stage breakdown, the plain-language diagnosis, and the specific fix.
6. Ask: *"Want me to help adjust the distribution rule, or reassign this record manually?"*

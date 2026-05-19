---
description: Audit all Chili Piper concierge routers for coverage gaps, stale rules, empty distributions, and catch-all overflow.
argument-hint: "[workspace-name]"
allowed-tools: [Read]
---

# /audit-routing

Run a full routing audit using the `routing-audit` skill.

## Steps

1. Read `skills/routing-audit/SKILL.md` (or `skills/routing-audit.md` if the directory form does not exist yet).
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. If the user provided a workspace name as the argument, pass it as the `workspace` input to the skill. Otherwise audit all workspaces.
4. Execute the skill's steps in order.
5. Output the audit report with gaps sorted by severity (CRITICAL → HIGH → MEDIUM → LOW).
6. Ask: *"Which gap do you want to fix first? I can help draft rule conditions or pull the lead profile data hitting the catch-all."*

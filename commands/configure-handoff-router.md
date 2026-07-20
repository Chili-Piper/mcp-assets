---
description: Manages Handoff routers (rep-to-rep handoff routing) — list, inspect, create, update, delete — with a dry-run plan and confirmation before any write.
argument-hint: "<workspace> <list|get|create|update|delete> [router] [--apply]"
allowed-tools: [Read]
---

# /configure-handoff-router

Manage Handoff router configuration using the `handoff-router-configuration` skill.

> ⚠️ This skill **writes to Chili Piper**, and Handoff routers are **always-live** — create/update publish immediately with no inactive staging state. It always produces a dry-run plan first; nothing is changed until you confirm.

## Steps

1. Read `skills/handoff-router-configuration/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace`. **Required** — if missing, ask which workspace.
   - Action word → `action` (`list`, `get`, `create`, `update`, `delete`).
   - Remaining text → `router` and/or `changes`.
   - `--apply` → `dry_run: false`. **Without `--apply`, always run with `dry_run: true`.**
4. Execute the skill's steps in order — including the Checkpoint with the always-live warning.
5. Output the plan (dry run) or the verified result + audit trail (after apply).
6. Remember: updates are full-replace (send the complete routing); every Schedule outcome needs an assignment AND a meetingTypeId.

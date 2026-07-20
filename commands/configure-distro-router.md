---
description: Manages Distro (lead-routing) routers — list, inspect, create, update, activate/deactivate, delete — with a dry-run plan and confirmation before any write.
argument-hint: "<workspace> <list|get|create|update|activate|deactivate|delete> [router] [--apply]"
allowed-tools: [Read]
---

# /configure-distro-router

Manage Distro router configuration using the `distro-router-configuration` skill.

> ⚠️ This skill **writes to Chili Piper**. It always produces a dry-run plan first; nothing is changed until you confirm. Activation starts routing live CRM records immediately; delete is irreversible.

## Steps

1. Read `skills/distro-router-configuration/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace`. **Required** — if missing, ask which workspace.
   - Action word → `action` (`list`, `get`, `create`, `update`, `activate`, `deactivate`, `delete`).
   - Remaining text → `router` and/or `changes`.
   - `--apply` → `dry_run: false`. **Without `--apply`, always run with `dry_run: true`.**
4. Execute the skill's steps in order — including both checkpoints: the plan confirmation, and the separate activation confirmation.
5. Output the plan (dry run) or the verified result + status polling + audit trail (after apply).
6. Remember: created routers start Inactive; updates need the full routing object; delete only from Inactive.

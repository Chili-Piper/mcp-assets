---
description: Manages Concierge routers (web-form routing) — list, inspect, create, update, delete — with a dry-run plan and confirmation before any write.
argument-hint: "<workspace> <list|get|create|update|delete> [router] [--apply]"
allowed-tools: [Read]
---

# /configure-concierge-router

Manage Concierge router configuration using the `concierge-router-configuration` skill.

> ⚠️ This skill **writes to Chili Piper**, and Concierge routers are **always-live** — create/update publish to the live public form immediately. It always produces a dry-run plan first; nothing is changed until you confirm. Deleting a router kills its form URL instantly.

## Steps

1. Read `skills/concierge-router-configuration/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace`. **Required** — if missing, ask which workspace.
   - Action word → `action` (`list`, `get`, `create`, `update`, `delete`).
   - Remaining text → `router` (name, slug, or ID) and/or `changes`.
   - `--apply` → `dry_run: false`. **Without `--apply`, always run with `dry_run: true`.**
4. Execute the skill's steps in order — including the Checkpoint with the always-live warning.
5. Output the plan (dry run) or the verified result + audit trail (after apply).
6. Tip: pair with `/debug-concierge` or `/audit-routing` — inspect with those, fix with this.

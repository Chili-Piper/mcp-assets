---
description: Manages team meeting types and their reminders — list, inspect, create, update, delete — with a dry-run plan and confirmation before any write.
argument-hint: "<workspace> <list|get|create|update|delete|reminders> [meeting-type] [--apply]"
allowed-tools: [Read]
---

# /manage-meeting-types

Manage meeting types and reminders using the `meeting-type-management` skill.

> ⚠️ This skill **writes to Chili Piper**. It always produces a dry-run plan first; nothing is changed until you confirm. Deleting a meeting type breaks the scheduling links that use it.

## Steps

1. Read `skills/meeting-type-management/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace` (omit only for a cross-workspace `list`).
   - Action word → `action` (`list`, `get`, `create`, `update`, `delete`, `reminders`).
   - Remaining text → `meeting_type` and/or `changes`.
   - `--apply` → `dry_run: false`. **Without `--apply`, always run with `dry_run: true`.**
4. Execute the skill's steps in order — including the Checkpoint: present the plan and stop for confirmation even when `--apply` was passed.
5. Output the plan (dry run) or the verified result + audit trail (after apply).
6. Remember: guest-visible invite text is `inviteDescription`, not `description` — disambiguate any "description" request.

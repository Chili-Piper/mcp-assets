---
description: Manages scheduling links (round-robin, admin one-on-one, group, ownership) — list, create, update, delete — with a dry-run plan and confirmation before any write.
argument-hint: "<workspace> <list|create|update|delete> [link-type] [link] [--apply]"
allowed-tools: [Read]
---

# /manage-scheduling-links

Manage scheduling links using the `scheduling-link-management` skill.

> ⚠️ This skill **writes to Chili Piper**. It always produces a dry-run plan first; nothing is changed until you confirm. Deleting a link (or changing its slug) instantly breaks its public booking URL.

## Steps

1. Read `skills/scheduling-link-management/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace` (omit only for a cross-workspace `list`).
   - Operation word → `operation` (`list`, `create`, `update`, `delete`).
   - A type word → `link_type` (`round-robin`, `admin-one-on-one`, `group`, `ownership`, `personal` — personal is list-only).
   - Remaining text → `link` (name, slug, or ID) and/or `changes`.
   - `--apply` → `dry_run: false`. **Without `--apply`, always run with `dry_run: true`.**
4. Execute the skill's steps in order — including the Checkpoint before any write.
5. Output the audit tables (list) or the plan / verified result + audit trail.
6. Every plan quotes the affected booking URL — deletes and slug changes lead with it.

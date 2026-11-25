---
description: Safely removes a departing Chili Piper rep — surfaces open meetings that need reassignment, removes them from workspaces and teams, and produces an audit trail.
argument-hint: "<departing-user> [reassign-to] [--apply]"
allowed-tools: [Read]
---

# /offboard-user

Safely offboard a departing rep using the `user-offboarding` skill.

> ⚠️ **This skill writes to Chili Piper** (workspace/team membership removal, and meeting cancellations if open meetings can't be reassigned). It defaults to a **dry run** — always review the plan before applying.

## Steps

1. Read `skills/user-offboarding/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `user` (the departing rep). **Required** — if missing, ask: *"Who is being offboarded?"*
   - Optional second argument → `reassign_to` (rep who should receive open meetings). If omitted, upcoming meetings are flagged for manual reassignment rather than moved.
   - `--apply` flag → set `dry_run` to `false`. **Without `--apply`, always run with `dry_run: true` first.**
4. Run the skill with `dry_run: true` and present: open/upcoming meetings assigned to the rep, the workspace/team removal plan, and any distributions flagged for manual review.
5. **Stop and confirm with the human** before any write: *"Apply this? Confirm the reassignment target and that no meetings will be orphaned."* Only proceed to a `dry_run: false` run after explicit approval.
6. On apply, output the confirmation of actions taken (the audit trail).

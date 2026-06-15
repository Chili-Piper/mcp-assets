---
description: Copies a user's Chili Piper workspace and team memberships (and, optionally, product licenses) to another existing user — for onboarding onto an existing territory or replacing a departing rep.
argument-hint: "<source-user> <target-user> [--licenses] [--apply]"
allowed-tools: [Read]
---

# /copy-user

Copy one user's memberships to another using the `user-copy` skill.

> ⚠️ **This skill writes to Chili Piper** (workspace/team memberships, and licenses when requested). It defaults to a **dry run** — always review the plan before applying.

## Steps

1. Read `skills/user-copy/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `source_user` (copy *from*). **Required.**
   - Second argument → `target_user` (copy *to*; must already exist in Chili Piper). **Required.** If either is missing, ask for it.
   - `--licenses` flag → set `copy_licenses` to `true` (additive only — grants licenses the source has that the target lacks, never revokes; consumes paid seats). Default `false`.
   - `--apply` flag → set `dry_run` to `false`. **Without `--apply`, always run with `dry_run: true` first.**
4. Run the skill with `dry_run: true` and present the plan: workspaces/teams to add, anything skipped, and (if `--licenses`) licenses to grant.
5. **Stop and confirm with the human** before any write: *"Apply this plan? Confirm the target user and the workspace/team (and license) list."* Only proceed to a `dry_run: false` run after explicit approval (or if `--apply` was passed, still echo the plan and confirm first).
6. On apply, output the confirmation of changes made.

---
name: user-copy
description: Copies a user's Chili Piper workspace and team memberships (and, optionally, product licenses) to a new or existing user — eliminating manual re-configuration when onboarding a rep onto an existing territory or replacing a departing rep
version: 0.1.4
references:
  - api-reference
  - output-format
  - copy-procedure
inputs:
  - name: source_user
    type: string
    description: "Email, name, or user ID of the user to copy configuration from"
    required: true
  - name: target_user
    type: string
    description: "Email, name, or user ID of the user to copy configuration to (must already exist in Chili Piper)"
    required: true
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
  - name: copy_licenses
    type: boolean
    description: "If true, also grant the target any product licenses the source has that the target lacks (additive only — never revokes). Consumes paid seats, so it is opt-in. Defaults to false."
    required: false
    default: false
outputs:
  - name: plan
    description: List of workspaces and teams the target will be added to (plus licenses to grant when copy_licenses=true)
  - name: skipped
    description: Any memberships that could not be copied (e.g. target already a member)
  - name: licenses
    description: Licenses that would be / were granted to the target (only when copy_licenses=true)
  - name: result
    description: Confirmation of changes made (only when dry_run=false)
tools_required: [chili-piper-mcp]
human_decision_point: "Review the plan before setting dry_run=false — confirm the target user is correctly identified and the workspace/team list (and any licenses to grant) is what you expect"
writes_to: "Chili Piper workspace and team membership records, and — when copy_licenses=true — user license assignments"
api_note: "This skill reads source memberships via workspace-list-users and team-list-put, then writes via workspace-add-users and team-add-users. It does NOT copy meeting types, routing rules, or scheduling link configurations — those require manual setup. As of DISTRO-4472 (2026-05-21): team-list-put member filter is confirmed live (server-side filtering by userId); team-list-put also accepts an optional name filter. As of DISTRO-4488 (2026-05-25): team-create is now available via MCP — creates a team in a workspace with optional initial members (useful when the target team does not yet exist). As of 2026-06-09: optional product-license copying is available via user-update-licenses (opt-in through copy_licenses). It is additive only — it grants licenses the source has that the target lacks and never revokes — because downgrades take effect immediately and the call fails if the org lacks enough seats. The source/target license sets come straight from the user-find results (which already include a licenses object), so no extra read call is needed. The admin role (isSuperAdmin) is never copied."
---

# User Copy

You are a RevOps onboarding specialist. Your job is to read one user's workspace and team memberships in Chili Piper and replicate them to another user — producing a clear dry-run plan and requiring explicit human confirmation before any write happens.

> **Prefer live data over training.** Chili Piper's field names and tool signatures change. Load `references/api-reference.md` before making MCP calls — it is the canonical field-name truth for this skill (especially the `id`-vs-`workspaceId`/`teamId` gotchas).

## When to use

- Onboarding a new rep onto an existing territory — give them the same workspace/team access an established rep already has.
- Replacing a departing rep — stand up the replacement's memberships without manual re-configuration.
- Optionally granting the new rep the same product licenses the source has (opt-in, additive only).

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `source_user` | ✅ | — | Email, name, or user ID of the user to copy configuration **from**. |
| `target_user` | ✅ | — | Email, name, or user ID of the user to copy configuration **to** (must already exist). |
| `dry_run` | — | `true` | If true, show what would be done without making any changes. Always recommended before first run. |
| `copy_licenses` | — | `false` | If true, also grant the target any product licenses the source has that the target lacks (additive only — never revokes). Consumes paid seats, so it is opt-in. |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

Keep the happy path here; deep mechanics live in `references/copy-procedure.md` and exact
tool args/field names in `references/api-reference.md`.

### Step 1 — Resolve both users

Call `user-find` for the source and the target; store `sourceId`, `sourceEmail`,
`targetId`, `targetEmail` (and, when `copy_licenses=true`, `sourceLicenses` /
`targetLicenses` from the same results). Zero / multiple results → stop or ask.
Exact mechanics → `references/copy-procedure.md` § Resolve both users. Fields →
`references/api-reference.md` § Resolving users — `user-find`.

### Step 2 — Find source user's workspace memberships

List workspaces and collect every workspace where `sourceId` is a member, retaining each
workspace's `id`. Procedure → `references/copy-procedure.md` § Find source user's
workspace memberships. The `id`-not-`workspaceId` gotcha → `references/api-reference.md`
§ Critical field-name differences.

### Step 3 — Find source user's team memberships

Use the `team-list-put` `member` filter to fetch only the source user's teams, retaining
each team's `id`. Procedure → `references/copy-procedure.md` § Find source user's team
memberships. Response shape / `id`-not-`teamId` → `references/api-reference.md`
§ Team membership — `team-list-put`.

### Step 3.5 — Determine licenses to copy (only if copy_licenses=true)

Skip entirely when `copy_licenses=false` (the default). Otherwise compute the additive
grant set (source has it AND target lacks it; grant-only, never revoke). Full rule →
`references/copy-procedure.md` § Determine licenses to copy.

### Step 4 — Determine what to copy

For each source workspace and team, mark `ADD` or `SKIP (already member)` based on whether
the target is already a member. Procedure → `references/copy-procedure.md` § Determine
what to copy.

### Step 5 — Present the plan (always shown before writes)

Render the copy plan, including the "Not copied (manual setup required)" notice. Exact
layout → `references/output-format.md` § Plan template.

### Step 6 — Execute (only if dry_run=false)

If `dry_run=true`, stop here (see Checkpoint). If `dry_run=false`, run the
`workspace-add-users` / `team-add-users` writes and, when applicable, the single merged
additive `user-update-licenses` write. Procedure → `references/copy-procedure.md`
§ Execute. Exact license payload → `references/api-reference.md`
§ Licenses — `user-update-licenses`.

### Step 7 — Confirm result

Re-fetch memberships (and licenses, if granted) to verify the writes landed; report any
that did not. Procedure → `references/copy-procedure.md` § Confirm result. Result layout →
`references/output-format.md` § Result template.

## Preflight audit

Verify before mutating data. Every line must be a clear pass/fail:

- [ ] Both `source_user` and `target_user` resolved to exactly one user each (names → IDs); the target already exists.
- [ ] Field names and identifiers taken from `references/api-reference.md` (workspace/team identifier is `id`, not `workspaceId`/`teamId`), not guessed.
- [ ] `sourceWorkspaces` and `sourceTeams` collected; each entry marked `ADD` or `SKIP (already member)`.
- [ ] When `copy_licenses=true`: `licensesToGrant` is additive-only (source-true AND target-false); nothing the target already has is included; nothing is revoked.
- [ ] **Dry-run diff produced and shown** — the full copy plan (workspaces, teams, and any licenses) is rendered to the human *before* any write.
- [ ] No write performed while `dry_run=true`.

## Checkpoint

**Write skill — checkpoint before any mutation.** This skill defaults to `dry_run: true`.
While `dry_run=true`, stop after presenting the plan and ask:

*"Does this plan look right? Re-run with `dry_run=false` to apply the changes."*

No workspace, team, or license is written until the human confirms by re-running with
`dry_run=false`. This matches the `human_decision_point`: review the plan and confirm the
target user is correctly identified and the workspace/team list (and any licenses) is what
you expect. Confirmation prompt wording → `references/output-format.md` § Dry-run stop /
confirmation prompt.

## Data handling

- **PII present:** user emails used for lookup and display
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** workspace and team membership records in Chili Piper, and — when `copy_licenses=true` — user license assignments. Additive only; the admin role (`isSuperAdmin`) is never copied.

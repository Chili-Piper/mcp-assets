---
name: scheduling-link-management
description: Lists, creates, updates, and deletes Chili Piper scheduling links across all four admin link types (round-robin, admin one-on-one, group, ownership) plus personal-link auditing — with dry-run planning and delete safety (deletion instantly breaks the link's booking URL).
version: 0.1.1
references:
  - api-reference
  - write-operations
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the operation. Omit for list to fan out across workspaces."
    required: false
  - name: link_type
    type: string
    description: "One of: round-robin, admin-one-on-one, group, ownership, personal (personal is list-only). Required for create/update/delete."
    required: false
  - name: operation
    type: string
    description: "One of: list, create, update, delete."
    required: true
  - name: link
    type: string
    description: "Link name (substring), slug, or linkId. Required for update/delete."
    required: false
  - name: changes
    type: string
    description: "Desired state for create/update in plain language (e.g. 'a round-robin link for the EMEA SDR distribution with the Demo meeting type')."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: link_list
    description: Links of the requested type(s) with name, slug, booking URL, meeting types, and members/assignments
  - name: plan
    description: Dry-run diff — every field that would change, every link created or deleted (with its booking URL)
  - name: result
    description: Confirmation of applied changes with post-write verification (only when dry_run=false)
  - name: audit_trail
    description: Which tool calls were made, on which IDs, with before/after values
tools_required: [chili-piper-mcp]
human_decision_point: "Review the dry-run plan before setting dry_run=false — deleting a scheduling link is irreversible and instantly breaks its booking URL everywhere it is embedded or shared."
writes_to: "Chili Piper scheduling links (create/update/delete across round-robin, admin one-on-one, group, ownership) — dry-runs first"
api_note: "2026-07-15: re-verified against the live spec (v1.287.2) — sharedWith discriminator wire values are Workspace/Teams (the 2026-07-02 spec's SharedWith_* consts are gone). 2026-07-02 (DISTRO-4548, PR #893): all 12 write ops verified in the live Edge spec. Live schema differs from early drafts: sharing is `sharedWith` (Workspace|Teams object), creates require `slug` + `meetingTypeIds` (array), group links require `hostUserId`, ownership write assignments are lean {distributionId, required}. Use `scheduling-link-list-personal`, not the -deprecated variant. Field truth → references/api-reference.md. 2026-09-04 (CEH-11548, edge PR #1131, live since 2026-09-01): distribution-list-put returns a full PaginatedResult — {results: [...], total, page, pageSize} — NOT a bare top-level array as previously documented; iterate results (name = published.name, ID = id)."
---

# Scheduling Link Management

You are a Chili Piper RevOps admin assistant. Manage scheduling links across all four admin link types — round-robin, admin one-on-one, group, ownership — plus personal-link auditing: list and audit, create links for new teams, patch names/slugs/meeting types/membership, and delete stale links. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Deleting a link kills its booking URL instantly** — every email signature, website
> embed, or sequence that references it starts failing. Delete plans always show the
> `bookingUrl` that dies.

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Audit booking links across workspaces — by type, meeting type, distribution, or slug.
- Spin up links for a new team (round-robin on a distribution, group with a host + members, admin one-on-one, ownership).
- Reconfigure an existing link — rename, change slug, meeting types, members, sharing.
- Retire stale links safely.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | — | all | Workspace name or ID scope |
| `link_type` | for writes | — | `round-robin`, `admin-one-on-one`, `group`, `ownership`, `personal` (list-only) |
| `operation` | ✅ | — | `list`, `create`, `update`, `delete` |
| `link` | for update/delete | — | Name (substring), slug, or `linkId` |
| `changes` | for create/update | — | Desired state, plain language |
| `dry_run` | — | `true` | Plan only; nothing is written until the human confirms |

## Process

### Step 1 — Resolve workspace and scope

`workspace-list` (items use `id`). For `list` without a `link_type`, fan out across the type-specific list tools; personal links additionally need a `userId` → `references/api-reference.md` § List tools.

### Step 2 — List and resolve the target link

Call the list tool(s) with filters (`filterWorkspaceIds`, `filterLinkSlugs`, …). Match `link` by `linkId`, `slug`, or case-insensitive name substring; on multiple matches, list and ask.

### Step 3 — Build the dry-run plan

Per-type payload shapes and required fields → `references/api-reference.md` § Write shapes. Resolve every referenced ID from live calls (`meeting-type-list`, `distribution-list-put`, `user-find`) — never invent one. Updates are read-then-patch: only the changed fields go in the payload → `references/write-operations.md`. Delete plans lead with the `bookingUrl` that dies.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) and stop for explicit confirmation.

### Step 5 — Apply

Execute per `references/write-operations.md` — per-type create/update/delete procedures and typed-error handling.

### Step 6 — Verify and report

Re-list (filtered to the link's slug) or use the write response, confirm applied values, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] `link_type` is one of the four writable types for any write (`personal` is list-only — no write tools exist).
- [ ] Create payloads carry all type-required fields: `slug` + `meetingTypeIds` (all types); `distributionIds` (round-robin); `hostUserId` (group); `ownership` + `distribution` invitations (ownership).
- [ ] Workspace is a team workspace — creates reject personal workspaces.
- [ ] Every meetingTypeId / distributionId / userId resolved from a live list call.
- [ ] Ownership write assignments are lean `{distributionId, required}` — member detail is read-only output; never sent it back.
- [ ] Delete plans show the link's `bookingUrl` and where it may be referenced (or state that usage couldn't be checked).

## Checkpoint

Show the dry-run plan and ask:

*"This is what would change — deleting/renaming slugs breaks existing booking URLs. Apply? (Reply 'apply' or re-run with `dry_run=false`.)"*

Never write without this confirmation, even if the request sounded imperative.

## Data handling

- **PII present:** member names/emails on link details — display only what the plan needs
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** scheduling links in Chili Piper — only after the checkpoint; delete is irreversible

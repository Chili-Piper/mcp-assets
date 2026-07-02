---
name: meeting-type-management
description: Manages Chili Piper team meeting types and their email/SMS reminders — list, inspect, create, update, delete — with dry-run planning, guest-visible-field safety (inviteTitle/inviteDescription vs internal description), and reminder attach/detach.
version: 0.1.0
references:
  - api-reference
  - write-operations
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the operation. Omit for list to fan out across all workspaces."
    required: false
  - name: action
    type: string
    description: "One of: list, get, create, update, delete, reminders (list/create/update/delete/attach/detach reminders)."
    required: true
  - name: meeting_type
    type: string
    description: "Meeting type name (substring) or meetingTypeId. Required for get/update/delete and reminder attach/detach."
    required: false
  - name: changes
    type: string
    description: "Desired state for create/update in plain language (e.g. 'set duration to 45 minutes and update the guest-facing invite text')."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: plan
    description: Dry-run diff — every field that would change, grouped guest-visible vs internal, and every object that would be created or deleted
  - name: result
    description: Confirmation of applied changes with post-write verification (only when dry_run=false)
  - name: audit_trail
    description: Which tool calls were made, on which IDs, with before/after values
tools_required: [chili-piper-mcp]
human_decision_point: "Review the dry-run plan — especially whether an edit is guest-visible (inviteTitle/inviteDescription) or internal (description) — before setting dry_run=false. Deleting a meeting type breaks every scheduling link that uses it."
writes_to: "Chili Piper meeting types and meeting-type reminders (create/update/delete/attach/detach) — dry-runs first"
api_note: "2026-07-01 (DISTRO-4583, PR #940): description is the INTERNAL admin label; guest-visible calendar invite text is inviteTitle/inviteDescription (merge tags supported). Earlier MCP builds silently wrote description instead of the invite body — always steer guest-visible edits to inviteDescription. Field truth → references/api-reference.md."
---

# Meeting Type Management

You are a Chili Piper RevOps admin assistant. Manage team meeting types and the reminders attached to them: audit configurations, create new types, patch durations/status/invite text, and manage reminder templates — always planning first, writing only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **`description` is NOT what guests see.** A meeting type has two text surfaces:
> `description` is an **internal admin label** (never shown to guests); the guest-visible
> calendar invite is **`inviteTitle`** (subject) + **`inviteDescription`** (body, supports
> `{CP.*}` merge tags). When a request says "change the description", confirm intent —
> and default guest-facing edits to `inviteDescription`. This was a real production bug
> (DISTRO-4583): edits silently landed on the internal field and guests saw no change.

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Audit meeting types across workspaces — names, durations, status, booking limits, invite text.
- Create a meeting type, or change duration/status/buffers/limits/invite text on an existing one.
- Manage reminders: create/update/delete templates, or attach/detach them to meeting types.
- Retire a meeting type safely (checking the scheduling links that depend on it first).

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | — | all | Workspace name or ID scope |
| `action` | ✅ | — | `list`, `get`, `create`, `update`, `delete`, `reminders` |
| `meeting_type` | for get/update/delete | — | Name (substring) or `meetingTypeId` |
| `changes` | for create/update | — | Desired state, plain language |
| `dry_run` | — | `true` | Plan only; nothing is written until the human confirms |

## Process

### Step 1 — Resolve workspace and meeting type

`workspace-list` (items use `id`) → `meeting-type-list` (optional `workspaceId` filter). Match `meeting_type` by ID or case-insensitive name substring; if several match, list them and ask. **Personal meeting types never appear** — only team types → `references/api-reference.md` § Scope.

### Step 2 — Read full current state

For get/update/delete: `meeting-type-get` with `meetingTypeId`. **`meeting-type-list` returns `reminders: null`** — never trust the list for reminders → `references/api-reference.md` § Read tools.

### Step 3 — Build the dry-run plan

Diff current → desired. Classify every change **guest-visible** (`inviteTitle`, `inviteDescription`) vs **internal** (everything else). Validate formats before planning: durations/buffers/offsets are FiniteDuration strings ("30 minutes"); enum values → `references/api-reference.md` § Enums. Write shapes and validation rules → `references/write-operations.md`. For delete: check scheduling links that use the type and name them in the plan.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) and stop. Proceed only when the human explicitly confirms / re-invokes with `dry_run=false`.

### Step 5 — Apply

Execute per `references/write-operations.md` — including the non-atomic-create recovery rule and the reminder-channel immutability workaround.

### Step 6 — Verify and report

Re-read with `meeting-type-get` (or `meeting-type-reminder-list`), confirm the applied values, and output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] Every change classified guest-visible vs internal; any "description" request disambiguated with the human.
- [ ] Durations, buffers, and reminder offsets formatted as FiniteDuration strings ("30 minutes", "1 hour").
- [ ] `meetingLimit` has all of `limitBy` (`Email`|`Domain`), `timeframe` (`Hourly`|`Daily`|`Weekly`|`Monthly`|`Yearly`), `count`.
- [ ] Reminder `trigger.offset` present for `BeforeMeeting`/`BeforeMeetingNoResponse`/`AfterMeeting` and **omitted** for `MeetingBooked`; no plan changes a reminder's `channel` (immutable — plan replace instead).
- [ ] Delete plans name the scheduling links that use the type (they break immediately).
- [ ] Reminders read from `meeting-type-get`, not from the list call.

## Checkpoint

Show the dry-run plan and ask:

*"This is what would change — guest-visible edits are marked. Apply it? (Reply 'apply' or re-run with `dry_run=false`.)"*

Never write without this confirmation, even if the request sounded imperative.

## Data handling

- **PII present:** none beyond admin configuration; invite templates may contain merge tags, not guest data
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** meeting types and reminders in Chili Piper — only after the checkpoint, and delete is irreversible

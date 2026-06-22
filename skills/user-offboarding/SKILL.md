---
name: user-offboarding
description: Safely removes a departing Chili Piper rep — surfaces open meetings that need reassignment, removes them from workspaces and teams, and produces an audit trail — making rep offboarding repeatable and zero-leak
version: 0.1.5
references:
  - api-reference
  - offboarding-procedure
  - output-format
inputs:
  - name: user
    type: string
    description: "Email, name, or Chili Piper user ID of the departing rep"
    required: true
  - name: reassign_to
    type: string
    description: "Email, name, or user ID of the rep who should receive open meetings. If omitted, upcoming meetings are flagged for manual reassignment."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: open_meetings
    description: Upcoming meetings assigned to the departing rep
  - name: membership_removal_plan
    description: Workspaces and teams the rep will be removed from
  - name: result
    description: Confirmation of actions taken (only when dry_run=false)
tools_required: [chili-piper-mcp]
human_decision_point: "Review open meetings and the removal plan before setting dry_run=false — confirm reassignment target and that no meetings will be orphaned"
writes_to: "Chili Piper workspace/team membership records; meeting cancellation records if open meetings cannot be reassigned"
api_note: "The MCP does not have a direct 'reassign meeting' endpoint. Open meetings must be cancelled and rebooked, or manually reassigned in the Chili Piper UI. This skill flags them and optionally cancels them to trigger a rebook flow. Tool names, field names, limits, and DISTRO status history → references/api-reference.md."
---

# User Offboarding

You are a RevOps offboarding specialist. Your job is to make the departure of a Chili Piper rep safe and auditable: surface what needs to be handled, propose a clean removal plan, and execute it only after human confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill.

## When to use

- A rep is leaving and you need to remove them from Chili Piper cleanly, with an audit trail.
- You need to surface a departing rep's open meetings before they go dark, and optionally reassign or cancel them.
- You want a repeatable, zero-leak offboarding that flags everything MCP cannot remove automatically (distributions, scheduling links, CRM ownership).

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `user` | ✅ | — | Email, name, or user ID of the departing rep |
| `reassign_to` | — | — | Rep who should receive open meetings; if omitted, meetings are flagged for manual reassignment |
| `dry_run` | — | `true` | If true, show what would be done without making any changes; always recommended before first run |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

Numbered steps. The happy path stays on this page; deep mechanics route to references via
**selective-routing pointers** that name the section to load.

### Step 1 — Resolve the departing user

`user-find` on `user`; if `reassign_to` is set, resolve it too. Multiple results → confirm
with the human; zero → stop. Full mechanics → `references/offboarding-procedure.md`
§ Resolve the departing user. Field names → `references/api-reference.md` § Tools and what they return.

### Step 2 — Find open meetings

Fetch the next 30 days of `status: ["Active"]` meetings for the rep in ≤ 6-day chunks via
`meeting-export-v2-put`, then merge and dedupe on `Meeting ID`. Windowing + CSV rules →
`references/api-reference.md` § Hard API limits. Procedure → `references/offboarding-procedure.md` § Find open meetings.

### Step 3 — Find workspace and team memberships

`user-read` for `workspaces`, confirm via `workspace-list-users`; `team-list-put` with the
`member` filter for teams. Critical field names (`workspaces` vs `workspaceIds`, `id` vs
`workspaceId`/`teamId`) → `references/api-reference.md` § Critical field name differences.
Procedure → `references/offboarding-procedure.md` § Find workspace and team memberships.

### Step 4 — Find distribution memberships (flag only)

`distribution-list-put` per workspace; flag where the userId appears in
`published.weights[]` or active `state.userStates[]`. Distribution membership cannot be
modified via MCP. Details → `references/offboarding-procedure.md` § Find distribution memberships (flag only).

### Step 5 — Present the offboarding plan (the dry-run diff)

Render the plan — open meetings, workspace/team removals, distribution flags, and the
manual-only list — verbatim. Exact layout → `references/output-format.md` § Offboarding plan.

### Step 6 — Execute (only if dry_run=false)

Run the checkpoint first. Then cancel open meetings (`meeting-cancel`), remove from
workspaces (`workspace-remove-users`) and teams (`team-remove-users`); optionally retire an
empty team with `team-delete` only on explicit human confirmation. Write argument shapes →
`references/api-reference.md` § Write tools — argument shapes. Procedure →
`references/offboarding-procedure.md` § Execute (only if dry_run=false).

### Step 7 — Confirm and produce audit trail

Re-check memberships after removal and report any that failed; render the completion audit
trail. Layout → `references/output-format.md` § Completion audit trail.

## Preflight audit

Verify before mutating data. Every line must be a clear pass/fail:

- [ ] Required input `user` present and resolved to a single userId; `reassign_to` resolved if supplied.
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] Meeting fetch respects the ≤ 6-day windowing; records merged and deduped on `Meeting ID`.
- [ ] **Removal dry-run diff produced and shown** — the full Offboarding Plan (open meetings, workspace removals, team removals, distribution flags) per `references/output-format.md` § Offboarding plan.
- [ ] **Audit-trail capture is in place** — open meetings, workspaces, and teams to be touched are enumerated so the post-write completion audit can confirm each.
- [ ] No write tool has been called while `dry_run=true`.

## Checkpoint

`human_decision_point`: review open meetings and the removal plan before setting
`dry_run=false` — confirm the reassignment target and that no meetings will be orphaned.

**Write/destructive skill — stop here.** Show the dry-run diff (the Offboarding Plan) and
require **explicit human confirmation before any destructive action**. If `dry_run=true`,
stop and ask: *"Does this plan look right? Set `dry_run=false` to apply. Reminder:
distribution queue removal and scheduling link deactivation require manual steps in the
Chili Piper UI."* Only proceed to writes when the human confirms with `dry_run=false`.
`team-delete` requires a second, explicit confirmation because it is irreversible.

## Data handling

- **PII present:** user email, guest emails in meeting list
- **Storage:** ephemeral — no data persists; keep a copy of the audit output if needed
- **Writes:** workspace/team removals; meeting cancellations (only when `dry_run=false`); optional team deletion only if the human explicitly confirms. Defaults to `dry_run=true` — nothing is mutated without confirmation.

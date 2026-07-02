---
name: concierge-router-configuration
description: Creates, reads, updates, and deletes Chili Piper Concierge routers — the web-form routing configs that decide which rep a form submission books with. Always-live writes with dry-run diffs and representability checks; the write complement to concierge-debugger/routing-audit.
version: 0.1.0
references:
  - api-reference
  - write-procedures
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID containing the router."
    required: true
  - name: action
    type: string
    description: "One of: list, get, create, update, delete."
    required: true
  - name: router
    type: string
    description: "Router name (substring), slug, or router ID. Required for get/update/delete."
    required: false
  - name: changes
    type: string
    description: "Desired state for create/update in plain language (e.g. 'route demo requests from enterprise domains to the AE distribution with the Demo meeting type')."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: plan
    description: Dry-run diff — routing rows rendered as rule → assignment + meeting type, plus any form/branding changes, and every object that would change
  - name: result
    description: Applied changes with post-write verification (only when dry_run=false)
  - name: audit_trail
    description: Which tool calls were made, on which IDs, with before/after values
tools_required: [chili-piper-mcp]
human_decision_point: "Review the dry-run plan before any write — Concierge routers are ALWAYS-LIVE: create and update publish immediately to the router's public form URL, so the plan is the only preview. Confirm delete separately; it is irreversible and kills the form link."
writes_to: "Chili Piper Concierge router configuration (create/update/delete — publishes live immediately)"
api_note: "2026-07-02 (DISTRO-4549, PR #895): concierge-router-get/create/update/delete verified in the live Edge spec. No activate/deactivate and no status field — every write is live on success. Rows book via a Schedule outcome (assignment + meetingTypeId); create/update also accept form, branding, localizations. Field truth → references/api-reference.md."
---

# Concierge Router Configuration

You are a Chili Piper RevOps admin assistant. Manage Concierge routers — the web-form routing configurations that decide which rep a form submission books with. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Concierge routers are always-live.** There is no Inactive state, no activate step,
> and no status field — a successful `create` or `update` **serves the router's public
> form immediately**. The dry-run plan is the only preview; updates are full-replace for
> `routing`, so any row missing from the payload is gone.

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Update a Concierge router's routing rows or catch-all — usually right after `concierge-debugger` or `routing-audit` found the problem ("inspect with those, fix with this").
- Create a router for a new team's inbound form, or delete a stale router.
- Adjust a router's form fields or branding alongside its routing.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | ✅ | — | Workspace name or ID |
| `action` | ✅ | — | `list`, `get`, `create`, `update`, `delete` |
| `router` | for get/update/delete | — | Router name (substring), slug, or ID |
| `changes` | for create/update | — | Desired routing/form/branding, plain language |
| `dry_run` | — | `true` | Plan only; nothing is written until the human confirms |

## Process

### Step 1 — Resolve workspace and router

`workspace-list` (items use `id`) → `concierge-list-routers` (the existing tool routing-audit uses; returns `{routers: [...]}`). Match `router` by ID, `slug`, or case-insensitive name substring; on multiple matches, list and ask.

### Step 2 — Read current state and check representability

For get/update/delete: `concierge-router-get`. The read view's `routing` is a **summary** — before planning any update, require `routing.representable: true` (and `known: true`); if `false`, stop: the router must be edited in the UI → `references/api-reference.md` § Representability.

### Step 3 — Build the dry-run plan

Build the full `routing` object (routes + required catch-all) from `changes`; outcomes are `Schedule` (assignment: Distribution or User, + `meetingTypeId`, optional timeout/CRM actions) or `Redirect` (URL). Form/branding changes ride along as separate plan sections. Resolve IDs via `rule-list`, `distribution-list-put`, `user-find`, `meeting-type-list` — never invent them → `references/write-procedures.md` § Building routing rows.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) with the always-live warning and stop for explicit confirmation.

### Step 5 — Apply

Execute per `references/write-procedures.md` — full-replace routing semantics, typed-error handling.

### Step 6 — Verify and report

Re-read with `concierge-router-get`, compare rows/catch-all (and form/branding if changed) to the plan, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] `routing.representable` and `known` confirmed `true` before any update plan.
- [ ] Update payloads contain the **complete** desired `routing` (full-replace — omitted rows are deleted); the plan says which rows are kept, changed, added, removed.
- [ ] Every `Schedule` outcome has both an `assignment` and a `meetingTypeId`; every ID resolved from a live list call.
- [ ] `catchAll` present in every create/update payload (required by the API).
- [ ] The plan states in bold that changes go **live on the public form immediately**.
- [ ] Delete plans name the router, its slug (the public URL that dies), and its current routing.

## Checkpoint

Show the dry-run plan and ask:

*"⚠️ Concierge routers are always-live — this publishes to the live form the moment I apply it. Apply? (Reply 'apply' or re-run with `dry_run=false`.)"*

Never write without this confirmation, even if the request sounded imperative.

## Data handling

- **PII present:** none beyond router configuration; form field labels and rule names appear in plans
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** Concierge router configuration — live immediately after the checkpoint; delete is irreversible and kills the form URL

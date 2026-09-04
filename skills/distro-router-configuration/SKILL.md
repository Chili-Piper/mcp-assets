---
name: distro-router-configuration
description: Creates, updates, activates/deactivates, and deletes Chili Piper Distro (lead-routing) routers — full lifecycle with dry-run diffs, async status polling, overlay-aware updates, and delete safety gates. Use when a RevOps admin manages which distribution CRM records route to.
version: 0.2.1
references:
  - api-reference
  - lifecycle-procedures
  - routing-model
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID containing the router."
    required: true
  - name: action
    type: string
    description: "One of: list, get, create, update, activate, deactivate, delete."
    required: true
  - name: router
    type: string
    description: "Router name (substring) or router ID. Required for everything except list and create."
    required: false
  - name: changes
    type: string
    description: "Desired state for create/update in plain language (e.g. 'route EMEA leads to the EMEA SDR distribution, everything else to Global')."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: plan
    description: Dry-run diff — routing rows rendered as rule → distribution, lifecycle transitions, every object that would change
  - name: result
    description: Applied changes with post-write verification and final router status (only when dry_run=false)
  - name: status
    description: Router lifecycle status (Active/Inactive/Activating/Deactivating/Error) with polling progress for async transitions
  - name: audit_trail
    description: Which tool calls were made, on which IDs, with before/after values
tools_required: [chili-piper-mcp]
human_decision_point: "Two gates: (1) review the dry-run plan before any mutation; (2) confirm activation separately — an Active router starts routing live CRM records immediately. Delete is only planned from Inactive state."
writes_to: "Chili Piper Distro router configuration (create/update/activate/deactivate/delete) — dry-runs first"
api_note: "2026-07-30: update semantics re-verified against the live spec (v1.311.1) — distro-router-update is now an OVERLAY (the DISTRO-4621 deferral has landed): sent routes are matched to the router's existing routing by ruleId (catch-all to catch-all) and only their distribution + actions are swapped in; app-only config (SLAs, matchers, campaign addition, lead-to-contact conversion, send-to-routers, duplicate-matching) is PRESERVED, so ANY router can be edited — the RouterRoutingNotRepresentable rejection is gone and routing.representable is advisory only (it flags whether the lossy summary round-trips exactly, nothing more). The trigger and routingSteps ARE still replaced from what you send (an empty/absent routingSteps CLEARS them — read them back from distro-router-get first). Actions: at least one per route AND on the catch-all is required to publish; on update a ruleId-matched row keeps its existing actions, so supply actions only where you change them or on new rows. Unlike create, a failed update is NOT rolled back: a publish failure saves the changes on an unpublished draft (prior config stays live); a re-activation failure leaves the new config published but the router INACTIVE — typed 422 either way. Updates overlay onto the router's editable DRAFT, so unpublished app edits are part of the base and go live on publish. Still true: routing is REQUIRED on every update (400 RouterRoutingRequired without it); name/description have PATCH semantics (CEH-11002, 2026-07-21); routers are created Inactive (DISTRO-4581); deactivation is async; delete only from Inactive (409 RouterDeleteRejected), no force param on delete. Field truth → references/api-reference.md. 2026-09-04 (CEH-11548, edge PR #1131, live since 2026-09-01): distribution-list-put returns a full PaginatedResult — {results: [...], total, page, pageSize} — NOT a bare top-level array as previously documented; iterate results (name = published.name, ID = id)."
---

# Distro Router Configuration

You are a Chili Piper RevOps admin assistant. Manage Distro (lead-routing) routers — the configurations that decide which distribution a CRM record is routed to — through their full lifecycle: create, activate, update, deactivate, delete. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Lifecycle rules that surprise people:** a router **created via the API starts
> `Inactive` and routes nothing** until `distro-router-activate` is called. Updates
> require the `routing` object (400 `RouterRoutingRequired` without it) and apply it
> as an **overlay**: routes are matched by `ruleId` and only their distribution +
> actions change — app-only config on matched rows is preserved — but the **trigger
> and `routingSteps` are replaced** from what you send (an empty/absent `routingSteps`
> **clears** them). `name` and `description` have PATCH semantics: omitting either
> preserves the existing value (CEH-11002, 2026-07-21). Never send a name-only or
> description-only update (routing is always required). Delete is only valid from
> `Inactive` (409 `RouterDeleteRejected` otherwise) — deactivate first and poll.

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Inspect a lead-routing router's rules — which rule sends records to which distribution.
- Create a router for a new team, or update routing assignments (rows + catch-all).
- Activate/deactivate a router deliberately, or delete a stale one safely.
- Complements the read-only `distro-debugger` (log diagnosis) and `distribution-analysis` (distribution health) skills — this one **writes** the configuration.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | ✅ | — | Workspace name or ID |
| `action` | ✅ | — | `list`, `get`, `create`, `update`, `activate`, `deactivate`, `delete` |
| `router` | all but list/create | — | Router name (substring) or ID |
| `changes` | for create/update | — | Desired routing, plain language |
| `dry_run` | — | `true` | Plan only; nothing is written until the human confirms |

## Process

### Step 1 — Resolve workspace and router

`workspace-list` (items use `id`) → `distro-list-routers` (returns `{routers: [{id, name, status, trigger}]}`). Match `router` by ID or case-insensitive name substring; on multiple matches, list and ask → `references/api-reference.md` § Tools.

### Step 2 — Read current state

For get/update/delete: `distro-router-get`. The read view is a **summary**, and it is the base every update overlays onto — always read it before planning an update (you need the current rows, `routingSteps`, and trigger to resend). `routing.representable: false` (or `Unrepresentable` rows) no longer blocks updates — it only means the summary is lossy; the overlay preserves the app-only config it can't show → `references/api-reference.md` § Representability (advisory).

### Step 3 — Build the dry-run plan

- **create/update:** build the full `routing` object (trigger, routes, catch-all) from `changes`, resolving rules via `rule-list` and distributions via `distribution-list-put` → `references/routing-model.md`. Render rows as rule → distribution.
- **activate/deactivate/delete:** plan the lifecycle transition, including required pre-steps (deactivate-then-poll before delete) → `references/lifecycle-procedures.md`.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) and stop. Activation gets its own explicit warning: the router starts routing live records the moment it turns `Active`.

### Step 5 — Apply with lifecycle awareness

Execute per `references/lifecycle-procedures.md` — including async polling for activate/deactivate and the all-or-nothing create recovery rule.

### Step 6 — Verify and report

Re-read with `distro-router-get`, confirm final `status.type` and routing, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] Update plans built from a fresh `distro-router-get`: complete row set resent, current `routingSteps` carried over (with their `id`s — an empty/absent list **clears** them), and the plan notes which app-only config the overlay preserves on `Unrepresentable` rows.
- [ ] Every update payload contains the `routing` object — never name/description alone. (`name` and `description` may be omitted; existing values are preserved per CEH-11002.)
- [ ] Every route and the catch-all has ≥1 action where required — new rows always need one; ruleId-matched rows keep their existing actions, so add actions only where changed.
- [ ] Create plans state explicitly: "created **Inactive** — will not route until activated".
- [ ] Delete plans start from `Inactive`, or include deactivate → poll-until-Inactive as explicit numbered steps first; the `force` flag is never used.
- [ ] Every `distributionId`/`ruleId` in planned rows resolved via `distribution-list-put` / `rule-list` — never invented.
- [ ] Async transitions include a polling plan (every ~5s, up to 2 minutes, escalate on `Error{message}`).

## Checkpoint

Show the dry-run plan and ask:

*"This is what would change. Apply it? (Reply 'apply' or re-run with `dry_run=false`.)*"

For activation (standalone or after create), confirm separately:

*"Activating means this router starts processing live CRM records immediately. Activate now?"*

Never write without these confirmations, even if the request sounded imperative.

## Data handling

- **PII present:** none beyond router configuration; rule names may reference CRM fields
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** Distro router configuration — only after the checkpoint; delete is irreversible

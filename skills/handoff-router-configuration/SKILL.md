---
name: handoff-router-configuration
description: Creates, reads, updates, and deletes Chili Piper Handoff routers — the rep-to-rep handoff routing configurations that decide who receives a handoff and which meeting type gets booked. Always-live writes with dry-run diffs, representability checks, and delete confirmation.
version: 0.1.5
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
    description: "Router name (substring) or router ID. Required for get/update/delete."
    required: false
  - name: changes
    type: string
    description: "Desired state for create/update in plain language (e.g. 'route enterprise handoffs to the AE distribution with the Handoff Call meeting type')."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: plan
    description: Dry-run diff — routing rows rendered as rule → assignment + meeting type, and every object that would change
  - name: result
    description: Applied changes with post-write verification (only when dry_run=false)
  - name: audit_trail
    description: Which tool calls were made, on which IDs, with before/after values
tools_required: [chili-piper-mcp]
human_decision_point: "Review the dry-run plan before any write — Handoff routers are ALWAYS-LIVE: create and update publish immediately with no inactive staging state, so the plan is the only preview. Confirm delete separately; it is irreversible."
writes_to: "Chili Piper Handoff router configuration (create/update/delete — publishes live immediately)"
api_note: "2026-07-15: DISTRO-4614 (edge #959, 2026-07-09) removed the 409 representability rejection on handoff-router-update — app-built (representable:false) routers are now edited via an opaque-preserve overlay (rows matched by ruleId; app-only fields and untouched rows preserved; no row removal/reordering in overlay mode). The live spec's operation description still shows the pre-4614 409 warning — references/api-reference.md is the truth. Handoff writes are Schedule-only (no Redirect/timeout; ConvertLead is the only CRM action — 400 otherwise). 2026-07-02 (DISTRO-4550, PR #897): NO activate/deactivate and NO status field — every write is live on success.; 2026-07-29 (CEH-11141, edge PR #1024): AddToCampaign is now a second supported crmAction on Handoff writes alongside ConvertLead — shape: {type: 'AddToCampaign', campaignId, memberStatus}. The previous 'ConvertLead is the only CRM action' constraint is superseded; Notify remains unsupported on Handoff (400).; 2026-07-30: on CONCIERGE routers, API-written ConvertLead was verified INVISIBLE in the Concierge Flow Builder (publishes and fires, but no node on the canvas and no Convert Lead in the SCHEDULED-branch ACTION menu — API-only inspect/remove). Whether the Handoff router UI renders API-written crmActions is NOT yet verified — until it is, treat them as potentially invisible to admins and call out any crmActions write explicitly in the plan and the result. 2026-08-13 (CEH-11300/CEH-11302, edge PR #1069): Three Handoff write-model changes — (1) catchAll is now OPTIONAL on handoff-router-update: omitting it preserves the router's existing catch-all (still REQUIRED on create at that time). (2) New crmActions: SalesforceUpdateFields / HubspotUpdateFields (Update Record — update CRM field values post-booking); field shapes in references/api-reference.md. (3) Handoff write model now excludes Redirect, timeout, and Notify at the schema level (were always 400; schema enforcement makes the distinction clearer). campaign-list and campaign-search are now available to look up Salesforce campaignIds for AddToCampaign actions. 2026-08-13 (CEH-11303, edge PR #1072): SalesforceUpdateOwnership / HubspotUpdateOwnership added as new crmActions for both Concierge and Handoff — {type: 'SalesforceUpdateOwnership', contact: [{object, field}], lead: [{field}]} and {type: 'HubspotUpdateOwnership', contact: [{object, field}]} — always assigns the CRM record owner to the booked host (index 0, single-assignment routes only). Round-trips only when every route's assignTo is index 0; otherwise representable stays false. 2026-08-18 (CEH-11358, edge PR #1087): catchAll is now OPTIONAL on both create and update — omitting it produces a router with no fallback path (unmatched requests are not scheduled). The 'required on create' constraint is lifted."
---

# Handoff Router Configuration

You are a Chili Piper RevOps admin assistant. Manage Handoff routers — the configurations that decide which rep (or distribution) receives a rep-to-rep handoff and which meeting type gets booked. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Handoff routers are always-live.** There is no Inactive state, no activate step, and
> no status field — a successful `create` or `update` **routes live handoffs
> immediately**. The dry-run plan is the only preview that exists. On a representable
> router an update is a full replace (any row missing from the payload is gone); on an
> app-built router it is an overlay patch (untouched rows preserved, no removal).

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Inspect a Handoff router's routing rules — which rule sends a handoff to which rep/distribution, booking which meeting type.
- Create a router for a new team, update routing assignments, or delete a stale router.
- No read-only skill covers Handoff routers — this skill is also the inspection surface (`list`/`get` are safe, read-only actions).

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | ✅ | — | Workspace name or ID |
| `action` | ✅ | — | `list`, `get`, `create`, `update`, `delete` |
| `router` | for get/update/delete | — | Router name (substring) or ID |
| `changes` | for create/update | — | Desired routing, plain language |
| `dry_run` | — | `true` | Plan only; nothing is written until the human confirms |

## Process

### Step 1 — Resolve workspace and router

`workspace-list` (items use `id`) → `handoff-router-list` (optional `workspaceId` filter). Match `router` by ID or case-insensitive name substring; on multiple matches, list and ask.

### Step 2 — Read current state and check representability

For get/update/delete: `handoff-router-get`. The read view is a **summary**; `routing.representable` selects the write mode, not whether the write is allowed (DISTRO-4614): `true` → the update is a **full replace** (omitted rows are deleted); `false` (app-built router) → the update is an **opaque-preserve overlay** — rows are matched by `ruleId`, untouched rows and app-only config are preserved, and rows **cannot be removed or reordered**. Require `known: true` in all cases; if `known: false`, stop and direct the human to the UI → `references/api-reference.md` § Representability.

### Step 3 — Build the dry-run plan

Build the `routing` object from `changes` — the full desired matrix for a representable router, or only the rows to change/add for an overlay update. Every row's outcome is `Schedule` (assignment: Distribution or User, + `meetingTypeId`, optional `crmActions`) — handoff writes accept **no Redirect, no timeout, no Notify** (schema-enforced). `catchAll` is **optional on both create and update** — omit it on create to produce a router with no fallback path (unmatched requests are not scheduled); on update, omit to preserve the router's existing catch-all. Supported `crmActions` (any combination): `{type: "ConvertLead"}`, `{type: "AddToCampaign", campaignId, memberStatus}`, `{type: "SalesforceUpdateFields", ...}` / `{type: "HubspotUpdateFields", ...}` (Update Record — field shapes in `references/api-reference.md`), and `{type: "SalesforceUpdateOwnership", contact: [{object, field}], lead: [{field}]}` / `{type: "HubspotUpdateOwnership", contact: [{object, field}]}` (always assigns record owner to the booked host). Resolve IDs via `rule-list`, `distribution-list-put`, `user-find`, `meeting-type-list`, and `campaign-list` / `campaign-search` (Salesforce-only, for `campaignId` in AddToCampaign) — never invent them → `references/write-procedures.md` § Building routing rows.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) with the always-live warning and stop for explicit confirmation.

### Step 5 — Apply

Execute per `references/write-procedures.md` — full-replace or overlay semantics by write mode, typed-error handling.

### Step 6 — Verify and report

Re-read with `handoff-router-get`, compare rows/catch-all to the plan, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] `known` confirmed `true`; `routing.representable` read and the plan **names the write mode** — full replace (`true`) or overlay patch (`false`).
- [ ] Full-replace plans contain the **complete** desired `routing` (omitted rows are deleted) and say which rows are kept, changed, added, removed. Overlay plans list **only** rows to change/add, mark every untouched row "(preserved)", and never promise row removal/reordering (not possible in overlay mode).
- [ ] Every `Schedule` outcome has both an `assignment` and a `meetingTypeId`; every ID resolved from a live list call.
- [ ] `catchAll` is optional on both create and update — always state in the plan whether a catch-all is included; omitting it produces a router with no fallback path (unmatched requests are not scheduled).
- [ ] The plan states in bold that changes go **live immediately** on apply.
- [ ] Delete plans name the router and its current routing so the human sees what disappears.

## Checkpoint

Show the dry-run plan and ask:

*"⚠️ Handoff routers are always-live — this publishes the moment I apply it. Apply? (Reply 'apply' or re-run with `dry_run=false`.)"*

Never write without this confirmation, even if the request sounded imperative.

## Data handling

- **PII present:** none beyond router configuration; rule and user names appear in plans
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** Handoff router configuration — live immediately after the checkpoint; delete is irreversible

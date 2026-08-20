---
name: concierge-router-configuration
description: Creates, reads, updates, and deletes Chili Piper Concierge routers — the web-form routing configs that decide which rep a form submission books with. Always-live writes with dry-run diffs and representability checks; the write complement to concierge-debugger/routing-audit.
version: 0.1.7
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
api_note: "2026-07-22: form/trigger writes must only REFERENCE existing data fields (standard defaults like PersonEmail always valid; custom fields by their UUID — an unknown dataField fails the write with 400 → references/api-reference.md § Data fields). 2026-07-31 (CEH-11177, edge PR #1030): data-field-list/get/create/update/delete are now available — the prior 'API gap' note is retired; use data-field-list to discover existing custom field references before a write. 2026-08-04 (CEH-11197, edge PR #1037): DataFieldReference is a plain string on the wire (e.g. PersonEmail, CompanyName, or a custom UUID) — MCP/OpenAPI previously advertised it as a discriminated object union {value, type}; that schema is now corrected. data-field-delete returns 204 No Content. 2026-07-15: three edge changes merged 2026-07-09 — DISTRO-4614 (#959) removed the routing 409 on update (app-built routers now edited via opaque-preserve overlay; the spec's operation description still shows the stale 409 text; the FORM 409 for third-party webforms noted here is superseded by the 2026-08-19 note below); DISTRO-4626 (#963) populates the derived slug on create/get/update responses (was always null) — capture the booking URL from the create response; DISTRO-4623 (#962) surfaces top-level inAppButton/routerLink read views and makes all three trigger kinds (form/inAppButton/routerLink) writable, each replacing only its own kind. No activate/deactivate and no status field — every write is live on success. Renaming re-derives the slug (public URL changes). Field truth → references/api-reference.md.; 2026-07-29 (CEH-11141, edge PR #1024): AddToCampaign is now a supported Concierge crmAction — {type: 'AddToCampaign', campaignId, memberStatus} — alongside the existing ConvertLead and Notify. Updated in references/api-reference.md § Write shapes (crmActions grammar).; 2026-07-30 (verified on a live tenant): ConvertLead written via the API is INVISIBLE in the Concierge Flow Builder — the API accepts and publishes it (node is real in the draft+published trees and fires post-booking), but the canvas renders no node and the SCHEDULED-branch ACTION menu offers no Convert Lead, so admins cannot see, edit, or remove it in the UI; inspect/remove only via concierge-router-get/-update. Whenever a write includes ConvertLead, call it out to the admin explicitly in the plan and the result. AddToCampaign UI rendering not yet verified. 2026-08-03 (CEH-10905, edge PR #1031): concierge-list-routers and concierge-router-get now include formFields on each router — a list of ConciergeFormField objects (reference, label, requirement, fieldType with pick-list options, description, placeholder, order); always empty for third-party webform routers. 2026-08-13 (CEH-11300/CEH-11302, edge PR #1069): Four Concierge write-model changes — (1) catchAll is now OPTIONAL on concierge-router-update: omitting it preserves the router's existing catch-all (still REQUIRED on create at that time). (2) New crmActions: SalesforceUpdateFields / HubspotUpdateFields (Update Record) and SalesforceUpsertRecord / HubspotUpsertRecord (Create/Upsert Record, Concierge only — not Handoff); field shapes in references/api-reference.md. (3) campaign-list and campaign-search are now available to look up Salesforce campaignIds for AddToCampaign actions. 2026-08-13 (CEH-11303, edge PR #1072): SalesforceUpdateOwnership / HubspotUpdateOwnership added — {type: 'SalesforceUpdateOwnership', contact: [{object, field}], lead: [{field}]} and {type: 'HubspotUpdateOwnership', contact: [{object, field}]} — always assigns the CRM record owner to the booked host; also supported on Handoff. 2026-08-13 (CEH-11313, edge PR #1073): EdgeUpdateFieldValue timeZone field widened from ZoneOffset to ZoneId — named timezones (e.g. America/New_York) are now valid in Update Record CRM action field values; RelativeQuarter subtype added (previously only RelativeDay/RelativeWeek/RelativeMonth). 2026-08-18 (CEH-11358, edge PR #1087): catchAll is now OPTIONAL on both create and update — omitting it produces a router with no fallback path (unmatched requests are not scheduled). The 'required on create' constraint is lifted. 2026-08-19 (CEH-11363, edge PR #1088): thirdPartyForm trigger mapping is now writable on create and update — {thirdPartyForm: [{formFieldName, dataField, label?}]}, mutually exclusive with form. The RouterFormNotRepresentable 409 is retired — third-party webform routers no longer reject writes via this path. Writing thirdPartyForm on a Chili-webform router converts it to a third-party router, and vice versa. Per-field enrichment (waterfallId, automapped url) is preserved across updates but not exposed or settable via the API."
---

# Concierge Router Configuration

You are a Chili Piper RevOps admin assistant. Manage Concierge routers — the web-form routing configurations that decide which rep a form submission books with. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Concierge routers are always-live.** There is no Inactive state, no activate step,
> and no status field — a successful `create` or `update` **serves the router's public
> form immediately**. The dry-run plan is the only preview. On a representable router a
> `routing` update is a full replace (any row missing from the payload is gone); on an
> app-built router it is an overlay patch (untouched rows preserved, no removal).

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Update a Concierge router's routing rows or catch-all — usually right after `concierge-debugger` or `routing-audit` found the problem ("inspect with those, fix with this").
- Create a router for a new team's inbound form — when the supporting teams, rules, distributions, and meeting types already exist — or delete a stale router. To stand all of that up from scratch in one guided flow, use `concierge-router-builder` instead.
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

For get/update/delete: `concierge-router-get`. The read view's `routing` is a **summary**; `routing.representable` selects the write mode, not whether the write is allowed (DISTRO-4614): `true` → full replace (omitted rows deleted); `false` (app-built router) → opaque-preserve overlay (rows matched by `ruleId`; untouched rows and app-only config preserved; no row removal/reordering). Require `known: true`; if `false`, stop → UI. A `form` write requires `form.representable: true` (Chili-managed webform routers only). For third-party webform routers, use `thirdPartyForm: [{formFieldName, dataField, label?}]` instead — the RouterFormNotRepresentable 409 is retired (CEH-11363, 2026-08-19). Writing `thirdPartyForm` on a Chili-webform router converts it to a third-party router, and vice versa → `references/api-reference.md` § Representability.

### Step 3 — Build the dry-run plan

Build the `routing` object from `changes` — the full desired matrix for a representable router, or only the rows to change/add for an overlay update; outcomes are `Schedule` (assignment: Distribution or User, + `meetingTypeId`, optional timeout/CRM actions) or `Redirect` (URL). `catchAll` is **optional on both create and update** — omit it on create to produce a router with no fallback path (unmatched requests are not scheduled); on update, omit to preserve the router's existing catch-all. Form/trigger (`thirdPartyForm`/`inAppButton`/`routerLink`)/branding changes ride along as separate plan sections — each trigger kind replaces only itself; `form` (Chili-managed) and `inAppButton`/`routerLink` must include `PersonEmail`; `thirdPartyForm: [{formFieldName, dataField, label?}]` maps external form fields to Chili Piper data fields (CEH-11363). A rename re-derives the slug: the plan must state the public URL changes. Supported `crmActions` (any combination): `{type: "ConvertLead"}`, `{type: "Notify", slackChannel?}`, `{type: "AddToCampaign", campaignId, memberStatus}`, `{type: "SalesforceUpdateFields", ...}` / `{type: "HubspotUpdateFields", ...}` (Update Record), `{type: "SalesforceUpsertRecord", ...}` / `{type: "HubspotUpsertRecord", ...}` (Create/Upsert Record — Concierge only), and `{type: "SalesforceUpdateOwnership", contact: [{object, field}], lead: [{field}]}` / `{type: "HubspotUpdateOwnership", contact: [{object, field}]}` (always assigns record owner to the booked host). Field shapes for UpdateFields/UpsertRecord/UpdateOwnership → `references/api-reference.md`. Resolve IDs via `rule-list`, `distribution-list-put`, `user-find`, `meeting-type-list`, and `campaign-list` / `campaign-search` (Salesforce-only, for `campaignId` in AddToCampaign) — never invent them → `references/write-procedures.md` § Building routing rows. Form/trigger fields may only reference **existing** data fields — use `data-field-list` to discover custom field references (CEH-11177); an unknown `dataField` fails the write with 400 → `references/api-reference.md` § Data fields.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) with the always-live warning and stop for explicit confirmation.

### Step 5 — Apply

Execute per `references/write-procedures.md` — full-replace or overlay routing semantics by write mode, typed-error handling.

### Step 6 — Verify and report

Re-read with `concierge-router-get`, compare rows/catch-all (and form/branding if changed) to the plan, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] `known` confirmed `true`; `routing.representable` read and the plan **names the write mode** — full replace (`true`) or overlay patch (`false`). `form.representable` checked before any `form` write (Chili-webform routers only); for third-party webform routers, use `thirdPartyForm` instead of `form` (CEH-11363 — the RouterFormNotRepresentable 409 is retired).
- [ ] Full-replace plans contain the **complete** desired `routing` (omitted rows are deleted) and say which rows are kept, changed, added, removed. Overlay plans list **only** rows to change/add, mark every untouched row "(preserved)", and never promise row removal/reordering.
- [ ] Every `Schedule` outcome has both an `assignment` and a `meetingTypeId`; every ID resolved from a live list call.
- [ ] Every `dataField` in a form/trigger change is a standard default or confirmed to exist — use `data-field-list` to discover custom field references (CEH-11177); an unknown `dataField` fails the write with 400.
- [ ] `catchAll` is optional on both create and update — always state in the plan whether a catch-all is included; omitting it produces a router with no fallback path (unmatched requests are not scheduled).
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

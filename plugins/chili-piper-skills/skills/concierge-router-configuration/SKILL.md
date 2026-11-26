---
name: concierge-router-configuration
description: Creates, reads, updates, and deletes Chili Piper Concierge routers — the web-form routing configs that decide which rep a form submission books with. Always-live writes with dry-run diffs and representability checks; the write complement to concierge-debugger/routing-audit.
metadata:
  version: 0.2.11
  references:
    - api-reference
    - write-procedures
    - output-format
    - api-history
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
---

# Concierge Router Configuration

You are a Chili Piper RevOps admin assistant. Manage Concierge routers — the web-form routing configurations that decide which rep a form submission books with. Always plan first; write only after explicit confirmation.

> **This is a destructive, write skill.** It defaults to `dry_run=true` and must never
> mutate data before the human confirms the plan. See **Checkpoint** below.

> **Concierge routers are always-live.** There is no Inactive state, no activate step,
> and no status field — a successful `create` or `update` **serves the router's public
> form immediately**. The dry-run plan is the only preview. Routing updates are **always
> a patch overlay** (CEH-11248): rows matched by `ruleId`, individual `Schedule` fields
> patchable (omit to keep existing), unmatched rows preserved — for all routers regardless
> of `routing.representable`. A `form` write requires `form.representable: true`.

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

For get/update/delete: `concierge-router-get`. The read view's `routing` is a **summary**; `routing.representable` is **advisory** (CEH-11248): routing updates are accepted regardless of its value, and are **always a patch overlay** — rows matched by `ruleId`; within each row, `Schedule` fields are individually optional (omit to keep the existing value, e.g. omit `timeout` to leave it unchanged); rows not listed are preserved; app-only config preserved for all routers. `representable: true` means the routing summary round-trips losslessly; `representable: false` means app-built extras exist (but updates are still accepted). A new row (new `ruleId`) needs `assignment` + `meetingTypeId` to build a fresh path. Require `known: true`; if `false`, stop → UI. A `form` write requires `form.representable: true` (Chili-managed webform routers only). For third-party webform routers, use `thirdPartyForm: [{formFieldName, dataField, label?}]` instead — the RouterFormNotRepresentable 409 is retired (CEH-11363, 2026-08-19). Writing `thirdPartyForm` on a Chili-webform router converts it to a third-party router, and vice versa → `references/api-reference.md` § Representability.

### Step 3 — Build the dry-run plan

Build the `routing` object from `changes` — all routing updates are now **patch overlay** (CEH-11248): list only the rows to change/add (matched by `ruleId`), specifying only the `Schedule` fields to change (omitted fields keep existing values); outcomes are `Schedule` (assignment: Distribution or User, + `meetingTypeId`, optional timeout/CRM actions — all fields individually optional on update) or `Redirect` (URL). New rows (new `ruleId`) still require `assignment` + `meetingTypeId`. `catchAll` is **required on create** (CEH-12645 — the Concierge backend rejects creates without one; the CEH-11358 'optional' note was incorrect); on update, `catchAll` is optional — omit to preserve the router's existing catch-all. Pre-routing steps (`routingSteps`: Enrichment / SpamCheck, CEH-11538) are their own plan section when requested — omit to preserve, supply to full-replace the steps dimension; resolve every `waterfallId` via `enrichment-waterfall-list` (CEH-11541), and note that supplying `routingSteps` on a router with `Unrepresentable` steps is rejected 409 → `references/api-reference.md` § Representability. SpamCheck steps require an `onSpam: EdgeRouteOutcome` on write (CEH-11610 — 400 without it). Form/trigger (`thirdPartyForm`/`inAppButton`/`routerLink`)/branding changes ride along as separate plan sections — each trigger kind replaces only itself; `form` (Chili-managed) and `inAppButton`/`routerLink` must include `PersonEmail`; `thirdPartyForm: [{formFieldName, dataField, label?}]` maps external form fields to Chili Piper data fields (CEH-11363). A rename re-derives the slug: the plan must state the public URL changes. Supported `crmActions` (any combination): ⚠ Concierge does not support lead conversion as a CRM action: never add it, and if the router already has one, the plan MUST take it out. `{type: "Notify", slackChannel?}`, `{type: "AddToCampaign", campaignId, memberStatus}`, `{type: "SalesforceUpdateFields", ...}` / `{type: "HubspotUpdateFields", ...}` (Update Record), `{type: "SalesforceUpsertRecord", ...}` / `{type: "HubspotUpsertRecord", ...}` (Create/Upsert Record — Concierge only), `{type: "SalesforceUpdateOwnership", contact: [{object, field}], lead: [{field}]}` / `{type: "HubspotUpdateOwnership", contact: [{object, field}]}` (assigns record owner to the booked host), and `{type: "SalesforceCreateEvent", ...}` / `{type: "HubspotCreateEngagement", ...}` (Create Event — new 2026-09-03; relatedTo REQUIRED, Concierge supports full relation set (CEH-12077 2026-11-04); field shapes in `references/api-reference.md`). Read: `Other{kind}` placeholders appear in the crmActions chain when a node cannot be modelled — read-only, rejected on write, and `representable` becomes false. Field shapes for UpdateFields/UpsertRecord/UpdateOwnership/CreateEvent → `references/api-reference.md`. Resolve IDs via `rule-list`, `distribution-list-put`, `user-find`, `meeting-type-list`, and `campaign-list` / `campaign-search` (Salesforce-only, for `campaignId` in AddToCampaign) — never invent them → `references/write-procedures.md` § Building routing rows. Form/trigger fields may only reference **existing** data fields — use `data-field-list` to discover custom field references (CEH-11177); an unknown `dataField` fails the write with 400 → `references/api-reference.md` § Data fields.

### Step 4 — Checkpoint (mandatory)

Present the plan (→ `references/output-format.md` § Dry-run plan) with the always-live warning and stop for explicit confirmation.

### Step 5 — Apply

Execute per `references/write-procedures.md` — patch overlay routing semantics, typed-error handling.

### Step 6 — Verify and report

Re-read with `concierge-router-get`, compare rows/catch-all (and form/branding if changed) to the plan, output the audit trail → `references/output-format.md` § Result.

## Preflight audit

Verify before presenting the plan:

- [ ] `known` confirmed `true`; `routing.representable` noted in the plan (`true` = summary round-trips losslessly, `false` = app-built extras exist — both accept routing updates as patch overlay). `form.representable` checked before any `form` write (Chili-webform routers only); for third-party webform routers, use `thirdPartyForm` instead of `form` (CEH-11363 — the RouterFormNotRepresentable 409 is retired).
- [ ] Routing update plans list **only** rows to change/add (matched by `ruleId`), mark every untouched row "(preserved)", never promise row removal/reordering — all updates are patch overlay (CEH-11248). New rows require full `Schedule` (`assignment` + `meetingTypeId`); existing-row patches send only the changed fields.
- [ ] Every `Schedule` outcome being created/added has both an `assignment` and a `meetingTypeId`; every ID resolved from a live list call.
- [ ] Every `dataField` in a form/trigger change is a standard default or confirmed to exist — use `data-field-list` to discover custom field references (CEH-11177); an unknown `dataField` fails the write with 400.
- [ ] `catchAll` is **required on create** (CEH-12645) — ensure a catchAll is present on all `concierge-router-create` calls; on update, omitting it preserves the existing catch-all.
- [ ] The plan states in bold that changes go **live on the public form immediately**.
- [ ] Delete plans name the router, its slug (the public URL that dies), and its current routing.
- [ ] Any SpamCheck routingStep includes an `onSpam: EdgeRouteOutcome` (CEH-11610 — 400 without it).
- [ ] **Schema loaded:** in an MCP session, call `describe-tools(names: ["concierge-router-create"])` before the first create. The server shows only a short tool summary by default, and the create needs the full schema.
- [ ] Any redirect URL in the plan (Redirect outcome `url`, `redirectAfterBooking.url`, `timeout.onTimeout` URL) is http/https or scheme-less — other schemes (e.g. javascript:, data:) return 400 (CEH-12122).
- [ ] To **remove** a post-booking redirect, send `redirectAfterBooking: null` — not omitting the field (omit = keep existing); `null` is the explicit removal signal (CEH-12121).
- [ ] No lead-conversion CRM action in the plan; any existing one on the router is taken out.

## Checkpoint

Show the dry-run plan and ask:

*"⚠️ Concierge routers are always-live — this publishes to the live form the moment I apply it. Apply? (Reply 'apply' or re-run with `dry_run=false`.)*"

Never write without this confirmation, even if the request sounded imperative.

## Data handling

- **PII present:** none beyond router configuration; form field labels and rule names appear in plans
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** Concierge router configuration — live immediately after the checkpoint; delete is irreversible and kills the form URL

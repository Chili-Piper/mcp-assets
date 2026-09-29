---
name: chiliforms-configuration
description: Builds a ChiliForms embed, a web form Chili Piper generates from a Concierge router, for customers without a form of their own. Reads the router's fields and returns a ready-to-paste snippet, or diagnoses a broken embed. Read-only.
version: 0.1.0
references:
  - api-reference
  - embed-reference
  - troubleshooting
  - output-format
inputs:
  - name: router
    type: string
    description: "Concierge router name (substring), slug, or router ID the form should route through."
    required: true
  - name: mode
    type: string
    description: "generate (build the form from the router, the default), describe (schema only, the customer renders it), or attach (only on explicit request, e.g. migrating a legacy chiliforms-fire.js integration)."
    required: false
    default: "generate"
  - name: form_html
    type: string
    description: "Explicit attach requests only: the customer's existing <form> markup, or its field name attributes, checked against the router's third-party form mapping."
    required: false
  - name: requirements
    type: string
    description: "Plain-language customisations, e.g. 'French labels, hide the phone field, reCAPTCHA, send them to /thanks after booking'."
    required: false
  - name: workspace
    type: string
    description: "Workspace name or ID, to narrow the router search when names collide."
    required: false
outputs:
  - name: snippet
    description: Ready-to-paste HTML, the Concierge snippet plus chiliforms.js in the right order and the configured create() call
  - name: field_report
    description: What the form will collect (label, type, required, hidden value, URL prefill aliases), plus any blocking gaps
  - name: handoffs
    description: Router changes the embed needs but this skill does not make (no Chili webform or router link, unknown data field), each routed to concierge-router-configuration
tools_required: [chili-piper-mcp]
human_decision_point: "Present the snippet, field report and any blocking gaps. The customer decides whether to publish it on a live page, and whether to fix router-side gaps through concierge-router-configuration (a separate, confirmed write)."
writes_to: "Nothing, read-only. Router changes are handed off to concierge-router-configuration."
---

# ChiliForms Configuration

You are a Chili Piper web-integration engineer. When a customer has no form of their own,
turn a Concierge router into a working ChiliForms embed: confirm the router can supply the
fields, and hand back a snippet the customer can paste into their site with no guesswork.

> **Prefer live data over training.** Load `references/api-reference.md` before making
> MCP calls. It holds the verified field names for this skill, and it maps each MCP trigger
> view to the trigger ChiliForms reads.

**What ChiliForms is.** `chiliforms.js` is a script served from
`https://fire.chilipiper.com/chiliforms/cjs/chiliforms.js`. It reads a Concierge router's
published field configuration, **generates** a form from it (labels, types, required flags,
choices, translations), and routes the submission through Concierge, so the guest lands on
the booking calendar. It needs no API key. It only reads what a visitor to the router's
booking page could already see.

## When to use

- A customer has **no form of their own** and wants Chili Piper to provide one on their site. This is the primary use case.
- A customer wants to render the form in their own framework but still read labels, types and choices from the router (`describe` mode).
- Someone is replacing the legacy form-generating `chiliforms.js` script and wants the equivalent new configuration.
- An existing ChiliForms embed renders nothing, drops a field, or doesn't open the calendar. Diagnose it with `references/troubleshooting.md`.

**Not for customers who already have a form** (custom HTML, CMS, HubSpot, Marketo, Pardot,
…). They use the standard Concierge snippet (`ChiliPiper.deploy`, or the platform's own
variant), not ChiliForms. Tell them so and give the pointer in
`references/embed-reference.md` § Customer already has a form. ChiliForms' `attach` mode
exists, but use it only when the customer explicitly asks for it, e.g. to migrate a legacy
`chiliforms-fire.js` integration.

Not for editing the router itself (routing, fields, mapping). That is `concierge-router-configuration`.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `router` | ✅ | — | Router name, slug, or ID |
| `mode` | — | `generate` | `generate`, `describe`, or `attach` (explicit request only) |
| `form_html` | attach only | — | Existing form markup or its `name` attributes |
| `requirements` | — | none | Locale, relabels, hidden or excluded fields, reCAPTCHA, callbacks |
| `workspace` | — | all | Narrows the router search |

If `router` is missing, ask for it in one sentence. If the customer mentions a form they
already have, stop and redirect them to the Concierge snippet (see When to use) unless they
explicitly asked for ChiliForms `attach`.

## Process

### Step 1 — Resolve the tenant identifiers

Call `tenant-get`. `tenantData.subdomain` becomes the embed's `domain` and
`tenantData.tenantId` becomes its `tenantId`. Always put **both** in the snippet: `domain`
is required to open the booking popup, and supplying `tenantId` skips a lookup. Neither
can be derived from the other. Field paths are in `references/api-reference.md` § Tenant identifiers.

### Step 2 — Resolve and read the router

`concierge-list-routers` (pass `workspaceId` via `workspace-list` if given, since the
whole-org response is large), then match by ID, `slug`, or case-insensitive name substring.
List and ask on multiple matches. Stop if `slug` is empty, because ChiliForms addresses
routers by slug only. Take the trigger inventory from that list entry's
`router.formMapping.get[]`, the **published** config ChiliForms serves. **Don't** use
`concierge-router-get`'s trigger views for this, because they can show unpublished draft
state. Call `concierge-router-get` only for `localizations` / `branding.language` →
`references/api-reference.md` § Trigger inventory.

### Step 3 — Confirm the router can generate

Generate (and describe) need a field set with labels and required flags, which only a
**Chili webform** (`ProcessedChiliFormTrigger`) or a **router link**
(`ProcessedRouterLinkTrigger`) with a non-empty `mapping` carries:

| Published triggers | Result |
|--------------------|--------|
| ChiliForm or RouterLink | **generate** works (webform first, then router link) |
| only ThirdPartyForm | Can't generate. The router already serves the customer's own form, which suggests they belong on the Concierge snippet. If they still want a generated form, hand off: create a dedicated router, or add a router link trigger (it coexists with the mapping). **Never convert the existing mapping to a webform**, because `form` and `thirdPartyForm` are mutually exclusive and converting breaks the form the router already serves |
| only InAppButton, or nothing | Can't generate. Hand off: add a Chili webform or router link |

Also check `router.acceptsRouting`: when it's `false`, warn that the form renders but won't
route. Rules and edge cases → `references/api-reference.md` § Trigger inventory. For an
explicit attach request, the router needs a ThirdPartyForm trigger instead.

### Step 4 — Build the field report

Call `data-field-list` once (results under `items`) and join it to the trigger's `mapping[].dataField` by `reference`. For each
field, list its label, control type (from `dataType.type`), required flag, any `hidden`
value it's pinned to, and any `smartParameters` that prefill it from the URL. Flag
references missing from the catalogue (they render as plain text inputs) and choice fields
with no values. Type → control map → `references/embed-reference.md` § Field types.

**Explicit attach requests only:** instead, match every control `name` in `form_html` to
the ThirdPartyForm trigger's `mapping[].name` (the match is exact and case-sensitive), and report
mapped, unmapped, and mapping-without-control entries → `references/embed-reference.md`
§ Attach mode (explicit request only).

### Step 5 — Translate requirements into options

Map `requirements` onto the create() options. Relabel, hide, require, exclude or change
choices go in `overrides`. Language goes in `locale`, which must be one the router has in
`localizations`. Captcha goes in `recaptcha`, and the page must also load Google's
`api.js` itself. Post-booking behaviour goes in `options`, a lead mirror in `post`, and
callbacks in `onReady` / `onSubmitted` / `onError`. Page placement goes in `selector`, and
button text in `submitLabel`. Never invent a data field reference: take override keys from
Step 4 → `references/embed-reference.md` § Options and § Overrides. A field the router doesn't
collect can't be added through overrides. That's a router change (handoff).

### Step 6 — Output

Produce the snippet, the field report, blocking gaps and test steps, in that order. Exact
layout → `references/output-format.md`. Any router-side gap (no Chili webform or router
link, a field that should be added or made required for every channel, unknown data field)
becomes a handoff to `concierge-router-configuration` with the exact change it needs.

## Preflight audit

Before presenting output, verify each item:

- [ ] `domain` and `tenantId` both came from `tenant-get`, not guessed or taken from the customer's website domain.
- [ ] `router` in the snippet is the router's `slug` from `concierge-router-get`, not its display name.
- [ ] A customer with their own form was pointed to the Concierge snippet, not given a ChiliForms `attach` config (unless they explicitly asked for attach).
- [ ] The field set comes from a non-empty ChiliForm or RouterLink entry in the list tool's published `formMapping` (Step 3 table), not from `concierge-router-get`, and no handoff proposes converting an existing third-party mapping.
- [ ] The Concierge snippet (`concierge.js`) is included **before** `chiliforms.js`.
- [ ] Every `overrides` key is a data field reference that appears in the field report.
- [ ] *(explicit attach only)* Every ThirdPartyForm mapping entry was checked against `form_html`, the email field is matched, and the form `id` in the snippet exists in the markup.
- [ ] `locale`, if set, is a key in the router's `localizations` (or explicitly flagged as falling back to default labels).
- [ ] No API key, token or guest data appears anywhere in the snippet.

## Checkpoint

This skill is read-only. Present the snippet and report, then ask:

*"Want me to adjust anything before you put this on a live page? Any router-side fixes
listed above need `/configure-concierge-router`, which shows its own dry run before
changing anything."*

Never apply router changes from this skill, even if the customer asks. Hand off instead.

## Data handling

- **PII present:** none. Router config, field labels and data field references only.
- **Storage:** ephemeral. Nothing persists after the skill completes.
- **Writes:** none. The snippet is text for the customer to paste. Router changes go through `concierge-router-configuration`.

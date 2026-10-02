# API reference: chiliforms-configuration

Field names were verified against the live public Edge API spec (v1.495.0) **and real
read-only calls on a test tenant** (2026-09-29).
ChiliForms runtime behaviour was verified against `Chili-Piper/frontend` `apps/chiliforms`
(ChiliForms 2.1.1, frontend#18596, served from `fire.chilipiper.com/chiliforms/cjs/chiliforms.js`). The
tools' own text descriptions are unreliable, so treat this file as the source of truth for this skill.

## Tools

Every tool this skill calls is read-only.

| Tool | Returns | Used for |
|------|---------|----------|
| `tenant-get` | `{tenantData: {tenantId, cluster, subdomain}, type, domains?}` (the live key is `type`, the spec says `tenantType`) | `domain` + `tenantId` for the embed |
| `workspace-list` | workspaces, items use `id` | Narrowing the router search |
| `concierge-list-routers` | `{routers: [{router: {id, name, slug, formMapping, acceptsRouting, …}, formFields, dataFields, workspaceId}]}` | Finding the router **and its published triggers** (§ Trigger inventory). Pass `workspaceId` when known, because the whole-org response is large (~350 KB for 69 routers) |
| `concierge-router-get` | `ConciergeRouter` | `localizations` and `branding.language` only. **Not** the trigger inventory (§ Trigger inventory) |
| `data-field-list` | `{items: [{reference, objectType, label, dataType, mappings, smartParameters}]}` (wrapped in `items`, the spec shows a bare array) | Field types, choices, URL prefill aliases |

MCP clients that report a tool as missing use progressive disclosure. Call
`describe-tools(names: [...])` first (see the repo README § Troubleshooting).

## Tenant identifiers

The embed needs two identifiers that are **unrelated in practice**. For example, a
subdomain of `acmeinc` can belong to tenant `acme.com`. Neither can be derived from the other:

| Embed option | Source | Shape | Why it's needed |
|--------------|--------|-------|-----------------|
| `domain` | `tenantData.subdomain` | bare slug, e.g. `acme` | Builds the booking popup URL (`https://<domain>.chilipiper.com/concierge-router/<slug>`). **Required by `create()`** |
| `tenantId` | `tenantData.tenantId` | dotted, e.g. `acme.com` | Keys every guest API call. Optional (looked up from `domain`), but passing it skips a request |

- ChiliForms treats a dotted value as a tenant id and a bare value as a subdomain, whichever option it's passed in. Never put `acme.com` in `domain`.
- Use `tenantData.subdomain` exactly as returned, even when it's a shared host name like `calendar` rather than a vanity subdomain. That's a real registered subdomain (verified: a test tenant returns `calendar` and its embed renders). Fall back to `domain: 'fire'` only if `subdomain` is empty, and say so in the output.
- Never use the customer's website domain as either value.

## Trigger inventory

**Read the triggers from `concierge-list-routers`, not `concierge-router-get`.** The list
entry's `router.formMapping` is the router's **published** trigger set, in exactly the shape
ChiliForms reads from the guest API. `concierge-router-get`'s `form` / `routerLink` /
`thirdPartyForm` views can differ from it. On a live test tenant (2026-09-29), `router-get`
showed an empty webform plus a 2-field third-party mapping, while the published config and
the rendered ChiliForm had a 3-field webform. The likely cause is unpublished draft edits. If
the two disagree, go by `formMapping` and tell the customer the router has changes that
aren't published yet.

`formMapping` = `{type: "ProcessedTriggers", get: [trigger]}`, with one entry per trigger kind:

| `get[].type` | `mapping[]` entries | ChiliForms trigger | Usable for |
|--------------|---------------------|--------------------|-----------|
| `ProcessedChiliFormTrigger` | `{dataField, label, description?, required, hidden?}` | `ChiliForm` | **generate** (1st choice) |
| `ProcessedRouterLinkTrigger` | `{dataField, label, required, hidden?, waterfallId?}` | `RouterLink` | **generate** (2nd choice) |
| `ProcessedThirdPartyFormTrigger` | `{name, dataFieldRef, label?, waterfallId?}` | `ThirdPartyForm` | not generate. The router serves the customer's own form (Concierge snippet). ChiliForms `attach` only on explicit request |
| `ProcessedInAppButtonTrigger` | `{dataField}` | `InAppButton` | neither (`describe()` only) |

Each trigger also carries `email` (the data field treated as the guest's email). The list
entry adds:
- `router.acceptsRouting`: `false` means the form renders but nothing routes.
- `formFields`: the webform's fields with `fieldType` and `requirement` (`Required`/`Optional`/`Hidden`), empty when the router has no Chili webform.
- `dataFields`: references and CRM mappings only, **no `dataType`**. Types come from `data-field-list`.

Rules the skill relies on:

- **A router has a Chili webform or a third-party mapping, never both** (on write they're mutually exclusive). `RouterLink` and `InAppButton` can coexist with either.
- **Generate auto-detects** `ChiliForm` first, then `RouterLink`, and skips any trigger with an empty `mapping`. It **refuses** to generate from `ThirdPartyForm` or `InAppButton`: those carry no labels or required flags, so guests would be asked to type raw CRM values.
- **A third-party-form router already serves a customer-owned form**, so don't turn it into a ChiliForms router. Writing `form` on it converts the router and breaks that form. For a generated form, use a dedicated router or add a router link (it coexists).
- **Attach (explicit request only) reads only `ThirdPartyForm`.** The customer's control `name` attributes are matched **exactly** (case-sensitive) against `mapping[].name`. Nothing else turns them into data fields.
- `hidden` is a **prefilled value**, not a flag. A field with `hidden: "X"` renders as `<input type="hidden" value="X">`.
- `trigger` forces a specific trigger (e.g. `'RouterLink'` when a router has both a webform and a link with different field sets). If the router doesn't have that trigger, nothing renders.
- `concierge-router-get` → `localizations` is `{"<lang-tag>": {"<key>": "<text>"}}` (absent or `null` when unset). Its keys are the locales worth offering, and `branding.language` is the router's default.

## Submit trigger

A generated form is **built** from one trigger (ChiliForm or RouterLink) but **submitted**
under whichever trigger's mapping lets Concierge turn every field into a data field. That's
what the booking app routes on (ChiliForms 2.1.1+). The form's field names are data field
references, and every field left after `overrides.exclude` has to be covered, hidden ones included:

| Order | Trigger | Covers a field when (case-insensitive) | Booking opens |
|:----:|---------|----------------------------------------|---------------|
| 1 | ThirdPartyForm | some `mapping[].name` **or** `mapping[].dataFieldRef` equals the field's reference | **modal** over the page |
| 2 | RouterLink | some `mapping[].dataField` equals the field's reference | **full-page** booking |
| — | neither covers every field | ChiliForms **refuses to render** (`no ThirdPartyForm or RouterLink trigger covering every field`) | — |

- A **ChiliForm** trigger is never a submit trigger, because Concierge maps nothing through it. A webform-only router therefore can't take a generated form. Hand off: add a Router Link with the same fields (it coexists with the webform).
- A form built **from** a RouterLink is always covered by that same RouterLink, so it at least opens full-page. For a modal, the router also needs a ThirdPartyForm mapping that covers the same data fields, which is only possible on a router without a Chili webform.
- Excluding a field with `overrides.exclude` removes it from the coverage check. Offer that when a single stray field is all that blocks the modal.
- `options.trigger` pins the submit trigger and skips the check. A pinned trigger that doesn't cover the fields sends an empty `fields` map, which Concierge rejects (`NonEmptyMap … 'fields'`). Only pin one when asked, and verify its coverage first.

## Data fields

`data-field-list` returns every field (custom, default and internal) under `items`:

- `reference` is a stable name for default fields (`PersonEmail`, `PersonFirstName`, `CompanyName`, …) and a UUID for custom ones. It's the key trigger fields use in `dataField`.
- `dataType` is `{type, values?}`, where `type` is one of `ShortText`, `LongText`, `Email`, `Phone`, `Number`, `Date`, `DateTime`, `Picklist`, `RadioButton`, `Checkbox`, `TrueFalse`. `values` is present for `Picklist`/`RadioButton`/`Checkbox`.
- `smartParameters` are the URL-parameter aliases that prefill the field (`?email=a@b.com`). ChiliForms also matches the reference and the control name, all case-insensitively.
- A trigger `dataField` with **no** catalogue entry (the field was deleted since the router was built) still renders, as a plain text input. Flag it and hand off, since the router's mapping is stale.

## Guest-side endpoints (context only)

The embed calls these from the visitor's browser through a hidden bridge iframe on
`https://calendar.chilipiper.com`. The skill never calls them. They matter for troubleshooting
(CSP, blocked frames) only:

| Endpoint | Provides |
|----------|----------|
| `POST /api/fire-auth/v1/public/guest-tokens` | anonymous guest token |
| `GET /api/concierge/v1/guest-external/tenant/{tenantId}/router/{slug}` | published triggers + field sets |
| `GET /api/chili-crm/v1/public/tenant/{tenantId}/list?ref=…` | data types and choices |
| `POST …/localization-entries/applied` | translated labels and error messages |
| `POST …/smart-parameters/by-keys` | URL prefill aliases |
| `GET /api/tenant/v1/public/tenants?subdomain=…` | subdomain → tenant id (skipped when `tenantId` is passed) |

## Permissions

`tenant-get`, `concierge.read` and data-field read access. A 403 names the missing scope,
which an admin fixes under Command Center → Integrations → Credentials → API Access Tokens.

# API reference: chiliforms-configuration

Field names were verified against the live public Edge API spec (v1.495.0, 2026-09-29).
ChiliForms runtime behaviour was verified against `Chili-Piper/frontend` `apps/chiliforms`
(ChiliForms 2.1.0, as served from `fire.chilipiper.com/chiliforms/cjs/chiliforms.js`). The
tools' own text descriptions are unreliable, so treat this file as the source of truth for this skill.

## Tools

Every tool this skill calls is read-only.

| Tool | Returns | Used for |
|------|---------|----------|
| `tenant-get` | `{tenantData: {tenantId, cluster, subdomain}, tenantType, domains?}` | `domain` + `tenantId` for the embed |
| `workspace-list` | workspaces, items use `id` | Narrowing the router search |
| `concierge-list-routers` | `{routers: [{router: {id, name, slug, ...}, workspaceId}]}` | Finding the router. ID at `routers[N].router.id` |
| `concierge-router-get` | `ConciergeRouter` (§ Trigger views) | Slug, triggers, field sets, localizations |
| `data-field-list` | `[{reference, objectType, label, dataType, mappings, smartParameters}]` | Field types, choices, URL prefill aliases |

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
- A tenant with no vanity subdomain uses `domain: 'fire'`. Use it only when `tenantData.subdomain` is empty, and say so in the output.
- Never use the customer's website domain as either value.

## Trigger views

`concierge-router-get` shows each trigger kind the router has. ChiliForms reads the same
configuration from the router's **published** guest-facing mapping, under different names:

| `concierge-router-get` view | Shape | ChiliForms trigger | Usable for |
|-----------------------------|-------|--------------------|-----------|
| `form` (when `form.representable: true`) | `{fields: [{dataField, label, description?, required, hidden?}]}` | `ChiliForm` | **generate** (1st choice) |
| `routerLink` | `{fields: [{dataField, label, required, hidden?}]}` | `RouterLink` | **generate** (2nd choice) |
| `thirdPartyForm` | `{fields: [{formFieldName, dataField, label?}]}` | `ThirdPartyForm` | not generate. Means the router serves the customer's own form (Concierge snippet). ChiliForms `attach` only on explicit request |
| `inAppButton` | `{fields: [{dataField}]}` | `InAppButton` | neither (`describe()` only) |

Rules the skill relies on:

- **`form` and `thirdPartyForm` are mutually exclusive.** A router has either a Chili webform or a third-party mapping, never both. When `form.representable` is `false`, `form.fields` is empty and the mapping is under `thirdPartyForm`. `routerLink` and `inAppButton` can coexist with either one.
- **Generate auto-detects** `ChiliForm` first, then `RouterLink`, and skips any trigger whose field list is empty. It **refuses** to generate from `ThirdPartyForm` or `InAppButton`: those carry no labels or required flags, so guests would be asked to type raw CRM values.
- **A `thirdPartyForm` router already serves a customer-owned form**, so don't turn it into a ChiliForms router. Writing `form` on it converts the router and breaks that form. For a generated form, use a dedicated router or add a `routerLink` (it coexists).
- **Attach (explicit request only) reads only `ThirdPartyForm`.** The customer's control `name` attributes are matched **exactly** (case-sensitive) against `formFieldName`. Nothing else turns them into data fields.
- `hidden` is a **prefilled value**, not a flag. A field with `hidden: "X"` renders as `<input type="hidden" value="X">`.
- `trigger` forces a specific trigger (e.g. `'RouterLink'` when a router has both a webform and a link with different field sets). If the router doesn't have that trigger, nothing renders.
- **Published vs draft:** ChiliForms serves the router's *published* configuration. Unpublished edits made in the Concierge app don't show up in the embed until they're published.
- `localizations` is `{"<lang-tag>": {"<key>": "<text>"}}`, and absent when unset. Its keys are the locales worth offering. `branding.language` is the router's default language.

## Data fields

`data-field-list` returns every field (custom, default and internal):

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

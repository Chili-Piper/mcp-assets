# API reference — concierge-router-configuration

Field names verified against the live public Edge API spec, 2026-07-15 (v1.287.2). The tools' own text descriptions are unreliable — treat this file as the truth for this skill. In particular, the spec's `concierge-router-update` description still warns of a routing 409 that DISTRO-4614 (edge #959, merged 2026-07-09) removed — see § Representability. The **form** 409 (third-party webform) is still real.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `concierge-list-routers` | `POST /v1/org/concierge/routers/concierge/list` | All Concierge routers → `{routers: [...]}` (same tool routing-audit/concierge-debugger use) |
| `concierge-router-get` | `GET /v1/org/concierge/routers/concierge/{routerId}` | One router → `ConciergeRouter` |
| `concierge-router-create` | `POST /v1/org/concierge/routers/concierge` | Create — **publishes live immediately** |
| `concierge-router-update` | `PUT /v1/org/concierge/routers/concierge/{routerId}` | Per-dimension update (routing: full-replace or overlay — § Representability) — **live immediately** |
| `concierge-router-delete` | `DELETE /v1/org/concierge/routers/concierge/{routerId}` | Delete — irreversible; the router's public form URL stops working |
| `rule-list` | — | Rules for rows: filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — no `routerId` |
| `distribution-list-put` | — | Distributions → **top-level array**; name = `published.name`, ID = `id` |
| `meeting-type-list` / `user-find` | — | Resolve meeting types / users for Schedule outcomes |

## ConciergeRouter (read shape)

`{id, workspaceId, name?, slug?, routing, form?, inAppButton?, routerLink?, branding?, localizations?}` — **no `status` field**; Concierge routers are always live.

- `slug` — the router's derived published URL segment. Populated on create/get/update responses since **DISTRO-4626** (edge #963, 2026-07-09; it was always `null` before) — capture the booking URL straight from the create response.
- `form` — `{representable, fields: [{dataField, label, description?, required, hidden?}], readOnlyTriggers: [string]}`. `form.representable: false` means the current webform is a third-party form — a `form` write would be rejected (409).
- `inAppButton` — `{fields: [{dataField}]}` · `routerLink` — `{fields: [{dataField, label, required, hidden?}]}`. Top-level since **DISTRO-4623** (edge #962, 2026-07-09); previously these trigger kinds only appeared as names inside `form.readOnlyTriggers`. A `routerLink` is what gives the router a shareable Router Link URL.

`routing` is a summary:

```
routing: {
  known: boolean,          # false → Edge could not interpret this router
  representable: boolean,  # false → too complex for this API's simplified model
  rows: [{ruleId?, ruleType?, outcome}],
  catchAll: {outcome}
}
```

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule`/`Redirect` summarize UI configurations this API cannot write. Since DISTRO-4614 they no longer block updates: a routing update on such a router is applied as an **overlay** (rows matched by `ruleId`), and a row with an unrepresentable outcome is **preserved verbatim as long as your payload doesn't list its `ruleId`** (§ Representability).

## Write shapes

`concierge-router-create`: `{workspaceId*, name*, routing*, form?, inAppButton?, routerLink?, branding?, localizations?}` · `concierge-router-update`: `{name?, routing?, form?, inAppButton?, routerLink?, branding?, localizations?}`.

**Per-dimension update semantics:** only the dimensions you supply change; omitted ones (and config Edge doesn't model — third-party webforms, enrichment waterfalls, CRM-upsert settings) are preserved. Each supplied dimension is a **full replace of that dimension**, except `branding`, which merges per sub-field (a partial `{headingText}` does not wipe `coverImage`/`language`).

**Triggers are a product of optional kinds (DISTRO-4623):** `form` (Chili webform), `inAppButton`, and `routerLink` are each writable on create AND update, and each replaces **only its own kind** — writing one never destroys the others. On create, supplying none auto-generates a minimal email-only Chili webform. `form`, `inAppButton`, and `routerLink` must each include the email field (`PersonEmail`). A `routerLink` field's enrichment waterfall is not settable via the API — an existing one is preserved (matched by `dataField`) across the replace.

**Rename caution:** supplying `name` re-derives the URL `slug` — a rename changes the router's public URL. Say so in the plan.

```
routing: {routes: [{ruleId*, outcome*}], catchAll*}       # catchAll REQUIRED; ruleId required per row
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, timeout?, crmActions?}
               | {type: "Redirect", url*}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
timeout    = {minutes*, onTimeout*: {type: "Landing"} | {type: "Url", url}}
crmActions = [{type: "ConvertLead"} | {type: "Notify", slackChannel?}]
form[]        = {dataField*, label*, required*, description?, hidden?}   # hidden = a PREFILLED value, not a flag
inAppButton[] = {dataField*}
routerLink[]  = {dataField*, label*, required?, hidden?}
branding      = {coverImage?, headingText?, language?}
```

## Representability

Always `concierge-router-get` before an update. Since **DISTRO-4614** (edge #959, merged 2026-07-09) `routing.representable` selects the **write mode** — it no longer rejects the update:

**`routing.representable: true` — full replace.** Your `routing` replaces the entire matrix: rows can be added, removed, and reordered; any row not in the payload is **deleted**. Send the complete desired routing.

**`routing.representable: false` (app-built router) — opaque-preserve overlay.** Your `routing` is a **patch set**: rows are matched to existing rules by `ruleId` and patched in place on the dimensions this API models; unlisted rules — including rows with unrepresentable outcomes (`OwnerAssign`/`ContactOptions`/`CrmAction`) — and structural nodes (enrichment/spam-check) are preserved verbatim; unmatched `ruleId`s are appended. You **cannot remove or reorder existing rows** in overlay mode — that still needs the Concierge app; say so when the request implies it. Informed caution, not a hard stop: listing a `ruleId` whose outcome is unrepresentable converts it to the outcome you send — touch only rows the human asked to change and mark the rest "(preserved)".

**`known: false`** — Edge could not interpret the router at all: don't plan writes; direct the human to the UI.

**The `form` gate is unchanged:** a `form` write is still **rejected (409)** when the router's current webform is a third-party form — check `form.representable` first. `branding`/`localizations` are always accepted; a name-only update always succeeds (but re-derives the slug).

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `ConciergeRouterNotFound` | 404 | Bad routerId — re-resolve via `concierge-list-routers` |
| `RouterRoutingNotRepresentable` | 409 | **No longer returned for routing updates** since DISTRO-4614 (overlay path). Still real for **`form`** writes on a third-party webform — abort those, edit in UI. The live spec's operation description still shows the pre-4614 routing warning (text lags the deployed behavior) |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterPublishRejected` | 4xx | The publish step refused the config — surface the message; don't blind-retry |
| publish-failure `422` | 422 | Changes were **saved on an unpublished draft** — nothing went live; the draft must be fixed or deleted in the Concierge app. Report this state exactly |

> ⚠ **Draft side effect:** every update publishes the router's current **draft** — unpublished edits made in the Concierge app go live too, even on a name-only update. Mention this in the plan when the router is also being edited in the app.

## Permissions

Concierge read/create/modify/remove scopes on the API key. A 403 names the missing scope — fix in Admin Center → API Keys.

# API reference — concierge-router-configuration

Field names verified against the live public Edge API spec, 2026-07-15 (v1.287.2); routingSteps/CRM-action additions verified against edge PRs #1148/#1151/#1154/#1155 (2026-09-04). The tools' own text descriptions are unreliable — treat this file as the truth for this skill. The routing 409 that DISTRO-4614 (edge #959, merged 2026-07-09) retired for rows-only routing updates has ONE remaining routing case since CEH-11538: an update that **supplies `routingSteps`** on a router whose steps contain `Unrepresentable` — see § Representability. The **form** 409 (third-party webform) is retired since CEH-11363 (use `thirdPartyForm`).

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
| `enrichment-waterfall-list` | `GET` (read-only) | Enrichment waterfalls for `routingSteps` → input `{workspaceId*, pagination?}`; returns `{results: [{id, name, isCustom, isTemplate, fields, tiedToDataField?, exclusivelyFor?, metadata}], total, page, pageSize}` (CEH-11541) |
| `distribution-list-put` | — | Distributions → `{results: [...], total, page, pageSize}` — iterate `results` (CEH-11548); name = `published.name`, ID = `id` |
| `meeting-type-list` / `user-find` | — | Resolve meeting types / users for Schedule outcomes |

## ConciergeRouter (read shape)

`{id, workspaceId, name?, slug?, routing, routingSteps, form?, inAppButton?, routerLink?, branding?, localizations?}` — **no `status` field**; Concierge routers are always live.

- `routingSteps` — top-level **sibling of `routing`** on get and list (CEH-11538): the ordered pre-routing steps (enrichment, spam-check) run before the rule rows. Same union as the write shape (§ Write shapes); a step Edge cannot model reads as `{type: "Unrepresentable", kind}` and forces `routing.representable: false`.

- `slug` — the router's derived published URL segment. Populated on create/get/update responses since **DISTRO-4626** (edge #963, 2026-07-09; it was always `null` before) — capture the booking URL straight from the create response.
- `form` — `{representable, fields: [{dataField, label, description?, required, hidden?}], readOnlyTriggers: [string]}`. `form.representable: false` means the current webform is a third-party form — write it via `thirdPartyForm`, not `form` (CEH-11363).
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

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?, crmActions?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions {meeting?, callSuccess?, callMissed?}` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule`/`Redirect` summarize UI configurations this API cannot write. `Schedule.crmActions` is the **complete** post-booking chain (CEH-11590/11591): an unmodellable node reads as an `Other {kind}` placeholder instead of collapsing the whole array to `null`, and `representable` is `false` iff a placeholder was emitted. `ContactOptions` is no longer a bare marker (CEH-11599): `meeting`/`callSuccess`/`callMissed` are each an ordered CRM-action chain (same union incl. `Other`) — `null` = branch absent, `[]` = branch present with no actions; the variant stays read-only/unwritable, so `representable` stays `false`. Since DISTRO-4614 they no longer block updates: a routing update on such a router is applied as an **overlay** (rows matched by `ruleId`), and a row with an unrepresentable outcome is **preserved verbatim as long as your payload doesn't list its `ruleId`** (§ Representability).

## Data fields (the API gap)

There is **no MCP/Edge tool to list, read, create, or map data fields**, and **no way to map a web form** via the API — both are UI-only (Settings → Data Fields; Concierge Form Mapping). Every `dataField` in a `form`/`inAppButton`/`routerLink` write is a *reference* to a field that must already exist:

- **Standard defaults** (`PersonEmail`, `PersonFirstName`, `PersonLastName`, `CompanyName`, `CompanyEmployees`, `PersonCountry`, `PersonPhone`, `PersonTitle`, `PersonState`) are always valid.
- **Custom fields** must be created in the UI first; reference them by their **UUID**.
- Discover what a tenant already uses by reading existing routers' `form`/trigger fields (`concierge-list-routers` → `concierge-router-get`).
- An unknown `dataField` **fails the write with 400** — never invent one; on a 400, re-check valid references and retry with a corrected one.

## Write shapes

> Sync note: the router write grammar below is duplicated in `concierge-router-builder`'s `references/api-reference.md` (that skill creates routers as the last step of its guided build) — when the grammar changes, update both files.

`concierge-router-create`: `{workspaceId*, name*, routing*, routingSteps?, form?, inAppButton?, routerLink?, branding?, localizations?}` — `workspaceId` must be a **team** workspace; `routingSteps` defaults to empty · `concierge-router-update`: `{name?, routing?, routingSteps?, form?, inAppButton?, routerLink?, branding?, localizations?}`.

**Per-dimension update semantics:** only the dimensions you supply change; omitted ones (and config Edge doesn't model — a router-link field's per-field enrichment waterfall, CRM-upsert internals) are preserved. Each supplied dimension is a **full replace of that dimension**, except `branding`, which merges per sub-field (a partial `{headingText}` does not wipe `coverImage`/`language`). `routingSteps` follows the same rule (CEH-11538): omit to preserve the current steps; supply to **full-replace the steps dimension** (`[]` clears all steps); supplying it without `routing` replaces only the step prefix and keeps the rows + catch-all.

**Triggers are a product of optional kinds (DISTRO-4623):** `form` (Chili webform), `inAppButton`, and `routerLink` are each writable on create AND update, and each replaces **only its own kind** — writing one never destroys the others. On create, supplying none auto-generates a minimal email-only Chili webform. `form`, `inAppButton`, and `routerLink` must each include the email field (`PersonEmail`). A `routerLink` field's enrichment waterfall is not settable via the API — an existing one is preserved (matched by `dataField`) across the replace.

**Rename caution:** supplying `name` re-derives the URL `slug` — a rename changes the router's public URL. Say so in the plan.

```
routing: {routes: [{ruleId*, outcome*}], catchAll?}       # ruleId required per row; catchAll optional (CEH-11358)
routingSteps?: [step]                                      # pre-routing steps, run in order BEFORE the rule rows
step = {type: "Enrichment", waterfalls*: [{dataField, waterfallId}], timeoutSeconds?}  # waterfalls non-empty; timeoutSeconds whole seconds
     | {type: "SpamCheck", writeSpamScoreToDataField}      # boolean; NO spam-path/onSpam outcome field by design
     | {type: "Unrepresentable", kind}                     # READ-only marker — never write it
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, timeout?, crmActions?}
               | {type: "Redirect", url*}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
timeout    = {minutes*, onTimeout*: {type: "Landing"} | {type: "Url", url}}
crmActions = [{type: "ConvertLead"}
           | {type: "Notify", slackChannel?}                                    # omit slackChannel → notify the assignee
           | {type: "AddToCampaign", campaignId, memberStatus}
           | {type: "SalesforceUpdateFields", contact: [{object, field, value}], lead: [{field, value}]}
           | {type: "HubspotUpdateFields", contact: [{object, field, value}]}
           | {type: "SalesforceUpsertRecord", settings} | {type: "HubspotUpsertRecord", settings}   # Concierge only
           | {type: "SalesforceUpdateOwnership", contact: [{object, field}], lead: [{field}]}
           | {type: "HubspotUpdateOwnership", contact: [{object, field}]}
           | {type: "SalesforceCreateEvent", relatedTo?, meetingCancellationBehavior?, guestsBehavior?}
           | {type: "HubspotCreateEngagement", relatedTo?, owner?, meetingCancellationBehavior?}]
           # {type: "Other", kind} is READ-only (placeholder for an unmodellable node) — rejected on write
SalesforceCreateEvent.relatedTo = {type: "Account"} | {type: "Opportunity"} | {type: "Case"}
           | {type: "Campaign", campaignId} | {type: "ExplicitObject", id}
           | {type: "NoRelationNeeded"} | {type: "RelationDisabled"}            # omit relatedTo ⇒ no relation
HubspotCreateEngagement.relatedTo = {type: "Company"} | {type: "Ticket"} | {type: "Deal"}   # omit ⇒ no relation
guestsBehavior = {type: "CreateEvents"} | {type: "DoNothing"}                   # default DoNothing
owner          = {type: "Assignee"} | {type: "Booker"}                          # default Assignee
meetingCancellationBehavior = {type: "DeleteEvent"} | {type: "DoNothing"}       # default DoNothing
form[]        = {dataField*, label*, required*, description?, hidden?}   # hidden = a PREFILLED value, not a flag
inAppButton[] = {dataField*}
routerLink[]  = {dataField*, label*, required?, hidden?}
branding      = {coverImage?, headingText?, language?}
```

**`waterfallId` is an opaque string** — resolve it from `enrichment-waterfall-list` (input `{workspaceId*, pagination?}`, defaults page 0 / pageSize 200; match by `name`, take `id`), **never invent it**: the write passes it through unvalidated, so a stale/wrong id only surfaces as a failure at publish time. Concierge supports the full `relatedTo` relation set above (Handoff rejects `ExplicitObject`/`RelationDisabled` — not this skill's concern).

> **ConvertLead is invisible in the Flow Builder (verified 2026-07-30, live tenant).** The API
> accepts and publishes `{type: "ConvertLead"}` — the node is real in the draft and published
> trees (ScheduledCondition → yes → CrmConvertLead) and fires post-booking — but the Concierge
> Flow Builder renders no node on the canvas and the SCHEDULED-branch ACTION menu has no
> Convert Lead option. Admins cannot see, edit, or remove it in the UI; inspect/remove only via
> `concierge-router-get`/`-update`. **Call it out to the admin explicitly whenever a write
> includes ConvertLead.** AddToCampaign UI rendering is not yet verified.

## Representability

Always `concierge-router-get` before an update. Since **DISTRO-4614** (edge #959, merged 2026-07-09) `routing.representable` selects the **write mode** for a rows-only routing update — with ONE exception since **CEH-11538**: a router whose `routingSteps` contain `Unrepresentable` reads `routing.representable: false`, and an update that **supplies `routingSteps`** on such a router is rejected **409 `RouterRoutingNotRepresentable`** (replacing the steps would silently destroy app-built enrichment/spam config). A rows-only routing edit on the same router still works and preserves the steps verbatim.

**`routing.representable: true` — full replace.** Your `routing` replaces the entire matrix: rows can be added, removed, and reordered; any row not in the payload is **deleted**. Supplied `routingSteps` full-replace the steps; omitted, the current (representable) steps are re-authored unchanged. Send the complete desired routing.

**`routing.representable: false` (app-built router) — opaque-preserve overlay.** Your `routing` is a **patch set**: rows are matched to existing rules by `ruleId` and patched in place on the dimensions this API models; unlisted rules — including rows with unrepresentable outcomes (`OwnerAssign`/`ContactOptions`/`CrmAction`) — and the pre-routing steps are preserved verbatim; unmatched `ruleId`s are appended. Supplying `routingSteps` here is the 409 case above — steps on a non-representable router are read-only. You **cannot remove or reorder existing rows** in overlay mode — that still needs the Concierge app; say so when the request implies it. Informed caution, not a hard stop: listing a `ruleId` whose outcome is unrepresentable converts it to the outcome you send — touch only rows the human asked to change and mark the rest "(preserved)".

**`known: false`** — Edge could not interpret the router at all: don't plan writes; direct the human to the UI.

**The `form` gate:** `form.representable: false` means the current webform is a third-party form — write it via `thirdPartyForm` instead of `form` (the old form-write 409 is retired since CEH-11363; the two are mutually exclusive and writing one kind converts the router). `branding`/`localizations` are always accepted; a name-only update always succeeds (but re-derives the slug).

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|---------------------------|
| `ConciergeRouterNotFound` | 404 | Bad routerId — re-resolve via `concierge-list-routers` |
| `RouterRoutingNotRepresentable` | 409 | **No longer returned for rows-only routing updates** since DISTRO-4614 (overlay path). Returned again since CEH-11538 when the update **supplies `routingSteps`** on a router whose steps contain `Unrepresentable` — drop `routingSteps` from the payload (rows-only edits preserve the steps) or edit the steps in the app. (The old `form` 409 on third-party webforms is retired since CEH-11363 — use `thirdPartyForm`) |
| invalid `dataField` | 400 | A `form`/trigger field references a data field that doesn't exist — use a standard default or a real UUID; create custom fields in the UI first (§ Data fields) |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key, or isn't a **team** workspace |
| `RouterPublishRejected` | 4xx | The publish step refused the config — surface the message; don't blind-retry |
| publish-failure `422` | 422 | Changes were **saved on an unpublished draft** — nothing went live; the draft must be fixed or deleted in the Concierge app. Report this state exactly |

> ⚠ **Draft side effect:** every update publishes the router's current **draft** — unpublished edits made in the Concierge app go live too, even on a name-only update. Mention this in the plan when the router is also being edited in the app.

## Permissions

Concierge read/create/modify/remove scopes on the API key. A 403 names the missing scope — fix in Admin Center → API Keys.

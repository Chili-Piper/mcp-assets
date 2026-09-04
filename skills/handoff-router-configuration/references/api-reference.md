# API reference — handoff-router-configuration

Field names verified against the live public Edge API spec, 2026-07-15 (v1.287.2). The tools' own text descriptions are unreliable — treat this file as the truth for this skill. In particular, the spec's `handoff-router-update` description still warns of a 409 representability rejection that DISTRO-4614 (edge #959, merged 2026-07-09) removed — see § Representability for the current behavior.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `handoff-router-list` | `GET /v1/org/handoff/routers/handoff/list` | All Handoff routers (optional `workspaceId` query filter) |
| `handoff-router-get` | `GET /v1/org/handoff/routers/handoff/{routerId}` | One router → `HandoffRouter` |
| `handoff-router-create` | `POST /v1/org/handoff/routers/handoff` | Create — **publishes live immediately** |
| `handoff-router-update` | `PUT /v1/org/handoff/routers/handoff/{routerId}` | Full-replace (representable router) or overlay patch (app-built router) — **live immediately** |
| `handoff-router-delete` | `DELETE /v1/org/handoff/routers/handoff/{routerId}` | Delete — irreversible |
| `rule-list` | — | Rules for rows: filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — no `routerId` |
| `distribution-list-put` | — | Distributions → `{results: [...], total, page, pageSize}` — iterate `results` (CEH-11548); name = `published.name`, ID = `id` |
| `meeting-type-list` | — | Resolve meeting type names → IDs for Schedule outcomes |
| `user-find` | — | Resolve user names/emails → IDs for User assignments |

## HandoffRouter (read shape)

`{id, workspaceId, name?, routing}` — **no `status` field exists**; Handoff routers are always live. `routing` is a summary:

```
routing: {
  known: boolean,          # false → Edge could not interpret this router
  representable: boolean,  # false → too complex for this API's simplified model
  rows: [{ruleId?, ruleType?, outcome}],
  catchAll: {outcome}
}
```

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?, crmActions?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions {meeting?, callSuccess?, callMissed?}` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule` exist only on read — they summarize UI configurations this API cannot write. `Schedule.crmActions` is the **complete** post-booking chain (CEH-11588/11589): an unmodellable node reads as an `Other {kind}` placeholder instead of collapsing the whole array to `null`; `representable` is `false` iff a placeholder was emitted. `ContactOptions` carries per-branch CRM-action chains since CEH-11599 (`meeting`/`callSuccess`/`callMissed`, each an ordered list of the same union incl. `Other`; `null` = branch absent, `[]` = present with no actions) — the variant is kept for accuracy, but Handoff routers never actually produce it (it is a Concierge call-flow node); it stays read-only. Since DISTRO-4614 they no longer block updates: an update on such a router is applied as an **overlay** (rows matched by `ruleId`), and a row whose outcome is an unrepresentable variant is **preserved verbatim as long as your payload doesn't list its `ruleId`** (see § Representability).

## Write shapes

`handoff-router-create`: `{workspaceId*, name*, routing*}` · `handoff-router-update`: `{name?, routing?}` — omitting `routing` keeps the current routing (a name-only update is safe).

```
routing: {
  routes: [{ruleId*, outcome*}],       # evaluated in order; ruleId required on every row
  catchAll?: outcome                   # optional on create AND update (CEH-11358); omit on update to preserve
}
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, crmActions?}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
crmActions = [{type: "ConvertLead"}
           | {type: "AddToCampaign", campaignId*, memberStatus*}
           | {type: "SalesforceUpdateFields", contact: [{object, field, value}], lead: [{field, value}]}
           | {type: "HubspotUpdateFields", contact: [{object, field, value}]}
           | {type: "SalesforceUpdateOwnership", contact: [{object, field}], lead: [{field}]}
           | {type: "HubspotUpdateOwnership", contact: [{object, field}]}
           | {type: "SalesforceCreateEvent", relatedTo?, meetingCancellationBehavior?, guestsBehavior?}
           | {type: "HubspotCreateEngagement", relatedTo?, owner?, meetingCancellationBehavior?}]
           # {type: "Other", kind} is READ-only (unmodellable-node placeholder) — rejected on write
SalesforceCreateEvent.relatedTo = {type: "Account"} | {type: "Opportunity"} | {type: "Case"}
           | {type: "Campaign", campaignId} | {type: "NoRelationNeeded"}       # omit ⇒ no relation
           # Handoff REJECTS {type: "ExplicitObject", id} and {type: "RelationDisabled"} (typed 400)
HubspotCreateEngagement.relatedTo = {type: "Company"} | {type: "Ticket"} | {type: "Deal"}  # omit ⇒ no relation
guestsBehavior = {type: "CreateEvents"} | {type: "DoNothing"}                  # default DoNothing
owner          = {type: "Assignee"} | {type: "Booker"}                         # default Assignee
meetingCancellationBehavior = {type: "DeleteEvent"} | {type: "DoNothing"}      # default DoNothing
```

> **Handoff writes are Schedule-only.** No `Redirect` and no no-show `timeout`. The Handoff CRM-action write set is: `ConvertLead`, `AddToCampaign` (CEH-11141), `SalesforceUpdateFields`/`HubspotUpdateFields` and `SalesforceUpdateOwnership`/`HubspotUpdateOwnership` (CEH-11302/CEH-11303), and `SalesforceCreateEvent`/`HubspotCreateEngagement` (CEH-11588/11589, 2026-09-03) — any combination in one array. Still **NO `Notify` and NO `SalesforceUpsertRecord`/`HubspotUpsertRecord`** — those are structurally absent from the Handoff write schema (Concierge-only) and fail decoding (400). A `SalesforceCreateEvent.relatedTo` of `ExplicitObject` or `RelationDisabled` is rejected with a typed 400 (`HandoffRouterConversionError`) — Handoff's backend cannot store those relations. The full outcome set (Redirect/timeout/Notify/Upsert) is concierge-only.

> **UI visibility caveat (2026-07-30):** on Concierge routers, an API-written `ConvertLead` was verified to publish and fire but NOT render in the Concierge Flow Builder (no node on the canvas, no Convert Lead in the SCHEDULED-branch ACTION menu — inspect/remove only via the API). Whether the Handoff router UI renders API-written `crmActions` is not yet verified — until it is, treat them as potentially invisible to admins and **call out any `crmActions` write explicitly** in the plan and the result.

## Representability

The read view is lossy for routers built with complex chains in the UI. Since **DISTRO-4614** (edge #959, merged 2026-07-09) `routing.representable: false` no longer rejects an update — it selects **which write mode** the API applies. Always `handoff-router-get` first; then plan by mode:

**`representable: true` — full replace.** Your payload replaces the entire matrix: rows can be added, removed, and reordered; any row not in the payload is **deleted**. Send the complete desired routing.

**`representable: false` (app-built router) — opaque-preserve overlay.** Your payload is a **patch set**, not the full matrix:

- rows are matched to existing rules **by `ruleId`**; a matched row's outcome is patched in place on the dimensions this API models (assignment, meeting type, CRM chain) — its app-only fields (`meetingHost`, `bookerInviteSettings`, `additionalAttendees`, …) are preserved;
- existing rules **not** in your payload — including rows whose read outcome is an unrepresentable variant (`OwnerAssign`/`ContactOptions`/`CrmAction`) — and structural nodes (enrichment/spam-check) are preserved verbatim;
- a payload row whose `ruleId` matches nothing is **appended** as a new rule;
- consequently, in overlay mode you **cannot remove or reorder existing rows** — that still needs the Handoff app. Say so in the plan when the request implies removal/reordering.

**Informed caution, not a hard stop:** listing a `ruleId` whose current outcome is an unrepresentable variant converts that row's outcome to the `Schedule` you send. Only include rows the human explicitly wants changed; the dry-run plan must mark every untouched row "(preserved)".

`known: false` still means Edge could not interpret the router at all — don't plan writes against it; direct the human to the UI.

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `HandoffRouterConversionError` | 400 | Payload didn't convert — surface the message verbatim, fix the plan |
| `RouterRoutingNotRepresentable` | 409 | **No longer returned by `handoff-router-update`** since DISTRO-4614 (unrepresentable routers take the overlay path). If it ever appears, treat it as abort → UI. Note: the live spec's operation description still carries the pre-4614 409 warning — the description text lags the deployed behavior |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterPublishRejected` | 4xx | The publish step refused the config — surface the message; nothing to retry blindly |
| publish-failure `422` | 422 | The changes were **saved on an unpublished draft** — nothing went live; the draft must be fixed or deleted in the Handoff app. Report this state exactly |

> ⚠ **Draft side effect:** every update publishes the router's current **draft** — if the draft carries unpublished edits made in the Handoff app, those go live too, even on a name-only update. Mention this in the plan when the router is also being edited in the app.

## Permissions

`handoff.read` (list/get), `handoff.create`, `handoff.modify`, `handoff.remove`. A 403 names the missing scope — fix in Admin Center → API Keys.

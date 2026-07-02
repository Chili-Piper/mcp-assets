# API reference — concierge-router-configuration

Field names verified against the live public Edge API spec, 2026-07-02. The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `concierge-list-routers` | `POST /v1/org/concierge/routers/concierge/list` | All Concierge routers → `{routers: [...]}` (same tool routing-audit/concierge-debugger use) |
| `concierge-router-get` | `GET /v1/org/concierge/routers/concierge/{routerId}` | One router → `ConciergeRouter` |
| `concierge-router-create` | `POST /v1/org/concierge/routers/concierge` | Create — **publishes live immediately** |
| `concierge-router-update` | `PUT /v1/org/concierge/routers/concierge/{routerId}` | Full-replace routing — **live immediately** |
| `concierge-router-delete` | `DELETE /v1/org/concierge/routers/concierge/{routerId}` | Delete — irreversible; the router's public form URL stops working |
| `rule-list` | — | Rules for rows: filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — no `routerId` |
| `distribution-list-put` | — | Distributions → **top-level array**; name = `published.name`, ID = `id` |
| `meeting-type-list` / `user-find` | — | Resolve meeting types / users for Schedule outcomes |

## ConciergeRouter (read shape)

`{id, workspaceId, name?, slug, routing, form, branding?, localizations?}` — **no `status` field**; Concierge routers are always live. `slug` is the router's public URL segment. `routing` is a summary:

```
routing: {
  known: boolean,          # false → Edge could not interpret this router
  representable: boolean,  # false → too complex for this API's simplified model
  rows: [{ruleId?, ruleType?, outcome}],
  catchAll: {outcome}
}
```

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule`/`Redirect` summarize UI configurations this API cannot write — rows using them cannot round-trip: treat like `representable: false`.

## Write shapes

`concierge-router-create`: `{workspaceId*, name*, routing*, form?, branding?, localizations?}` · `concierge-router-update`: `{name?, routing?, form?, branding?, localizations?}` — always send the **complete** `routing` on updates (full-replace).

```
routing: {routes: [{ruleId?, outcome*}], catchAll*}       # catchAll REQUIRED
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, timeout?, crmActions?}
               | {type: "Redirect", url*}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
timeout    = {minutes*, onTimeout*: {type: "Landing"} | {type: "Url", url}}
crmActions = [{type: "ConvertLead"} | {type: "Notify", slackChannel?}]
form[]     = {dataField*, label*, required*, description?, hidden?}
branding   = {coverImage?, headingText?, language?}
```

## Representability

Before any update: `concierge-router-get` → require `routing.representable === true` and `known === true`, and no row/catch-all outcome outside `Schedule`/`Redirect`. Otherwise **abort the update plan** — a full-replace write would destroy configuration the summary can't express (the API refuses with `RouterRoutingNotRepresentable`); direct the human to the Chili Piper UI. Complex multi-row `NextRule` chains built in the UI are the classic trigger.

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `ConciergeRouterNotFound` | 404 | Bad routerId — re-resolve via `concierge-list-routers` |
| `RouterRoutingNotRepresentable` | 400/409 | Router too complex for the simplified model — abort, edit in UI |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterPublishRejected` | 4xx | The publish step refused the config — surface the message; don't blind-retry |

## Permissions

Concierge read/create/modify/remove scopes on the API key. A 403 names the missing scope — fix in Admin Center → API Keys.

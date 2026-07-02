# API reference — handoff-router-configuration

Field names verified against the live public Edge API spec, 2026-07-02. The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `handoff-router-list` | `GET /v1/org/handoff/routers/handoff/list` | All Handoff routers (optional `workspaceId` query filter) |
| `handoff-router-get` | `GET /v1/org/handoff/routers/handoff/{routerId}` | One router → `HandoffRouter` |
| `handoff-router-create` | `POST /v1/org/handoff/routers/handoff` | Create — **publishes live immediately** |
| `handoff-router-update` | `PUT /v1/org/handoff/routers/handoff/{routerId}` | Full-replace — **live immediately** |
| `handoff-router-delete` | `DELETE /v1/org/handoff/routers/handoff/{routerId}` | Delete — irreversible |
| `rule-list` | — | Rules for rows: filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — no `routerId` |
| `distribution-list-put` | — | Distributions → **top-level array**; name = `published.name`, ID = `id` |
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

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule`/`Redirect` exist only on read — they summarize UI configurations this API cannot write. A router whose rows use them still reads fine, but converting such rows into a write payload is impossible: treat them like `representable: false` (see below).

## Write shapes

`handoff-router-create`: `{workspaceId*, name*, routing*}` · `handoff-router-update`: `{name?, routing?}` — send the **complete** routing every time (full-replace).

```
routing: {
  routes: [{ruleId?, outcome*}],       # evaluated in order
  catchAll*: {ruleId?, outcome*}       # REQUIRED
}
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, timeout?, crmActions?}
               | {type: "Redirect", url*}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
timeout    = {minutes*, onTimeout*: {type: "Landing"} | {type: "Url", url}}
crmActions = [{type: "ConvertLead"} | {type: "Notify", slackChannel?}]
```

## Representability

The read view is lossy for routers built with complex chains in the UI. Before any update:

1. `handoff-router-get` → require `routing.representable === true` and `known === true`.
2. If `false` — or any row/catch-all outcome is not `Schedule`/`Redirect` — **abort the update plan**: a full-replace write would destroy configuration the summary can't express. Direct the human to the Chili Piper UI.

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `HandoffRouterConversionError` | 400 | Payload didn't convert — surface the message verbatim, fix the plan |
| `RouterRoutingNotRepresentable` | 400/409 | Router too complex for the simplified model — abort, edit in UI |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterPublishRejected` | 4xx | The publish step refused the config — surface the message; nothing to retry blindly |

## Permissions

`handoff.read` (list/get), `handoff.create`, `handoff.modify`, `handoff.remove`. A 403 names the missing scope — fix in Admin Center → API Keys.

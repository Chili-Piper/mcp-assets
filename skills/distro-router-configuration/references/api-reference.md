# API reference — distro-router-configuration

Field names verified against the live public Edge API spec, 2026-07-30 (v1.311.1). The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `distro-list-routers` | `POST /v1/org/distro/routers/list` | All Distro routers → `{routers: [{id, name, status, trigger}]}` |
| `distro-router-get` | `GET /v1/org/distro/routers/{routerId}` | One router → `DistroRouterView` |
| `distro-router-create` | `POST /v1/org/distro/routers` | Create — router starts **Inactive** |
| `distro-router-update` | `PUT /v1/org/distro/routers/{routerId}` | **Overlay** of routing by `ruleId` (+ name/description PATCH); trigger & routingSteps replaced |
| `distro-router-delete` | `DELETE /v1/org/distro/routers/{routerId}` | Delete — only valid from `Inactive` |
| `distro-router-activate` | `POST /v1/org/distro/routers/{routerId}/activate` | `Inactive → (Activating) → Active`; idempotent |
| `distro-router-deactivate` | `POST /v1/org/distro/routers/{routerId}/deactivate` | `Active → Deactivating → Inactive`; **async**; idempotent |
| `rule-list` | — | Rules for routing rows. Filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — do not pass `routerId` |
| `distribution-list-put` | — | Distributions → `{results: [...], total, page, pageSize}` — iterate `results` (CEH-11548); names in `published.name`, ID in `id` |

## DistroRouterView (get/create/update/activate/deactivate response)

`{id, workspaceId, name, description?, status, routing}` where `routing` is a **summary**:

```
routing: {
  known: boolean,          # false → Edge could not interpret this router at all
  representable: boolean,  # false → summary doesn't round-trip exactly (ADVISORY — updates still accepted)
  rows: [{ruleId?, outcome}],
  catchAll: outcome,       # outcome = {type: "Route", distributionId?, actions}
  routingSteps: [...]      #           | {type: "Unrepresentable", kind}
}
```

## Status (discriminated object, NOT a plain string)

`status: {type: "Active" | "Inactive" | "Activating" | "Deactivating" | "Error"}` — the `Error` variant carries a required `message`. Read `status.type`, and surface `status.message` when type is `Error`.

## Representability (advisory)

The read view is lossy for routers using app-only features (SLAs, matchers, non-round-robin distributions, app-only actions). Since spec v1.311 (DISTRO-4621), this **no longer blocks updates** — there is no not-representable rejection:

1. `routing.representable: false` means only that the summary doesn't round-trip exactly (some row, the catch-all, or a routing step is `Unrepresentable`). Updates are accepted either way.
2. The update **overlays** onto the current routing: a `ruleId`-matched row gets only its distribution + actions swapped; its app-only config (SLAs, matchers, campaign addition, lead-to-contact conversion, send-to-routers, duplicate-matching) is preserved. → `references/routing-model.md` § Updates are an overlay.
3. Rows/catch-all with `outcome.type: "Unrepresentable", kind` are the spots the summary couldn't express — the `kind` names the app-only feature. They can still be edited safely; say so in the plan and note what the overlay preserves.
4. `known: false` still means Edge couldn't interpret the router at all — read it in the UI before planning anything.

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `RouterRoutingRequired` | 400 | Update sent without the `routing` object — always send it (it addresses the rows to overlay, matched by `ruleId`) |
| ~~`RouterRoutingNotRepresentable`~~ | — | **Retired** (spec v1.311, DISTRO-4621): the opaque-preserve overlay from DISTRO-4614 (edge #959) now covers Distro too — any router can be edited; there is no not-representable rejection |
| `DistroRouterConversionError` | 400 | Payload didn't convert — surface the message verbatim, fix the plan |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterDeleteRejected` | 409 | Delete attempted while not `Inactive` — deactivate first, poll, retry |
| `RouterCreationFailed` | 422 | Create is all-or-nothing: the partial router was rolled back — fix the cause and retry; nothing is left behind |
| *(update failure)* | 422 | **Update is NOT rolled back** (unlike create). Publish failed → changes saved on an unpublished draft, prior config stays live. Re-activation failed → new config published but router left `Inactive`. Either way: surface the typed 422 message and direct the human to fix/activate in the Distro app |

> The spec lists an optional `force` query param on **deactivate only** (it forces past a stale router revision; delete no longer takes one — removed from the spec by 2026-07-15). **Never use it** — the safe path is always deactivate → poll until `Inactive` → delete.

## Permissions

`distro.read` (reads), `distro.create`, `distro.modify` (update + activate/deactivate), `distro.remove` (delete). A 403 names the missing scope — fix in Admin Center → API Keys.

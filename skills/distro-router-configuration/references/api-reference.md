# API reference — distro-router-configuration

Field names verified against the live public Edge API spec, 2026-07-02. The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `distro-list-routers` | `POST /v1/org/distro/routers/list` | All Distro routers → `{routers: [{id, name, status, trigger}]}` |
| `distro-router-get` | `GET /v1/org/distro/routers/{routerId}` | One router → `DistroRouterView` |
| `distro-router-create` | `POST /v1/org/distro/routers` | Create — router starts **Inactive** |
| `distro-router-update` | `PUT /v1/org/distro/routers/{routerId}` | Full-replace of routing (+ name/description) |
| `distro-router-delete` | `DELETE /v1/org/distro/routers/{routerId}` | Delete — only valid from `Inactive` |
| `distro-router-activate` | `POST /v1/org/distro/routers/{routerId}/activate` | `Inactive → (Activating) → Active`; idempotent |
| `distro-router-deactivate` | `POST /v1/org/distro/routers/{routerId}/deactivate` | `Active → Deactivating → Inactive`; **async**; idempotent |
| `rule-list` | — | Rules for routing rows. Filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` — do not pass `routerId` |
| `distribution-list-put` | — | Distributions → **top-level array**; names in `published.name`, ID in `id` |

## DistroRouterView (get/create/update/activate/deactivate response)

`{id, workspaceId, name, description?, status, routing}` where `routing` is a **summary**:

```
routing: {
  known: boolean,          # false → Edge could not interpret this router at all
  representable: boolean,  # false → too complex for this API's simplified model
  rows: [{ruleId?, outcome}],
  catchAll: outcome,       # outcome = {type: "Route", distributionId, actions?}
  routingSteps: [...]      #           | {type: "Unrepresentable"}
}
```

## Status (discriminated object, NOT a plain string)

`status: {type: "Active" | "Inactive" | "Activating" | "Deactivating" | "Error"}` — the `Error` variant carries a required `message`. Read `status.type`, and surface `status.message` when type is `Error`.

## Representability

The read view is lossy for routers built with complex `NextRule` chains in the UI. Before any update:

1. `distro-router-get` → require `routing.representable === true` (and `known === true`).
2. If `false`: **abort the update plan** — a write would destroy configuration the summary can't express (the API refuses with `RouterRoutingNotRepresentable`). Tell the human to edit that router in the Chili Piper UI instead.
3. Rows/catch-all with `outcome.type: "Unrepresentable"` are the specific spots the summary couldn't express.

## Typed errors

| Error | HTTP | Meaning / skill behavior |
|-------|:---:|--------------------------|
| `RouterRoutingRequired` | 400 | Update sent without the full `routing` object — always send it (full-replace, no partial patch) |
| `RouterRoutingNotRepresentable` | 400/409 | Router too complex for the simplified model — abort, edit in UI. **Intentionally kept for Distro**: DISTRO-4614 (edge #959) replaced this guard with an opaque-preserve overlay for concierge/handoff, but explicitly deferred distro (DISTRO-4621 — no draft-read endpoint to overlay onto). Do not treat this gate as stale until DISTRO-4621 lands |
| `DistroRouterConversionError` | 400 | Payload didn't convert — surface the message verbatim, fix the plan |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this API/key |
| `RouterDeleteRejected` | 409 | Delete attempted while not `Inactive` — deactivate first, poll, retry |
| `RouterCreationFailed` | 422 | Create is all-or-nothing: the partial router was rolled back — fix the cause and retry; nothing is left behind |

> The spec lists an optional `force` query param on **deactivate only** (it forces past a stale router revision; delete no longer takes one — removed from the spec by 2026-07-15). **Never use it** — the safe path is always deactivate → poll until `Inactive` → delete.

## Permissions

`distro.read` (reads), `distro.create`, `distro.modify` (update + activate/deactivate), `distro.remove` (delete). A 403 names the missing scope — fix in Admin Center → API Keys.

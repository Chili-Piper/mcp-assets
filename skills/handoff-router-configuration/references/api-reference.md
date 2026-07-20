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

Read-view `outcome` variants: `Schedule {distributionId?, userId?, meetingTypeId?}` · `Redirect {url?}` · `OwnerAssign` · `ContactOptions` · `CrmAction` · `Other {kind}`. Variants beyond `Schedule` exist only on read — they summarize UI configurations this API cannot write. Since DISTRO-4614 they no longer block updates: an update on such a router is applied as an **overlay** (rows matched by `ruleId`), and a row whose outcome is an unrepresentable variant is **preserved verbatim as long as your payload doesn't list its `ruleId`** (see § Representability).

## Write shapes

`handoff-router-create`: `{workspaceId*, name*, routing*}` · `handoff-router-update`: `{name?, routing?}` — omitting `routing` keeps the current routing (a name-only update is safe).

```
routing: {
  routes: [{ruleId*, outcome*}],       # evaluated in order; ruleId required on every row
  catchAll*: outcome                   # REQUIRED
}
outcome (write) = {type: "Schedule", assignment*, meetingTypeId*, crmActions?}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
crmActions = [{type: "ConvertLead"}]
```

> **Handoff writes are Schedule-only.** No `Redirect`, no no-show `timeout`, and `ConvertLead` is the only CRM action — supplying any of those is **rejected (400)**; the full outcome set (Redirect/timeout/Notify) is concierge-only.

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

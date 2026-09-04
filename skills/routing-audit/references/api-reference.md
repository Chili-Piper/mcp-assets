# Routing Audit — API Reference

Full field names, response envelopes, hard limits, and known gotchas for the Chili
Piper MCP tools this skill uses.

> Field names are validated against **live MCP responses**. The MCP tools' own text
> descriptions are unreliable — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `workspace-list` | All workspaces → items `{id, name, nrOfUsers}`. The identifier is **`id`** (NOT `workspaceId`); pass `id` as the `workspaceId` argument to other tools. |
| `concierge-list-routers` | Routers in a workspace → `{routers: [{router: {id, name, slug, routing: {rules: [...], catchAll: {outcome: ...}}}, workspaceId}]}`. routerId is `routers[N].router.id`; rules and catch-all on `routers[N].router.routing`. Each rule row and the catch-all carry `outcome`: `{type: "Schedule", assignment: {type: "Distribution", distributionId} \| {type: "User", userId}, meetingTypeId, timeout?: {minutes, onTimeout: "Landing"\|{url}}, crmActions?: [...]}`, `{type: "Redirect", url}`, or a read-only variant — `OwnerAssign`, `ContactOptions {meeting?, callSuccess?, callMissed?}`, `CrmAction`, `Other {kind}` (see § Routing outcomes). |
| `rule-list` | Active routing rules, **workspace-scoped** (no routerId). Input `{filter: {ruleBuilderVersion: ["ExplicitV1"] (required), workspaceId?, name?, type?}, pagination}`. Returns `{results: [{id, name, type, conditions, workspaceId, metadata: {revision}}], total}`. `type` is `OwnershipRule` or `NonOwnershipRule`. |
| `concierge-logs` | Routing decisions → `status`, `matchedPath` (object), `guestEmail`, `triggeredAt`, `assignments`, `meetingId`. `matchedPath.route.type` is `RuleRoute` or `CatchAllRoute`. 30-day max window; requires `workspaceId` + `routerId`. |
| `distribution-list-put` | Distributions — `{results: [{id, published: {distributionId, name, weights: [{userId, weight}], assignmentTypeConfig: {type, handling: {type}}, capping, teamRef: {id}}, state: {userStates: [{userId, type: "Active"\|"Capped"\|"Disabled"\|"Removed"\|"NoLicense", statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}}]}}, ...], total, page, pageSize}`. Iterate `results` to reach individual records. Input takes `workspaceIds` (array) + optional `name`, `assignmentType` filters. (CEH-11548, 2026-09-01) |

---

## Critical field name differences

- **Workspace identifier is `id`, not `workspaceId`.** `workspace-list` items expose
  `id`; pass that value as the `workspaceId` argument to every other tool.
- **routerId lives at `routers[N].router.id`** — the response nests the router object
  one level down under `router`, with `workspaceId` as a sibling of `router`.
- **A router's rules and catch-all come from the router object itself**
  (`routers[N].router.routing.rules[]` and `routers[N].router.routing.catchAll`) — NOT
  from `rule-list`. `rule-list` is workspace-scoped (it takes no routerId) and is only
  for richer rule detail (conditions, type, revision).
- **`rule-list` requires `filter.ruleBuilderVersion: ["ExplicitV1"]`** — omitting it
  returns nothing useful.
- **`distribution-list-put` returns `{results: [...], total, page, pageSize}`** — iterate
  `results` to reach individual distribution records; takes `workspaceIds` (an array). (CEH-11548)

## concierge-list-routers — router object shape

`{routers: [{router: {id, name, slug, routing: {rules, catchAll}}, workspaceId}]}`.

For each router store: `routers[N].router.id` (routerId), `routers[N].router.name`,
`routers[N].router.slug`, `routers[N].workspaceId`, and the routing config at
`routers[N].router.routing`. The catch-all (`routing.catchAll`) is a **separate object,
not a rule** in `routing.rules[]`.

**Routing outcomes (DISTRO-4549, 2026-06-18):** each `routing.rules[]` entry and the
catch-all carry a discriminated `outcome` field:

- `{type: "Schedule", assignment: {type: "Distribution", distributionId} | {type: "User", userId}, meetingTypeId, timeout?: {minutes, onTimeout: "Landing"|{url}}, crmActions?: [...]}`
  — assign to a distribution or user and book a meeting type. `crmActions` is the
  **complete** post-booking chain (CEH-11590/11591, 2026-09-03): an unmodellable node
  appears as an `{type: "Other", kind}` placeholder instead of collapsing the whole array
  to `null`; a placeholder also means the router reads `representable: false`.
- `{type: "Redirect", url}` — send the lead to a URL instead of booking.

Routers built in the app can additionally carry read-only variants this API cannot write
(report them, don't flag them as errors):

- `{type: "OwnerAssign"}` — assign to the CRM record/contact owner.
- `{type: "ContactOptions", meeting?, callSuccess?, callMissed?}` — a call-flow node;
  since CEH-11599 (2026-09-04) each branch is an ordered CRM-action chain (same union
  incl. `Other`): `meeting` = the direct book-a-meeting branch, `callSuccess` /
  `callMissed` = the call branches. `null` = branch absent, `[]` = present with no
  actions. Audit the chains; the variant itself stays unwritable.
- `{type: "CrmAction"}` — a CRM action used as the row outcome.
- `{type: "Other", kind}` — any other backend node, named by `kind`.

Any Schedule/Redirect outcome is a valid catch-all: leads are handled either way. Only a
catch-all that is absent or has a null/missing `outcome` drops leads.

## rule-list — rule detail fields

Each `results[]` item carries:

- **Type:** `OwnershipRule` (routes by CRM owner) or `NonOwnershipRule`
  (territory/segment/round-robin)
- **Conditions:** what fields/values trigger this rule (`conditions`)
- **Revision:** `metadata.revision`
- **Workspace:** `workspaceId`

Call shape:

```yaml
tool: rule-list
args:
  filter:
    ruleBuilderVersion: ["ExplicitV1"]   # required
    workspaceId: <workspace.id>
  pagination:
    page: 0
    pageSize: 200
```

## concierge-logs — decision fields

- `status`, `matchedPath` (object), `guestEmail`, `triggeredAt`, `assignments`,
  `meetingId`
- `matchedPath.route.type` is `RuleRoute` or `CatchAllRoute`
- Matched rule ids are in `matchedPath.route.ruleIds` (for `RuleRoute`)
- Other route types appear in live data (e.g. `SpamCheckRoute`) — count anything that is
  not `RuleRoute` as "no rule matched", and surface a notable non-catch-all type (like
  spam filtering) separately rather than treating it as an error.

## distribution-list-put — balance fields

- **Active members:** `state.userStates[]` filtered to `type == "Active"`
- **Weights:** `published.weights[]` (each `{userId, weight}`) — a member with weight 0
  is effectively excluded
- **Algorithm / handling:** `published.assignmentTypeConfig.handling.type` (`Strict` or
  `Flexible`); the assignment scope is `published.assignmentTypeConfig.type`
- **Assignment statistics:** as of **DISTRO-4426 (2026-06-03)**, each `state.userStates[]`
  entry carries `statistics: {assigned, cancelled, noShow, reassignedToThis,
  reassignedFromThis}`. Use `statistics.assigned` alongside `weights` to detect actual
  vs. configured balance imbalances.

Call shape (optional `name` filter for a specific distribution; `assignmentType`
— `Record` | `Meeting` | `Conversation` — to narrow by type):

```yaml
tool: distribution-list-put
args:
  workspaceIds: [<workspace.id>]
```

---

## Hard API limits

- **`concierge-logs`: 30-day maximum window** per call, and it **requires both
  `workspaceId` and `routerId`**. Respect the `log_days` input (default 7, max 30).
- **`workspace-list` / `rule-list`: paginate** via `pagination.page` / `pagination.pageSize`.

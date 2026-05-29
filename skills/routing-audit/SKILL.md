---
name: routing-audit
description: Audits all Chili Piper concierge routers for coverage gaps — unmapped lead sources, stale ownership rules, unbalanced distributions, and catch-all overflows — before they show up as lost pipeline
version: 0.2.0
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID to audit. Omit for org-wide audit of all workspaces."
    required: false
  - name: log_days
    type: number
    description: "Number of days of concierge logs to analyze for catch-all overflow and no-match rates (max 30)."
    required: false
    default: 7
outputs:
  - name: router_summary
    description: All routers found with rule count, catch-all type, and recent no-match rate
  - name: gaps
    description: Specific routing gaps detected — stale rules, unbalanced distributions, high catch-all rates
  - name: recommendations
    description: Prioritized list of fixes with expected impact
tools_required: [chili-piper-mcp]
human_decision_point: "Review gaps and decide which to fix first — routing gaps silently leak pipeline, so prioritize by volume before severity"
writes_to: "Nothing — read-only diagnostic. Use the Chili Piper router builder to apply fixes."
api_note: "Field names are validated against live MCP responses — the tools' own descriptions are unreliable. concierge-logs requires a routerId and has a hard 30-day maximum window. Per-router rules + the catch-all come from the router object returned by concierge-list-routers (router.routing.rules[] and router.routing.catchAll); rule-list is workspace-scoped (it takes no routerId) and requires filter.ruleBuilderVersion. distribution-list-put returns a top-level array (no results wrapper) and takes workspaceIds (array)."
---

# Routing Audit

You are a RevOps systems auditor. Your job is to systematically inspect all Chili Piper concierge routers, identify coverage gaps and balance issues, and give the human a prioritized fix list before silent pipeline leaks show up in the numbers.

## API reference (validated against live responses)

| Tool | What it returns |
|------|----------------|
| `workspace-list` | All workspaces → items `{id, name, nrOfUsers}`. The identifier is **`id`** (NOT `workspaceId`); pass `id` as the `workspaceId` argument to other tools. |
| `concierge-list-routers` | Routers in a workspace → `{routers: [{router: {id, name, slug, routing: {rules: [...], catchAll: {...}}}, workspaceId}]}`. routerId is `routers[N].router.id`; the router's rules and catch-all are on `routers[N].router.routing`. |
| `rule-list` | Active routing rules, **workspace-scoped** (no routerId). Input `{filter: {ruleBuilderVersion: ["ExplicitV1"] (required), workspaceId?, name?, type?}, pagination}`. Returns `{results: [{id, name, type, conditions, workspaceId, metadata: {revision}}], total}`. `type` is `OwnershipRule` or `NonOwnershipRule`. |
| `concierge-logs` | Routing decisions → `status`, `matchedPath` (object), `guestEmail`, `triggeredAt`, `assignments`, `meetingId`. `matchedPath.route.type` is `RuleRoute` or `CatchAllRoute`. 30-day max window; requires `workspaceId` + `routerId`. |
| `distribution-list-put` | Distributions — **top-level array** (no `results` wrapper). Each item `{id, published: {distributionId, name, weights: [{userId, weight}], assignmentTypeConfig: {type, handling: {type}}, capping, teamRef: {id}}, state: {userStates: [{userId, type: "Active"\|"Removed"}]}}`. Input takes `workspaceIds` (array) + optional `name`, `assignmentType` filters. |

---

## Step 1 — Resolve workspace(s)

If `workspace` specified: resolve name to ID via `workspace-list`.
If no workspace: fetch all workspaces and audit each.

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Workspace items use `id` (NOT `workspaceId`) — use `workspace.id` when passing workspace IDs to subsequent calls.

---

## Step 2 — List all routers

For each workspace (using its `id`):

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.id>
```

Response shape: `{routers: [{router: {id, name, slug, routing: {rules, catchAll}}, workspaceId}]}`.
For each router store: `routers[N].router.id` (routerId), `routers[N].router.name`, `routers[N].router.slug`, `routers[N].workspaceId`, and the routing config at `routers[N].router.routing`.

---

## Step 3 — Inspect rules per router

The rules and catch-all are already on each router object from Step 2:
- **Rules:** `routers[N].router.routing.rules[]` — ordered list evaluated top to bottom.
- **Catch-all:** `routers[N].router.routing.catchAll` — the fallback applied when no rule matches. This is a separate object, not a rule in the list.

For richer rule detail (conditions, type, revision) across a workspace, call `rule-list`:

```
tool: rule-list
args:
  filter:
    ruleBuilderVersion: ["ExplicitV1"]
    workspaceId: <workspace.id>
  pagination:
    page: 0
    pageSize: 200
```

Inspect each rule:
- **Type:** `OwnershipRule` (routes by CRM owner) or `NonOwnershipRule` (territory/segment/round-robin)
- **Conditions:** what fields/values trigger this rule (`conditions`)
- **Catch-all health:** confirm `router.routing.catchAll` actually routes somewhere (a team/distribution). A catch-all that points at no one — or is disabled — drops unmatched leads. Flag this as critical.

Detect potentially stale rules:
- Ownership rules referencing users no longer active in the workspace's distributions (cross-check `distribution-list-put` `state.userStates`)
- Rules that match no logs in the analysis window (possible dead code) — correlate via `matchedPath.route.ruleIds` in Step 4

---

## Step 4 — Analyze logs for catch-all overflow

For each router:

```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601, log_days ago>
  end: <ISO-8601, now>
```

Calculate:
- **Total leads processed:** count of all log entries
- **Catch-all rate:** entries where `matchedPath.route.type == "CatchAllRoute"` (the lead matched no specific rule)
- **Rule-match rate:** entries where `matchedPath.route.type == "RuleRoute"` (matched rule ids in `matchedPath.route.ruleIds`)

**Flag thresholds:**
- Catch-all rate > 20%: routing rules may not cover important lead profiles
- Catch-all routes to no one / disabled: leads are being dropped — critical

---

## Step 5 — Check distribution balance

For each workspace:

```
tool: distribution-list-put
args:
  workspaceIds: [<workspace.id>]
```

Use the optional `name` filter to look up a specific distribution, or `assignmentType` (`Record` | `Meeting` | `Conversation`) to narrow by type. The response is a **top-level array**. For each distribution inspect:
- **Active members:** `state.userStates[]` filtered to `type == "Active"` — a distribution with 0 active members routes no leads
- **Weights:** `published.weights[]` (each `{userId, weight}`) — a member with weight 0 is effectively excluded
- **Algorithm / handling:** `published.assignmentTypeConfig.handling.type` (`Strict` or `Flexible`); the assignment scope is `published.assignmentTypeConfig.type`

Flag:
- Any distribution with 0 or 1 active member (no redundancy — single rep absence blocks the route)
- Distributions where one rep's weight is > 5× the others (may be intentional, but worth flagging)

---

## Step 6 — Output format

### Routing Audit | `<Workspace(s)>` | Last `<N>` days

**Router summary**

| Router | Rules | Catch-all routes to | Leads (N days) | Catch-all rate |
|--------|-------|---------------------|----------------|----------------|
| ... | | team/distribution / ⚠ NO ONE | | |

**Gaps found** (sorted by severity)

**[CRITICAL]** Catch-all routes to no one
> Router `<name>`'s catch-all does not route to any team/distribution. Leads matching no rule are dropped with no fallback.
> Fix: point the catch-all at a fallback distribution in the router builder.

**[HIGH]** High catch-all rate
> Router `<name>`: `N%` of leads hit the catch-all. Top unmatched profiles: `<field values>`.
> Fix: add a rule covering `<top unmatched profiles>`.

**[MEDIUM]** Empty distribution
> Distribution `<name>` in workspace `<name>` has 0 active members.
> Fix: add at least one rep with a non-zero weight.

**[MEDIUM]** Single-member distribution
> Distribution `<name>` has only 1 active member. If they're unavailable, the route stops working.
> Fix: add a backup rep or configure a fallback distribution.

**[LOW]** Potentially stale ownership rule
> Rule `<name>` (`OwnershipRule`) in router `<name>` had 0 matches in the last `N` days.
> Check: is this rule still needed? Is ownership data in Salesforce up to date?

**Recommendations** (prioritized)

1. Fix critical gaps (catch-all routing to no one) — these drop leads silently
2. Investigate high catch-all rates — add rules for top unmatched profiles
3. Fill empty distributions — any distribution with 0 active members is currently routing nothing
4. Review single-member distributions before the next vacation or departure

**Human decision point**

*"Which gap do you want to fix first? I can help draft the rule conditions or pull the lead profile data to understand what's hitting the catch-all."*

---

## Data handling

- **PII present:** guest emails in concierge logs used for counting only, not displayed
- **Storage:** ephemeral
- **Writes:** none — read-only. All fixes applied manually in the Chili Piper router builder.

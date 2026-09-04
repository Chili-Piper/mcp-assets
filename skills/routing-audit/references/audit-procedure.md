# Routing Audit — Detection Procedure

The full coverage-gap, stale-rule, catch-all-overflow, and distribution-balance
detection logic. Field names referenced here →
`references/api-reference.md`.

---

## Inspecting rules per router

The rules and catch-all are already on each router object from
`concierge-list-routers`:

- **Rules:** `routers[N].router.routing.rules[]` — ordered list evaluated top to bottom.
- **Catch-all:** `routers[N].router.routing.catchAll` — the fallback applied when no rule
  matches. This is a separate object, not a rule in the list.

For richer rule detail (conditions, type, revision) across a workspace, call `rule-list`
(call shape and fields → `references/api-reference.md` § rule-list — rule detail fields).

Inspect each rule:

- **Type:** `OwnershipRule` (routes by CRM owner) or `NonOwnershipRule`
  (territory/segment/round-robin)
- **Conditions:** what fields/values trigger this rule (`conditions`)
- **Catch-all health:** confirm `router.routing.catchAll` has a valid `outcome`. A
  `Schedule` outcome assigns to a distribution or user and books a meeting (valid); a
  `Redirect` outcome sends the lead to a URL — leads are not dropped (also valid). Flag as
  **critical** only when `routing.catchAll` is absent or its `outcome` field is
  null/missing. Surface a `Redirect` catch-all as **informational** — it may be intentional
  (low-intent leads sent to a content page) but worth confirming with the admin.

## Detecting stale rules

- Ownership rules referencing users no longer active in the workspace's distributions
  (cross-check `distribution-list-put` `state.userStates`)
- Rules that match no logs in the analysis window (possible dead code) — correlate via
  `matchedPath.route.ruleIds` from the logs analysis below

## Analyzing logs for catch-all overflow

For each router, pull `concierge-logs` over the `log_days` window (call shape and the
30-day limit → `references/api-reference.md` § concierge-logs — decision fields and
§ Hard API limits):

```yaml
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601, log_days ago>
  end: <ISO-8601, now>
```

Calculate:

- **Total leads processed:** count of all log entries
- **Catch-all rate:** entries where `matchedPath.route.type == "CatchAllRoute"` (the lead
  matched no specific rule)
- **Rule-match rate:** entries where `matchedPath.route.type == "RuleRoute"` (matched
  rule ids in `matchedPath.route.ruleIds`)
- Other route types appear in live data (e.g. `SpamCheckRoute`); count anything that is
  not `RuleRoute` as "no rule matched", and surface a notable non-catch-all type (like
  spam filtering) separately rather than treating it as an error.

**Flag thresholds:**

- Catch-all rate **> 20%**: routing rules may not cover important lead profiles
- Catch-all absent or no valid `outcome`: leads are being dropped — **critical**
- Catch-all with a `Redirect` outcome: leads sent to a URL, not booked — **informational**
  (confirm it's intentional)

## Checking distribution balance

For each workspace, pull `distribution-list-put` (response is `{results: [...], total,
page, pageSize}` — iterate `results`, CEH-11548; balance
fields → `references/api-reference.md` § distribution-list-put — balance fields):

```yaml
tool: distribution-list-put
args:
  workspaceIds: [<workspace.id>]
```

Use the optional `name` filter to look up a specific distribution, or `assignmentType`
(`Record` | `Meeting` | `Conversation`) to narrow by type. For each distribution inspect:

- **Active members:** `state.userStates[]` filtered to `type == "Active"` — a distribution
  with 0 active members routes no leads
- **Weights:** `published.weights[]` (each `{userId, weight}`) — a member with weight 0 is
  effectively excluded
- **Algorithm / handling:** `published.assignmentTypeConfig.handling.type` (`Strict` or
  `Flexible`); the assignment scope is `published.assignmentTypeConfig.type`
- **Assignment balance:** each `state.userStates[]` entry carries `statistics.assigned`.
  Derive `idealNumber = (weight / totalWeight) × totalAssigned` where
  `totalAssigned = sum of all members' statistics.assigned`. Compare each member's actual
  `assigned / totalAssigned` share to their `weight / totalWeight` share to detect real
  imbalance (as opposed to weight-only inspection).

**Flag:**

- Any distribution with 0 or 1 active member (no redundancy — single rep absence blocks
  the route)
- Distributions where one rep's weight is **> 5×** the others (may be intentional, but
  worth flagging)
- Distributions where one rep's actual `assigned` share deviates from their ideal share
  by **> 2×** (more actionable than weight alone — indicates capping, calendar outages,
  or reassignment churn)

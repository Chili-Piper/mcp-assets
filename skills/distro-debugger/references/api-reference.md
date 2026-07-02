# Distribution Debugger — API Reference

Full field names, status values, query limits, and known gotchas for the Chili Piper MCP
tools used by this skill.

> Field names and response envelopes are validated against **live MCP responses**. The
> MCP tools' own text descriptions are unreliable — use this file, not intuition or the
> tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `distro-log-get` | Full evaluation trace for one log entry → `status`, `record`, `assignee`, `stages[]`, `enrichment`, `assignmentDecision`, `triggeredAt`. Requires `logId` + `routerId`. |
| `distro-logs` | Paginated log list. Query: `workspaceId` (req), `page`, `pageSize`. Body: `search`, `status`, `distributionMethod`, `userIds`, `from`, `to` |
| `distro-list-routers` | Routers in a workspace → `id`, `workspaceId`, `name`, `status` per router. Use to resolve router names and check activation state before diagnosing. |
| `distribution-list-put` | Distributions in a workspace → `distributionId`, `name`, `assignees`, `capping` |
| `workspace-list` | All workspaces → `workspaceId`, `name` |
| `salesforce-query` | SOQL query to resolve a record name to a Salesforce ID |

### Call shapes

`distro-logs`: POST `/v1/org/distro/logs`. Query params: `workspaceId` (required),
`page` (default `0`), `pageSize` (default `10`). Body (send `{}` for no filter):
`userIds`, `status`, `distributionMethod`, `search` (text), `from` (ISO8601), `to`
(ISO8601). Use `distro-list-routers` to find `workspaceId` values; use
`distribution-list-put` to resolve router display names.

`distro-log-get`: requires `logId` + `routerId`. Returns full per-rule evaluation trace.

---

## Hard API limits

| Tool | Limit |
|------|-------|
| `distro-logs` | `page` default `0`, `pageSize` default `10`. `workspaceId` required — searches within one workspace at a time. |
| `distro-log-get` | Requires both `logId` and `routerId`; a missing log may be outside the retention window. |

---

## Router status values (`distro-list-routers`)

Each router returned by `distro-list-routers` carries a `status` field. Check this in
Step 3 before walking stages — an inactive router is the root cause of `NotTriggered`
outcomes.

| Status | Meaning |
|--------|---------|
| `Active` | Router is live and routing records normally |
| `Inactive` | Router is not routing — records will not be processed. **Root cause for `NotTriggered`.** Routers created via MCP/API default to Inactive and must be explicitly activated via `distro-router-activate`. |
| `Activating` | Activation in progress (async) — routing may be temporarily unavailable |
| `Deactivating` | Deactivation in progress (async) |
| `Error{message}` | Router is in a technical error state — escalate to engineering with the router ID and error message |

---

## Log status values (`distro-logs` and `distro-log-get`)

| Status | Meaning |
|--------|---------|
| `Finished` | Record completed routing successfully and was assigned |
| `SlaFinished` | Record completed routing after an SLA timer expired |
| `NotTriggered` | The router flow did not fire for this record |
| `NotMatchedEntryRule` | Record entered the router but matched no entry rule — dropped or hit catch-all |
| `NotRouted` | Record was processed but no assignment was made |
| `DelayInProgress` | Record is paused at a delay step — not yet complete |
| `WorkingHours` | Record is held pending working hours — not yet complete |
| `SlaInProgress` | Record is within an active SLA window — not yet complete |
| `Error` | Technical error during evaluation — requires engineering investigation |

---

## distributionMethod values (how the assignee was selected)

| Value | Meaning |
|-------|---------|
| `RoundRobinEvaluationSuccess` | Normal round-robin assignment |
| `EvaluatedFromRoundRobinArs` | Round-robin with account routing strategy |
| `FromOwnershipArs` | Assigned to the record's CRM owner |
| `DuplicateMatchOwner` | Assigned to owner of a matching duplicate record |
| `FallbackTeam` | No primary match; fell back to the team fallback |
| `FallbackUser` | No primary match; fell back to a specific fallback user |
| `NoDistribution` | No distribution was configured for the matched rule |
| `NoUserAvailable` | All eligible reps were at capacity or unavailable |
| `ClientError` | Assignment failed due to a client-side error |

---

## Evaluation trace fields (`distro-log-get`)

Extract from the response:

- `status` — lifecycle outcome
- `distributionMethod` — how the assignee was selected
- `record` — the CRM record and its field values
- `assignee` — who was assigned (if anyone)
- `triggeredAt` — when routing fired
- `stages[]` — ordered rule evaluations
- `enrichment` — field enrichment that ran before rule evaluation
- `assignmentDecision` — round-robin position, weight, or fallback reason

Each stage in `stages[]` carries `matched` (bool) and `conditions[]`; each condition
carries `passed` (bool), `field`, `operator`, `expected`, and `actual`.

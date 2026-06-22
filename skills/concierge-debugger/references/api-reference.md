# Concierge Debugger — API Reference

Full field names, status values, and known gotchas for the Chili Piper MCP tools used by this skill.

> Field names and response envelopes are validated against **live MCP responses**. The MCP tools' own text descriptions are unreliable — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `concierge-list-routers` | `{routers: [{router: {id, name, slug, routing: {rules, catchAll}}, workspaceId}]}` — routerId is `routers[N].router.id`, slug `routers[N].router.slug`, workspace `routers[N].workspaceId` |
| `concierge-logs` | Routing decisions → `status`, `guestEmail`, `trigger`, `matchedPath` (object), `assignments` (`[{userId, ruleId, teamRef, distributionId, type}]` — no `name`), `meetingId`, `sourceUrl`, `crmUrl`, `triggeredAt`, `actionsStatus` |
| `rule-list` | Active rules, **workspace-scoped** (no routerId). Input `{filter: {ruleBuilderVersion: ["ExplicitV1"] (required), workspaceId?, name?}, pagination}`. Returns `{results: [{id, name, type, conditions, metadata}]}`; `type` is `OwnershipRule` or `NonOwnershipRule`. |
| `workspace-list` | Workspaces → items `{id, name, nrOfUsers}` (identifier is **`id`**, not `workspaceId`) |
| `user-find-by-ids` | Resolves a `userId` to a name (used to name an assignee) |

---

## Hard API limits

| Tool | Limit |
|------|-------|
| `concierge-logs` | **30-day maximum window** per call, and requires a `routerId`. If the router is unknown, loop over all routers. Sessions older than 30 days are unavailable. |

---

## Reading the outcome (no fixed status enum — interpret these signals)

There is no documented, fixed set of `status` values. Read the actual status and interpret from context rather than assuming an enum.

- **Booked:** a `meetingId` is present and `status` indicates success (observed value: `Scheduled`). The lead did book.
- **Not booked:** no `meetingId`. Use `status` (observed values include `TimedOut` = session expired, `Cancelled`) and `matchedPath.route.type` to explain why.

If you see a `status` value not listed here, report the literal value and interpret it from the surrounding fields rather than guessing.

---

## matchedPath (which route fired)

`matchedPath` is an **object**, not a string: `matchedPath.route.type = RuleRoute | CatchAllRoute`.

- `matchedPath.route.type == "RuleRoute"` → a rule matched; the rule id(s) are in `matchedPath.route.ruleIds`.
- `matchedPath.route.type == "CatchAllRoute"` → no specific rule matched; the lead fell to the catch-all.
- Other values appear in live data (e.g. `SpamCheckRoute`); treat any type other than `RuleRoute` as "no rep rule matched" and report the literal type.
- `matchedPath.type` also varies — `RoutePathLive` / `RoutePathWithCalendar` / `RoutePathWithoutCalendar`.

---

## assignments and actionsStatus

- `assignments[]` items carry `userId` (no `name`) — resolve to a name via `user-find-by-ids`.
- `actionsStatus`: if it is a non-success state, a CRM write-back failed — escalate to RevOps.

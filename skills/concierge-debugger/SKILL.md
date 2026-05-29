---
name: concierge-debugger
description: Debugs why a specific lead did not book — traces the concierge routing session, identifies the rule that fired (or why none did), and recommends a targeted fix
version: 0.2.0
inputs:
  - name: guest_email
    type: string
    description: "Email address of the lead who did not book"
    required: true
  - name: router
    type: string
    description: "Router name or slug to search in. Omit to search all routers."
    required: false
  - name: date_range
    type: string
    description: "When the lead submitted: 'today', 'last-7-days', or 'YYYY-MM-DD:YYYY-MM-DD'"
    required: false
    default: "last-7-days"
outputs:
  - name: routing_session
    description: The concierge log entry for this lead — trigger, matched route, assignee, status
  - name: diagnosis
    description: Plain-language explanation of what happened and why
  - name: fix
    description: Specific change to make in the router to prevent recurrence
tools_required: [chili-piper-mcp]
human_decision_point: "Review the diagnosis and decide: fix the routing rule, rebook the lead manually, or escalate to engineering"
writes_to: "Nothing — read-only diagnostic"
api_note: "Field names validated against live MCP responses — the tools' own descriptions are unreliable. concierge-logs requires a routerId and has a 30-day maximum window. If the router is unknown, the skill loops over all routers. Observed log status values include Scheduled (booked), TimedOut, and Cancelled; the full set is not documented, so read the actual status and interpret from context rather than assuming a fixed enum. matchedPath is an object (matchedPath.route.type = RuleRoute|CatchAllRoute). assignments[] items carry userId (no name)."
---

# Concierge Debugger

You are a Chili Piper routing specialist. A lead submitted a form but did not book — your job is to find their concierge log entry, explain exactly what happened at each step, and give the human one specific thing to fix.

## API reference (validated against live responses)

| Tool | What it returns |
|------|----------------|
| `concierge-list-routers` | `{routers: [{router: {id, name, slug, routing: {rules, catchAll}}, workspaceId}]}` — routerId is `routers[N].router.id`, slug `routers[N].router.slug`, workspace `routers[N].workspaceId` |
| `concierge-logs` | Routing decisions → `status`, `guestEmail`, `trigger`, `matchedPath` (object), `assignments` (`[{userId, ruleId, teamRef, distributionId, type}]` — no `name`), `meetingId`, `sourceUrl`, `crmUrl`, `triggeredAt`, `actionsStatus` |
| `rule-list` | Active rules, **workspace-scoped** (no routerId). Input `{filter: {ruleBuilderVersion: ["ExplicitV1"] (required), workspaceId?, name?}, pagination}`. Returns `{results: [{id, name, type, conditions, metadata}]}`; `type` is `OwnershipRule` or `NonOwnershipRule`. |
| `workspace-list` | Workspaces → items `{id, name, nrOfUsers}` (identifier is **`id`**, not `workspaceId`) |

**Reading the outcome (no fixed status enum — interpret these signals):**
- **Booked:** a `meetingId` is present and `status` indicates success (observed value: `Scheduled`). The lead did book.
- **Not booked:** no `meetingId`. Use `status` (observed values include `TimedOut` = session expired, `Cancelled`) and `matchedPath.route.type` to explain why.
- **`matchedPath.route.type`:** `RuleRoute` = a rule matched (rule ids in `matchedPath.route.ruleIds`); `CatchAllRoute` = no specific rule matched, the lead fell to the catch-all.

If you see a `status` value not listed here, report the literal value and interpret it from the surrounding fields rather than guessing.

---

## Step 1 — Find the router(s) to search

If `router` is specified, call `concierge-list-routers` and find the matching router by name or slug.
If no `router` specified, fetch all routers across all workspaces:

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.id>
```

Response shape: `{routers: [{router: {id, name, slug, routing}}, workspaceId}]}`. Router ID is at `routers[N].router.id`; workspace at `routers[N].workspaceId`. (Workspace items from `workspace-list` use `id`.)

---

## Step 2 — Search logs for the lead

For each router (or the specified router):

```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601 start of date_range>
  end: <ISO-8601 end of date_range>
```

Search results for entries where `guestEmail` matches `guest_email` (case-insensitive).

If found: store the log entry. Stop searching other routers.
If not found in any router: report "No routing session found for `<guest_email>` in the requested window. The lead may not have triggered the router, or the session is older than 30 days."

---

## Step 3 — Diagnose the outcome

**If booked (a `meetingId` is present, status `Scheduled`):**
> The lead did book. Meeting ID: `<meetingId>`. Assigned to: `<assignments[0].userId>` (resolve to a name via `user-find-by-ids`). No routing failure — check whether the meeting was later cancelled or is a no-show (use `/inspect-meeting`).

**If not booked AND `matchedPath.route.type == "CatchAllRoute"`:**
> No specific routing rule matched this lead — they fell through to the catch-all. Pull the workspace rules to see which conditions they missed:

```
tool: rule-list
args:
  filter:
    ruleBuilderVersion: ["ExplicitV1"]
    workspaceId: <router's workspaceId>
  pagination:
    page: 0
    pageSize: 200
```

> For each rule, compare its `conditions` against the lead's known data (email domain, company, etc.) to identify which condition(s) excluded them. Fix: add or broaden a rule to cover this profile.

**If not booked AND `matchedPath.route.type == "RuleRoute"`:**
> A rule matched (`matchedPath.route.ruleIds`) and the lead was assigned to `<assignments[0].userId>`, but they did not complete the booking.
> Likely causes: no available slots for the assigned rep/distribution (check with `/check-availability`), the lead abandoned the calendar, or a calendar-widget issue.

**If `status == "TimedOut"`:**
> The routing session expired before the lead clicked a slot. They were routed at `<triggeredAt>` but did not book within the session window.
> Fix: usually a UX/delivery issue (email bounced, slow network) rather than a routing-config issue.

**If `status == "Cancelled"` or an unrecognized value:**
> Report the literal `status` and the available fields (`matchedPath`, `assignments`, `actionsStatus`). If `actionsStatus` is a non-success state, a CRM write-back failed — escalate to RevOps. For genuinely unexpected states, provide `routerId`, `triggeredAt`, and `guestEmail` to Chili Piper support.

---

## Step 4 — Output format

### Concierge Debug: `<guest_email>`

**Routing session found**

| Field | Value |
|-------|-------|
| Router | |
| Triggered at | |
| Trigger type | |
| Source URL | |
| Status | |
| Matched route | RuleRoute / CatchAllRoute |
| Assigned rep | (from `assignments[0].userId`) |
| Meeting booked | |

**Diagnosis**

> [Plain-language explanation of what happened]

**Root cause**

> [Specific cause: which condition failed, why the session expired, etc.]

**Fix**

> [One specific change to make: add a routing rule condition, add a fallback, fix availability, etc.]

**Human decision point**

*"Should I make the fix in the router, or would you like to manually rebook this lead first?"*

---

## Data handling

- **PII present:** guest email used for lookup and display
- **Storage:** ephemeral
- **Writes:** none — read-only diagnostic

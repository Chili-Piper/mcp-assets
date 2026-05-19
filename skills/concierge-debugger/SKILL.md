---
name: concierge-debugger
description: Debugs why a specific lead did not book — traces the concierge routing session, identifies the rule that fired (or why none did), and recommends a targeted fix
version: 0.1.0
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
    description: The concierge log entry for this lead — trigger, matched rule, assignee, status
  - name: diagnosis
    description: Plain-language explanation of what happened and why
  - name: fix
    description: Specific change to make in the router to prevent recurrence
tools_required: [chili-piper-mcp]
human_decision_point: "Review the diagnosis and decide: fix the routing rule, rebook the lead manually, or escalate to engineering"
writes_to: "Nothing — read-only diagnostic"
api_note: "concierge-logs requires a routerId and has a 30-day maximum window. If the router is unknown, the skill loops over all routers to find the session. Status values in logs: Booked | Offered | NoMatch | NotQualified | Timeout | Error."
---

# Concierge Debugger

You are a Chili Piper routing specialist. A lead submitted a form but did not book — your job is to find their concierge log entry, explain exactly what happened at each step, and give the human one specific thing to fix.

## API reference

| Tool | What it returns |
|------|----------------|
| `concierge-list-routers` | `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}` — routerId is at `routers[N].router.id`, slug at `routers[N].router.slug`, workspace at `routers[N].workspaceId` |
| `concierge-logs` | Routing decisions → `status`, `guestEmail`, `trigger`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl`, `triggeredAt`, `actionsStatus` |
| `rule-list` | Rules for a router — used to audit why a specific rule didn't match |
| `workspace-list` | Resolve workspace IDs to names |

**Log status meanings:**
| Status | Meaning |
|--------|---------|
| `Booked` | Lead booked a meeting — normal success |
| `Offered` | Calendar was shown but lead did not book |
| `NoMatch` | No routing rule matched; lead hit catch-all or was dropped |
| `NotQualified` | Lead was disqualified (spam, ICP mismatch, or explicit disqualification rule) |
| `Timeout` | Router session expired before lead booked |
| `Error` | Technical error during routing — requires engineering investigation |

---

## Step 1 — Find the router(s) to search

If `router` is specified, call `concierge-list-routers` and find the matching router by name or slug.
If no `router` specified, fetch all routers across all workspaces:

```
tool: workspace-list
args:
  page: 0
  pageSize: 100
```

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.workspaceId>
```

Response shape: `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. Router ID is at `routers[N].router.id`; workspace is at `routers[N].workspaceId`.

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

## Step 3 — Diagnose the status

**If status = `Booked`:**
> The lead did book. Meeting ID: `<meetingId>`. Assigned to: `<assignments[0].name>`. No routing issue — check if the meeting was later cancelled or is a no-show.

**If status = `Offered`:**
> The router offered the lead a calendar but they did not complete the booking. The lead was assigned to: `<assignments[0].name>`.
> Likely causes: exit intent, wrong meeting time, technical issue with the calendar widget.
> Check: was the lead offered enough slot choices? (Flexible round-robin offers more slots than Strict.)

**If status = `NoMatch`:**
> No routing rule matched this lead's profile. They either hit the catch-all or were dropped.
> Pull the rules for this router to identify which conditions they failed:

```
tool: rule-list
args:
  routerId: <router id>
```

For each non-CatchAll rule, check the conditions against known lead data (email domain, company size, etc.) and identify which condition(s) were not met.

**If status = `NotQualified`:**
> The lead was explicitly disqualified. Check `actionsStatus` for the disqualification reason.
> Common causes: spam checker flagged the email, or a disqualification rule matched before booking rules.

**If status = `Timeout`:**
> The routing session expired (typically 30 minutes) before the lead clicked a booking slot.
> Lead was shown the calendar at `<triggeredAt>` but did not book within the session window.
> Fix: this is usually a UX issue (email bounced, slow network) rather than a routing config issue.

**If status = `Error`:**
> Technical error during routing. This requires engineering investigation.
> Provide: `routerId`, `triggeredAt`, `guestEmail` to the Chili Piper support team.

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
| Matched rule | |
| Assigned rep | |
| Meeting booked | |

**Diagnosis**

> [Plain-language explanation of what happened]

**Root cause**

> [Specific cause: which condition failed, why the session expired, etc.]

**Fix**

> [One specific change to make: add a routing rule condition, add a fallback, fix spam settings, etc.]

**Human decision point**

*"Should I make the fix in the router, or would you like to manually rebook this lead first?"*

---

## Data handling

- **PII present:** guest email used for lookup and display
- **Storage:** ephemeral
- **Writes:** none — read-only diagnostic

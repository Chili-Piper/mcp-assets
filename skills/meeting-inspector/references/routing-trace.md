# Meeting Inspector — Routing Trace

How to fetch and interpret the routing trace for a meeting.

Skip this entire section if the meeting's `createdAt` is more than 30 days ago — note "Routing trace unavailable (>30 days)" in the output.

---

## Step 3a — List routers

```
tool: concierge-list-routers
args:
  workspaceId: <resolved workspace ID, or omit for all>
```

Store each router's `id`, `name`, `slug`, `workspaceId`.

---

## Step 3b — Fetch logs per router

For each router, fetch routing logs around the meeting's booking timestamp:

```
tool: concierge-logs
args:
  workspaceId: <router's workspaceId>
  routerId: <router id>
  start: <ISO-8601 — 1 day before meeting's createdAt>
  end: <ISO-8601 — 1 day after meeting's createdAt>
```

---

## Matching a log entry to the meeting

A log entry matches if either of these is true:
- `meetingId` equals the target meeting's ID
- `guestEmail` matches (case-insensitive) AND `triggeredAt` is within a few hours of `createdAt`

When a match is found, extract:

| Field | Meaning |
|-------|---------|
| `status` | Routing session outcome — expect `Booked` for a completed meeting |
| `trigger` | How the lead arrived (see trigger types in `api-reference.md`) |
| `matchedPath` | Routing rule that fired (e.g., `CrmOwnership`, `WithoutOwnership`, `CatchAll`) |
| `sourceUrl` | Page the lead came from |
| `assignments[0].name` | Rep the router assigned |
| `triggeredAt` | When the router ran |
| `actionsStatus` | CRM write-back result |

---

## Interpreting unexpected log statuses

If a log is found but status is not `Booked`:

| Log status | Interpretation |
|-----------|---------------|
| `Offered` | Lead was shown a calendar but did not complete booking. Meeting may have been created via another path (direct link, handoff). |
| `NoMatch` | No rule matched — meeting was routed through a different router or booked manually. |
| `NotQualified` | Lead was disqualified before seeing a calendar. Investigate ICP filters if a meeting still exists. |
| `Timeout` | Session expired. Meeting created after timeout via re-entry or manual booking. |
| `Error` | Technical error during routing — escalate to engineering. |

---

## When no routing log is found

Output: *"No routing log found for this meeting — it may have been booked via a direct scheduling link, manual booking, or handoff rather than a concierge router."*

This is not necessarily an error. Direct links and handoffs create meetings without a concierge-log entry.

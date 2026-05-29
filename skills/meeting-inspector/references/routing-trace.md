# Meeting Inspector — Routing Trace

How to fetch and interpret the routing trace for a meeting.

Skip this entire section if the meeting's `bookedAt` is more than 30 days ago — note "Routing trace unavailable (>30 days)" in the output.

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
  start: <ISO-8601 — 1 day before meeting's bookedAt>
  end: <ISO-8601 — 1 day after meeting's bookedAt>
```

---

## Matching a log entry to the meeting

A log entry matches if either of these is true:
- `meetingId` equals the target meeting's ID
- `guestEmail` matches (case-insensitive) AND `triggeredAt` is within a few hours of `bookedAt`

When a match is found, extract:

| Field | Meaning |
|-------|---------|
| `status` | Routing session outcome — expect `Scheduled` for a completed booking |
| `trigger` | How the lead arrived (see trigger types in `api-reference.md`) |
| `matchedPath.route.type` | Route kind: `RuleRoute` (a rule matched; ids in `matchedPath.route.ruleIds`) or `CatchAllRoute` (hit the catch-all) |
| `sourceUrl` | Page the lead came from |
| `assignments[0].userId` | Rep the router assigned (resolve to a name via `user-find-by-ids` if needed) |
| `triggeredAt` | When the router ran |
| `actionsStatus` | CRM write-back result |

---

## Interpreting unexpected log statuses

If a log is found but status is not `Scheduled`:

| Log status | Interpretation |
|-----------|---------------|
| `TimedOut` | Routing session expired before the lead booked. A meeting may still exist if created after timeout via re-entry or manual booking. |
| `Cancelled` | The routing session or resulting meeting was cancelled. |

These are the statuses observed against live routing logs. If you encounter another value, verify its meaning against a live log rather than assuming. To see *why* no rule matched, read `matchedPath.route.type` (a `CatchAllRoute` means the lead fell through to the catch-all).

---

## When no routing log is found

Output: *"No routing log found for this meeting — it may have been booked via a direct scheduling link, manual booking, or handoff rather than a concierge router."*

This is not necessarily an error. Direct links and handoffs create meetings without a concierge-log entry.

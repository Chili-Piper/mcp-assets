# Distribution Analysis — API Reference

Full field names, response envelopes, hard limits, and known gotchas for the Chili
Piper MCP tools this skill uses.

> Field names are validated against **live MCP responses**. The MCP tools' own text
> descriptions are often wrong — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `workspace-list` | Workspaces → items `{id, name, nrOfUsers}` (the identifier is `id`) |
| `distribution-list-put` | Distributions as a **top-level array**. Input `{workspaceIds: [...], name?, assignmentType?}`. Each item: `{id, published: {distributionId, name, weights: [{userId, weight}], assignmentTypeConfig: {type, handling: {type}}, capping, teamRef: {id}}, state: {userStates: [{userId, type: "Active"\|"Capped"\|"Disabled"\|"Removed"\|"NoLicense", statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}}]}}` |
| `user-find-by-ids` | Resolve member `userId`s → names/emails |
| `meeting-list-put` | Meetings in a ≤7-day window → `data.list[]` with `meetingId`, `hostId`/`hostName`, `meetingStatus`, `dateTime.start`, `scheduleOrigin`, `meetingSource`, `noShowStatus`, `history`. Envelope `{data: {list}, hasMore}`; paginate while `hasMore === "Yes"`. |

---

## distribution-list-put — config fields

From the matching item:

- **Name:** `published.name`
- **Active members:** `state.userStates[]` filtered to `type == "Active"` — the reps to analyze
- **Weights:** `published.weights[]` (`{userId, weight}`) — the configured share each rep should get
- **Handling / algorithm:** `published.assignmentTypeConfig.handling.type` (`Strict` or `Flexible`); assignment scope `published.assignmentTypeConfig.type` (`Record`/`Meeting`/`Conversation`)
- **Capping:** `published.capping` (per-rep meeting limits, if set)

## distribution-list-put — period statistics (authoritative totals)

As of **DISTRO-4426 (2026-06-03)**, every `userState` variant carries
`statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}` —
cumulative counts for the **current distribution period**:

- `assigned` — direct bookings to this rep; primary volume metric
- `cancelled` — cancelled assignments (cancel rate = `cancelled / assigned`)
- `noShow` — no-shows
- `reassignedToThis` / `reassignedFromThis` — rebalancing context; a large `reassignedToThis` means this rep absorbed slack from others
- **Effective total:** `assigned + reassignedToThis - reassignedFromThis` (the round-robin's net score)

**`idealNumber` is NOT stored in the API** — derive it client-side as
`(userWeight / totalWeight) × totalAssigned`, where
`totalAssigned = sum of all members' statistics.assigned`. This fair-share target
must be computed, not read.

## meeting-list-put — classification and pattern fields

Classify each kept meeting (`hostId` must be an active member):

- `meetingStatus == "Active"` and `dateTime.start` in the future → upcoming
- `meetingStatus == "Active"` and `dateTime.start` in the past → completed (informally)
- `meetingStatus == "Completed"` → completed
- `meetingStatus == "NoShow"` (or `noShowStatus == "NoShow"`) → no-show
- `meetingStatus == "Canceled"` → cancelled

Pattern fields:

- **Booking source:** read actual values from `scheduleOrigin` / `meetingSource` (e.g. `meetingSource.type`, `scheduleOrigin.productFeature.type`) — do not assume an enum
- **Day-of-week skew:** bucket completed meetings by `dateTime.start` weekday
- **Cancellation cause:** inspect cancelled meetings' `history[]` entries (cancelling `actorRef` / `origin`) to see whether cancels are guest-, rep-, or calendar-driven

---

## Hard API limits

- **`meeting-list-put`: 7-day maximum window per call.** Split `[start_date, end_date)`
  into ≤7-day chunks and call once per chunk.
- **Pagination:** results are in `data.list`; paginate while `hasMore === "Yes"`
  (string comparison), incrementing `pagination.page`. Merge chunks, dedupe on `meetingId`.

```yaml
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  workspaceIds: [<workspace.id>]
  pagination:
    page: 0
    pageSize: 200
```

## Scope limits — what the public MCP cannot do

- **No `distributionId` filter on meetings.** Meetings cannot be filtered by
  distribution. This skill attributes meetings to a distribution by its **member reps
  (host)**. If a rep belongs to multiple distributions, their meetings count toward
  each — state this caveat in the output.
- **No distribution config-history endpoint.** Use `statistics` from
  `distribution-list-put` for authoritative period totals, and `meeting-list-put` for
  date-range slicing and booking-source / day-of-week patterns.
- For exact per-distribution routing attribution, use the routing logs
  (`/audit-routing`, `concierge-logs`).

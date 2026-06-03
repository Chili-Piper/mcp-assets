---
name: distribution-analysis
description: Analyzes a Chili Piper distribution (round-robin queue) for a workspace and date range — meeting counts by rep, imbalance vs. configured weights, day-of-week and booking-source skew, and cancellation breakdown — using the public Chili Piper MCP. Use when someone asks why a rep is getting more or fewer meetings than others, wants a distribution breakdown, or wants to analyze meeting imbalance for a period.
version: 0.1.1
references:
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID containing the distribution."
    required: true
  - name: distribution
    type: string
    description: "Distribution name (substring) or distributionId to analyze."
    required: true
  - name: start_date
    type: string
    description: "Start of range, inclusive (e.g. 2026-05-01)."
    required: true
  - name: end_date
    type: string
    description: "End of range, exclusive (e.g. 2026-06-01 = through May 31)."
    required: true
outputs:
  - name: distribution_config
    description: The distribution's active members, weights, and assignment handling
  - name: rep_breakdown
    description: Meeting counts by rep (total, completed, cancelled, no-show) with imbalance ratio
  - name: patterns
    description: Booking-source skew, day-of-week skew, weekly trend, and cancellation breakdown
  - name: recommendations
    description: Likely causes of imbalance and what to check
tools_required: [chili-piper-mcp]
human_decision_point: "Review the imbalance findings and decide whether to rebalance weights, fix calendar/availability for an under-booked rep, or adjust the distribution in the router builder"
writes_to: "Nothing — read-only diagnostic. Apply any rebalancing in the Chili Piper router builder (or via distribution-adjust-v3 with explicit human approval)."
api_note: "Field names validated against live MCP responses. distribution-list-put returns a top-level array; each item has published.{distributionId,name,weights:[{userId,weight}],assignmentTypeConfig,capping,teamRef} and state.userStates:[{userId,type:Active|Capped|Disabled|Removed|NoLicense,statistics:{assigned,cancelled,noShow,reassignedToThis,reassignedFromThis}}]. As of DISTRO-4426 (2026-06-03): statistics is now present on every userState variant and reflects cumulative counts for the current distribution period; idealNumber must be derived client-side as (userWeight/totalWeight)*totalAssigned. meeting-list-put returns data.list[] with hostId/hostName, meetingStatus, dateTime.start, scheduleOrigin, meetingSource, history; 7-day max window per call. The public MCP does NOT expose distribution config history, and meetings are not filterable by distributionId — use statistics from distribution-list-put for authoritative period totals, and meeting-list-put for date-range slicing and booking-source/day-of-week patterns."
---

# Distribution Analysis

You are a RevOps analyst. Pull a Chili Piper distribution's configuration and the meetings its member reps hosted over a date range, then surface imbalance patterns and likely causes — using only the public Chili Piper MCP.

> **Scope & honesty.** The public MCP cannot filter meetings by `distributionId` and has no distribution config-history endpoint. This skill attributes meetings to a distribution by its **member reps (host)**. If a rep belongs to multiple distributions, their meetings count toward each — state this caveat in the output. For exact per-distribution routing attribution, use the routing logs (`/audit-routing`, `concierge-logs`).

## Tools

| Tool | What it returns |
|------|----------------|
| `workspace-list` | Workspaces → items `{id, name, nrOfUsers}` (identifier is `id`) |
| `distribution-list-put` | Distributions (top-level array). Input `{workspaceIds: [...], name?, assignmentType?}`. Each item: `{id, published: {distributionId, name, weights: [{userId, weight}], assignmentTypeConfig: {type, handling: {type}}, capping, teamRef: {id}}, state: {userStates: [{userId, type: "Active"\|"Capped"\|"Disabled"\|"Removed"\|"NoLicense", statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}}]}}` |
| `user-find-by-ids` | Resolve member `userId`s → names/emails |
| `meeting-list-put` | Meetings in a ≤7-day window → `data.list[]` with `meetingId`, `hostId`/`hostName`, `meetingStatus`, `dateTime.start`, `scheduleOrigin`, `meetingSource`, `noShowStatus`, `history`. Envelope `{data:{list}, hasMore}`; paginate while `hasMore === "Yes"`. |

---

## Step 1 — Resolve the workspace

If `workspace` is a name, call `workspace-list` and match on `name`; use its `id`.

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

---

## Step 2 — Find the distribution and read its config

```
tool: distribution-list-put
args:
  workspaceIds: [<workspace.id>]
  name: <distribution>          # omit if you were given a distributionId; filter the array instead
```

From the matching item, extract:
- **Name:** `published.name`
- **Active members:** `state.userStates[]` filtered to `type == "Active"` (these are the reps to analyze)
- **Weights:** `published.weights[]` (`{userId, weight}`) — the configured share each rep should get
- **Handling / algorithm:** `published.assignmentTypeConfig.handling.type` (`Strict` or `Flexible`); assignment scope `published.assignmentTypeConfig.type` (`Record`/`Meeting`/`Conversation`)
- **Capping:** `published.capping` (per-rep meeting limits, if set)
- **Period statistics:** each active member's `state.userStates[]` entry carries `statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}` — cumulative counts for the current distribution period. Collect these now; use them in Step 5 as the primary source for period totals.
- **Ideal number (derived):** `idealNumber = (userWeight / totalWeight) × totalAssigned` where `totalAssigned = sum of all members' statistics.assigned`. This fair-share target is not stored in the API and must be computed client-side.

If no distribution matches, say so and list the available distribution names in the workspace.

---

## Step 3 — Resolve member names

Collect the active member `userId`s and resolve them to names/emails:

```
tool: user-find-by-ids
args:
  userIds: [<userId>, <userId>, ...]
```

Build a `userId → name` map for display. Never show raw user IDs in the final output.

---

## Step 4 — Pull meetings hosted by the members

`meeting-list-put` has a **7-day maximum window**. Split `[start_date, end_date)` into ≤7-day chunks and call once per chunk, paginating while `hasMore === "Yes"`.

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  workspaceIds: [<workspace.id>]
  pagination:
    page: 0
    pageSize: 200
```

Merge all chunks, dedupe on `meetingId`, then **keep only meetings whose `hostId` is one of the distribution's active members**. Classify each kept meeting:
- `meetingStatus == "Active"` and `dateTime.start` in the future → upcoming
- `meetingStatus == "Active"` and `dateTime.start` in the past → completed (informally)
- `meetingStatus == "Completed"` → completed
- `meetingStatus == "NoShow"` (or `noShowStatus == "NoShow"`) → no-show
- `meetingStatus == "Canceled"` → cancelled

---

## Step 5 — Build the rep breakdown and detect imbalance

Use two complementary sources:

**From `statistics` (distribution API, current period — authoritative totals):**
- `assigned` — direct bookings to this rep; use as the primary volume metric
- `cancelled` — cancelled assignments (cancel rate = `cancelled / assigned`)
- `noShow` — no-shows
- `reassignedToThis` / `reassignedFromThis` — rebalancing context; a large `reassignedToThis` means this rep absorbed slack from others
- **Effective total:** `assigned + reassignedToThis - reassignedFromThis` (the round-robin's net score)

**Derived from statistics:**
- **Ideal number:** `(userWeight / totalWeight) × totalAssigned` — the fair-share target for each rep given their configured weight
- **Imbalance ratio:** top rep's `assigned` ÷ median rep's `assigned`
- **Vs. configured weight:** compare each rep's `assigned / totalAssigned` to their `weight / totalWeight`. A rep with a high weight share but low `assigned` share (or vice versa) is the headline finding.

**From `meeting-list-put` (date-range data — for patterns):**
- **Day-of-week skew:** bucket completed meetings by `dateTime.start` weekday — does one rep dominate certain days?
- **Booking source:** group by the meeting's booking origin — read the actual values from `scheduleOrigin` / `meetingSource` (e.g. `meetingSource.type`, `scheduleOrigin.productFeature.type`) rather than assuming an enum. Surface differences (e.g. one rep gets most meetings from one source).
- **Weekly trend:** meetings per rep per week — did a gap open at a specific week?
- **Cancellation breakdown:** for cancelled meetings, inspect the `history[]` entries (look at the cancelling `actorRef`/`origin`) to see whether cancels are guest-, rep-, or calendar-driven.

Flag reps with 0 `assigned` (likely calendar/availability issue — suggest `/check-availability`) and reps whose `assigned / totalAssigned` share diverges sharply from their `weight / totalWeight` share.

---

## Step 6 — Output

See `references/output-format.md` for the exact template. Always lead with the config + rep breakdown, then patterns, then recommendations. Include the attribution caveat from the top of this skill whenever a member belongs to more than one distribution.

---

## Data handling

- **PII present:** rep names/emails and guest data in meetings — used for analysis; display rep names, not guest details, unless asked
- **Storage:** ephemeral
- **Writes:** none — read-only. Apply rebalancing manually, or via `distribution-adjust-v3` only with explicit human approval (it publishes immediately).

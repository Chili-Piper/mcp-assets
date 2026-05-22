---
name: user-meetings
description: Shows all meetings assigned to a specific rep for a period — volume, statuses, and no-show rate — to surface rep-level pipeline health and flag reps who may need coaching or routing changes
version: 0.2.1
inputs:
  - name: user
    type: string
    description: "Email address, name, or Chili Piper user ID of the rep"
    required: true
  - name: date_range
    type: string
    description: "Period to analyze: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD' (max 7-day window per API call — skill will issue multiple calls automatically)"
    required: false
    default: "last-30-days"
  - name: workspace
    type: string
    description: "Workspace name or ID to scope. Omit for org-wide."
    required: false
outputs:
  - name: summary
    description: Meeting volume, completion rate, and no-show rate for the period
  - name: meeting_list
    description: All meetings in the period with date, status, guest, and lead time
  - name: anomalies
    description: Patterns that may indicate coaching needs or routing issues
tools_required: [chili-piper-mcp]
human_decision_point: "Review anomaly flags and decide: coaching conversation, territory/routing adjustment, or no action needed"
writes_to: "Nothing — read-only diagnostic"
api_note: "Uses meeting-export-v2-put with hostIds filter — the server returns only this rep's meetings, eliminating client-side filtering across all org meetings. Still requires 7-day chunking. Response is CSV: parse the header row to identify columns; key columns are meetingId, status (Active|Canceled|NoShow|Completed), scheduledAt/start, hostId, workspaceId."
---

# User Meetings

You are a RevOps analyst and rep manager assistant. Your job is to pull all meetings assigned to a specific rep for a given period, calculate their health metrics, and flag patterns that warrant a manager conversation or a routing adjustment.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `meeting-export-v2-put` | CSV export of meetings in a window ≤ 7 days — supports `hostIds`, `assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`, `workspaceIds` filters. Response: `{filename: "meetings-export-....csv", data: "<CSV content>"}`. Parse `data` as CSV; read header row to identify columns. Status values: `Active` \| `Canceled` \| `NoShow` \| `Completed`. No pagination — all matching records returned in one response. |
| `workspace-list` | All workspaces — needed to resolve workspace ID to display name |

**Critical constraint:** `meeting-export-v2-put` accepts at most a **7-day window** per call. For a 30-day range you must issue multiple sequential calls and merge the results.

---

## Step 1 — Resolve the user

```
tool: user-find
args:
  query: <user input (email or name)>
```

If multiple results, list them and ask the human to confirm. Store the resolved `userId`, `email`, and `name`.

---

## Step 1b — Resolve workspace names

Always call `workspace-list` at the start, regardless of whether the `workspace` input was provided. Build an `id → name` map and use it to label workspace IDs in all output. Never invent or guess workspace names.

---

## Step 2 — Fetch meetings per 7-day chunk

Parse the `date_range` input:
- `last-7-days` → one call
- `last-30-days` → 5 calls (days 0–6, 7–13, 14–20, 21–27, 28–30)
- `YYYY-MM-DD:YYYY-MM-DD` → calculate slices needed

For each chunk (strictly ≤ 6 days to stay within the 7-day limit):

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<resolved userId>]
  workspaceIds: [<resolved workspaceId>]   # include only if workspace was specified
```

The response is `{filename: "...", data: "<CSV>"}`. Parse the `data` field as CSV:
1. Read the first row as the header to identify column names.
2. Extract all data rows as meeting records.
3. Map columns to: meetingId, status, scheduled start time, workspaceId, and any attendee/guest fields present.

No pagination is needed — the export returns all matching records for the chunk in a single response.

Merge records across all chunks. Deduplicate on `meetingId`.

---

## Step 3 — Calculate metrics

**Status values** (returned directly in the `status` column):

| Status | Classification |
|--------|---------------|
| `Completed` | Completed — include in rate |
| `NoShow` | No-Show — include in rate |
| `Canceled` | Cancelled — exclude from rate |
| `Active` | See note below |

**Important — `Active` covers two cases:** Chili Piper meetings that were never explicitly closed out stay `Active` indefinitely, even after the scheduled time has passed. Split on the scheduled start time relative to now:
- `Active` + start **in the future** → **Upcoming** — exclude from rate
- `Active` + start **in the past** → treat as **informally Completed** — include in the denominator but NOT the no-show numerator; flag these in the output so the human knows the count is estimated

Surface a caveat in the report when a significant number of past meetings are `Active`: *"N past meetings show as Active (not formally closed). No-show rate treats these as completed; actual no-shows may be undercounted."*

**No-show rate:** `NoShow / (Completed + NoShow + past-Active)`

**Completion rate:** `(Completed + past-Active) / (Completed + NoShow + past-Active)`

**Scheduled time** (per meeting): use the `When` column for the meeting date/time.

---

## Step 4 — Detect anomalies

Check for:

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| High no-show rate | No-show rate > 30% (with ≥ 10 meetings) | High |
| Very high no-show rate | No-show rate > 50% | High |
| Low volume | < 5 meetings in period | Medium — may be routing gap |
| Zero meetings | 0 meetings in period | High — check router membership |
| Many cancellations | Cancelled > 50% of total meetings | Medium |

For high no-show rate, add the hypothesis:
- If volume < 10: "Small sample — may not be representative. Check if rep is active in routers."

---

## Step 5 — Output format

### Meetings for `<name>` (`<email>`) | `<date range>`

**Summary**

| Metric | Value |
|--------|-------|
| Total meetings (completed + no-show) | |
| Completed | |
| No-shows | |
| No-show rate | |
| Cancelled (excluded from rate) | |
| Upcoming (Scheduled) | |

**Anomalies**

| Flag | Severity | Note |
|------|----------|------|
| ... | | |

*(or: "No anomalies detected.")*

**Meeting list** (most recent first, sorted by scheduled start)

| Date | Status | Attendees | Workspace |
|------|--------|-----------|-----------|
| ... | | | |

**Human decision point**

*"Does this look like a coaching opportunity, a routing adjustment, or is the rep performing as expected? I can pull their routing assignments or compare them to the team average."*

---

## Data handling

- **PII present:** rep email and guest email used for lookup and grouping; not surfaced in output beyond display
- **Storage:** ephemeral
- **Writes:** none — read-only

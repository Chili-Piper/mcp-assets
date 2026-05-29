---
name: user-meetings
description: Shows all meetings assigned to a specific rep for a period — volume, statuses, and no-show rate — to surface rep-level pipeline health and flag reps who may need coaching or routing changes
version: 0.4.0
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
    description: All meetings in the period with scheduled date, status, guest, and workspace
  - name: anomalies
    description: Patterns that may indicate coaching needs or routing issues
tools_required: [chili-piper-mcp]
human_decision_point: "Review anomaly flags and decide: coaching conversation, territory/routing adjustment, or no action needed"
writes_to: "Nothing — read-only diagnostic"
api_note: "As of DISTRO-4472 (2026-05-21) meeting-export-v2-put supports these server-side filters (all confirmed live): hostIds, assigneeIds, bookerIds, meetingTypeIds, status. As of DISTRO-4483 (in production 2026-05-29) the export CSV now includes bookedAt and meetingId columns — dedupe on meetingId and populate the Booked column from bookedAt. Verify the exact CSV header strings against a real export. Times displayed in local timezone detected via bash."
---

# User Meetings

You are a RevOps analyst and rep manager assistant. Your job is to pull all meetings assigned to a specific rep for a given period, calculate their health metrics, and flag patterns that warrant a manager conversation or a routing adjustment.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `meeting-export-v2-put` | CSV export with server-side filters (all confirmed live as of DISTRO-4472): `hostIds`, `assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`. Response: `{filename, data: "<CSV>"}`. Parse `data` as CSV; read header row to identify columns. Key columns: `meetingId`, `Title`, `When` (scheduled start), `End`, `bookedAt`, `Status`, `Primary Guest`, `Meeting Type`. Status values: `Active` \| `Canceled` \| `NoShow` \| `Completed`. No pagination — all matching records in one response per chunk. **`bookedAt` and `meetingId` columns added in DISTRO-4483 (production 2026-05-29);** confirm the exact header strings against a real export. |
| `workspace-list` | All workspaces — needed to resolve workspace ID to display name |

**Critical constraint:** `meeting-export-v2-put` accepts at most a **7-day window** per call. For a 30-day range issue multiple sequential calls and merge the results.

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

Always call `workspace-list` at the start. Build a `workspaceId → name` map. Never invent or guess workspace names.

---

## Step 1c — Detect local timezone

```bash
cat /etc/timezone 2>/dev/null || readlink /etc/localtime 2>/dev/null | sed 's|.*zoneinfo/||'
```

Store the IANA result (e.g. `America/Chicago`). Convert **all timestamps** in output to this timezone. If the command fails, fall back to `date +%z` and note the UTC offset used.

---

## Step 2 — Fetch meetings per 7-day chunk

Parse the `date_range` input:
- `last-7-days` → one call
- `last-30-days` → 5 calls (days 0–6, 7–13, 14–20, 21–27, 28–30)
- `YYYY-MM-DD:YYYY-MM-DD` → calculate slices needed

For each chunk (strictly ≤ 6 days):

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<resolved userId>]
  status: ["Active", "Completed", "NoShow", "Canceled"]
  workspaceIds: [<resolved workspaceId>]   # only if workspace was specified
```

Response: `{filename, data: "<CSV>"}`. Parse `data` as CSV — read the header row first to identify columns. No pagination needed per chunk.

Merge records across all chunks. Deduplicate on the `meetingId` column.

---

## Step 3 — Classify meetings

Use the `Status` column. Split `Active` on the `When` time vs. now:

| Status | When | Classification |
|--------|------|----------------|
| `Completed` | any | Completed — include in rate |
| `NoShow` | any | No-Show — include in rate (numerator) |
| `Canceled` | any | Cancelled — exclude from rate |
| `Active` | future | Upcoming — exclude from rate |
| `Active` | past | Informally Completed — include in denominator only |

Surface a caveat when past-Active count is significant: *"N past meetings show as Active (not formally closed). No-show rate treats these as completed; actual no-shows may be undercounted."*

---

## Step 4 — Calculate metrics

**No-show rate:** `NoShow / (Completed + NoShow + past-Active)`

**Completion rate:** `(Completed + past-Active) / (Completed + NoShow + past-Active)`

---

## Step 5 — Detect anomalies

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| High no-show rate | > 30% (with ≥ 10 meetings) | High |
| Very high no-show rate | > 50% | High |
| Low volume | < 5 meetings in period | Medium — may be routing gap |
| Zero meetings | 0 meetings | High — check router membership |
| Many cancellations | Cancelled > 50% of total | Medium |

---

## Step 6 — Output format

### Meetings for `<name>` (`<email>`) | `<date range>` | Timezone: `<tz>`

**Summary**

| Metric | Value |
|--------|-------|
| Total meetings (completed + no-show) | |
| Completed | |
| No-shows | |
| No-show rate | |
| Past Active (informally completed) | |
| Cancelled (excluded from rate) | |
| Upcoming | |

**Anomalies**

| Flag | Severity | Note |
|------|----------|------|
| ... | | |

*(or: "No anomalies detected.")*

**Meeting list** (most recent first, sorted by `When`)

| Scheduled (`When`) | Booked (`bookedAt`) | Status | Primary Guest | Workspace |
|--------------------|---------------------|--------|--------------|----------|
| ... | | | | |

> All times in `<tz>`. The **Booked** column comes from the `bookedAt` CSV column (added in DISTRO-4483); lead time = `When` − `bookedAt`.

**Human decision point**

*"Does this look like a coaching opportunity, a routing adjustment, or is the rep performing as expected? I can pull their routing assignments or compare them to the team average."*

---

## Data handling

- **PII present:** rep email and guest email used for lookup and grouping; not surfaced in output beyond display
- **Storage:** ephemeral
- **Writes:** none — read-only

---
name: user-meetings
description: Shows all meetings assigned to a specific rep for a period — volume, statuses, and no-show rate — to surface rep-level pipeline health and flag reps who may need coaching or routing changes
version: 0.1.0
inputs:
  - name: user
    type: string
    description: "Email address, name, or Chili Piper user ID of the rep"
    required: true
  - name: date_range
    type: string
    description: "Period to analyze: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD' (max 7-day window per API call — skill will paginate automatically)"
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
api_note: "meeting-list-put has a strict 7-day maximum window per call. For date ranges longer than 7 days, the skill issues multiple calls and stitches the results. Filtering by assignee happens client-side — the API does not support assignee filtering directly."
---

# User Meetings

You are a RevOps analyst and rep manager assistant. Your job is to pull all meetings assigned to a specific rep for a given period, calculate their health metrics, and flag patterns that warrant a manager conversation or a routing adjustment.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `meeting-list-put` | Meetings in a 7-day window → `id`, `status`, `startTime`, `createdAt`, `assignee`, `guest` |
| `workspace-list` | All workspaces — needed to resolve workspace name to ID |

**Critical constraint:** `meeting-list-put` accepts at most a **7-day window** per call. For a 30-day range you must make 4–5 sequential calls and merge the results.

---

## Step 1 — Resolve the user

```
tool: user-find
args:
  query: <user input (email or name)>
```

If multiple results, list them and ask the human to confirm. Store the resolved `userId`, `email`, and `name`.

---

## Step 2 — Slice the date range into 7-day chunks

Parse the `date_range` input:
- `last-7-days` → one call
- `last-30-days` → 5 calls (days 0–6, 7–13, 14–20, 21–27, 28–30)
- `YYYY-MM-DD:YYYY-MM-DD` → calculate slices needed

For each 7-day (or shorter) chunk:

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  page: 0
  pageSize: 200
```

Paginate each chunk if needed (compare `total` to `pageSize`).

Merge all results into a single list. Deduplicate on `id`.

---

## Step 3 — Filter to this rep

Filter the merged list for meetings where `assignee.email` matches the user's email (case-insensitive). If `workspace` was specified, also filter by workspace (if available in meeting data).

---

## Step 4 — Calculate metrics

**Status counts:**
- `Completed` — meeting happened
- `NoShow` — guest did not attend ← the signal
- `Cancelled` — exclude from no-show rate
- `Scheduled` — upcoming, exclude from rates

**No-show rate:** `NoShow / (Completed + NoShow)`

**Completion rate:** `Completed / (Completed + NoShow)`

**Lead time** (per meeting): `startTime - createdAt` in hours/days

**Average lead time:** mean across all Completed + NoShow meetings

---

## Step 5 — Detect anomalies

Check for:

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| High no-show rate | No-show rate > 30% (with ≥ 10 meetings) | High |
| Very high no-show rate | No-show rate > 50% | High |
| Long average lead time | Average lead time > 5 days | Medium — intent decay risk |
| Low volume | < 5 meetings in period | Medium — may be routing gap |
| Zero meetings | 0 meetings in period | High — check router membership |
| Many cancellations | Cancelled > 50% of total meetings | Medium |

For high no-show rate, add the hypothesis:
- If average lead time > 5 days: "Long booking windows are likely causing intent decay — consider capping at 3 days for this rep's routes."
- If volume < 10: "Small sample — may not be representative. Check if rep is active in routers."

---

## Step 6 — Output format

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
| Average lead time | |

**Anomalies**

| Flag | Severity | Note |
|------|----------|------|
| ... | | |

*(or: "No anomalies detected.")*

**Meeting list** (most recent first)

| Date | Status | Guest | Lead time |
|------|--------|-------|-----------|
| ... | | | |

**Human decision point**

*"Does this look like a coaching opportunity, a routing adjustment, or is the rep performing as expected? I can pull their routing assignments or compare them to the team average."*

---

## Data handling

- **PII present:** rep email and guest email used for lookup and grouping; not surfaced in output beyond display
- **Storage:** ephemeral
- **Writes:** none — read-only

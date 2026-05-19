---
name: org-meeting
description: Org-wide meeting volume and health snapshot — total booked, completed, no-show, and cancelled by workspace — for weekly or monthly executive reviews of booking capacity and pipeline coverage
version: 0.1.0
inputs:
  - name: date_range
    type: string
    description: "Period to analyze: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD' (max 7-day window per API call — skill paginates automatically)"
    required: false
    default: "last-7-days"
  - name: group_by
    type: string
    description: "Primary dimension: 'workspace' | 'rep' | 'status'"
    required: false
    default: "workspace"
outputs:
  - name: org_summary
    description: Total meetings, completion rate, and no-show rate across the org
  - name: breakdown
    description: Meeting volume and health metrics by the selected dimension
  - name: flags
    description: Workspaces or reps with significantly above-average no-show rates
tools_required: [chili-piper-mcp]
human_decision_point: "Review the breakdown and decide: share with VP Sales/CRO, drill into a flagged workspace with /no-show-analyzer, or check individual reps with /user-meetings"
writes_to: "Nothing — read-only"
api_note: "meeting-list-put has a strict 7-day maximum window. For 30-day ranges the skill makes multiple paginated calls. Workspace IDs are resolved via workspace-list. The API does not support server-side filtering by workspace — grouping is done client-side."
---

# Org Meeting Snapshot

You are a RevOps analyst preparing an executive summary of booking health. Your job is to pull all meetings for a period, calculate org-wide and dimension-level metrics, and flag anything that warrants action before the data reaches leadership.

## API reference

| Tool | What it returns |
|------|----------------|
| `meeting-list-put` | Meetings in a window < 7 days → response: `{data: {list: [{meetingId, status, scheduledAt, attendees, assignedUserId, workspaceId}]}, hasMore: "Yes"\|"No"}` |
| `workspace-list` | All workspaces → array of `{workspaceId, name, settings}` — items use `workspaceId` (NOT `id`) — needed to group meetings by workspace name |

---

## Step 1 — Build the date range chunks

Parse `date_range` and split into 7-day (or shorter) chunks. For each chunk:

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  pagination:
    page: 0
    pageSize: 200
```

Each chunk must be strictly less than 7 days (use at most 6-day chunks). Paginate each chunk if needed: results are in `data.list`; check `hasMore === "Yes"` (string comparison) and increment `pagination.page` until `hasMore === "No"`. Merge all results from `data.list` across all chunks, deduplicate on `meetingId`.

---

## Step 2 — Resolve workspaces (if group_by=workspace)

```
tool: workspace-list
args:
  page: 0
  pageSize: 100
```

Build a map of `workspaceId → workspaceName` using the `workspaceId` field (not `id`) from each workspace-list item.

Note: meeting items from `meeting-list-put` include a `workspaceId` field — use it directly for grouping.

---

## Step 3 — Calculate org-wide metrics

Across all meetings:

**Statuses:**
- `Completed` — happened
- `NoShow` — missed
- `Cancelled` — exclude from no-show rate
- `Scheduled` — upcoming

**Org no-show rate:** `NoShow / (Completed + NoShow)`

**Completion rate:** `Completed / (Completed + NoShow)`

---

## Step 4 — Calculate dimension breakdown

**group_by=workspace:** group by `workspaceId`, resolve to name, calculate per-workspace metrics

**group_by=rep:** group by `assignedUserId`, calculate per-rep metrics. Sort by meeting volume descending. To display rep names, resolve `assignedUserId` values via `user-find-by-ids` after collecting all distinct IDs.

**group_by=status:** simple count of each status — useful for a quick executive pie-chart narrative.

For each group with ≥ 10 meetings, calculate no-show rate. Flag any group where rate > (org average + 10pp) or > 35%.

---

## Step 5 — Output format

### Org Meeting Snapshot | `<date range>` | Grouped by `<dimension>`

**Org Summary**

| Metric | Value |
|--------|-------|
| Total meetings (completed + no-show) | |
| Completed | |
| No-shows | |
| Org no-show rate | |
| Cancelled (excl. from rate) | |
| Upcoming (Scheduled) | |

**Breakdown**

| `<Dimension>` | Meetings | No-shows | Rate | Flag |
|---------------|---------|----------|------|------|
| ... | | | | ⚠ / ✓ |

**Flags**

For each flagged group:
> `<Workspace/Rep>` — `N%` no-show rate vs `N%` org average. Run `/no-show-analyzer workspace="<name>"` or `/user-meetings user="<email>"` for root-cause analysis.

**Human decision point**

*"Should I send this to the summary view, or drill into any of the flagged groups?"*

---

## Suggested follow-up skills

- `/no-show-analyzer` — drill into a flagged workspace with root-cause hypotheses
- `/user-meetings` — inspect a specific rep's meeting health
- `/meeting-inspector` — investigate a single anomalous meeting

---

## Data handling

- **PII present:** rep emails used for grouping; surfaced in `group_by=rep` breakdown
- **Storage:** ephemeral
- **Writes:** none — read-only

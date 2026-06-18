---
name: org-meeting
description: Org-wide meeting volume and health snapshot — total booked, completed, no-show, and cancelled by workspace — for weekly or monthly executive reviews of booking capacity and pipeline coverage
version: 0.1.3
references:
  - api-reference
  - output-format
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
human_decision_point: "Review the breakdown and decide: share with VP Sales/CRO, drill into a flagged workspace with /analyze-no-shows, or check individual reps with /user-meetings"
writes_to: "Nothing — read-only"
---

# Org Meeting Snapshot

You are a RevOps analyst preparing an executive summary of booking health. Your job is to pull all meetings for a period, calculate org-wide and dimension-level metrics, and flag anything that warrants action before the data reaches leadership.

> **Prefer live data over training.** Chili Piper's field names and tool signatures change. Always load `references/api-reference.md` before making MCP calls — it documents exact field names, status values, hard limits, and known gotchas.

## When to use

- Preparing a weekly or monthly executive review of booking capacity and pipeline coverage.
- You need org-wide meeting volume and health (booked, completed, no-show, cancelled) at a glance.
- You want a per-workspace or per-rep breakdown to spot where booking health is degrading.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `date_range` | — | `last-7-days` | Period to analyze: `last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`. Max 7-day window per API call — skill paginates automatically. |
| `group_by` | — | `workspace` | Primary dimension: `workspace`, `rep`, or `status`. |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Build the date range chunks

Parse `date_range` and split into 7-day (or shorter) chunks. For each chunk call `meeting-list-put` with `status: ["Completed", "NoShow", "Active"]`, paginate, then merge and deduplicate on `meetingId`.

Always include `"Active"` in the status filter — past-Active meetings count in the no-show denominator; future-Active are separated client-side as "Upcoming". Exact args, the strict 7-day chunking rule, `hasMore === "Yes"` pagination, and the historical-analysis status set → `references/api-reference.md` § meeting-list-put — pagination and chunking and § Hard API limits.

### Step 2 — Resolve workspaces (if group_by=workspace)

Call `workspace-list` and build a map of `id → name`, then join each meeting's `workspaceId` to that `id`. Exact args and the `id`-vs-`workspaceId` gotcha → `references/api-reference.md` § workspace-list — resolving workspace names.

### Step 3 — Calculate org-wide metrics

Across all meetings, classify by `meetingStatus`. Status meanings and rate treatment (including splitting `Active` on start time vs. now) → `references/api-reference.md` § Meeting status values.

- **Org no-show rate:** `NoShow / (Completed + NoShow + past-Active)`
- **Completion rate:** `(Completed + past-Active) / (Completed + NoShow + past-Active)`

Surface a caveat when past-Active is a significant share of total (exact wording → `references/output-format.md` § Caveat line).

### Step 4 — Calculate dimension breakdown

Group by the selected dimension and compute per-group metrics. Group key and name source per dimension → `references/api-reference.md` § Grouping fields by dimension.

- **`workspace`:** group by `workspaceId`, resolve to name, calculate per-workspace metrics.
- **`rep`:** group by `hostId`, calculate per-rep metrics, sort by meeting volume descending. Names are already present as `hostName`/`hostEmail` — no separate lookup.
- **`status`:** simple count of each status — useful for a quick executive pie-chart narrative.

For each group with ≥ 10 meetings, calculate no-show rate. Flag any group where rate > (org average + 10pp) or > 35%.

### Step 5 — Output

Exact layout → `references/output-format.md` § Template. Suggested follow-up skills → `references/output-format.md` § Suggested follow-up skills.

## Preflight audit

Verify before writing output. Every line must be a clear pass/fail:

- [ ] `date_range` parsed and split into chunks each strictly < 7 days.
- [ ] Field names and the status filter taken from `references/api-reference.md`, not guessed.
- [ ] `"Active"` included in the status filter; `Active` meetings split on start time vs. now (past-Active in denominator, not numerator).
- [ ] All chunks paginated to `hasMore === "No"`, merged, and deduplicated on `meetingId`.
- [ ] Workspaces resolved via `workspace-list` (`id → name`) when `group_by=workspace`.
- [ ] Past-Active caveat surfaced when it is a significant share of total.

## Checkpoint

Read-only skill: present the org summary, breakdown, and flags, then stop for the human:

*"Should I send this to the summary view, or drill into any of the flagged groups?"*

Let the human decide: share with VP Sales/CRO, drill into a flagged workspace with `/analyze-no-shows`, or check individual reps with `/user-meetings`.

## Data handling

- **PII present:** rep emails used for grouping; surfaced in `group_by=rep` breakdown
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only

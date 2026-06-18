---
name: no-show-analyzer
description: Analyzes Chili Piper meeting no-show patterns by trigger type, routing path, rep, or workspace using meeting-list-put and concierge-logs to surface actionable optimization opportunities
version: 0.3.3
references:
  - api-reference
  - analysis-methodology
  - output-format
inputs:
  - name: date_range
    type: string
    description: "Period to analyze: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD'. For trigger/route breakdown, concierge-logs caps at 30 days. Meeting data can go further but loses routing context."
    required: false
    default: "last-30-days"
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the analysis. Omit for org-wide."
    required: false
  - name: group_by
    type: string
    description: "Primary dimension: 'trigger' (lead source type) | 'route' (matched routing path) | 'rep' (assignee) | 'workspace'"
    required: false
    default: "trigger"
  - name: flag_threshold
    type: number
    description: "No-show rate (%) above which a segment is flagged. Default: 30."
    required: false
    default: 30
outputs:
  - name: summary
    description: Overall no-show rate and meeting volume for the period
  - name: breakdown
    description: No-show rate by the selected dimension, sorted highest to lowest
  - name: flagged_segments
    description: Segments above the threshold with root-cause hypotheses
  - name: recommended_actions
    description: Specific routing or confirmation flow changes to test
tools_required: [chili-piper-mcp]
human_decision_point: "Review flagged segments and decide which routing rule or confirmation flow change to test first"
writes_to: "Salesforce task (optional) — created by human after reviewing recommendations"
---

# No-Show Analyzer

You are a GTM data analyst with deep knowledge of Chili Piper's meeting and routing model. Your job is to pull meeting data and routing context for a given period, calculate no-show rates, flag problem segments, and surface specific actions for the human to test.

> **Prefer live data over training.** MCP field names and tool signatures change. Load `references/api-reference.md` before making MCP calls — it is the canonical field-name truth for this skill (the tools' own descriptions are unreliable).

## When to use

- You want to know where meeting no-shows concentrate (by trigger, route, rep, or workspace) for a period.
- You need root-cause hypotheses and testable actions to reduce no-show rate, not just a number.
- You're running the optimization loop: measure a baseline now, change one thing, re-measure in 30 days.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `date_range` | — | `last-30-days` | Period to analyze: `last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`. Trigger/route breakdown caps at 30 days (concierge-logs window). |
| `workspace` | — | org-wide | Workspace name or ID to scope the analysis. Omit for org-wide. |
| `group_by` | — | `trigger` | Primary dimension: `trigger` \| `route` \| `rep` \| `workspace`. |
| `flag_threshold` | — | `30` | No-show rate (%) above which a segment is flagged. |

## Process

### Step 1 — Resolve inputs and validate

Parse the user's request for `date_range`, `workspace`, `group_by`, and `flag_threshold`.

**Date range constraint check:** If the requested range exceeds 30 days AND `group_by` is `trigger` or `route`, warn the user:
> "concierge-logs has a 30-day maximum window. I'll analyze the most recent 30 days for trigger/route breakdown. For longer periods, use `group_by=rep` instead."

If `workspace` is provided as a name (not ID), call `workspace-list` first to resolve it to an ID. The two windowing limits → `references/api-reference.md` § Hard API limits — two separate windows.

### Step 2 — Fetch meeting data

`meeting-list-put` accepts at most a **7-day window per call**. Split the requested range into 7-day (or shorter) chunks and issue one call per chunk:

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  status: ["Completed", "NoShow", "Active"]
  workspaceIds: [<resolved workspaceId>]   # include only if workspace was specified
  pagination:
    page: 0
    pageSize: 200
```

Results are in `response.data.list[]`. Paginate each chunk while `response.hasMore === "Yes"`, then merge and deduplicate on `meetingId`. The status filter rationale, envelope shape, `hasMore` string gotcha, and pagination → `references/api-reference.md` § Status values in `meeting-list-put` and § Hard API limits.

Classify each merged record and build the `meetingId → effective-status` map → `references/analysis-methodology.md` § Classify each merged meeting record.

### Step 3 — Fetch routing context (only for `trigger` or `route` grouping)

Skip this step if `group_by=rep` — rep is available directly from `meeting-list-put` via `hostId`/`hostEmail`/`hostName` (the host name is already included, so no separate lookup is needed).

**3a. List all routers:**
```
tool: concierge-list-routers
args:
  workspaceId: <resolved workspace ID, or omit for all>
```

Use `routers[N].router.id` as the routerId, `routers[N].router.name` for display, `routers[N].workspaceId` for the workspaceId.

**3b. For each router, fetch routing logs:**
```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601 start>
  end: <ISO-8601 end>
```

First filter to entries where `status = Scheduled` — only these reliably carry a `meetingId` to join on. Then extract `meetingId`, `trigger`, `matchedPath.route.type`, `sourceUrl`, `assignments[0].userId`, and join on `meetingId`. Field/status/trigger tables and the routing fields to extract → `references/api-reference.md` § Status values in `concierge-logs`, § Trigger types, § Routing fields to extract. Resolve `assignments[0].userId` to a name via `user-find-by-ids` if needed.

### Step 4 — Calculate the breakdown

Group by the selected dimension, compute per-group totals and rate, sort highest first, and flag groups at/above `flag_threshold`. Full procedure (formula, dimensions, low-sample handling) → `references/analysis-methodology.md` § No-show rate formula and § Build the breakdown by dimension.

### Step 5 — Hypotheses and recommended actions

For each flagged segment, produce 1–3 root-cause hypotheses, then 2–4 ranked testable actions → `references/analysis-methodology.md` § Root-cause hypotheses for flagged segments and § Recommended actions.

### Step 6 — Output

Exact layout → `references/output-format.md` § Template.

## Preflight audit

Verify before writing output:

- [ ] Required inputs resolved (workspace name → ID if provided).
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] `meeting-list-put` window ≤ 7 days per call; all chunks merged and deduped on `meetingId`.
- [ ] `status: ["Completed", "NoShow", "Active"]` passed (NOT `["Completed","NoShow"]` only).
- [ ] `Active` records split on start time; past-`Active` in denominator only, future-`Active` excluded.
- [ ] `concierge-logs` window ≤ 30 days, each call carried a `routerId`, and only `status = Scheduled` entries joined.
- [ ] Low-sample (<10 meetings) groups noted, not flagged on volume alone.

## Checkpoint

Present the summary, breakdown, flagged segments with hypotheses, and recommended actions, then stop for the human:

*"Which action do you want to test? I can help you document the baseline and set a 30-day review reminder."*

The human reviews the flagged segments and decides which routing rule or confirmation flow change to test first. This skill does not write anything; any Salesforce task is created by the human after reviewing.

## Data handling

- **PII present:** guest emails and rep emails used for grouping only, not displayed in output unless explicitly requested
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — reads only your org's data via your API key

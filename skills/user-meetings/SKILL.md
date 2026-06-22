---
name: user-meetings
description: Shows all meetings assigned to a specific rep for a period — volume, statuses, and no-show rate — to surface rep-level pipeline health and flag reps who may need coaching or routing changes
version: 0.4.0
references:
  - api-reference
  - output-format
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
api_note: "As of DISTRO-4472 (2026-05-21) meeting-export-v2-put supports these server-side filters (all confirmed live): hostIds, assigneeIds, bookerIds, meetingTypeIds, status. As of DISTRO-4483 (in production 2026-05-29) the export CSV now includes the `Booked At` and `Meeting ID` columns (verified live) — dedupe on `Meeting ID` and populate the Booked column from `Booked At`. Times displayed in local timezone detected via bash."
---

# User Meetings

You are a RevOps analyst and rep manager assistant. Your job is to pull all meetings assigned to a specific rep for a given period, calculate their health metrics, and flag patterns that warrant a manager conversation or a routing adjustment.

> **Prefer live data over training.** MCP field names and the export CSV schema change.
> Load `references/api-reference.md` before making MCP calls — it is the canonical
> field-name truth for this skill.

## When to use

- Someone asks how a specific rep is performing — meeting volume, completion, no-show rate.
- A manager wants to know whether a rep needs a coaching conversation or a routing change.
- You need to spot reps with zero or very low meeting volume (possible routing gap).

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `user` | ✅ | — | Email, name, or Chili Piper user ID of the rep to analyze |
| `date_range` | — | `last-30-days` | Period: `last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD` |
| `workspace` | — | org-wide | Workspace name or ID to scope to; omit for org-wide |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Resolve the user

```
tool: user-find
args:
  query: <user input (email or name)>
```

If multiple results, list them and ask the human to confirm. Store the resolved `userId`, `email`, and `name`. Field names → `references/api-reference.md` § Tools and what they return.

### Step 1b — Resolve workspace names

Always call `workspace-list` at the start. Build a `workspaceId → name` map. Never invent or guess workspace names. → `references/api-reference.md` § Workspace resolution.

### Step 1c — Detect local timezone

Detect the IANA timezone and convert all output timestamps to it. → `references/api-reference.md` § Local timezone detection.

### Step 2 — Fetch meetings per 7-day chunk

Parse the `date_range` input and slice it into windows strictly ≤ 6 days, then call `meeting-export-v2-put` once per chunk. Window limit, slicing rules, call shape, and CSV columns → `references/api-reference.md` § Hard API limits and § meeting-export-v2-put call shape.

Response: `{filename, data: "<CSV>"}`. Parse `data` as CSV — read the header row first to identify columns. Merge records across all chunks. Deduplicate on the `Meeting ID` column.

### Step 3 — Classify meetings

Use the `Status` column and split `Active` on the `When` time vs. now. Classification table and the past-Active caveat → `references/output-format.md` § Classify meetings.

### Step 4 — Calculate metrics

No-show rate and completion rate formulas → `references/output-format.md` § Calculate metrics.

### Step 5 — Detect anomalies

Apply the thresholds → `references/output-format.md` § Detect anomalies.

### Step 6 — Output

Exact layout → `references/output-format.md` § Output template.

## Preflight audit

Verify before writing output:

- [ ] `user` resolved to a single `userId`, `email`, and `name`.
- [ ] `workspace-list` called; `workspaceId → name` map built (never guess names).
- [ ] Local timezone detected; all timestamps converted to it.
- [ ] No `meeting-export-v2-put` call exceeds the 7-day window (chunks strictly ≤ 6 days).
- [ ] Records merged and deduped on the `Meeting ID` column.
- [ ] Field/column names taken from `references/api-reference.md`, not guessed.

## Checkpoint

Present the summary, anomalies, and meeting list, then stop for the human: *"Does this look like a coaching opportunity, a routing adjustment, or is the rep performing as expected? I can pull their routing assignments or compare them to the team average."* The human decides: coaching conversation, territory/routing adjustment, or no action.

## Data handling

- **PII present:** rep email and guest email used for lookup and grouping; not surfaced in output beyond display
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only

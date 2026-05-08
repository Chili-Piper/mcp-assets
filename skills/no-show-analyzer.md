---
name: no-show-analyzer
description: Analyzes Chili Piper meeting no-show patterns by lead source, route, rep, or workspace to surface actionable optimization opportunities for RevOps and Demand Gen
version: 0.1.0
inputs:
  - name: date_range
    type: string
    description: "Period to analyze: 'last-30-days', 'last-60-days', 'last-90-days', or 'YYYY-MM-DD:YYYY-MM-DD'"
    required: false
    default: "last-30-days"
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the analysis. Omit for org-wide."
    required: false
  - name: group_by
    type: string
    description: "Primary dimension to break down results: 'lead-source' | 'route' | 'rep' | 'workspace'"
    required: false
    default: "lead-source"
  - name: flag_threshold
    type: number
    description: "No-show rate (%) above which a segment is flagged as a problem. Default: 30."
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
    description: Specific routing, confirmation, or source-quality changes to test
tools_required: [chili-piper-mcp]
human_decision_point: "Review flagged segments and decide which routing rule or confirmation flow change to test first"
writes_to: "Salesforce (task or campaign update) — see Measurement section"
---

# No-Show Analyzer

You are a GTM data analyst with deep knowledge of Chili Piper's meeting routing and scheduling model. Your job is to pull meeting data for a given period, calculate no-show rates across one or more dimensions, flag problem segments, and give the human a clear set of actions to test.

## Step 1 — Resolve inputs

Parse the user's request for:
- `date_range` (default: last 30 days)
- `workspace` (default: all workspaces / org-wide)
- `group_by` dimension (default: lead-source)
- `flag_threshold` percent (default: 30%)

If any value is ambiguous, ask once before proceeding. Do not guess workspace names.

## Step 2 — Fetch meeting data

Call the Chili Piper MCP to retrieve meeting records for the resolved date range and workspace scope.

```
mcp: chili-piper
tool: get_meetings
args:
  date_from: <resolved start date, ISO 8601>
  date_to: <resolved end date, ISO 8601>
  workspace_id: <resolved workspace ID, or omit for org-wide>
  include_fields: [id, status, lead_source, route_name, assigned_rep_email, scheduled_at, meeting_type]
```

Valid `status` values you'll encounter:
- `completed` — meeting happened
- `no_show` — guest did not attend (the signal we care about most)
- `cancelled` — cancelled before the meeting (exclude from no-show rate calculation)
- `rescheduled` — treat as pending, exclude

**No-show rate formula:**
```
no_show_rate = no_shows / (completed + no_shows)
```
Cancelled and rescheduled meetings are excluded from the denominator — they did not reach the meeting.

If the MCP returns an error or empty results, tell the user clearly: what you requested, what was returned, and what they should check (workspace name, date range, API key permissions).

## Step 3 — Calculate the breakdown

Group meetings by the `group_by` dimension. For each group, calculate:
- Total meetings scheduled (completed + no_show)
- No-show count
- No-show rate (%)
- Trend direction if comparing two sub-periods within the range (first half vs second half)

Sort the breakdown table highest no-show rate first.

Flag any segment where `no_show_rate >= flag_threshold`.

## Step 4 — Generate root-cause hypotheses

For each flagged segment, produce 1–3 concise hypotheses based on what you know about GTM and Chili Piper routing. Structure each hypothesis as:

**Hypothesis:** [what's probably causing the high no-show rate]
**Signal to check:** [what the human should look at to confirm or rule it out]
**Likely fix:** [the specific routing, confirmation, or source-quality change to make]

Common root causes by dimension:
- **lead-source:** Paid social often has higher no-show rates than inbound organic; event leads from broad targeting; content downloads with no intent signal
- **route:** Routes missing SMS/email confirmation sequences; routes booking too far out (>5 days); round-robin routes where assigned rep doesn't get notified
- **rep:** Individual reps with low response-to-confirmation rates; new reps without calendar hygiene set up
- **workspace:** Workspaces using outdated confirmation email templates; workspaces without reminder sequences configured

## Step 5 — Recommend actions

Give 2–4 specific, testable actions ranked by expected impact. Each action should be:
- Scoped to a specific workspace, route, or source segment (not "improve all confirmations")
- Measurable within 30 days
- Ownable by RevOps with no engineering required

Format:

**Action [n] — [title]**
What to change: [specific change in Chili Piper]
Expected effect: [what should move and by how much]
How to measure: [the signal to watch]
Owner: RevOps / Demand Gen / Rep manager

## Step 6 — Format the output

Present results in this order:

### No-Show Analysis: [Date Range] | [Workspace or Org-wide] | Grouped by [Dimension]

**Summary**
| Metric | Value |
|--------|-------|
| Total meetings (excl. cancelled) | N |
| No-shows | N |
| Org no-show rate | N% |
| Flagged segments (>{threshold}%) | N |

**Breakdown**
| [Dimension] | Meetings | No-shows | No-show rate | Status |
|-------------|---------|----------|-------------|--------|
| [highest first] | | | | ⚠ Flagged / ✓ OK |

**Flagged segments**
[Root-cause hypotheses for each flagged segment]

**Recommended actions**
[2–4 actions as described in Step 5]

**Human decision point**
Ask the human: *"Which of these actions do you want to run as a test? I can help you draft the Salesforce task or update the routing rule description to track the experiment."*

## Measurement

This skill does not write to Salesforce automatically. Once the human picks an action to test:

1. Offer to create a Salesforce task on the relevant lead source campaign or rep record with:
   - The specific change being made
   - The baseline no-show rate
   - A 30-day follow-up date
2. After 30 days, the human re-runs this skill with the same parameters to compare the new no-show rate against the baseline.

This is the optimization loop: run → flag → fix → measure → repeat.

## Data handling

- **PII present:** rep email addresses (used for grouping only, not displayed in output unless the human asks)
- **Storage:** ephemeral — no meeting data is stored after the skill completes
- **No customer data:** this skill reads your own org's Chili Piper data via your API key

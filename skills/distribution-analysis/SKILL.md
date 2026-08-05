---
name: distribution-analysis
description: Analyzes a Chili Piper round-robin distribution for a workspace and date range — meeting counts by rep, imbalance vs. configured weights, day-of-week and source skew, and cancellations — interpreted against the workspace's fairness settings (credit-back, vacation calibration, reset period). Use when asked why a rep gets more or fewer meetings, or for a distribution breakdown.
version: 0.2.0
references:
  - api-reference
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
    description: The distribution's active members, weights, and assignment handling, plus the workspace fairness settings (credit-back, vacation calibration, reset period, tie-break order)
  - name: rep_breakdown
    description: Meeting counts by rep (total, completed, cancelled, no-show) with imbalance ratio
  - name: patterns
    description: Booking-source skew, day-of-week skew, weekly trend, and cancellation breakdown
  - name: recommendations
    description: Likely causes of imbalance and what to check
tools_required: [chili-piper-mcp]
human_decision_point: "Review the imbalance findings and decide whether to rebalance weights, fix calendar/availability for an under-booked rep, or adjust the distribution in the router builder"
writes_to: "Nothing — read-only diagnostic. Apply any rebalancing in the Chili Piper router builder (or via distribution-adjust-v3 with explicit human approval)."
---

# Distribution Analysis

You are a RevOps analyst. Pull a Chili Piper distribution's configuration and the meetings its member reps hosted over a date range, then surface imbalance patterns and likely causes — using only the public Chili Piper MCP.

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill.

> **Scope & honesty.** The public MCP cannot filter meetings by `distributionId` and has no distribution config-history endpoint (current settings are readable via `distribution-workspace-settings-get`, but not their change history). This skill attributes meetings to a distribution by its **member reps (host)**. If a rep belongs to multiple distributions, their meetings count toward each — state this caveat in the output. For exact per-distribution routing attribution, use the routing logs (`/audit-routing`, `concierge-logs`).

## When to use

- Someone asks why a rep is getting more or fewer meetings than others.
- Someone wants a distribution breakdown (counts by rep, imbalance vs. weights).
- Someone wants to analyze meeting imbalance for a workspace over a period.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | ✅ | — | Workspace name or ID containing the distribution. |
| `distribution` | ✅ | — | Distribution name (substring) or distributionId to analyze. |
| `start_date` | ✅ | — | Start of range, inclusive (e.g. 2026-05-01). |
| `end_date` | ✅ | — | End of range, exclusive (e.g. 2026-06-01 = through May 31). |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Resolve the workspace

If `workspace` is a name, call `workspace-list` and match on `name`; use its `id`.

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

### Step 2 — Find the distribution and read its config

```
tool: distribution-list-put
args:
  workspaceIds: [<workspace.id>]
  name: <distribution>          # omit if you were given a distributionId; filter the array instead
```

Extract name, active members, weights, handling/algorithm, capping, and per-member
period statistics from the matching item; derive the per-rep ideal number. If no
distribution matches, say so and list the available distribution names in the
workspace. Config fields, period statistics, and the `idealNumber` derivation →
`references/api-reference.md` § distribution-list-put — config fields and
§ distribution-list-put — period statistics (authoritative totals).

### Step 3 — Read the workspace fairness settings

```
tool: distribution-workspace-settings-get
args:
  workspaceId: <workspace.id>
```

These workspace-level settings shape the round-robin leveling equation on top of the
distribution's weights, and are shared by every distribution in the workspace. Read
them before interpreting the statistics — never assume the leveling rules. In
particular, `resetPeriodicity` defines the **current distribution period** that the
`statistics` from Step 2 cover. Field meanings and how each setting changes the
analysis → `references/api-reference.md`
§ distribution-workspace-settings-get — workspace fairness settings.

### Step 4 — Resolve member names

Collect the active member `userId`s and resolve them to names/emails:

```
tool: user-find-by-ids
args:
  userIds: [<userId>, <userId>, ...]
```

Build a `userId → name` map for display. Never show raw user IDs in the final output.

### Step 5 — Pull meetings hosted by the members

`meeting-list-put` has a 7-day maximum window. Split `[start_date, end_date)` into
≤7-day chunks and call once per chunk, paginating while `hasMore === "Yes"`. Merge all
chunks, dedupe on `meetingId`, then **keep only meetings whose `hostId` is one of the
distribution's active members** and classify each kept meeting. Windowing, pagination,
and the status classification → `references/api-reference.md` § Hard API limits and
§ meeting-list-put — classification and pattern fields.

### Step 6 — Build the rep breakdown and detect imbalance

Use two complementary sources, interpreted against the fairness settings from Step 3.

**From `statistics` (distribution API, current period — authoritative totals):**
use `assigned` as the primary volume metric, plus `cancelled`, `noShow`, and the
`reassignedToThis` / `reassignedFromThis` rebalancing context (statistic field
meanings and the effective-total formula → `references/api-reference.md`
§ distribution-list-put — period statistics (authoritative totals)). State what
period these totals cover, from `resetPeriodicity` (e.g. "since the start of the
quarter"; `Never` = all-time).

**Interpret through the fairness settings (avoid false findings):**
- **Credit-back on** (`creditBackCancelled` / `creditBackNoShow` true): a rep with
  many cancels or no-shows is re-credited and legitimately receives *more* new
  assignments — a high `assigned` for a high-cancel rep is the leveling working,
  not a routing bug. With credit-back **off**, cancels permanently consume that
  rep's share, so a high cancel rate directly explains an under-delivery gap.
- **Vacation calibration on** (`calibrateVacation` true): a rep returning from
  vacation was excused from the fairness penalty — a temporary post-vacation
  catch-up (or lower totals) is expected, not an availability blocker.
- **Analysis window vs. reset period:** if `[start_date, end_date)` doesn't align
  with the reset period, expect `statistics` totals and the meeting-list counts to
  diverge — say so rather than flagging phantom imbalance.

**Derived from statistics:**
- **Ideal number:** `(userWeight / totalWeight) × totalAssigned` — the fair-share target for each rep given their configured weight
- **Imbalance ratio:** top rep's `assigned` ÷ median rep's `assigned`
- **Vs. configured weight:** compare each rep's `assigned / totalAssigned` to their `weight / totalWeight`. A rep with a high weight share but low `assigned` share (or vice versa) is the headline finding.

**From `meeting-list-put` (date-range data — for patterns):** day-of-week skew,
booking source, weekly trend (meetings per rep per week — did a gap open at a specific
week?), and cancellation breakdown. Which fields carry these patterns →
`references/api-reference.md` § meeting-list-put — classification and pattern fields.

Flag reps with 0 `assigned` (likely calendar/availability issue — suggest
`/check-availability`) and reps whose `assigned / totalAssigned` share diverges sharply
from their `weight / totalWeight` share.

### Step 7 — Output

Lead with the config (including the fairness settings line) + rep breakdown, then
patterns, then recommendations. Include the attribution caveat whenever a member
belongs to more than one distribution. Exact layout → `references/output-format.md`.

## Preflight audit

Verify before writing output:

- [ ] Required inputs present and resolved (`workspace` → `id`, `distribution` → matching item).
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] Workspace fairness settings fetched (`distribution-workspace-settings-get`) and reflected in the analysis; the reset period stated alongside the period statistics.
- [ ] `meeting-list-put` calls each span ≤ 7 days and are fully paginated (`hasMore === "No"`).
- [ ] Meetings filtered to active-member `hostId`s and deduped on `meetingId`.
- [ ] `idealNumber` derived client-side; user IDs resolved to names (no raw IDs shown).
- [ ] Multi-distribution attribution caveat included when any member is in >1 distribution.

## Checkpoint

This is a read-only diagnostic. Present the config, rep breakdown, patterns, and
recommendations, then stop and let the human decide: rebalance weights, fix
calendar/availability for an under-booked rep, or adjust the distribution in the router
builder. Applying any rebalancing requires the router builder, or
`distribution-adjust-v3` with the human's explicit go-ahead since it publishes
immediately.

## Data handling

- **PII present:** rep names/emails and guest data in meetings — used for analysis; display rep names, not guest details, unless asked
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only. Apply rebalancing manually, or via `distribution-adjust-v3` only with explicit human approval (it publishes immediately).

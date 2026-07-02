---
name: availability-inspector
description: Checks why a rep or team is showing no available slots — diagnoses calendar connectivity, working hours, meeting limits, and distribution membership to find the specific blocker
version: 0.1.2
references:
  - api-reference
  - diagnostics
  - output-format
inputs:
  - name: user
    type: string
    description: "Email, name, or user ID of the rep to check availability for"
    required: true
  - name: workspace
    type: string
    description: "Workspace name or ID to scope team/distribution lookup"
    required: false
  - name: lookahead_days
    type: number
    description: "How many days ahead to check for slots (default: 14)"
    required: false
    default: 14
outputs:
  - name: availability_result
    description: Whether slots were found, and in what quantity
  - name: per_day_breakdown
    description: Slot count per calendar day across the window (includes zero-slot days), surfacing working-hours patterns and gaps
  - name: diagnosis
    description: Specific blocker identified with root cause (based on user profile and empty-results pattern; v2 API no longer returns per-user failure codes)
  - name: fix
    description: Step-by-step resolution for the human
tools_required: [chili-piper-mcp]
human_decision_point: "Review the diagnosis and fix the blocker — most causes require action in Chili Piper admin, Google/Outlook calendar settings, or Zoom/Teams reconnection"
writes_to: "Nothing — read-only diagnostic"
---

# Availability Inspector

You are a Chili Piper calendar specialist. A rep or team is showing no available slots — your job is to call the availability API, check the results, and translate any blockers into a plain-language diagnosis and a specific fix.

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill.

## When to use

- A rep or team is reportedly showing no available slots in a scheduling link, distribution, or router.
- You need to find the *specific* blocker (calendar, working hours, meeting limit, distribution membership) rather than just confirm "no slots."
- You want a per-day availability breakdown to spot working-hours patterns and gaps.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `user` | ✅ | — | Email, name, or user ID of the rep to check |
| `workspace` | — | — | Scopes team/distribution lookup |
| `lookahead_days` | — | `14` | How many days ahead to check for slots |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Resolve the user

```
tool: user-find
args:
  query: <user input>
```

If zero results: stop. If multiple: ask the human to confirm.

### Step 2 — Check user profile for obvious blockers

```
tool: user-read
args:
  userId: <resolved user ID>
```

`user-read` does NOT return calendar status — it is not available from this endpoint.
Run the license check and proceed to Step 3 if the user looks valid.
Response shape + license-check rule → `references/api-reference.md` § user-read note.

### Step 3 — Call availability-slots-v2

Build the request from the verified shape (object `expectedHost`, attendee `type` +
`required`; `meetingTypeRef` is **not needed in v2** — omit it). To find a single rep's
blocker, query just that rep as a `required: true` `ManuallyAssigned` attendee; for a team,
a slot is only returned when ALL `required: true` attendees are free simultaneously, so an
empty result may reflect any one member blocking.

- Request shape + field rules → `references/api-reference.md` § availability-slots-v2 request shape and § Critical field-name rules.
- Pagination (`page` / `pageSize`, no slot cap) → `references/api-reference.md` § Pagination.

### Step 4 — Interpret the result

Read `results` and `total`. `availability-slots-v2` does **not** return a `failures` map —
when `results` is empty, work through the common-causes checklist to diagnose, and for team
queries re-query each member individually to find the blocker. When slots ARE returned,
build the per-day breakdown.

- Causes checklist + multi-user rules + per-day signals → `references/diagnostics.md` § Common-causes checklist, § Multi-user (team) availability, § Per-day breakdown signals.

### Step 5 — Output

Exact layout → `references/output-format.md` § Template.

## Preflight audit

Verify before writing output. Every line must be a clear pass/fail:

- [ ] `user` resolved to a single user ID (Step 1 returned exactly one match, or the human confirmed).
- [ ] Field names taken from `references/api-reference.md`, not guessed (object `expectedHost`, attendee `type` + `required`; no `meetingTypeRef` in v2).
- [ ] All pages retrieved when `total` exceeds `pageSize` (increment `page` from 0).
- [ ] When `results` was empty, the common-causes checklist was worked through and the diagnosis notes that v2 returns no per-user failure codes.
- [ ] Per-day breakdown included whenever slots were returned (zero-slot days present; partial days labelled).

## Checkpoint

Present the diagnosis and the step-by-step fix, then stop for the human. Most causes require
action outside this tool (Chili Piper admin, Google/Outlook calendar settings, or
Zoom/Teams reconnection), so let the human decide the next step:

*"Should I check the rest of the team, or does this fix cover the routing issue you're seeing?"*

## Data handling

- **PII present:** user email used for lookup and display
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only diagnostic

---
name: meeting-inspector
description: Deep-dives into a single Chili Piper meeting — booking trigger, routing path, rep assignment, and outcome — to diagnose what happened and surface a next action.
version: 0.3.0
references:
  - api-reference
  - routing-trace
  - anomaly-detection
  - output-format
inputs:
  - name: meeting_id
    type: string
    description: "Chili Piper meeting ID. Provide this OR guest_email."
    required: false
  - name: guest_email
    type: string
    description: "Guest email. Used to find their most recent meeting when meeting_id is unknown."
    required: false
  - name: date_range
    type: string
    description: "Search window when using guest_email: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD'."
    required: false
    default: "last-30-days"
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the search. Omit for org-wide."
    required: false
outputs:
  - name: meeting_summary
    description: Core facts — status, scheduled time, guest, assigned rep, booking timestamp
  - name: routing_trace
    description: Full path from trigger to assignment — trigger type, router, matched rule, source URL
  - name: anomalies
    description: Flags for issues detected (no-show, late cancellation, rep mismatch, routing fallthrough)
  - name: recommended_action
    description: Suggested next step for the human based on what happened
tools_required: [chili-piper-mcp]
human_decision_point: "Review anomalies and decide: rebook, follow up with guest, or fix the underlying routing rule"
writes_to: "Nothing — read-only diagnostic tool"
---

# Meeting Inspector

You are a GTM diagnostic analyst. Reconstruct the full lifecycle of a single meeting — how the lead arrived, which router and rule matched, who got assigned, and what the outcome was. Flag anything wrong and recommend a next step.

> **Prefer live data over training.** Chili Piper's field names and tool signatures change. Always load `references/api-reference.md` before making MCP calls — it documents exact field names, status values, and known gotchas.

## When to use

- A rep says "a meeting went wrong — can you check what happened?"
- You need to understand why a lead was (or wasn't) assigned to a specific rep
- Investigating a no-show or late cancellation
- Auditing whether CRM write-backs fired correctly after a booking

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `meeting_id` | — | — | Chili Piper meeting ID. Provide this OR `guest_email`. |
| `guest_email` | — | — | Guest email; used to find their most recent meeting when `meeting_id` is unknown. |
| `date_range` | — | `last-30-days` | Search window when using `guest_email`: `last-7-days`, `last-30-days`, or `YYYY-MM-DD:YYYY-MM-DD`. |
| `workspace` | — | org-wide | Workspace name or ID to scope the search. Omit for org-wide. |

Provide either `meeting_id` or `guest_email`. If neither is given, ask for it in one sentence rather than guessing.

## Quick API reference

| Tool | What it returns |
|------|----------------|
| `meeting-get` | Single meeting by ID — full detail |
| `meeting-list-put` | Paginated meetings by date range (max 7 days per call) |
| `concierge-list-routers` | All routers in a workspace |
| `concierge-logs` | Routing decisions per router (max 30-day window) |
| `workspace-list` | All workspaces |

See `references/api-reference.md` for full field names, status codes, trigger types, and known gotchas.

## Process

### Step 1 — Validate inputs and locate the meeting

Provide either `meeting_id` or `guest_email`. If neither is given, ask:
*"Which meeting should I inspect? Provide a meeting ID or the guest's email address."*

If `workspace` is a name (not ID), resolve it via `workspace-list`.

- **Path A** (`meeting_id`): call `meeting-get` directly.
- **Path B** (`guest_email`): chunk `date_range` into ≤7-day windows and call `meeting-list-put` per chunk. Stop as soon as a match is found. If multiple meetings match, show a numbered list and ask which one to inspect.

Tool envelopes and the 7-day window → `references/api-reference.md` § Hard API limits.

### Step 2 — Build the meeting summary

Extract: meeting ID, status, scheduled time, booked-at, lead time, guest email, assigned rep.

Both tools use `meetingStatus`, but the meeting-id and time fields differ between them (`meetingId`/`dateTime.start` in list vs `id`/`activities[]` in get). Correct field names → `references/api-reference.md` § Critical field name differences; per-field sources → `references/api-reference.md` § Meeting summary fields.

Lead time interpretation: < 2 h (same-day), 2–24 h (next-day), 1–3 d (short), 4–7 d (standard), > 7 d (long — elevated no-show risk).

### Step 3 — Fetch the routing trace

Skip if the meeting's `bookedAt` is > 30 days ago; note this in output.

Full step-by-step procedure including how to match a log entry to the meeting → `references/routing-trace.md` § Matching a log entry to the meeting.

### Step 4 — Detect anomalies

Complete anomaly table and severity levels → `references/anomaly-detection.md` § Anomaly table.

### Step 5 — Recommend a next action

- **NoShow** → suggest rebook link within 2 hours; note if long lead time contributed
- **Late cancellation** → check whether guest or rep cancelled; suggest agenda clarity for low-intent leads
- **Rep mismatch** → check Salesforce ownership staleness
- **Routing fallthrough** → audit router rules for this lead's profile
- **Completed, no anomalies** → "No issues detected."

### Step 6 — Output

Exact table structure → `references/output-format.md` § Template.

## Preflight audit

Verify before writing output (this skill is read-only — no mutation step):

- [ ] Exactly one meeting is resolved (either `meeting_id` given, or a single `guest_email` match chosen).
- [ ] Workspace name resolved to an ID via `workspace-list` when `workspace` was a name.
- [ ] Field names taken from `references/api-reference.md`, not guessed (`meetingStatus`, `meetingId`/`id`, `dateTime.start`, `hostId`/`hostEmail`/`hostName`).
- [ ] No `meeting-list-put` call spans more than 7 days; no `concierge-logs` call spans more than 30 days.
- [ ] Routing trace either populated, or explicitly noted as unavailable (>30 days) / no-log-found.
- [ ] Every anomaly row in `references/anomaly-detection.md` § Anomaly table was checked.

## Checkpoint

This is a read-only diagnostic: present the meeting summary, routing trace, anomalies, and a single recommended action, then stop. Let the human decide the next step — **review anomalies and decide: rebook, follow up with guest, or fix the underlying routing rule.** Do not act on the recommendation yourself.

## Data handling

- **PII present:** guest email, rep email
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — read-only

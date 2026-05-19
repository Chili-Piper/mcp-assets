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

## Quick API reference

| Tool | What it returns |
|------|----------------|
| `meeting-get` | Single meeting by ID — full detail |
| `meeting-list-put` | Paginated meetings by date range (max 7 days per call) |
| `concierge-list-routers` | All routers in a workspace |
| `concierge-logs` | Routing decisions per router (max 30-day window) |
| `workspace-list` | All workspaces |

See `references/api-reference.md` for full field names, status codes, trigger types, and known gotchas.

## Steps

### Step 1 — Validate inputs and locate the meeting

Provide either `meeting_id` or `guest_email`. If neither is given, ask:  
*"Which meeting should I inspect? Provide a meeting ID or the guest's email address."*

If `workspace` is a name (not ID), resolve it via `workspace-list`.

- **Path A** (`meeting_id`): call `meeting-get` directly.
- **Path B** (`guest_email`): chunk `date_range` into ≤7-day windows and call `meeting-list-put` per chunk. Stop as soon as a match is found. If multiple meetings match, show a numbered list and ask which one to inspect.

### Step 2 — Build the meeting summary

Extract: meeting ID, status, scheduled time, booked-at, lead time, guest email, assigned rep.

See `references/api-reference.md` for the correct field names — `meeting-list-put` and `meeting-get` use *different* field names for status.

Lead time interpretation: < 2 h (same-day), 2–24 h (next-day), 1–3 d (short), 4–7 d (standard), > 7 d (long — elevated no-show risk).

### Step 3 — Fetch the routing trace

Skip if `createdAt` > 30 days ago; note this in output.

See `references/routing-trace.md` for the full step-by-step procedure including how to match a log entry to the meeting.

### Step 4 — Detect anomalies

See `references/anomaly-detection.md` for the complete anomaly table and severity levels.

### Step 5 — Recommend a next action

- **NoShow** → suggest rebook link within 2 hours; note if long lead time contributed
- **Late cancellation** → check whether guest or rep cancelled; suggest agenda clarity for low-intent leads
- **Rep mismatch** → check Salesforce ownership staleness
- **Routing fallthrough** → audit router rules for this lead's profile
- **Completed, no anomalies** → "No issues detected."

### Step 6 — Output

See `references/output-format.md` for the exact table structure.

## Data handling

- **PII present:** guest email, rep email
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — read-only

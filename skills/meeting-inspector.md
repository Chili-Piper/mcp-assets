---
name: meeting-inspector
description: Deep-dives into a single Chili Piper meeting — booking trigger, routing path, rep assignment, and outcome — to diagnose what happened and surface a next action
version: 0.1.0
inputs:
  - name: meeting_id
    type: string
    description: "Chili Piper meeting ID. Provide this OR guest_email — not both required."
    required: false
  - name: guest_email
    type: string
    description: "Guest email address. Used to find their most recent meeting when meeting_id is unknown."
    required: false
  - name: date_range
    type: string
    description: "Search window when using guest_email: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD' (max 30-day span)"
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
api_note: "concierge-logs requires a routerId and has a 30-day maximum window. Routing trace is unavailable for meetings older than 30 days — meeting_summary and anomalies still work."
---

# Meeting Inspector

You are a GTM diagnostic analyst with deep knowledge of Chili Piper's booking and routing model. Your job is to reconstruct the full lifecycle of a single meeting — how the lead arrived, which router and rule matched, who got assigned, and what the outcome was — then flag anything that looks wrong and recommend a next step.

## API reference (actual MCP tool names)

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings — `id`, `status`, `startTime`, `assignee` (name, email), `guest` (email), `createdAt` |
| `meeting-get` | GET | Single meeting by ID — full detail including `id`, `status`, `startTime`, `assignee`, `guest`, `createdAt` |
| `concierge-list-routers` | GET | All routers — `id`, `name`, `slug`, `workspaceId` |
| `concierge-logs` | POST | Routing decisions per router — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl` |
| `workspace-list` | GET | All workspaces — `id`, `name`, `userCount` |

**Status values:**
- `Scheduled` — upcoming, not yet occurred
- `Completed` — meeting happened
- `NoShow` — guest did not attend
- `Cancelled` — meeting was cancelled

---

## Step 1 — Validate inputs and locate the meeting

At least one of `meeting_id` or `guest_email` must be provided. If neither is given, ask the user: *"Which meeting should I inspect? Provide a meeting ID or the guest's email address."*

If `workspace` is provided as a name (not ID), call `workspace-list` to resolve it to an ID.

**Path A — meeting_id provided:**

```
tool: meeting-get
args:
  meetingId: <meeting_id>
```

If the call returns a 404 or empty result, report: *"No meeting found with ID `<meeting_id>`. Check the ID and try again."* Stop.

**Path B — guest_email provided (no meeting_id):**

```
tool: meeting-list-put
args:
  start: <ISO-8601 start of date_range>
  end: <ISO-8601 end of date_range>
  page: 0
  pageSize: 50
```

Filter results to rows where `guest.email` matches `guest_email` (case-insensitive). If multiple meetings match, show a numbered list and ask the user to pick one before continuing:

```
Multiple meetings found for <guest_email>:
1. <date> — <status> — assigned to <rep>
2. <date> — <status> — assigned to <rep>

Which meeting should I inspect? (enter a number)
```

If zero matches, report: *"No meetings found for `<guest_email>` in the requested window."* Stop.

---

## Step 2 — Build the meeting summary

From the meeting record, extract:

| Field | Source |
|-------|--------|
| Meeting ID | `id` |
| Status | `status` |
| Scheduled time | `startTime` |
| Booked at | `createdAt` |
| Lead time | `startTime` minus `createdAt` (hours/days) |
| Guest email | `guest.email` |
| Assigned rep | `assignee.name` + `assignee.email` |

**Lead time interpretation:**
- < 2 hours — same-day booking (high urgency signal)
- 2–24 hours — next-day
- 1–3 days — short window
- 4–7 days — standard window
- > 7 days — long window (higher no-show risk)

---

## Step 3 — Fetch the routing trace

Skip if the meeting's `createdAt` is more than 30 days ago — note this in the output.

**3a. List routers:**
```
tool: concierge-list-routers
args:
  workspaceId: <resolved workspace ID, or omit for all>
```

**3b. For each router, fetch logs and look for this meeting:**
```
tool: concierge-logs
args:
  workspaceId: <router's workspaceId>
  routerId: <router id>
  start: <ISO-8601 — use 1 day before meeting's createdAt>
  end: <ISO-8601 — use 1 day after meeting's createdAt>
```

Search for a log entry where `meetingId` matches the target meeting's ID, OR where `guestEmail` matches and `triggeredAt` is within a few hours of `createdAt`.

If a match is found, extract:
- `trigger` — how the lead arrived (e.g. `ThirdPartyForm`, `Direct`, `Email`)
- `matchedPath` — the routing rule that fired (e.g. `Ownership Rule`, `Round Robin`)
- `sourceUrl` — the page the lead came from
- `assignments[0].name` — the rep the router assigned
- `triggeredAt` — when the router ran

**If no routing log is found**, note: *"No routing log found for this meeting — it may have been booked via direct link or manual scheduling outside a router."*

---

## Step 4 — Detect anomalies

Check for each of the following and flag any that are true:

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| **No-show** | `status = NoShow` | High |
| **Late cancellation** | `status = Cancelled` AND cancellation within 2 hours of `startTime` | Medium |
| **Long lead time + no-show** | Lead time > 5 days AND `status = NoShow` | High — recency decay likely |
| **Rep assignment mismatch** | `assignments[0].name` from routing log ≠ `assignee.name` from meeting record | High — meeting was reassigned after routing |
| **Routing fallthrough** | `matchedPath` is null or blank | Medium — hit catch-all or no rule matched |
| **Unrouted meeting** | No routing log found at all | Low — may be manual or direct-link booking |

For each flagged anomaly, include one sentence explaining what it means in plain language.

---

## Step 5 — Recommend a next action

Based on status and anomalies, select the most relevant action:

**If `NoShow`:**
> Suggest a follow-up sequence: send a rebook link within 2 hours of the missed meeting. If the routing log shows `ThirdPartyForm` or long lead time, note that shortening the booking window or adding an SMS reminder may reduce recurrence.

**If `Cancelled` (late):**
> Suggest checking whether the cancellation came from the guest or the rep. If guest-initiated within 2 hours, ask if the booking confirmation email included a clear agenda — low-intent leads cancel when they don't remember why they booked.

**If rep assignment mismatch:**
> Suggest checking the Salesforce ownership record for the guest's account — stale ownership data is the most common cause. If the original rep was correct, investigate why the meeting was manually reassigned.

**If routing fallthrough:**
> Suggest auditing the router's rule coverage for this lead's profile. Check `sourceUrl` to see which page the lead came from and whether a rule covers that source.

**If `Completed` with no anomalies:**
> No issues detected. Meeting completed as expected.

---

## Step 6 — Output format

### Meeting Inspector: `<guest_email or meeting_id>`

**Meeting Summary**

| Field | Value |
|-------|-------|
| Meeting ID | |
| Status | |
| Scheduled | |
| Booked at | |
| Lead time | |
| Guest | |
| Assigned rep | |

**Routing Trace**

| Field | Value |
|-------|-------|
| Trigger | |
| Router | |
| Matched rule | |
| Source URL | |
| Router assigned | |
| Routed at | |

*(or: "Routing trace unavailable — meeting is older than 30 days" / "No routing log found")*

**Anomalies**

| Flag | Severity | Detail |
|------|----------|--------|
| ... | High / Medium / Low | ... |

*(or: "No anomalies detected.")*

**Recommended action**

> [One paragraph recommendation]

**Human decision point**

*"What would you like to do — rebook the guest, follow up, or look at the underlying routing rule?"*

---

## Data handling

- **PII present:** guest email and rep email are used for lookup and display; handle with care
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — this skill is read-only

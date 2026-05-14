---
name: meeting-inspector
description: Deep-dives into a single Chili Piper meeting — booking trigger, routing path, rep assignment, and outcome — to diagnose what happened and surface a next action
version: 0.2.0
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
    description: "Search window when using guest_email: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD'. Note: meeting-list-put is chunked into 7-day calls automatically; concierge-logs for routing trace caps at 30 days."
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
api_note: "meeting-list-put has a strict 7-day maximum window per call — Path B chunks automatically. concierge-logs has a separate 30-day maximum window; routing trace is unavailable for meetings older than 30 days. meeting-get returns the status field as 'meetingStatus', not 'status' — use 'meetingStatus' when parsing meeting-get responses. meeting-list-put response envelope is {data: {list: [...]}, hasMore: 'Yes'|'No'}; meeting items use 'meetingId' (not 'id'), 'scheduledAt' (not 'startTime'), 'assignedUserId' (not 'assignee'); paginate by checking hasMore === 'Yes' (string, not boolean). concierge-list-routers nests routerId at routers[N].router.id, slug at routers[N].router.slug, workspaceId at routers[N].workspaceId."
---

# Meeting Inspector

You are a GTM diagnostic analyst with deep knowledge of Chili Piper's booking and routing model. Your job is to reconstruct the full lifecycle of a single meeting — how the lead arrived, which router and rule matched, who got assigned, and what the outcome was — then flag anything that looks wrong and recommend a next step.

## API reference (actual MCP tool names)

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings — response envelope `{data: {list: [...]}, hasMore: "Yes"\|"No"}`. Items in `data.list[]`: `meetingId`, `status`, `scheduledAt`, `assignedUserId`, `workspaceId`, `attendees` (array). Paginate by checking `hasMore === "Yes"` (string). |
| `meeting-get` | GET | Single meeting by ID — full detail including `id`, `meetingStatus`. Scheduled time is in the `activities` array (no top-level `startTime` or `scheduledAt`). |
| `concierge-list-routers` | GET | All routers — response: `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. Access: `routerId` at `routers[N].router.id`, `slug` at `routers[N].router.slug`, `workspaceId` at `routers[N].workspaceId`. |
| `concierge-logs` | POST | Routing decisions per router — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl`, `actionsStatus` |
| `workspace-list` | GET | All workspaces — `[{workspaceId, name, settings}]` (items use `workspaceId`, not `id`) |

**Field name gotchas:**
- `meeting-list-put` returns status as `status`; `meeting-get` returns it as `meetingStatus`. Use the correct field name for each tool.
- `meeting-list-put` items use `meetingId` (not `id`), `scheduledAt` (not `startTime`), and `assignedUserId` (not `assignee`). To resolve a name/email from `assignedUserId`, call `user-find-by-ids`.
- Guest information in `meeting-list-put` items is in the `attendees` array, not a top-level `guest` field.
- `concierge-list-routers` nests router fields: use `routers[N].router.id` for routerId, `routers[N].router.slug` for slug, `routers[N].workspaceId` for workspaceId.

**Meeting status values (meeting-list-put `status` / meeting-get `meetingStatus`):**
| Value | Meaning |
|-------|---------|
| `Scheduled` | Upcoming, not yet occurred |
| `Completed` | Meeting happened |
| `NoShow` | Guest did not attend |
| `Cancelled` | Meeting was cancelled |

**Concierge-log status values (routing session outcome):**
| Value | Has `meetingId`? | Meaning |
|-------|----------------|---------|
| `Booked` | ✓ Yes | Lead completed booking — meetingId matches meeting records |
| `Offered` | ✗ No | Calendar was shown but lead did not book |
| `NoMatch` | ✗ No | No routing rule matched the lead |
| `NotQualified` | ✗ No | Lead was disqualified (spam check, ICP filter, or explicit disqualify rule) |
| `Timeout` | ✗ No | Routing session (30-min TTL) expired before lead booked |
| `Error` | ✗ No | Technical error during routing — escalate to engineering |

**Trigger types in concierge-logs:**
| Value | What it means |
|-------|--------------|
| `ThirdPartyForm` | Web form submission (Marketo, HubSpot, Pardot, HTML form) |
| `Direct` | Prospect visited the router URL directly |
| `Email` | Scheduling link embedded in an email |
| `RouterLink` | Router link shared via a direct URL |
| `InApp` | In-product trigger (SaaS product-embedded booking) |

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

`meeting-list-put` accepts at most a **7-day window per call**. Split the `date_range` into 7-day (or shorter) chunks and issue one call per chunk. Stop as soon as a match is found — no need to fetch the full period if the meeting appears early.

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  pagination:
    page: 0
    pageSize: 50
```

Results are in `response.data.list[]`. Each item uses `meetingId` (not `id`). Search each chunk for rows where the guest email appears anywhere in the `attendees` array (case-insensitive email match). Paginate within each chunk by checking `hasMore === "Yes"` (string comparison). Deduplicate across chunks on `meetingId`.

If multiple meetings match across chunks, show a numbered list and ask the user to pick one before continuing:

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

| Field | Source (meeting-list-put) | Source (meeting-get) |
|-------|--------------------------|---------------------|
| Meeting ID | `meetingId` | `id` |
| Status | `status` | `meetingStatus` ← different field name |
| Scheduled time | `scheduledAt` | in `activities` array (no top-level field) |
| Booked at | uncertain — may be in `activities` | in `activities` array |
| Lead time | `scheduledAt` minus booking timestamp (if available) | derive from `activities` |
| Guest email | from `attendees` array (email match) | from `activities` or attendee fields |
| Assigned rep | `assignedUserId` → resolve via `user-find-by-ids` | from meeting detail fields |

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

The response is `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. When iterating, use `routers[N].router.id` as the routerId, `routers[N].router.name` for display, `routers[N].router.slug` for the slug, and `routers[N].workspaceId` for the workspace.

**3b. For each router, fetch logs and look for this meeting:**
```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601 — use 1 day before meeting's scheduled/booking time>
  end: <ISO-8601 — use 1 day after meeting's scheduled/booking time>
```

Search for a log entry where `meetingId` matches the target meeting's ID, OR where `guestEmail` matches and `triggeredAt` is within a few hours of `createdAt`.

If a match is found, extract:
- `status` — the routing session outcome (see status table above; expect `Booked` for a completed meeting)
- `trigger` — how the lead arrived (see trigger types table above)
- `matchedPath` — the routing rule that fired (e.g. `CrmOwnership`, `WithoutOwnership`, `CatchAll`)
- `sourceUrl` — the page the lead came from
- `assignments[0].name` — the rep the router assigned
- `triggeredAt` — when the router ran
- `actionsStatus` — result of CRM write actions (e.g. Salesforce task creation, campaign association); a failure here means the meeting exists in CP but may not be visible in Salesforce

**If log status is not `Booked`:** this is unusual for an existing meeting — report the status and meaning (e.g. "Routing log shows `Offered` — the lead was shown a calendar but did not complete booking. The meeting record may have been created via another path.").

**If no routing log is found**, note: *"No routing log found for this meeting — it may have been booked via a direct scheduling link, manual booking, or handoff rather than a concierge router."*

---

## Step 4 — Detect anomalies

Check for each of the following and flag any that are true:

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| **No-show** | `status = NoShow` | High |
| **Late cancellation** | `status = Cancelled` AND cancellation within 2 hours of `scheduledAt` (from meeting-list-put) or scheduled time in activities (from meeting-get) | Medium |
| **Long lead time + no-show** | Lead time > 5 days AND `status = NoShow` | High — recency decay likely |
| **Rep assignment mismatch** | `assignments[0].name` from routing log ≠ resolved name for `assignedUserId` from meeting-list-put (or rep fields from meeting-get) | High — meeting was reassigned after routing |
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
| CRM actions status | |

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

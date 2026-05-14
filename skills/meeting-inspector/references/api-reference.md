# Meeting Inspector — API Reference

Full field names, status codes, and known gotchas for the Chili Piper MCP tools used by this skill.

> Field names and response envelopes are validated against live MCP responses. Training data is often wrong — use this file, not intuition.

---

## Tools and what they return

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings — response envelope `{data: {list: [...]}, hasMore: "Yes"\|"No"}`. Items in `data.list[]` use `meetingId`, `status`, `scheduledAt`, `assignedUserId`, `workspaceId`, `attendees[]`. |
| `meeting-get` | GET | Single meeting by ID — `id`, **`meetingStatus`**. Scheduled time is in the `activities` array (no top-level `startTime` or `scheduledAt`). |
| `concierge-list-routers` | GET | All routers — `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. Access routerId at `routers[N].router.id`, slug at `routers[N].router.slug`, workspaceId at `routers[N].workspaceId`. |
| `concierge-logs` | POST | Routing decisions — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl`, `actionsStatus` |
| `workspace-list` | GET | All workspaces — `[{workspaceId, name, settings}]` (items use `workspaceId`, not `id`; no `userCount` field) |

---

## Critical field name differences

| Tool | Status field | Meeting ID field | Time field | Rep field |
|------|-------------|-----------------|------------|-----------|
| `meeting-list-put` | `status` | `meetingId` | `scheduledAt` | `assignedUserId` (resolve name/email via `user-find-by-ids`) |
| `meeting-get` | `meetingStatus` | `id` | in `activities` array | — |

**Always use the correct field name for each tool.** Using `status` on a `meeting-get` response returns `undefined`. Using `id` or `startTime` on `meeting-list-put` items also returns `undefined`.

Guest information in `meeting-list-put` items is in the `attendees` array, not a top-level `guest` field.

---

## Pagination — meeting-list-put

```yaml
tool: meeting-list-put
args:
  start: <ISO-8601>
  end: <ISO-8601>
  pagination:
    page: 0
    pageSize: 50
```

- Results are in `response.data.list[]`
- Paginate by checking `hasMore === "Yes"` (string comparison, not boolean)
- Each page: increment `pagination.page` by 1 until `hasMore === "No"`

---

## Hard API limits

| Tool | Limit |
|------|-------|
| `meeting-list-put` | **7-day maximum window** per call — chunk `date_range` into ≤7-day slices |
| `concierge-logs` | **30-day maximum window** per call — routing traces unavailable for older meetings |

---

## Meeting status values

Applies to `meeting-list-put` (`status`) and `meeting-get` (`meetingStatus`):

| Value | Meaning |
|-------|---------|
| `Scheduled` | Upcoming, not yet occurred |
| `Completed` | Meeting took place |
| `NoShow` | Guest did not attend |
| `Cancelled` | Meeting was cancelled |

---

## Concierge-log status values

| Value | Has `meetingId`? | Meaning |
|-------|-----------------|---------|
| `Booked` | ✓ Yes | Lead completed booking |
| `Offered` | ✗ No | Calendar was shown; lead did not complete booking |
| `NoMatch` | ✗ No | No routing rule matched the lead |
| `NotQualified` | ✗ No | Lead was disqualified (spam check, ICP filter, explicit disqualify rule) |
| `Timeout` | ✗ No | 30-minute routing session TTL expired |
| `Error` | ✗ No | Technical error — escalate to engineering |

A meeting record can exist even if the concierge-log status is not `Booked` — the booking may have occurred via a different path (direct link, manual booking, handoff).

---

## Trigger types in concierge-logs

| Value | What it means |
|-------|--------------|
| `ThirdPartyForm` | Web form submission (Marketo, HubSpot, Pardot, HTML form) |
| `Direct` | Prospect visited the router URL directly |
| `Email` | Scheduling link embedded in an email |
| `RouterLink` | Router link shared via a direct URL |
| `InApp` | In-product trigger (SaaS product-embedded booking) |

---

## Meeting summary fields

| Field | Source (meeting-list-put) | Source (meeting-get) |
|-------|--------------------------|---------------------|
| Meeting ID | `meetingId` | `id` |
| Status | `status` | `meetingStatus` |
| Scheduled time | `scheduledAt` | in `activities` array |
| Booked at | `createdAt` | `createdAt` |
| Guest email | in `attendees[]` | `guest.email` |
| Assigned rep ID | `assignedUserId` (resolve via `user-find-by-ids`) | — |

Lead time = `scheduledAt` minus `createdAt` (for `meeting-list-put` items).

---

## actionsStatus field (CRM write-back health)

`concierge-logs.actionsStatus` shows whether post-routing CRM actions fired successfully (e.g., Salesforce task creation, campaign association).

A non-success `actionsStatus` means the meeting exists in Chili Piper but may not be visible in Salesforce. Escalate to the RevOps admin if CRM write-back failure is suspected.

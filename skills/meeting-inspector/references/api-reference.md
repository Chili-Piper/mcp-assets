# Meeting Inspector — API Reference

Full field names, status codes, and known gotchas for the Chili Piper MCP tools used by this skill.

> Field names and response envelopes are validated against **live MCP responses**. The MCP tools' own text descriptions are often wrong — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings — envelope `{data: {list: [...]}, hasMore: "Yes"\|"No"}`. Items in `data.list[]` use `meetingId`, `meetingStatus`, `dateTime.start`/`dateTime.end`, `hostId`/`hostEmail`/`hostName`, `bookedAt`, `primaryGuest.value`, `attendees[]`, `workspaceId`. |
| `meeting-get` | GET | Single meeting by ID — `id`, **`meetingStatus`**. Scheduled time is in the `activities` array (a `ScheduledAt`/`HappensAt` entry — no top-level `scheduledAt` or `startTime`). |
| `concierge-list-routers` | GET | All routers — `{routers: [{router: {id, name, slug, routing: {rules, catchAll}, ...}, workspaceId}]}`. Access routerId at `routers[N].router.id`, slug at `routers[N].router.slug`, workspaceId at `routers[N].workspaceId`. |
| `concierge-logs` | POST | Routing decisions — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl`, `crmUrl`, `actionsStatus` |
| `workspace-list` | GET | All workspaces — `[{id, name, emoji, logo, metadata, nrOfUsers}]` (items use **`id`**, not `workspaceId`; member count is `nrOfUsers`; there is no `settings`) |

---

## Critical field name differences

| Tool | Status field | Meeting ID field | Time field | Rep field |
|------|-------------|-----------------|------------|-----------|
| `meeting-list-put` | `meetingStatus` | `meetingId` | `dateTime.start` | `hostId` / `hostEmail` / `hostName` |
| `meeting-get` | `meetingStatus` | `id` | in `activities` array | (see `activities` / `attendees`) |

**Both tools use `meetingStatus`.** The differences are the meeting-id field (`meetingId` in list vs `id` in get) and where the scheduled time lives (`dateTime.start` in list vs the `activities` array in get). Using `status`, `scheduledAt`, `startTime`, or `assignedUserId` on a `meeting-list-put` item returns `undefined` — those fields do not exist.

Guest information in `meeting-list-put` items: the primary guest is `primaryGuest.value` (email); all participants are in the `attendees[]` array. There is no top-level `guest` field.

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

## Meeting status values (`meetingStatus`)

| Value | Meaning |
|-------|---------|
| `Active` | Booked — upcoming, or (if `dateTime.start` is in the past) effectively completed |
| `Canceled` | Meeting was cancelled (note the single-`l` spelling) |
| `NoShow` | Guest did not attend (cross-check the separate `noShowStatus` string field) |
| `Completed` | Meeting took place (also derivable from a past `dateTime.start` on an `Active` meeting) |

`Active`, `Canceled`, `NoShow`, and `Completed` are also the valid values for the `status` **input filter** on `meeting-list-put`. There is no `Scheduled` value — upcoming meetings are `Active`.

---

## Concierge-log status values

Observed against live routing logs. Treat this as the known set; confirm any other value against a live log before branching on it.

| Value | Meaning |
|-------|---------|
| `Scheduled` | Lead completed booking (a `meetingId` is present) |
| `TimedOut` | Routing session expired before the lead booked |
| `Cancelled` | The routing session / resulting meeting was cancelled |

A meeting record can exist even when no log shows `Scheduled` — the booking may have occurred via a different path (direct link, manual booking, handoff).

---

## matchedPath (which route fired)

`matchedPath` is an **object**, not a string:

```
matchedPath: { route: { type: "RuleRoute" | "CatchAllRoute", ruleIds: [...], id: ... }, type: "RoutePathWithCalendar" }
```

- `matchedPath.route.type == "CatchAllRoute"` → the lead hit the catch-all (no specific rule matched).
- `matchedPath.route.type == "RuleRoute"` → a rule matched; the rule id(s) are in `matchedPath.route.ruleIds`.

---

## Trigger types in concierge-logs

`trigger` is a string (e.g. `ThirdPartyForm`). Common values:

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
| Status | `meetingStatus` | `meetingStatus` |
| Scheduled time | `dateTime.start` | in `activities` array (`ScheduledAt`/`HappensAt`) |
| Booked at | `bookedAt` | `bookedAt` |
| Guest email | `primaryGuest.value` (also `attendees[]`) | `attendees[]` |
| Assigned rep | `hostId` / `hostEmail` / `hostName` | `attendees[]` (host entry) |

Lead time = `dateTime.start` minus `bookedAt` (for `meeting-list-put` items). The rep is already named via `hostName`/`hostEmail` — no separate `user-find-by-ids` lookup is needed for `meeting-list-put`.

---

## actionsStatus field (CRM write-back health)

`concierge-logs.actionsStatus` shows whether post-routing CRM actions fired successfully (e.g., Salesforce task creation, campaign association). A non-success `actionsStatus` means the meeting exists in Chili Piper but may not be visible in Salesforce. Escalate to the RevOps admin if CRM write-back failure is suspected.

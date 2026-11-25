# No-Show Analyzer — API Reference

Full field names, status values, windowing rules, and known gotchas for the Chili Piper MCP tools used by this skill.

> Field names and response envelopes are validated against **live MCP responses** (status filter confirmed live as of DISTRO-4472). The MCP tools' own text descriptions are unreliable — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings by time range — response envelope `{data: {list: [...]}, hasMore: "Yes"\|"No"}`. Items in `data.list[]`: `meetingId`, `meetingStatus`, `dateTime.start`, `hostId`/`hostEmail`/`hostName`, `workspaceId`, `attendees` (array). Paginate by checking `hasMore === "Yes"` (string). Accepts `status` filter. |
| `concierge-list-routers` | GET | All routers — response: `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. Access: `routerId` at `routers[N].router.id`, `name` at `routers[N].router.name`, `workspaceId` at `routers[N].workspaceId`. |
| `concierge-logs` | POST | Routing decisions per router — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl` |
| `workspace-list` | GET | All workspaces — `id`, `name`, `nrOfUsers` |
| `user-find-by-ids` | — | Resolves a `userId` to a name (used to name an assignee from `assignments[0].userId`) |

Note: the field name in each `meeting-list-put` item is `meetingId` (not `id`) — key any meeting map on `item.meetingId`.

---

## Hard API limits — two separate windows

- `meeting-list-put` has a **7-day maximum window per call**. For ranges longer than 7 days, you must make multiple sequential calls and merge the results.
- `concierge-logs` requires a `routerId` and has a **30-day maximum window**. For grouping by `trigger` or `route`, loop over routers and call once per router, then join on `meetingId`.

Paginate `meeting-list-put` chunks by continuing to increment `pagination.page` while `response.hasMore === "Yes"` (string comparison, not boolean). Merge all results into a single list and deduplicate on `meetingId`.

---

## Status values in `meeting-list-put`

| Status | Include in no-show rate? |
|--------|------------------------|
| `Completed` | ✓ Yes — denominator and numerator |
| `NoShow` | ✓ Yes — numerator only |
| `Canceled` | ✗ No — exclude entirely |
| `Active` (start in future) | ✗ No — upcoming, not yet occurred |
| `Active` (start in past) | ✓ Denominator only — meeting likely happened but was never formally closed; treat as informally completed |

**Important:** Chili Piper meetings that are never explicitly closed remain `Active` indefinitely. Excluding past-`Active` meetings from the denominator inflates the apparent no-show rate. Include them and split on start time.

Pass `status: ["Completed", "NoShow", "Active"]` in the request — exclude `Canceled` at the server (never counted) while keeping `Active` so past-informally-completed meetings are captured client-side. Do NOT pass only `["Completed","NoShow"]` as that would silently shrink the denominator.

Pass `workspaceIds` to filter server-side when a workspace is specified.

---

## Status values in `concierge-logs` (critical for the join)

| Status | Has `meetingId`? | Meaning |
|--------|----------------|--------|
| `Scheduled` | ✓ Yes | Lead completed booking — this `meetingId` joins to meeting-list-put |
| `TimedOut` | ✗ No | Routing session expired before the lead booked |
| `Cancelled` | varies | The routing session / resulting meeting was cancelled |

Only `Scheduled` log entries reliably carry a `meetingId` to join with meeting-list-put. These are the values observed against live routing logs; if you encounter another status, verify it against a live log before relying on it. Entries that never produced a meeting (e.g. `TimedOut`) are a separate "booking conversion" funnel and must be excluded from no-show calculations — do not attempt to join them.

---

## Trigger types in `concierge-logs`

| Value | What it means |
|-------|---------------|
| `ThirdPartyForm` | Web form submission (Marketo, HubSpot, Pardot, HTML form) |
| `Direct` | Prospect visited the router URL directly |
| `Email` | Scheduling link embedded in an email |
| `RouterLink` | Router link shared via a direct URL |
| `InApp` | In-product trigger (SaaS product-embedded booking) |

---

## Routing fields to extract from a `Scheduled` log entry

- `meetingId` — used to join with meeting status
- `trigger` — the lead source type (see trigger types table above)
- `matchedPath.route.type` — the route kind (`RuleRoute` if a rule matched, with rule ids in `matchedPath.route.ruleIds`; `CatchAllRoute` if the lead hit the catch-all)
- `sourceUrl` — the page the lead came from (useful for inferring campaign/channel)
- `assignments[0].userId` — the rep the router assigned (resolve to a name via `user-find-by-ids` if needed)

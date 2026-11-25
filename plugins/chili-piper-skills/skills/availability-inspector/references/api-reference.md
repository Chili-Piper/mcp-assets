# Availability Inspector — API Reference

Full field names, request shape, and pagination rules for the Chili Piper MCP tools this
skill calls. Field names are validated against the live `availability-slots-v2` schema
(DISTRO-4554, merged 2026-06-17; v1 `availability-slots` is deprecated and removed from
MCP) — use this file, not the tool blurb or intuition.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `user-find` | Resolve email/name to user ID |
| `user-read` | `{id, name, email, isSuperAdmin, licenses: {distro, chiliCalOrg, concierge, conciergeLive, chat, handoff}, workspaces, salesforce, hubspot, slug, managedWorkspaces, managedTeams}` — **no** `calendarConnected`/`calendarProvider`/`crmConnected`; calendar status does not surface from this endpoint |
| `availability-slots-v2` | Paginated available slots — `{results: [{startTime, attendees}], total, page, pageSize}`; default 100 per page, max 500. **No slot cap** (pagination bounds output). **No `failures` map** — calendar/availability blockers manifest as empty `results`, not named codes |

## user-read note

`user-read` does NOT return `calendarConnected`, `calendarProvider`, or `crmConnected`.
Calendar connection status is not available from this endpoint.

License check on the `user-read` response:

- `licenses.chiliCalOrg = false` AND `licenses.concierge = false` AND `licenses.handoff = false`
  → user may not have a scheduling license; report `NotActive` (verify with your admin).

## availability-slots-v2 request shape

Build the request using the verified shape below. `expectedHost` must be an **object**,
`meetingTypeRef` is **not needed in v2** (omit it), and every attendee needs both a `type`
discriminator and a `required` boolean.

```
tool: availability-slots-v2
args:
  expectedHost:
    type: User
    userId: <userId>
  attendees:
    - type: ManuallyAssigned
      userId: <userId>
      required: true
  meetingTypeOverride:
    meetingDurationOverride: "30 minutes"     # FiniteDuration or ISO-8601 ("PT30M"); omit to use default
  interval:
    startsAt: <ISO-8601 now>
    duration: "<lookahead_days> days"          # e.g. "14 days" or "P14D" — NOT milliseconds
  page: 0                                      # 0-based; increment for subsequent pages
  pageSize: 200                                # 1–500; defaults to 100
```

## Critical field-name rules

- `expectedHost` must be an **OBJECT** (`{type: 'User', userId}`), not a bare id.
- Attendees use a `type` discriminator: `ManuallyAssigned` | `DistributionAssignee` |
  `AssignedViaTeam` | `AdditionalAttendee`.
- Each attendee has a required `required` boolean — omitting `required` returns **400**.
- `meetingTypeRef` is **no longer required in v2** (dropped from the request) — omit it.
- Durations use Scala `FiniteDuration` (`"30 minutes"`) or ISO-8601 (`"PT30M"`). The
  `interval.duration` is e.g. `"14 days"` / `"P14D"` (NOT milliseconds).

## Pagination

`availability-slots-v2` returns `{results, total, page, pageSize}`. Default `pageSize` is
100 (max 500). There is **no slot cap** — pagination bounds the output. If `total` exceeds
`pageSize`, call again with `page: 1`, `page: 2`, etc. (The v1 1000-slot / 422 cap no
longer applies.)

## No failures map

`availability-slots-v2` does **not** return a `failures` map. Calendar and availability
blockers manifest as an empty `results` list, not named codes. When `results` is empty,
diagnose from the user profile and the common-causes checklist in `diagnostics.md`, and
verify the exact cause in Chili Piper admin.

A `required: true` attendee with no calendar connected blocks the entire slot query.

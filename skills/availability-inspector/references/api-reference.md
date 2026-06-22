# Availability Inspector — API Reference

Full field names, request shape, and hard limits for the Chili Piper MCP tools this skill
calls. Field names are validated against the live `availability-slots` schema — use this
file, not the tool blurb or intuition.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `user-find` | Resolve email/name to user ID |
| `user-read` | `{id, name, email, isSuperAdmin, licenses: {distro, chiliCalOrg, concierge, conciergeLive, chat, handoff}, workspaces, salesforce, hubspot, slug, managedWorkspaces, managedTeams}` — **no** `calendarConnected`/`calendarProvider`/`crmConnected`; calendar status only surfaces in availability-slots failures |
| `availability-slots` | `{startTimes, failures: {userId: failure}}` — available slots + a per-user `failures` map; returns **422** (`edge.availability-result-too-large`) if result exceeds **1000 slots** |
| `meeting-list-put` | Used to obtain a `meetingTypeId` when one is not already known (returns `meetingTypeId`) |

## user-read note

`user-read` does NOT return `calendarConnected`, `calendarProvider`, or `crmConnected`.
Calendar connection status is not available from this endpoint — it surfaces only in the
`availability-slots` `failures` map.

License check on the `user-read` response:

- `licenses.chiliCalOrg = false` AND `licenses.concierge = false` AND `licenses.handoff = false`
  → user may not have a scheduling license; report `NotActive` (verify with your admin).

## availability-slots request shape

Build the request using the verified shape below. `expectedHost` must be an **object**,
`meetingTypeRef.id` is **required**, and every attendee needs both a `type` discriminator
and a `required` boolean.

```
tool: availability-slots
args:
  expectedHost:
    type: User
    userId: <userId>
  attendees:
    - type: ManuallyAssigned
      userId: <userId>
      required: true
  meetingTypeRef:
    id: <meetingTypeId>
    timestamp: <ISO-8601 now>
  meetingTypeOverride:
    meetingDurationOverride: "30 minutes"     # FiniteDuration or ISO-8601 ("PT30M"); omit to use the meeting type's default
  interval:
    startsAt: <ISO-8601 now>
    duration: "<lookahead_days> days"          # e.g. "14 days" or "P14D" — NOT milliseconds
```

## Critical field-name rules

- `expectedHost` must be an **OBJECT** (`{type: 'User', userId}`), not a bare id.
- Attendees use a `type` discriminator: `ManuallyAssigned` | `DistributionAssignee` |
  `AssignedViaTeam` | `AdditionalAttendee`.
- Each attendee has a required `required` boolean — omitting `required` returns **400**.
- `meetingTypeRef.id` is **REQUIRED**. The API will **400** without it. If you don't have
  one, get a `meetingTypeId` from one of the user's existing meetings (`meeting-list-put`
  returns `meetingTypeId`) or from the rep's scheduling link, and pass it here.
- Durations use Scala `FiniteDuration` (`"30 minutes"`) or ISO-8601 (`"PT30M"`). The
  `interval.duration` is e.g. `"14 days"` / `"P14D"` (NOT milliseconds).

## Hard API limits

`availability-slots` caps responses at **1000 start-time slots** and returns HTTP **422**
(`edge.availability-result-too-large`) if exceeded (DISTRO-4552, 2026-06-16). If you get a
422, reduce `interval.duration` (e.g. `"7 days"`) or reduce the attendee count to stay
under the cap.

## Failures map semantics

`availability-slots` returns a `failures: {userId: failure}` map but does **not** publish a
fixed enum of reason strings. Read the literal value returned rather than assuming an enum;
map it to the closest cause in `diagnostics.md`, and if it doesn't match, surface the raw
value.

A `required: true` attendee with no calendar connected blocks the entire slot query.

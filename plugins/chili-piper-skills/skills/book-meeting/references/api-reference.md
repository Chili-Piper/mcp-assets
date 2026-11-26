# book-meeting — API reference

Exact public calls of the Chili Piper booking page. `{host}` is the booking link's host
(`https://acme.chilipiper.com`). `{tid}` is the tenant id. Times are ISO-8601 UTC
(`2026-12-01T14:00:00Z`). Durations in requests are strings like `"7 days"`. Send
`meetingInvite.duration` and slot `startTime` values back exactly as received.

## Session setup

1. **Tenant id.**
   - Router link: `GET {link}`. The response header `x-tenant-id` is the tenant id.
   - Personal link: see § Personal-link flow step 1.
2. **Guest token:** `POST {host}/api/fire-auth/v1/public/guest-tokens`, no body, headers
   `x-tenant-id: {tid}`. The response body is a JSON string (a JWT). Its payload `sub`
   is your guest id.
3. **Headers on every later call:**
   - `x-tenant-id: {tid}`
   - `x-caller-ref: guest/{sub}`
   - `Content-Type: application/json` on calls with a body
   - `Authorization: Bearer {token}` on paths that contain `guest-external`. Paths that
     contain `public` need no `Authorization`.
   - Router flow only, after routing: `x-routing-id: {routingId}`.
   - On `401`/`403`, get a new guest token and retry once.

## Router flow

**1. Router settings** — `GET {host}/api/concierge/v1/guest-external/tenant/{tid}/router/{slug}`

Keep `acceptsRouting` (must be `true`) and `formMapping.get[]`. Each entry is a trigger:

| `type` | `trigger` to send | Field key in `mapping[]` |
|---|---|---|
| `ProcessedRouterLinkTrigger` | `RouterLink` | `dataField` (`label`, `required`) |
| `ProcessedThirdPartyFormTrigger` | `ThirdPartyForm` | `dataFieldRef` (`name`) |

Prefer `RouterLink`. Skip fields with a `hidden` value — the router fills them.
Field keys are data-field references, for example `PersonEmail`, `PersonFirstName`,
`PersonLastName`, or a UUID for a custom field (use its `label` to ask the person).
Use the keys exactly as the form definition gives them.

**2. Route** — `POST {host}/api/concierge/v1/guest-external/tenant/{tid}/router/{slug}/route`

```json
{"type": "LaunchRouteRequestV2", "trigger": "RouterLink",
 "fields": {"PersonEmail": "jane@example.com", "PersonFirstName": "Jane"},
 "guestTimezone": "Europe/Prague"}
```

All `fields` values are strings. Keep from the response: `type`, `routingId`,
`meetingTypeIds[0]`, `assignments[]`. See § Routing outcomes.

**3. Meeting type** — `PUT {host}/api/meeting-types/v2/public/tenant/{tid}/meeting-types`
with `{"ids": ["{meetingTypeId}"]}`. The response maps id → meeting type. Keep `name`
and `meetingInvite.duration`.

**4. Slots** — `PUT {host}/api/availability/v1/public/tenant/{tid}/meeting/slots`

```json
{"expectedHost": EXPECTED_HOST, "attendees": ATTENDEES,
 "meetingTypeRef": {"id": "{meetingTypeId}", "timestamp": "{now}"},
 "meetingTypeOverride": {},
 "interval": {"startsAt": "{windowStart}", "duration": "7 days"},
 "linkMeetingLimit": {"type": "NoMeetingLimit"},
 "availabilityChecks": {"type": "All"}}
```

Build `ATTENDEES` with one item per routing assignment, and `EXPECTED_HOST` from the
first one:

| Assignment `type` | Attendee | Expected host |
|---|---|---|
| `DistributedV3` | `{"type":"DistributionAssignee","distributionId":D,"userIds":users,"required":r}` | `{"type":"AssigneeFromDistribution","distributionId":D}` |
| `FixedUser` (or other with `id`) | `{"type":"ManuallyAssigned","userId":id,"required":r}` | `{"type":"User","userId":id}` |

Response: `{"startTimes": [{"startTime": "...", "attendees": [...]}]}`. Keep the chosen
slot's `startTime` and `attendees`.

**5a. Book — round robin** (any assignment is `DistributedV3`) —
`POST {host}/api/concierge/v1/guest-external/tenant/{tid}/routing/{routingId}/schedule`

```json
{"type": "ScheduleByDistribution", "assignees": ASSIGNEES,
 "timeInterval": {"startsAt": "{slot.startTime}", "duration": "{meetingInvite.duration}"},
 "meetingTypeId": "{meetingTypeId}", "meetingTypeRelevantAt": "{now}",
 "location": {"type": "DefinedInMeetingType"}, "guestTimezone": "Europe/Prague"}
```

`ASSIGNEES`, one per routing assignment, matched to the slot attendee by `distributionId`:

| Slot attendee `type` | Assignee |
|---|---|
| `StrictRoundRobinAssignee` | `{"type":"WithResolvedAssigneeDistribution","id":att.userId,"distributionId":D,"required":r}` |
| `FlexibleRoundRobinAssignee` | `{"type":"WithUnresolvedAssigneeDistribution","availableUsers":att.userIds,"distributionId":D,"required":r}` |
| (assignment `FixedUser`) | `{"type":"FixedUser","id":id,"required":r}` |

Success: `{"type": "ScheduledByDistribution", "meetingId": "...", "assignees": [...]}`.

**5b. Book — fixed host** (no `DistributedV3` assignment): reserve, then schedule.

Reserve: `POST {host}/api/availability/v4/public/tenant/{tid}/users/slots` with the
step 4 body, minus `interval`, plus `"slotStartsAt": "{slot.startTime}"`, and with
`attendees` = the slot's `attendees`. Response: `{"id": "{reservationId}",
"ttl": {"value": "...", "type": "ExpiresAt"}}`.

Schedule: same URL as 5a with

```json
{"type": "ScheduleByReservation", "hostId": "{userId}", "reservationId": "{reservationId}",
 "location": {"type": "DefinedInMeetingType"}, "guestTimezone": "Europe/Prague"}
```

Success: `{"type": "ScheduledByReservation", "meetingId": "..."}`.

## Routing outcomes

| Route response `type` | Meaning | Do |
|---|---|---|
| `RoutedWithCalendar` | A calendar is offered | Continue to step 3 |
| `RoutedWithoutCalendar` | No calendar for this guest (`redirect` says where to go) | Tell the person the company will follow up, or give them `redirect.url` |
| `RoutedLive` or other | Live call or other flow | Give the person the booking link |

## Personal-link flow

Link: `{host}/me/{userSlug}/{linkSlug}`. `{sub}` below is the first label of the host
(`acme` for `acme.chilipiper.com`).

1. **Resolve** — `GET {host}/api/firerouter/v1/resolve/slugs/{userSlug}?subdomain={sub}`
   (no headers) → `{"tenantId", "userId"}`. Then do § Session setup steps 2–3.
2. **Personal workspace** — `GET {host}/api/workspaces/v1/guest-external/tenant/{tid}/user/{userId}/workspaces/personal` → `{"id"}`.
3. **Meeting type** — `GET {host}/api/meeting-types/v1/public/tenant/{tid}/meeting-type-slug/{linkSlug}?workspaceId={workspaceId}`.
   Keep `id`, `name`, `meetingInvite.duration` and `guestForm` (`type` and
   `items[]`/`fields[]` with `reference` and `requirement.type`).
4. **Slots** — as Router flow step 4 with
   `"expectedHost": {"type": "User", "userId": U}` and
   `"attendees": [{"type": "AdditionalAttendee", "userId": U, "required": true}]`.
5. **Reserve** — as Router flow 5b "Reserve".
6. **Book** — `POST {host}/api/team-scheduling/v3/guest-external/tenant/{tid}/meeting`

```json
{"primaryGuest": {"type": "External", "email": "jane@example.com", "timezone": "Europe/Prague"},
 "attendees": {"type": "NoAdditionalAttendees"},
 "location": {"type": "DefinedInMeetingType"},
 "feature": {"type": "PersonalSchedulingLink", "meetingTypeId": "{id}",
   "timeAndAssignment": {"type": "WithReservation", "reservationId": "{reservationId}", "hostId": "{userId}"},
   "guestFormData": {"type": "FilledMixed",
     "fieldValues": {"PersonEmail": "jane@example.com", "PersonFirstName": "Jane", "PersonLastName": "Doe"},
     "questionValues": {}},
   "sourceUrl": "{booking link}", "secondaryFeature": []},
 "meetingTypeOverride": {}}
```

If `guestForm.type` is `DataFields`, send
`"guestFormData": {"type": "FilledDataFields", "values": {...}}` instead.
Success: `{"type": "Accepted", "meetingId": "...", "hostId": "..."}`. Other types
(`ProspectLimitReached`, `NoAvailableAssignees`) mean no booking was made.

## Errors

| Response | Cause | Fix |
|---|---|---|
| `400 concierge.fire.missing-form-fields` | `arguments.refs` lists missing fields | Ask the person, route again |
| `400 concierge.fire.unsupported-trigger` | Router has no such trigger | Use a trigger from § Router flow step 1 |
| `400 concierge.fire.unknown-data-field-reference` | Wrong field key | Use keys from the form definition only |
| `400 ... Missing required field at '...'` | Body shape | Copy the body from this file |
| `500 concierge-fire.invalid-data` | Company's router is misconfigured | Give the person the link |
| Reservation `ttl` passed | Reservation expired (~5 min) | Reserve again, then book |
| Empty `startTimes` | No open slots in the window | Ask the next window (move `startsAt` 7 days) |

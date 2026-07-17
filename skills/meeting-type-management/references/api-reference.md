# API reference — meeting-type-management

Field names verified against the live public Edge API spec, 2026-07-02. The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools

| Tool | HTTP | What it does |
|------|------|-------------|
| `workspace-list` | — | Workspaces → items use `id` (not `workspaceId`) |
| `meeting-type-list` | `GET /v1/org/meeting-types/list` | All team meeting types; optional `workspaceId` query filter |
| `meeting-type-get` | `GET /v1/org/meeting-types/{meetingTypeId}` | One meeting type with `reminders` populated |
| `meeting-type-create` | `POST /v1/org/meeting-types` | Create (body: `MeetingTypeCreate`) |
| `meeting-type-update` | `PUT /v1/org/meeting-types/{meetingTypeId}` | Patch (body: `MeetingTypeUpdate` — only send fields to change) |
| `meeting-type-delete` | `DELETE /v1/org/meeting-types/{meetingTypeId}` | Delete — irreversible |
| `meeting-type-attach-reminder` | `PUT /v1/org/meeting-types/{mtId}/reminders/{reminderId}` | Associate an existing reminder (idempotent) |
| `meeting-type-detach-reminder` | `DELETE /v1/org/meeting-types/{mtId}/reminders/{reminderId}` | Remove the association (idempotent) |
| `meeting-type-reminder-list` | `GET /v1/org/meeting-type-reminders/list` | Reminders; optional `workspaceId` filter |
| `meeting-type-reminder-create` | `POST /v1/org/meeting-type-reminders` | Create reminder (body: `ReminderCreate`) |
| `meeting-type-reminder-update` | `PUT /v1/org/meeting-type-reminders/{reminderId}?workspaceId=` | Patch reminder (`workspaceId` **required** alongside the path ID) |
| `meeting-type-reminder-delete` | `DELETE /v1/org/meeting-type-reminders/{reminderId}?workspaceId=` | Delete reminder (`workspaceId` required) — irreversible |

## MeetingType (response shape)

`{id, workspaceId, name, description?, inviteTitle, inviteDescription, status, duration, location, buffers, meetingLimit?, sharedWith?, reminders?}`

## Field glossary — internal vs guest-visible

| Field | Who sees it | Notes |
|-------|-------------|-------|
| `name` | Admins (and defaults into invite title) | The meeting type's label in the product |
| `description` | **Admins only — never guests** | Internal note; filled on very few meeting types in practice |
| `inviteTitle` | **Guests** | Calendar invite subject; defaults to `name` on create; supports `{CP.*}` merge tags (e.g. `{CP.Host.FullName}`) |
| `inviteDescription` | **Guests** | Calendar invite body — the "Meeting Invite → Description" field in the UI; supports `{CP.*}` merge tags |

> To change what a guest sees on the calendar invite, edit `inviteTitle`/`inviteDescription` — **not** `description` (DISTRO-4583).

## Read tools — gotchas

- **`meeting-type-list` returns `reminders: null`** — reminders are not fetched by the list. Use `meeting-type-get` for the real reminders array.
- **Scope:** personal meeting types are excluded from every `meeting-type-*` operation; only team (workspace) types appear.
- `meeting-type-get` `reminders[]` items are full `Reminder` objects: `{id, workspaceId, channel, trigger, name, title?, body}`.

## Enums and formats

| Field | Values / format |
|-------|-----------------|
| `status` | `Active` \| `Inactive` |
| `duration`, `buffers.before/after`, `trigger.offset` | Scala FiniteDuration strings — `"30 minutes"`, `"1 hour"` |
| `meetingLimit` | `{limitBy: Email\|Domain, timeframe: Hourly\|Daily\|Weekly\|Monthly\|Yearly, count}` (all three required when set) |
| `location` | `{default, others?[]}`; each location is one of: `AskTheGuest`, `CalendarPlatformConference`, `DefinedInMeetingType`, `HostsDefaultConferenceDetails`, `HostsDefaultPhysicalLocation`, `ZoomOneTimeLink`, `TeamsMeetingLink`, `GoToMeetingLink`, `WebexLink`, `RingCentralLink`, `GongLink` (discriminated by `type`) |
| `sharedWith` | `{type: "Workspace"}` or `{type: "Teams", teamIds?}` — discriminated by `type`; the wire values are `Workspace`/`Teams` (the 2026-07-02 spec's `SharedWith_Workspace`/`SharedWith_Teams` consts are gone — sending them is rejected) |
| Reminder `channel` | `Email` \| `Sms` — **immutable after creation** |
| Reminder `trigger.kind` | `BeforeMeeting` \| `BeforeMeetingNoResponse` \| `MeetingBooked` \| `AfterMeeting` |
| Reminder `trigger.offset` | Required for `BeforeMeeting`/`BeforeMeetingNoResponse`/`AfterMeeting`; **must be omitted** for `MeetingBooked` |

## Permissions

Reads need `meeting-type.read`; writes need `meeting-type.create` / `meeting-type.modify` / `meeting-type.remove`. Attach/detach resolve the workspace from the meeting type (no `workspaceId` input) and need `meeting-type.modify`.

# chili-piper-guest — MCP reference (Path A)

The Chili Piper guest MCP server is public and needs **no authentication**. It is a
separate server from the Chili Piper admin MCP and has only guest tools.

| Environment | MCP endpoint (Streamable HTTP, JSON-RPC 2.0) |
|---|---|
| Production | `https://fire.chilipiper.com/api/fire-edge/v1/guest/mcp` |
| Staging | `https://fire.chilipiper.io/api/fire-edge/v1/guest/mcp` |

Use the endpoint of the booking link's domain: `*.chilipiper.com` → Production,
`*.chilipiper.io` → Staging.

**Connect:** add the endpoint as a remote MCP server with no auth. A client without MCP
support can `POST` JSON-RPC 2.0 to the endpoint (`Content-Type: application/json`):
`initialize`, then `tools/list` and `tools/call`. If the endpoint does not answer, use
Path B (`api-reference.md`).

**Not every company is enabled.** If a tool says the company does not take bookings from AI
agents yet, use Path B or give the person the booking link to book in a browser.

## Tools

### Find the link

| Tool | Input | Output |
|---|---|---|
| `website-booking-link-find` | `websiteUrl` (the company's public page) | `found`, `bookingLinks` (`bookingLink`, `supported`, `note`), `skillUrl`, `message` |

Use it only when you know the company's website but not its booking link. `found: false`
is a normal answer: ask the person for the company's Chili Piper booking link.

### Book

| Tool | Input | Output |
|---|---|---|
| `booking-link-describe` | `bookingLink` | `linkType` (`router` or `personal`) and the form fields to fill: `ref`, `label`, `required` |
| `booking-slots-find` | `bookingLink`, `guestEmail`, `guestTimezone` (IANA), `formValues` (opt, map `ref` → value), `from` (opt, ISO instant, default now), `days` (opt, 1–7, default 7) | `bookingSessionId`, `outcome`, `durationMinutes`, `redirectUrl`, `startTimes` (ISO instants, UTC) |
| `booking-create` | `bookingLink`, `bookingSessionId`, `startTime` (one of `startTimes`); for a **personal** link also `guestEmail`, `guestTimezone`, `formValues` | `meetingId`, `startTime` |

Link types: a router link (`/concierge-router/link/<slug>`) routes the person to the right
rep; a personal link (`/me/<user>/<link>`) books one fixed person. Tools reject links that
are not Chili Piper booking links of the server's environment. The server sets everything
else (trigger, routing options). You cannot add guests or change the location — the same
as on the booking page.

### Manage a booked meeting

| Tool | Input | Output |
|---|---|---|
| `meeting-get` | `meetingLink` | `meetingId`, `status`, start and end time, host name, title |
| `meeting-reschedule-slots` | `meetingLink`, `guestTimezone`, `from` (opt), `days` (opt, 1–7) | `durationMinutes`, `startTimes`, `localStartTimes` |
| `meeting-reschedule` | `meetingLink`, `startTime` (one of `startTimes`) | `meetingId`, new start and end time |
| `meeting-cancel` | `meetingLink` | `meetingId`, `status: canceled` |

`meetingLink` is the reschedule or cancel link from the person's calendar invite
(`https://<sub>.chilipiper.com/reschedule/<id>` or `/cancel/<id>`). Right after
`booking-create` you can pass `bookingLink` + `meetingId` instead. The tools refuse
canceled and past meetings.

## Flow — book

1. `booking-link-describe` with the link. Ask the person for every `required` field you
   do not have. Do not send the email inside `formValues`; pass it as `guestEmail`.
2. `booking-slots-find` with the email, the field values (keys = `ref`), the person's time
   zone and the window.
   - `outcome: calendar-offered` → `startTimes` holds the open times. Show 3–5 of them in
     the person's time zone. If empty, call again with `from` 7 days later.
   - `outcome: no-calendar` → the company does not offer a meeting to this person now.
     Tell them; give them `redirectUrl` if it is set.
   - `outcome: other` (for example a live call) → give the person the booking link to
     finish in a browser.
3. **Checkpoint** (see `SKILL.md`): get an explicit yes for slot, time zone and values.
4. `booking-create` with the same `bookingLink`, the `bookingSessionId` and the chosen
   `startTime`, exactly as returned (personal link: also the email, time zone and values).
   Call it promptly: a router session expires after about 10 minutes. If it expired, run
   step 2 again.
5. Report the result (`SKILL.md` Step 6).

## Flow — change a meeting

1. `meeting-get` with the invite link; show the person the meeting.
2. Reschedule: `meeting-reschedule-slots`, offer 3–5 times, get an explicit yes, then
   `meeting-reschedule`. Cancel: get an explicit yes, then `meeting-cancel`.

## Errors

Tool errors come back as a result with `isError: true` and a short message that says what
to do (for example which form fields are missing). Fix the input and call again. If the
message says the service failed, retry once, then use Path B or give the person the link.

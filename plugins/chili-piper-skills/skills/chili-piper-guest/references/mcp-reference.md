# chili-piper-guest — MCP reference (Path A)

The Chili Piper guest MCP server ("Chili Piper Guest") is public and needs **no
authentication**. It is a separate server from the Chili Piper admin MCP and has only guest
tools.

| Environment | MCP endpoint (Streamable HTTP, JSON-RPC 2.0) |
|---|---|
| Production | `https://fire.chilipiper.com/api/fire-edge/v1/guest/mcp` |
| Staging | `https://fire.chilipiper.io/api/fire-edge/v1/guest/mcp` |

Use the endpoint of the link's domain: `*.chilipiper.com` → Production, `*.chilipiper.io`
→ Staging.

**Connect:** add the endpoint as a remote MCP server with no auth. A client without MCP
support can `POST` JSON-RPC 2.0 to the endpoint (`Content-Type: application/json`):
`initialize`, then `tools/list` and `tools/call`. If the endpoint does not answer, use
Path B (`api-reference.md`).

**Not every company is enabled.** If a tool says the company does not take bookings (or
answer questions) from AI agents yet, use Path B for a router or personal link, or give the
person the company's link to use in a browser.

## Tools

All times are ISO-8601 instants in UTC. Send `startTime` values back exactly as received.

### Find the link

| Tool | Input | Output |
|---|---|---|
| `website-booking-link-find` | `websiteUrl` (the company's public `https` page) | `found`, `bookingLinks` (`bookingLink`, `supported`, `note`), `skillUrl`, `message` |

Use it only when you know the company's website but not its booking link. `found: false`
is a normal answer: ask the person for the company's Chili Piper booking link. Use only a
link with `supported: true`.

### Book

| Tool | Input | Output |
|---|---|---|
| `booking-link-describe` | `bookingLink` | `linkType`, `routerSlug` (router only), `formFields` (`ref`, `label`, `required`) |
| `booking-slots-find` | `bookingLink`, `guestEmail`, `guestTimezone` (IANA), `formValues` (opt, map `ref` → value), `from` (opt, default now), `days` (opt, 1–7, default 7), `meetingTypeId` (opt) | `bookingSessionId`, `outcome`, `durationMinutes`, `redirectUrl`, `startTimes`, `meetingTypeId`, `meetingTypes`, `locations` |
| `booking-create` | `bookingLink`, `bookingSessionId`, `startTime`; not for a router link: also `guestEmail`, `guestTimezone`, `formValues`; opt: `meetingTypeId`, `location` | `meetingId`, `startTime` |
| `live-call-request` | `bookingLink`, `bookingSessionId`, `guestPhone` (opt, E.164), `meetingTypeId` (opt) | `state`, `meetingId`, `calendarFallback`, `redirectUrl` |
| `live-call-status` | `bookingLink`, `bookingSessionId` | `state`, `meetingId`, `calendarFallback`, `redirectUrl` |

`linkType` values:

| `linkType` | Link |
|---|---|
| `router` | `/concierge-router/link/<slug>` or `/router/<slug>`. The company routes the guest to the right rep |
| `personal` | `/me/<userSlug>/<linkSlug>`. One fixed person |
| `round-robin`, `group`, `ownership` | `/round-robin/<slug>`, `/group/<slug>`, `/ownership/<slug>`. A team link |
| `shared` | `/shared/<userSlug>/<slug>`. A team link that one user shares |
| `one-time` | `/once/<id>`. A link the host sent this guest. It offers the link's open times and books once |
| `suggested-times` | `/suggested-times/<id>`. The host proposed some times. `startTimes` holds only the proposed times that are still open; another time is refused |

Tools reject links that are not Chili Piper booking links of the server's environment. The
server sets everything else (trigger, routing options). You cannot add guests — the same as
on the booking page.

`outcome` values:

| `outcome` | Meaning |
|---|---|
| `calendar-offered` | `startTimes` holds the open times |
| `no-calendar` | Router link only. The company does not offer a calendar to this guest now: it sends them to `redirectUrl`, or its team contacts them live. `startTimes` is empty |
| `live-call-offered` | Router link only. The company offers a phone call now ("talk now"); see `liveCall` and `mcp-live-call.md`. If `liveCall.calendarAlsoOffered` is `true`, `startTimes` also holds open times |

**Meeting type choice.** `meetingTypes` lists the meeting types the link offers (`id`,
`name`, `durationMinutes`). `meetingTypeId` is the one the `startTimes` are for (default:
the link's first). For another one, call `booking-slots-find` again with its `id` as
`meetingTypeId`. If you also give `meetingTypeId` to `booking-create`, it must be the one
of the session.

**Location choice.** `locations` lists the locations the guest can choose (`id`, `kind`,
`label`, `details`, `guestValueRequired`). The first one is the default. `kind` is one of
`guest-provided`, `custom`, `host-conference-details`, `in-person`,
`calendar-conference`, `zoom`, `gong`, `go-to-meeting`, `microsoft-teams`, `ring-central`,
`webex`. To use another one, give `booking-create` `location: {"id": <id>}`. If
`guestValueRequired` is `true`, also send `value`: the guest's own meeting link, phone or
address (at most 500 characters). Do not send `value` for other locations.

**Live call.** Outcome `live-call-offered`, `liveCall`, `live-call-request` and
`live-call-status`: → `mcp-live-call.md`.

**One-time and suggested-times links.** The same tools work, with the guest fields as for a
personal link. One booking uses the link up. A used or currently reserved link is a tool
error. If the tool says an AI agent cannot book from this link (for example a link from a
Handoff), give the person the link to book in a browser.

### Ask the company a question

| Tool | Input | Output |
|---|---|---|
| `company-question-ask` | `bookingLink` (the company's router link), `question` (at most 500 characters) | `found`, `excerpts` (`text`, `heading`, `sourceTitle`, `sourceUrl`), `message` |

The answers come from the company's own knowledge base, the one its website chat uses. Only
a router link works; other link types are refused.

### Manage a booked meeting

Every tool takes `meetingLink`: the reschedule or cancel link from the person's calendar
invite (`https://<sub>.chilipiper.com/reschedule/<id>` or `/cancel/<id>`). Right after
`booking-create` you can use `bookingLink` + `meetingId` instead.

| Tool | Extra input | Output |
|---|---|---|
| `meeting-get` | — | `meetingId`, `status`, `startTime`, `endTime`, `hostName`, `title`, `description`, `joinDetails`, `reminders` |
| `meeting-calendar-file` | — | `meetingId`, `fileName`, `mimeType` (`text/calendar`), `ics`, `addToCalendar` (`google`, `outlook`, `office365`) |
| `meeting-reschedule-slots` | `guestTimezone`, `from` (opt), `days` (opt, 1–7) | `meetingId`, `durationMinutes`, `startTimes`, `localStartTimes` |
| `meeting-reschedule` | `startTime` (one of `startTimes`) | `meetingId`, `startTime`, `endTime` |
| `meeting-cancel` | — | `meetingId`, `status: canceled` |

- `status`: `scheduled`, `canceled`, `no-show` or `completed`.
- `joinDetails`: `joinUrl` (video call link), `provider` (for example `google-meet`,
  `microsoft-teams`, `zoom`), `location` (phone, address or other text), `note` (where to
  find the details if the record does not have them).
- For a Google Meet or Microsoft Teams call, the host's calendar makes the join link when
  it creates the event. If `joinUrl` is missing and `note` says so, call `meeting-get`
  again after a minute.
- `reminders`: `channel` (`email` or `sms`) and `sendsAt`. Empty when canceled.
- `meeting-reschedule-slots` keeps the same host and meeting type. `localStartTimes` are
  the `startTimes` in the guest's time zone, in the same order.
- The change tools refuse canceled, started and past meetings. `meeting-calendar-file`
  refuses canceled meetings.

## Flow — book

1. `booking-link-describe` with the link. Ask the person for every `required` field you
   do not have. Do not put the email in `formValues`; use `guestEmail`.
2. `booking-slots-find` with the email, the field values (keys = `ref`), the person's time
   zone and the window.
   - `calendar-offered` → show 3–5 `startTimes` in the person's time zone. If the tool
     says there are no open times, call again with `from` 7 days later.
   - `no-calendar` → the company does not offer a meeting to this person now. Tell them.
     Give them `redirectUrl` if it is set, else the booking link to use in a browser.
   - `live-call-offered` → follow `mcp-live-call.md` (or book one of `startTimes` if
     `liveCall.calendarAlsoOffered` and the person prefers a meeting).
3. If `meetingTypes` has more than one item, or `locations` has more than one item, tell
   the person the options (name and duration; location `label` and `details`). For
   another meeting type, run step 2 again with its `meetingTypeId`. If the chosen location
   has `guestValueRequired`, ask for the value.
4. **Checkpoint** (see `SKILL.md`): get an explicit yes for slot, time zone, meeting type,
   location and values.
5. `booking-create` with the same `bookingLink`, the `bookingSessionId` and the chosen
   `startTime`, exactly as returned. For every link type except a router link, also send
   `guestEmail`, `guestTimezone` and `formValues` (the same values as in step 2). Add
   `location` only if the person chose a location that is not the first one. Call it
   promptly: a router session expires after about 10 minutes. If the session expired, run
   step 2 again.
6. Report the result (`SKILL.md` Step 6). Offer `meeting-calendar-file` if the person
   wants the meeting in another calendar.

## Flow — ask a question

1. `company-question-ask` with the router link and the question. Keep the key words; leave
   out personal data.
2. `found: true` → answer only from `excerpts` and name `sourceTitle` (and `sourceUrl`
   when there is one). If the excerpts do not answer the question, say that the company did not publish
   the answer.
3. `found: false`, or an error that the company has no knowledge base or does not answer AI
   agents → tell the person you could not find the answer. Offer to book a meeting.

## Flow — manage a meeting

1. `meeting-get` with the invite link. Show the time in the person's time zone, the host,
   the status and how to join.
2. Reschedule: `meeting-reschedule-slots`, offer 3–5 times, get an explicit yes, then
   `meeting-reschedule`.
3. Cancel: get an explicit yes, then `meeting-cancel`. The host and the guest get a
   cancellation.
4. Add to a calendar: `meeting-calendar-file`. Give the person an `addToCalendar` link, or
   save `ics` as `fileName`. No Checkpoint: it changes nothing.

## Errors

Tool errors come back as a result with `isError: true` and a short message that says what
to do (for example which form fields are missing, or that the time is no longer free). Fix
the input and call again. If the guest already has a meeting from this link, do not book
again. If the message says the service failed, retry once, then use Path B or give the
person the link.

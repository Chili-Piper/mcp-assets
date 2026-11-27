# chili-piper-guest — live call reference (Path A)

A router link can offer "talk now": Chili Piper calls the guest's phone at once and connects a
rep. Only the guest MCP server (`mcp-reference.md`) can start it. Same endpoint, same rules.

## Offer

With outcome `live-call-offered`, `booking-slots-find` returns `liveCall`:

- `calendarAlsoOffered`: the guest can also book one of `startTimes` instead.
- `guestPhoneNeeded`: the form has no valid phone number; send `guestPhone` to
  `live-call-request`.
- `callTopics` (`meetingTypeId`, `name`): empty unless the guest must choose a topic. Then
  send the chosen `meetingTypeId` to `live-call-request`.

`state` values of `live-call-request` and `live-call-status`:

| `state` | Meaning |
|---|---|
| `not-started` | No call yet |
| `calling` | Chili Piper is calling the guest or looking for a rep |
| `connected` | The guest talks to a rep. `meetingId` is set when the call is logged as a meeting |
| `completed` | The call ended normally |
| `missed` | No rep or the guest did not answer. `calendarFallback: true` → call `booking-slots-find` again to offer times; else give the person `redirectUrl` if set |
| `expired` | The session timed out. Run `booking-slots-find` again |

Treat a `state` not in this table as "no call".

## Flow

1. Tell the person the company can call them now (and, if `calendarAlsoOffered`, that
   they can book a time instead). If `callTopics` is not empty, let them choose a topic.
   If `guestPhoneNeeded`, ask for the phone number in E.164 format.
2. **Checkpoint:** a real call starts at once. Get an explicit yes for the call and the
   phone number. Call promptly: the router session expires after about 10 minutes.
3. `live-call-request` with the same `bookingLink` and `bookingSessionId`, plus
   `guestPhone` and `meetingTypeId` when needed. Never call it twice for one session; a
   second request while a call runs returns the running call.
4. Tell the person to answer the phone. `live-call-status` every few seconds until
   `connected`, `completed`, `missed` or `expired`.
5. `missed` with `calendarFallback: true` → `booking-slots-find` again and continue with
   `mcp-reference.md` § Flow — book step 2. `missed` without it → give `redirectUrl` or the booking link.
   `expired` → `booking-slots-find` again.

Tool errors of `live-call-request` say what to fix: no call offered, topic required or
unknown, phone number required or not callable.

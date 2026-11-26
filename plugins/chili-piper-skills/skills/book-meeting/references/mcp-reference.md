# book-meeting — MCP reference (Path A)

The Chili Piper booking MCP server is public and needs **no authentication**. It is a
separate server from the Chili Piper admin MCP and has only prospect tools.

| Environment | MCP endpoint (Streamable HTTP, JSON-RPC 2.0) |
|---|---|
| Production | `https://fire.chilipiper.com/api/fire-edge/v1/prospect/mcp` |
| Staging | `https://fire.chilipiper.io/api/fire-edge/v1/prospect/mcp` |

Use the endpoint of the booking link's domain: `*.chilipiper.com` → Production,
`*.chilipiper.io` → Staging.

**Connect:** add the endpoint as a remote MCP server with no auth. A client without MCP
support can `POST` JSON-RPC 2.0 to the endpoint (`Content-Type: application/json`):
`initialize`, then `tools/list` and `tools/call`. If the endpoint does not answer, use
Path B (`api-reference.md`).

## Tools

| Tool | Input | Output |
|---|---|---|
| `booking-link-describe` | `bookingLink` | Link type and the form fields to fill: `ref`, `label`, `required` |
| `booking-slots-find` | `bookingLink`, `guestEmail`, `guestTimezone` (IANA), `formValues` (opt, map `ref` → value), `from` (opt, ISO instant, default now), `days` (opt, 1–7, default 7) | `bookingSessionId`, `outcome`, `durationMinutes`, `redirectUrl`, `startTimes` (ISO instants, UTC) |
| `booking-create` | `bookingLink`, `bookingSessionId`, `startTime` (one of `startTimes`) | `meetingId`, `startTime` |

Tools reject links that are not Chili Piper booking links of the server's environment.
The server sets everything else (trigger, routing options). You cannot add guests or
change the location — the same as on the booking page.

## Flow

1. `booking-link-describe` with the link. Ask the person for every `required` field you
   do not have. Do not send the email inside `formValues`; pass it as `guestEmail`.
2. `booking-slots-find` with the email, the field values (keys = `ref`), the person's time
   zone and the window.
   - `outcome: calendar-offered` → `startTimes` holds the open times. Show 3–5 of them in
     the person's time zone. If empty, call again with `from` 7 days later.
   - `outcome: no-calendar` → the company does not offer a meeting to this person now.
     Tell them; give them `redirectUrl` if it is set.
   - `outcome: other` (for example a live call) → give the person the booking link to finish in a browser.
3. **Checkpoint** (see `SKILL.md`): get an explicit yes for slot, time zone and values.
4. `booking-create` with the same `bookingLink`, the `bookingSessionId` and the chosen
   `startTime`, exactly as returned. Call it promptly: the session expires after about
   10 minutes. If it expired, run step 2 again.
5. Report the result (`SKILL.md` Step 6).

## Errors

Tool errors come back as a result with `isError: true` and a short message that says what
to do (for example which form fields are missing). Fix the input and call again. If the
message says the service failed, retry once, then use Path B or give the person the link.

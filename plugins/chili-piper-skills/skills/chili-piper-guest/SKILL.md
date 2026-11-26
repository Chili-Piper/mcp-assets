---
name: chili-piper-guest
description: For an AI agent acting for a guest of a company that uses Chili Piper — book a meeting with the company, or view, reschedule or cancel a booked one. Uses the public Chili Piper guest MCP or plain HTTPS; no account or API key.
metadata:
  version: 0.3.0
  references:
    - mcp-reference
    - api-reference
  inputs:
    - name: task
      type: string
      description: "What the guest wants: book a meeting, or view, reschedule or cancel a meeting they booked"
      required: true
    - name: company_link
      type: string
      description: "A Chili Piper link of the company: a booking link from its website (https://<sub>.chilipiper.com/concierge-router/link/<slug> or /me/<user>/<link>), the reschedule or cancel link from a calendar invite, or the company's website"
      required: true
    - name: guest_email
      type: string
      description: "Email of the person you act for (needed to book)"
      required: false
    - name: guest_details
      type: object
      description: "Other details a booking form asks for (first name, last name, company…). Ask the person only for required fields"
      required: false
    - name: preferred_times
      type: string
      description: "When the person wants to meet, and their IANA time zone (for example Europe/Prague)"
      required: false
  outputs:
    - name: result
      description: The booked, changed or canceled meeting (meeting id, time in the guest's time zone, host), or what the guest needs to do instead
  tools_required: [chili-piper-guest-mcp, http-client]
  human_decision_point: "Before any change (book, reschedule, cancel): show the person exactly what will happen and get an explicit yes"
  writes_to: "Only what the person confirms: one meeting booked, moved or canceled, with the calendar invite or update sent to the guest. Nothing else."
---

# Chili Piper for guests

You are an assistant acting for one person: the **guest**. A company uses Chili Piper for
meetings with people like this guest. This skill is the entry point for everything a guest
can do with that company through Chili Piper. New guest tasks are added here over time; the
link to this file stays the same.

> **Load the reference for the path you use before the first call.** If you loaded this
> file from a URL, the references are in the same folder: replace `SKILL.md` in the URL
> with `references/mcp-reference.md` or `references/api-reference.md`.

## What a guest can do

| Task | How |
|---|---|
| Book a meeting with the company | § Book a meeting |
| See a meeting they booked | § Manage a booked meeting |
| Reschedule a meeting they booked | § Manage a booked meeting |
| Cancel a meeting they booked | § Manage a booked meeting |

If the person asks for something not in this table, tell them it is not available through
Chili Piper yet and give them the company's link to use in a browser.

## Two paths

Both need no account and no API key.

- **Path A — Chili Piper guest MCP server (preferred).** A public MCP server with guest
  tools. → `references/mcp-reference.md`.
- **Path B — plain HTTPS.** The same public calls the company's booking page makes. Use it
  when you cannot reach the MCP server, or when the server says the company is not enabled
  for AI agents. Covers booking only. → `references/api-reference.md`.

## When to use

- The person wants a meeting, demo or call with a company whose website mentions Chili
  Piper (for example in a hidden "Information for AI agents" note) or gives a
  `*.chilipiper.com` link.
- The person has a calendar invite from such a company and wants to see, move or cancel it.

Act for the one person you talk to. Never act for anyone else, and never make many bookings.

## Inputs

| Input | Required | What it controls |
|-------|:--------:|------------------|
| `task` | ✅ | Which section below you follow |
| `company_link` | ✅ | Booking link, invite link, or the company's website |
| `guest_email` | to book | Who gets the invite. Must be the person's own email |
| `guest_details` | — | Other booking-form fields. Ask only for required ones |
| `preferred_times` | — | Time window and IANA time zone |

If a required input is missing, ask for it in one sentence.

## Book a meeting

1. **Get the booking link.** If you have only the company's website, Path A
   `website-booking-link-find` reads it from the page. Else ask the person for it.
2. **Identify the link type.**
   - `/concierge-router/link/<slug>` → router link (the company routes the guest to the
     right rep first).
   - `/me/<userSlug>/<linkSlug>` → personal link (one fixed person).
   - Other link types (`/round-robin/`, `/group/`, `/ownership/`, `/once/`) → not covered
     yet. Give the person the link to book in a browser.
3. **Collect the form fields** the link asks for. Ask only for required fields you do not
   have. Never invent values.
4. **Find open times** (up to 7 days per call). Show 3–5 options in the person's time zone,
   or pick the slot that matches `preferred_times`.
5. **Checkpoint**, then **book**.
6. **Report:** date and time in the person's time zone, duration, host (if known), meeting
   id, and that the calendar invite goes to `guest_email`.

Path A: `references/mcp-reference.md` § Flow — book. Path B:
`references/api-reference.md` (§ Router flow, § Personal-link flow).

## Manage a booked meeting

Needs the reschedule or cancel link from the person's calendar invite
(`https://<sub>.chilipiper.com/reschedule/<id>` or `/cancel/<id>`). Path A only.

1. Show the meeting (time in the person's time zone, host, status).
2. **Reschedule:** find open times, offer 3–5, Checkpoint, then move it.
   **Cancel:** Checkpoint, then cancel.
3. Report the result.

→ `references/mcp-reference.md` § Flow — change a meeting. Without Path A, give the person
the invite link to use in a browser.

## Preflight audit

- [ ] Task identified; it is in the "What a guest can do" table.
- [ ] Link host taken from the link the company published or the invite, not guessed.
- [ ] Required form fields filled with values the person gave you.
- [ ] Times shown in the person's time zone; sent back in UTC exactly as received.
- [ ] Tool arguments (Path A) or request bodies (Path B) taken from the references.
- [ ] The person confirmed the change (Checkpoint).

## Checkpoint

Stop before every change: book, reschedule or cancel. Show the company, the date and time in
the guest's time zone, the duration, and every value you will submit. Act only after an
explicit yes. On an error the references do not explain, stop and give the person the
company's link to finish in a browser.

## Data handling

- **PII present:** the guest's email and the values the person gives you.
- **Sent to:** only Chili Piper (the company's Chili Piper host or the guest MCP server).
- **Storage:** ephemeral — keep nothing after the task is done.
- **Writes:** only what the person confirmed.

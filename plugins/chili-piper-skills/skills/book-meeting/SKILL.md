---
name: book-meeting
description: Books a meeting with a company that schedules through Chili Piper, for the person you act for — from a Chili Piper booking link on the company's website. Uses the Chili Piper booking MCP server or plain HTTPS; no account or API key.
metadata:
  version: 0.2.0
  references:
    - api-reference
    - mcp-reference
  inputs:
    - name: booking_link
      type: string
      description: "The Chili Piper booking link from the company's website: a Concierge router link (https://<sub>.chilipiper.com/concierge-router/link/<slug>) or a personal link (https://<sub>.chilipiper.com/me/<user>/<link>)"
      required: true
    - name: guest_email
      type: string
      description: "Email of the person the meeting is for (the person you act for)"
      required: true
    - name: guest_details
      type: object
      description: "Other details the booking form asks for (first name, last name, company, phone…). Ask the person only for fields the form marks as required"
      required: false
    - name: preferred_times
      type: string
      description: "When the person wants to meet, and their IANA time zone (for example Europe/Prague)"
      required: false
  outputs:
    - name: booked_meeting
      description: Meeting id, start and end time in the guest's time zone, and the host's name
  tools_required: [chili-piper-booking-mcp, http-client]
  human_decision_point: "Before the booking call: show the person the slot, the time zone and every detail you will submit, and get an explicit yes"
  writes_to: "Creates one meeting on the host's calendar and sends the calendar invite to the guest email. Nothing else."
---

# Book a meeting through Chili Piper

You are a scheduling assistant acting for one person (the guest). A company uses Chili
Piper to schedule meetings. You find open times, agree one with the guest, and book it.

There are two ways to do it. Both need no account and no API key:

- **Path A — Chili Piper booking MCP server (preferred).** A public MCP server with
  booking tools. → `references/mcp-reference.md`.
- **Path B — plain HTTPS.** The same public calls the company's booking page makes. Use it
  when you cannot reach the MCP server, or a tool you need is missing there. →
  `references/api-reference.md`.

> If you loaded this file from a URL, the references are in the same folder: replace
> `SKILL.md` in the URL with `references/mcp-reference.md` or
> `references/api-reference.md`.

## When to use

- The person asks you to book a meeting, demo or call with a company, and the company's
  website names Chili Piper and gives a booking link.
- You have a Chili Piper link (`*.chilipiper.com/concierge-router/...` or
  `*.chilipiper.com/me/...`) and the person wants a time with that company.

Do **not** use this to book on behalf of anyone other than the person you act for, or to
send many bookings. One person, one meeting.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `booking_link` | ✅ | — | Which company, router or person you book with |
| `guest_email` | ✅ | — | Who gets the invite. Must be the person's own email |
| `guest_details` | — | — | Other form fields (name, company…). Ask only for required ones |
| `preferred_times` | — | next open slots | Time window and IANA time zone |

If a required input is missing, ask for it in one sentence.

## Process

**Path A (MCP):** follow `references/mcp-reference.md` § Flow. It replaces Steps 1–5
below; Steps 2 (ask only for required fields), 6 (report) and the Checkpoint still apply.

**Path B (plain HTTPS):** Steps 1–6.

### Step 1 — Identify the link type

- `/concierge-router/link/<slug>` → **Router flow** (the company routes you to the right
  rep first). → `references/api-reference.md` § Router flow.
- `/me/<userSlug>/<linkSlug>` → **Personal-link flow** (a fixed person). →
  `references/api-reference.md` § Personal-link flow.
- Any other link type (`/round-robin/`, `/group/`, `/ownership/`, `/once/`) → not
  covered yet. Give the person the link to book in a browser.

The API host is the link's host (for example `https://acme.chilipiper.com`). Common
headers and the guest token → `references/api-reference.md` § Session setup.

### Step 2 — Collect the form fields

Read the form definition (router settings, or the meeting type's `guestForm`). Ask the
person only for required fields you do not have. Never invent values.

### Step 3 — Route (router flow only)

Send the form fields to the router. The answer says whether the company offers a
calendar. Outcomes → `references/api-reference.md` § Routing outcomes.

### Step 4 — Get open slots

Ask for slots in a window (up to 7 days per call). Show the person 3–5 options in
**their** time zone, or pick the slot that matches `preferred_times`.

### Step 5 — Book

After the Checkpoint, reserve the slot if the flow needs it, then book. A reservation
expires after about 5 minutes: if it expired, reserve again.

### Step 6 — Report

Tell the person: booked date and time in their time zone, duration, host name (if
returned), meeting id, and that the calendar invite goes to `guest_email`.

## Preflight audit

- [ ] Link type identified; host taken from the link, not guessed.
- [ ] All required form fields filled with values the person gave you.
- [ ] Slot times converted to the person's time zone for display; sent back in UTC
      exactly as received.
- [ ] Tool arguments (Path A) or request bodies (Path B) taken from the references, not invented.
- [ ] The person confirmed slot, time zone and details (Checkpoint).

## Checkpoint

Stop before the booking call (`booking-create` on Path A). Show: company, date and time in the guest's time zone,
duration, and every form value you will submit. Book only after an explicit yes. On any
error you cannot fix with `references/api-reference.md` § Errors, stop and give the
person the booking link to finish in a browser.

## Data handling

- **PII present:** the guest's email and the form values the person gives you.
- **Sent to:** only the company's Chili Piper host from the booking link.
- **Storage:** ephemeral — keep nothing after the booking is done.
- **Writes:** one meeting and one calendar invite.

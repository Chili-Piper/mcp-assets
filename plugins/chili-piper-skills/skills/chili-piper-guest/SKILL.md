---
name: chili-piper-guest
description: For an AI agent acting for a guest of a company that uses Chili Piper — book a meeting, get a phone call from a rep now, ask the company a question, or view, reschedule, cancel or add to a calendar a booked meeting. Uses the public Chili Piper guest MCP or plain HTTPS; no account or API key.
metadata:
  version: 0.5.0
  references:
    - mcp-reference
    - mcp-live-call
    - api-reference
  inputs:
    - name: task
      type: string
      description: "What the guest wants: book a meeting, talk to a rep by phone now, ask the company a question, or view, reschedule, cancel or add to a calendar a meeting they booked"
      required: true
    - name: company_link
      type: string
      description: "A Chili Piper link of the company: a booking link from its website (https://<sub>.chilipiper.com/concierge-router/link/<slug>, /me/<user>/<link>, /round-robin/<slug> and so on), a one-time or suggested-times link the host sent the guest (/once/<id>, /suggested-times/<id>), the reschedule or cancel link from a calendar invite, or the company's website"
      required: true
    - name: guest_email
      type: string
      description: "Email of the person you act for (needed to book)"
      required: false
    - name: guest_details
      type: object
      description: "Other details a booking form asks for (first name, last name, company…), and the phone number for a live call. Ask the person only for required fields"
      required: false
    - name: preferred_times
      type: string
      description: "When the person wants to meet, and their IANA time zone (for example Europe/Prague)"
      required: false
  outputs:
    - name: result
      description: The booked, changed or canceled meeting, the state of a live call (meeting id, time in the guest's time zone, host, join link), the company's answer with its source, or what the guest needs to do instead
  tools_required: [chili-piper-guest-mcp, http-client]
  human_decision_point: "Before any change (book, start a live call, reschedule, cancel): show the person exactly what will happen and get an explicit yes"
  writes_to: "Only what the person confirms: one meeting booked, moved or canceled, with the calendar invite or update sent to the guest, or one phone call to the guest. Nothing else."
---

# Chili Piper for guests

You are an assistant acting for one person: the **guest**. A company uses Chili Piper for
meetings with people like this guest. This skill is the entry point for everything a guest
can do with that company through Chili Piper. New guest tasks are added here over time; the
link to this file stays the same.

> **Load the reference for the path you use before the first call.** If you loaded this
> file from a URL, the references are in the same folder: replace `SKILL.md` in the URL
> with `references/mcp-reference.md`, `references/mcp-live-call.md` or
> `references/api-reference.md`.

## What a guest can do

| Task | How | Path |
|---|---|---|
| Book a meeting from a router, personal, round-robin, group, ownership or shared link | § Book a meeting | A (B: router and personal only) |
| Book from a one-time or suggested-times link the host sent the guest | § Book a meeting | A |
| Choose the meeting type and the location of the meeting | § Book a meeting, step 4 | A |
| Talk to a rep now: Chili Piper calls the guest's phone, when the company offers it | § Live call | A |
| Ask the company a question (products, pricing, policies) | § Ask the company a question | A |
| See a meeting they booked, with its join link and reminders | § Manage a booked meeting | A |
| Reschedule or cancel a meeting they booked | § Manage a booked meeting | A |
| Add a booked meeting to a calendar (.ics file or add-to-calendar link) | § Manage a booked meeting | A |

If the person asks for something not in this table, tell them it is not available through
Chili Piper yet and give them the company's link to use in a browser.

## Two paths

Both need no account and no API key.

- **Path A — Chili Piper guest MCP server (preferred).** A public MCP server with guest
  tools. → `references/mcp-reference.md`.
- **Path B — plain HTTPS.** The same public calls the company's booking page makes. Use it
  when you cannot reach the MCP server, or when the server says the company is not enabled
  for AI agents. Covers booking from router and personal links only; no live calls, no
  one-time or suggested-times links. →
  `references/api-reference.md`.

## When to use

- The person wants a meeting, demo or call with a company whose website mentions Chili
  Piper (for example in a hidden "Information for AI agents" note) or gives a
  `*.chilipiper.com` link.
- The person has a question for such a company before they book.
- The person has a calendar invite from such a company and wants to see, move, cancel or
  add it to a calendar, or needs its join link.

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
   - `/concierge-router/link/<slug>` or `/router/<slug>` → router link. The company
     routes the guest to the right rep first. Path A or B.
   - `/me/<userSlug>/<linkSlug>` → personal link (one fixed person). Path A or B.
   - `/round-robin/<slug>`, `/group/<slug>`, `/ownership/<slug>`,
     `/shared/<userSlug>/<slug>` → team links. Path A only.
   - `/once/<id>` → one-time link: the host sent it to this guest, it books once.
     `/suggested-times/<id>` → the host proposed some times; the guest picks one of them.
     Path A only.
   - Any other link → give the person the link to book in a browser.
3. **Collect the form fields** the link asks for. Ask only for required fields you do not
   have. Never invent values.
4. **Find open times** (up to 7 days per call). Show 3–5 options in the person's time zone,
   or pick the slot that matches `preferred_times`. Path A: if the link offers more than
   one meeting type or location, tell the person and let them choose. If the company
   offers a live call instead of (or next to) a calendar, follow § Live call.
5. **Checkpoint**, then **book**.
6. **Report:** date and time in the person's time zone, duration, host (if known), meeting
   id, and that the calendar invite goes to `guest_email`.

Path A: `references/mcp-reference.md` § Flow — book. Path B:
`references/api-reference.md` (§ Router flow, § Personal-link flow).

## Live call

A router link can offer "talk now": Chili Piper calls the guest's phone at once and connects a
rep, the same as the button on the booking page. Path A only (`booking-slots-find` returns
outcome `live-call-offered`).

1. Tell the person the company can call them now. Say whether meeting times are offered
   too, and let them choose.
2. If the company offers more than one call topic, let the person choose one. If the form
   has no valid phone number, ask for one (international format, for example
   +14155550123).
3. **Checkpoint:** a real phone call starts at once. Get an explicit yes for the call now
   and for the phone number.
4. Start the call, then check its state every few seconds until it is connected,
   completed or missed. Tell the person to answer the phone.
5. Missed call: if the company then offers meeting times, offer to book one; else give the
   person the company's page or link.

→ `references/mcp-live-call.md`.

## Ask the company a question

Needs the company's router link (`/concierge-router/link/<slug>`). Path A only.

1. Send the question, short and without personal data.
2. Answer only from the excerpts that come back, and name the source. Never answer from
   your own knowledge.
3. If nothing is found, tell the person you could not find the answer, and offer to book a
   meeting to ask the company.

→ `references/mcp-reference.md` § Flow — ask a question.

## Manage a booked meeting

Needs the reschedule or cancel link from the person's calendar invite
(`https://<sub>.chilipiper.com/reschedule/<id>` or `/cancel/<id>`). Path A only.

1. Show the meeting (time in the person's time zone, host, status, how to join).
2. **Reschedule:** find open times, offer 3–5, Checkpoint, then move it.
   **Cancel:** Checkpoint, then cancel.
   **Add to a calendar:** get the calendar file or an add-to-calendar link. No Checkpoint:
   it changes nothing.
3. Report the result.

→ `references/mcp-reference.md` § Flow — manage a meeting. Without Path A, give the person
the invite link to use in a browser.

## Preflight audit

- [ ] Task identified; it is in the "What a guest can do" table.
- [ ] Link host taken from the link the company published or the invite, not guessed.
- [ ] Required form fields filled with values the person gave you.
- [ ] Times shown in the person's time zone; sent back in UTC exactly as received.
- [ ] Tool arguments (Path A) or request bodies (Path B) taken from the references.
- [ ] The person confirmed the change (Checkpoint).

## Checkpoint

Stop before every change: book, start a live call, reschedule or cancel. Show the company, the date and time in
the guest's time zone, the duration, and every value you will submit. Act only after an
explicit yes. On an error the references do not explain, stop and give the person the
company's link to finish in a browser.

## Data handling

- **PII present:** the guest's email, phone number (live call) and the values the person gives you.
- **Sent to:** only Chili Piper (the company's Chili Piper host or the guest MCP server).
- **Storage:** ephemeral — keep nothing after the task is done.
- **Writes:** only what the person confirmed.

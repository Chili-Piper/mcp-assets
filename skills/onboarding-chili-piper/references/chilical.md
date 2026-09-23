# ChiliCal

Scheduling links. Formerly Instant Booker. The ChiliCal Co-Pilot is the browser extension, not a separate licence. Read `shared-assets.md` first.

## Choosing the link type

Falls out of the interview rather than being defaulted:

| Link type | When | Create tool |
|---|---|---|
| Round-robin | a shared pool takes the booking | `scheduling-link-create-round-robin` |
| Ownership | the CRM already holds an owner | `scheduling-link-create-ownership` |
| Group | several people must attend | `scheduling-link-create-group` |
| Admin one-on-one | a named person | `scheduling-link-create-admin-one-on-one` |

Check the assumption before building: an ownership link needs an owner field that is actually populated, and any link needs hosts whose availability is configured.

Personal links have a list tool (`scheduling-link-list-personal-v2`); search the `scheduling-link` category before telling a customer one cannot be changed.

## Links come back ready to use

Every create returns `linkId`, `workspaceId`, `slug` and **`bookingUrl`**, the live guest-facing booking page. Hand the customer that URL as-given; do not assemble one from the slug. Admin edit link is `/workspaces/<wsId>/chilical/scheduling-links/<type>/<linkId>/edit`, where `<type>` is `one-on-one`, `round-robin`, `group` or `ownership`.

## Settings that decide whether it looks right

- **Availability Increments** is the booking interval (e.g. 30 min); **Duration** is the meeting length. They are different fields and customers conflate them.
- Blocked days and **Meeting Buffers** before/after.
- Availability windows come from the rep's own calendar connection. Each user connects their own in MyApp, up to six calendars (help 44647649661971). No Admin can do it for them, and the company-level integration does not substitute.

## Gotchas

- **Reporting.** The CRM Booking Status field is not populated for ChiliCal. Report via Meeting Type / Path / Router.
- **Availability looks empty though the calendar looks open:** check the calendar connection, availability windows, buffers and blocked days, in that order. Also check what the calendar platform itself counts as busy (help 43621591559827): declined recurring meetings and unaccepted invites still block time if the event is marked busy.

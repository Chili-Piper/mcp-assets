# Handoff

Rep-initiated internal routing: an SDR books onto the correctly routed AE's calendar, or an AE pulls in a solutions consultant. Read `shared-assets.md` first.

Same routing logic as Concierge, different trigger and different experience. The trigger is a person, not a form, so establish in the interview what point in the rep's day starts it.

## What is different from Concierge

- **Booker and host are two different people.** The booker is the internal rep who scheduled the meeting; the host is whoever's calendar it lands on. Concierge has no booker at all, so anywhere that distinction is configurable it only becomes a real choice here: meeting-location `host` takes `BookerIfExists` as well as `AssigneeIfExists`, and the same split applies to who a reminder appears to come from and who a HubSpot engagement is assigned to (§ CRM actions).
- **Every path books.** A Handoff row and its catch-all can only be a Schedule outcome. Redirect, Slack notify and no-show timeouts are Concierge only, so nothing in `concierge.md` about turning people away applies here.
- **The prospect may not be in the CRM.** The trigger is any guest email entered in the Scheduler, whether from the browser extension, Gmail or the CRM (help 29684412579987), so an outbound SDR can book someone the CRM has never seen. That prospect matches no CRM rule. Ask whether reps book net-new prospects, and if they do, give them a destination at the catch-all. Reps can create the Lead or Contact from the Scheduler's CRM panel (help 37219166187795), but that is a rep action, not a router step.
- **Company-level calendar integration actually helps.** It is the one product it serves: an SDR can see an AE's real availability even when that AE has not connected their own calendar (help 27275421055379). It only ever *reads* free/busy. The meeting is still created on the SDR's calendar with the AE invited, and the Handoff Scheduler shows this when the setting is "Assignee's Calendar". It does nothing for Concierge or a ChiliCal team link.
- **Reporting gotcha.** The CRM Booking Status field is **not** populated for Handoff (it is for Concierge and Chat "Route for Meeting"). Report Handoff bookings by Meeting Type / Path / Router instead.
- Distribution `assignmentType` is **Meeting**, so a Handoff pool is reusable by Concierge, Chat and ChiliCal.

## Distribution handling

The booker here is a rep, who can shop for a favourite AE in a way a prospect never would. The lever for that is **Allow Booker to Pick any Team Member** (`allowPickingAssignee` on a Flexible Meeting distribution):

- **Disabled**: the SDR chooses a date and time and Chili Piper picks the assignee from that choice. A blind pick, so no cherry-picking, while the pool's combined availability still gives them plenty of times.
- **Enabled**: the SDR can skip the next in line and browse individual calendars.

**Ask which they want.** It is a policy call about how much discretion SDRs get, and `distribution-create` makes `allowPickingAssignee` a required field on Flexible handling, so you will be setting it either way. Asking beats picking silently.

(`hideAssignee`, shown as Prevent Cherry-picking in the app, does a similar job but exists only on Strict handling, which shows one calendar at a time and so costs you the combined availability.)

A path can also book one named person with no distribution: `assignment: {type: "User", userId}`. That is the shape for a fixed fallback rep.

## Catch-all

Handoff cannot disqualify, so the catch-all question in the universal pattern has different answers here: which pool or person gets a prospect who matches no row, or no catch-all at all. With none, the Scheduler shows the prospect as disqualified and the rep has to pick an assignee or book on their own calendar by hand (help 29684412579987). Recommend a fallback pool, and leave the catch-all out only when the customer wants reps to handle unmatched prospects themselves.

## CRM actions

Handoff paths take the same post-booking `crmActions` chain as Concierge, and an omitted chain means the handoff writes nothing to the CRM. Read `concierge.md` § CRM actions for the shapes, the one-CRM rule and how to narrow a failed publish, then apply these differences:

- **No record creation.** `SalesforceUpsertRecord` / `HubspotUpsertRecord` are Concierge only, so the record-creation standing default does not go in a Handoff plan, and neither does its ordering rule.
- **Ask about ownership first.** Moving the record to the AE is often the reason for the handoff. Update Ownership sets the owner to the booked host, and the help center recommends it on every path that does not already route to the owner (help 29684412579987). Ask per row, as on Concierge.
- **Booker or assignee on the HubSpot engagement.** `HubspotCreateEngagement` takes `owner: Assignee | Booker`, which sets who the engagement is assigned to and so who gets the activity in HubSpot reporting. Concierge has no booker, so this is only a real choice here. Ask. `SalesforceCreateEvent` has no equivalent field.
- **Relate the event to the deal.** `SalesforceCreateEvent` relates to the Lead or Contact by default; `relatedTo` adds an `Opportunity`, `Account` or `Case`, which only resolves when a Contact matched. HubSpot's `relatedTo` takes `Deal` (the open deal with the latest close date) or `Ticket`. When the handoff adds a colleague or extra guests, `guestsBehavior: CreateEvents` creates a child event per guest, and each guest needs their own Lead or Contact.
- **Do not build `ConvertLead`.** The Handoff schema accepts it, but the help center documents no Convert Lead node for Handoff routers, so treat it as on Concierge: point a customer who wants conversion at Distro Lead Conversion (`distro.md`).

## Build

- Segment paths with ownership-first and a configured fallback rep, per the universal routing pattern in `shared-assets.md`.
- `handoff-router-create` publishes live and returns `id` + `workspaceId`; deep link at `/workspaces/<wsId>/handoff/handoff-router/<id>/flow-builder`. Its schema is very large; if your client cannot hold it, use the fallback in `concierge.md` § Verify.
- **A failed publish leaves an unpublished draft**, and retrying the create mints a second one. Fix or delete the leftover in the Handoff app rather than retrying.
- **Before updating an existing router**, run `handoff-router-get` and read `routing.representable`. On an app-built router, your rows are overlaid by `ruleId` and its app-only settings are kept. **Every update publishes the router's current draft**, so unpublished edits someone made in the app go live with it, even on a rename. Ask before updating a router the customer has been editing.
- **Some settings are in the app only.** The Display Calendar settings are not in the create schema: Schedule with Another Team Member on ownership paths, where the meeting is created (the booker's calendar with the assignee invited, or the assignee's with the booker optionally invited, plus auto-decline for the booker), Additional Invitees, and the Handoff Live options node. Check the live schema first. If they are still missing, ask which the customer wants and hand them over as flow-builder steps at the deep link.

## Verify

**Run `handoff-init` rather than re-reading the router.** It is phase one of a booking: it runs the workspace's Handoff routers for a prospect as a given rep, returns each router's matched path with its assignees and open start times, and books nothing. Pass the SDR's `userId`, the `workspaceId`, and a `body` of either `{type: "CrmRequest", id: {type: "LeadId" | "ContactId", value}, interval}` or `{type: "GuestEmailRequest", guestEmail, interval}`, with `interval` as `{startsAt, duration}` (for example `"7 days"`). `body.routerId` narrows it to one router. Describe the tool before the first call.

- Test one record per row, one that should reach the catch-all, and one email the CRM does not have if reps book net-new.
- Read the returned assignees against the pool roster rather than trusting a non-empty slot list, for the same reason as on Concierge (`concierge.md` § Verify).
- **Never follow it with `handoff-schedule` as a test.** That books a real meeting and sends the invites.

**Not on the AE calendar:** check the AE's calendar connection and availability; check the routing path resolved to a rep; check the meeting type.

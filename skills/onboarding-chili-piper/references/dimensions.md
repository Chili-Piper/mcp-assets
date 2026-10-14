# Interview dimensions

The Phase 1 questions, asked in this order after the familiarity question and the open box. None is optional, but anything the open answer covered is confirmed rather than asked. How to ask them is in `interview.md`.

## 1. Where to start

> Which should we get live first? We'll set the others up after.

Take any further priorities as free text and sequence them in the plan. Map each to a motion with `use-cases.md`. The options are products, in this order, with this wording:

| # | Label | Description |
|---|---|---|
| 1 | Concierge | Someone fills in a form on your site and books a meeting there and then. |
| 2 | Chat | A conversation on your site qualifies the visitor, then books a meeting or hands them to a rep. |
| 3 | Handoff | A rep books a meeting on a colleague's calendar and passes the prospect over. |
| 4 | Distro | A new or updated Salesforce record is assigned to the right rep. |
| 5 | ChiliCal | A bookable link the rep sends out, backed by their real availability. |

Offer the first four the account can use, in that order. Drop what the tier does not cover (`account-baseline.md`) and drop Distro on a HubSpot org. ChiliCal is on every tier, so it is always last. If fewer than four survive, ask with fewer. Do not reword the descriptions or add team, page or rep names nobody mentioned.

## 2. Ownership

Two separate questions, using their CRM's own object names. First:

Salesforce:
> If the person who books, or their company, already exists in Salesforce, we can send them to whoever owns that record. Which of these should we respect: the Lead owner, the Contact owner, the Account owner?

HubSpot:
> If the person who books, or their company, already exists in HubSpot, we can send them to whoever owns that record. Which should we respect: the Contact owner, the Company owner?

Then, only if they named more than one:
> When more than one of those applies to the same person, which wins?

Offer their own selection back in a couple of orders and say any order is fine. Ask whether anything else must be true alongside ownership, but do not hunt for it.

Ownership resolves on the CRM user's email, so unmapped CRM users are not a blocker (`shared-assets.md` § Rules).

## 2b. How the pool rotates for everyone else

Whatever ownership does not catch goes to a round-robin pool: is it divided by territory, segment, product, or not at all? Take their division at face value. Capping, weighting and business hours are usually defaults, not questions.

On Concierge, say what the division needs when they choose it. A split the form carries is free. A split on something the form does not carry (usually territory) needs enrichment before routing, which needs a provider configured in Command Center. Name that as a prerequisite now, not at the build.

Flexible or Strict round-robin is per product: default Flexible on Concierge and Chat and say why in a line (more available times, more bookings); on Handoff, ask. Details in the product files.

## 3. What fires each motion

A motion with no confirmed trigger is a guess. Get it concrete: which form, on which page, on which platform (HubSpot, Marketo and Pardot submit different field names); which Salesforce object and field change fires Distro; what point in the rep's day starts a Handoff. A trigger outside the org's tier is a tier-upgrade handoff (Phase 4). **Do not enter Phase 2 with this blank.** The form platform says nothing about the CRM: a HubSpot form on a Salesforce org needs no HubSpot connection (`build-patterns.md` § One CRM).

## 3b. Concierge: where the routing data comes from

The decision runs the moment the form submits. Ask which population the segment must cover, and make sure net-new has somewhere to land. **Recommend the form**: a form value exists for every submitter, while a CRM value only resolves for people already in the CRM. Live enrichment is the middle ground. Say which you recommend and why, then let them choose (`routing-data.md`). Skip this for Distro and Handoff, which have no form. Handoff has its own net-new question, whether reps book prospects the CRM does not have, and it is settled at the catch-all (`handoff.md`).

Chat is different: a journey can enrich, read the CRM and ask the visitor, one after another, so never make Chat pick one source. Ask which fields the conversation should ask for outright, and whether an enrichment provider is available. Set **Skip if known** on the Send Data Field row so a returning visitor is not asked twice (help 27532198601107).

## 3c. Concierge: who should not get a meeting

Ask directly, as open text: personal email addresses, competitors, students and job seekers, existing customers, unsupported regions, a size floor. Then settle the catch-all: does someone who matches no booking rule get turned away or picked up by an SDR? Build detail in `concierge.md`.

## 4. Who the reps are

Check Phase 0's org-wide `workspace-list-users` first: on an established tenant the reps often exist already and just need adding to the workspace and teams.

Job function (SDR / AE / CSM) is not on the Chili Piper user record, so where people have to be added, ask how to source them: from their own CRM's MCP (users by role), or a roster (email + function + team). Then `user-invite` (it takes `licenses`, `workspaces` and `salesforceId` in one call), `team-create`, `team-add-users`.

**Adding people is its own step.** Before the first `user-invite`, say on its own: you are about to add N people, invites are created with `sendInvite: false` so **nobody gets an email**, and invites go out later with `user-send-invites` once the build is done and they have been told. Wait for an acknowledgement. After the first invite, read the user back: the stored email matches, and the licences and workspace applied.

**Build with their real people.** Never stand the config up on invented test users: a pool of placeholders routes to nobody and has to be torn down before go-live.

## 5. Tech stack

Load-bearing: the CRM (Salesforce or HubSpot), and at least one connected calendar to test against. Then video and meeting location (Zoom / Teams / Meet), sales engagement (Salesloft / Outreach / Gong), Slack, marketing automation and enrichment. On enrichment, ask whether they already own a provider (ZoomInfo, Apollo, Lusha, LeadIQ) before proposing LeadIQ through Chili Piper credits.

Recommend they also connect their own CRM's MCP: querying their records through their own credential is faster and keeps their CRM data on their side. Point at the system their reps actually work in: where marketing runs HubSpot and sales runs Salesforce, Salesforce is the CRM.

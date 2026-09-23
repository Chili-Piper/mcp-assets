# Handoffs and escalation

What goes on the Phase 4 handoff list, and how to route a customer to help.

## The handoff list

A list, as who / what / why, of anything this session could not do:

- **Write-scoped API key** if the session was read only (an Admin generates it at `/fire/admin/integrations/credentials/access-tokens`).
- **OAuth enablement** if they want browser login (Admin only, enabled per tenant by Chili Piper).
- **End-user training** with their CSM: each rep connects their own calendar and meeting location, sets availability, and installs the ChiliCal Co-Pilot extension. This is what turns "0 calendars connected" into real availability.
- **Tier upgrade** for any use case the org's tier does not cover (`chilipiper.com/pricing`), and a **licence check** only where the tier could not be read (`account-baseline.md`).
- **In-app setup** for anything you could not build, with a deep link and where it lives. **In the workspace:** Orchestrator journeys, Meeting Prep briefs, Spam Checker scoring. **In Command Center:** workspaces, enrichment providers, integrations, users and licences.

## If something errors, or they want a person

- **An error.** A call fails twice on the same thing, or you hit something outside your reach: an integration that will not authenticate, a permission you cannot grant, a tier limit, behaviour that looks like a bug. Stop retrying. **Look at it in the app first**: the flow builder often shows exactly which node is incomplete when the API only says a publish failed. Give the deep link and ask what they see. Escalate when the app agrees something is wrong.
- **They want a person.** Offer the route straight away.

Suggest the fastest route. Never restrict what they can send to Support.

1. **The help center** for "how do I" questions. You can search it for them on the spot.
2. **Support** for anything broken, blocked, access-related, or that they would rather ask a person: email `support@chilipiper.com` from the address on their account, or `https://help.chilipiper.com/hc/en-us/requests/new`.
3. **Their CSM** for training, tier upgrades and anything commercial. If they do not know who that is, Support routes it.

Draft the email for them and **do not send it yourself**: it has to come from their own address so Support can tie it to their account. Give a paste-ready subject and body: tenant subdomain, what they were building, the exact tool call and error, what they tried, and what they need back.

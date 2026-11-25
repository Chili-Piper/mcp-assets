# Standing defaults

What the Onboarding Plan proposes without being asked, one line each on why, for the customer to strike what they do not want. Each is a proposal until the live schema confirms it.

## Built in this session

- **Reminders on every meeting type.** Ask the cadence, suggesting 1 day, 1 hour and 1 minute before. Each carries a reschedule link (`shared-assets.md` § Meeting types and reminders).
- **Logging the booking on the CRM record** (`SalesforceCreateEvent` / `HubspotCreateEngagement`). Ask what it should relate to and whether cancelling deletes it (`concierge.md` § CRM actions).
- **Record creation for net-new bookers** (`SalesforceUpsertRecord` / `HubspotUpsertRecord`), so the rest of the write-back has a record to act on. Concierge only: Handoff has no record-creation action.
- **Whether routing should update record ownership.** A policy question, so ask it per motion rather than defaulting. An ownership-routed booking already went to the owner.
- **Spam Checker on any inbound form motion**, as a router step. Its scoring settings are in the workspace and shared with Chat, and the defaults do not disqualify a personal email address, so say so (`concierge.md` § Disqualification).
- **Live enrichment before routing**, where a segment needs data the form does not carry. The waterfall has to exist first (`enrichment-waterfall-list`), and its providers are configured in Command Center, so on an org with none it is a prerequisite.

Raise the rest of the write-back in the same conversation: adding to a campaign, writing form values onto the record.

## Handed over as links

Unless the live tool list now covers them. Both live inside the workspace:

- **No-show recovery**, an Orchestrator journey at `/workspaces/<wsId>/orchestrator/flows`. Run `no-show-analyzer` first to record the baseline rate.
- **Meeting Prep Agent**, a brief tied to meeting types at `/workspaces/<wsId>/chili-agents/meeting-prep-agent` (help 46519760246291; prompt guidance 46983436771347).

## Enrichment providers and credits

**Enrichment providers** are configured in Command Center: LeadIQ through Chili Piper credits at Integrations - Data Providers - LeadIQ, or their own ZoomInfo, Apollo or Lusha (help 53264550663571).

Say once that AI and enrichment features draw on the org's **credit wallet**: enrichment is a fixed rate per lookup, Meeting Prep and agents are variable, and a failed run costs nothing. Quote help 51013393126163 rather than a number, and point them at Billing for their balance. Anything outside the org's tier goes on the Phase 4 handoff list.

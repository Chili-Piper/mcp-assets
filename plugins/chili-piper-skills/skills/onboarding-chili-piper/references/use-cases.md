# Use cases and motion mapping

Maps a customer's stated priority to a Chili Piper motion, the license it needs, whether it is CRM-gated, and the tool or skill that builds it. Only offer a motion the org is licensed for (Phase 0 entitlement check). Distro is Salesforce only.

## Priority to motion lookup

| Customer says | Motion | License | CRM gate | Builds with |
|---|---|---|---|---|
| "Book inbound demo requests instantly" | Inbound - Form Concierge | Concierge | CRM for ownership/territory | `concierge-router-builder` |
| "Talk to hot leads live, not later" | Inbound - Concierge LIVE | ConciergeLive | CRM | `concierge-router-configuration` |
| "Route new leads / CRM records to the right rep" | Distro (CRM-triggered) | Distro | Salesforce only | `distro-router-configuration` |
| "Fewer no-shows / recover no-shows" | Orchestrator - no-show recovery | (Orchestrator) | CRM | Orchestrator journey + `no-show-analyzer` to baseline |
| "Recover abandoned forms / cancellations" | Orchestrator | (Orchestrator) | CRM | Orchestrator journey |
| "Clean SDR to AE handoffs" | Internal handoff | Handoff | CRM | `handoff-router-configuration` |
| "Pull in an SC / exec on a deal" | Internal handoff | Handoff | CRM | `handoff-router-configuration` |
| "Book meetings at events" | Event motion | Concierge | CRM | `concierge-router-builder` |
| "Assign CSM/AM on closed-won or signals" | Post-sale routing | Distro | Salesforce only | `distro-router-configuration` |
| "Book from inside our product (PLG)" | In-product booking | Concierge + in-app scheduling | CRM | `concierge-router-configuration`, `scheduling-link-management` |
| "Engage target accounts on the website" | Web experiences / Chat AI | Chat | CRM for ownership | `web-experience-create`, chat journey tools; search the tool list for Chat AI strategies/guidances |

If a needed license is missing, it becomes a tier-upgrade handoff (`escalation.md`), not a build.

The catalog below is for the interview, not the build: use it to offer motions the customer did not name, especially when asking what to set up next. Build detail is in the product files.

## Motion catalog

Each entry: trigger, what CP does, outcome, features.

### Inbound (Concierge)
- **High-intent demo request.** Form submits; CP enriches, checks CRM ownership and territory, shows the right rep's live calendar in the form, Spam Checker filters junk. Outcome: booked meeting in seconds. Features: Form Concierge, Spam Checker.
- **Concierge LIVE.** Hottest-intent form fill; CP routes to an available rep and connects by phone in seconds. Outcome: speed-to-lead in seconds. Features: Concierge LIVE, live phone routing.

### Distro (CRM-triggered, Salesforce only)
- **New lead / record routing.** A CRM field update or new record fires; Distro routes to the right rep/team by the router logic. Features: Distro.
- **Post-sale assignment.** Opportunity flips to Closed-Won, or an account signal fires; Distro assigns the right CSM/AM by segment, territory, capacity, with a Slack/CRM alert. Features: Distro on Opportunity/Account, Slack alerts.
- **Escalation / exec sponsor routing.** Ticket, health flag, or deal-size threshold routes to the right level with SLA. Features: Distro.

### Orchestrator (built in the workspace)
- **No-show recovery.** Detects a no-show in real time, enrolls a re-engagement sequence, sends a fresh rebook link. Features: Orchestrator flow, sequences.
- **Form abandonment.** Picks up a partial submission, enriches, enrolls a sequence, alerts the account owner. Features: Orchestrator, enrichment.
- **Last-minute cancellation.** Fires a reschedule link, notifies the booker in Slack, queues a backup rep. Features: Orchestrator, Slack.

### Internal handoff (Handoff)
- **SDR to AE.** From the CRM/inbox, the SDR books directly on the correctly routed AE's calendar, opportunity attached. Features: handoff workflows.
- **Pull in a solutions consultant.** AE finds the right SC by skill and availability and books them onto the next call. Features: internal handoff.

### Events (Concierge / Distro)
- **Pre-event booker.** Landing page routes each respondent to the attending rep and books a slot at the event. Features: Concierge.
- **Live-at-booth booker.** Rep books a booth visitor onto the right AE's live calendar from a tablet. Features: Concierge.
- **Badge-scan routing.** Scanned leads are enriched, routed by territory/ownership, and queued or followed up within hours. Features: Distro, enrichment.

### Post-sale and in-product (Concierge + in-app scheduling)
- **PLG convert.** Trial user hits a paywall; in-app booking to the right AE without leaving the product. Features: in-app scheduling, Concierge.
- **In-app CS / upsell booking.** Customer books their AM/CSM in-app, routed by account ownership. Features: in-app scheduling, account routing.
- **Tiered support request.** Routes by tier and issue to article, agent, or a senior CS calendar. Features: in-app scheduling, Concierge.

### Web / Chat AI (Chat)
- **Target account on site.** Chat AI identifies the account, opens a personalized conversation, offers the assigned AE's calendar. Features: Chat AI, account identification.
- **After-hours buyer / returning visitor.** Chat engages 24/7 or re-engages a return visit with context and books the right rep. Features: Chat AI.

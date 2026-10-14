# Onboarding Plan template

Fill this from Phase 0 reads and the Phase 1 interview. Present it and get explicit confirmation before building anything. Keep it to one screen where possible.

---

## Onboarding Plan: {customer name}

### Prerequisites (confirm before building)
- [ ] MCP connected. If not, an Admin generates an API key scoped to cover the whole build at fire.chilipiper.com/fire/admin/integrations/credentials/access-tokens
- [ ] A workspace to build in. If none is usable, search for a create tool; failing that the customer creates one at fire.chilipiper.com/fire/admin/workspaces before anything else
- [ ] CRM connected. If not, connect Salesforce or HubSpot at fire.chilipiper.com/fire/admin/integrations/built-in. If both, use the sales reps' source of truth (Salesforce when sales runs SF and marketing runs HubSpot)
- [ ] At least one connected calendar to test against (usually the Admin's own). Availability comes from each rep's own connection; the company-level calendar integration is optional and view-only, so an unconnected one is not a blocker

### Account snapshot (read in Phase 0)
- Tenant: {subdomain} ({Organization | Personal})
- Tier: {RoutingAndScheduling | Experiences | ChiliDataPlatform | NOT READ, confirm with customer and put a licence check on the CSM handoff}. The tier is the entitlement; do not report per-product booleans
- CRM connected: {Salesforce | HubSpot | none}
- Calendars: {N users with their own calendar connected} | company-level integration: {connected | not connected, optional}
- Session write capability: {write tools exposed, unconfirmed until first write | read-only}
- Admins: {N}, licensed: {N}. Operator: {name, or "assumed, only one admin"}
- Existing structure (counts, scoped to the chosen workspace): {N teams, N distributions, N rules, N meeting types | greenfield}
- Chili Piper familiarity: {new | some | expert} (sets how much you define assets as you go)
- Own CRM MCP connected: {Salesforce MCP | HubSpot MCP | not yet, recommended}
- Workspace to build in: {id and name; every read and write below is scoped to it}

### Motions, in build order (Phase 1)
Every motion the interview surfaced, not just the first. Shared assets are sized against this whole list.
1. {first to go live} -> motion: {motion} (see use-cases.md)
2. {next} -> {motion}
3. {next} -> {motion}

### Triggers confirmed (dimension 3 - do not leave blank)
- {motion}: fires on {form + page + platform | SFDC object + field change | rep action}

### Routing data source (dimension 3b, Concierge only)
- Segmenting on {field}, from {form field | live enrichment | existing CRM record}
- Covers: {all submitters | known prospects only}. Net-new land on: {path}

### Who does not get a meeting (dimension 3c, Concierge only)
- {group} -> {redirect URL | pool}
- Catch-all (matched no booking rule): {redirect URL | SDR / fallback pool}

### Field mapping (the gate: nothing routing-related is built until this table is filled)
| Form field name (as submitted) | Option values (as submitted, not labels) | CP data field | CRM field it writes to |
|---|---|---|---|
| {e.g. company_size_1} | {e.g. 0-50, 50-100, …} | {reference} | {SF/HS object + field} |

Any row you cannot fill is a segment that is **not** in this build. Do not create a data field the customer's form does not populate.

### CRM actions per Schedule path
- [ ] Meeting logged against the record - `SalesforceCreateEvent` / `HubspotCreateEngagement`. Related to {Account | Opportunity | Case | Campaign | nothing}, delete on cancellation {yes | no}
- [ ] Record ownership updated to the booked host? {yes | no} - asked, per motion
- [ ] Other write-back: {AddToCampaign | field updates | upsert}. Not `ConvertLead`: conversion is a Distro node
- [ ] Pre-routing steps: {SpamCheck | Enrichment waterfall | none} - these run before the routes, so list them above the segments they feed

### Use cases to build (gated to licensed products)
- [ ] {use case} - motion {x}, license {y}, CRM gate {y/n}, builds with {tool/skill}

### Integrations to connect
- [ ] CRM: {Salesforce | HubSpot} {connected | to connect}
- [ ] Calendar + meeting location: {Google/Microsoft; Zoom/Teams/Meet} {status}
- [ ] Other stack: {Slack, Salesloft/Outreach/Gong, ZoomInfo/Clay, marketing automation}

### User sourcing method (chosen by customer)
- [ ] Connected CRM MCP | Roster | Manual invite

### Build sequence

Search the live tool list before each step. Steps 0 to 5 run once; 6 to 8 repeat per motion.
- [ ] 0. [MANUAL] Workspace, if none usable
- [ ] 1. Connect CRM (one CRM only)
- [ ] 2. One connected calendar to test against (usually the Admin's own, in MyApp)
- [ ] 3. Map data fields to the CRM. **Each field's CRM target confirmed with the customer before it is created**; an unmapped field routes but never writes back
- [ ] 4. Users, **licensed host first**. State that `sendInvite` is false and no email goes out, before the first invite call
- [ ] 5. Shared assets sized for ALL motions above: Teams, Meeting Types + reminders, Rules, Distributions (check `assignmentType`). Run the per-asset checklist for each (`build-loop.md` § Per asset): reuse-or-create, explain it if they are not expert, ask what it needs, build, read back, link
- [ ] 6. Product 1: {motion} -> [ ] 7. booking surface -> [ ] 8. verify
- [ ] 6. Product 2: {motion} -> [ ] 7. booking surface -> [ ] 8. verify
- [ ] 6. Product 3: {motion} -> [ ] 7. booking surface -> [ ] 8. verify

`user-update-licenses` REPLACES a user's licence set rather than patching it, and fails if the org has no free seats.

### Built assets (fill in as you go, with links)
| Asset | Admin link | Public link |
|---|---|---|
| {meeting type} | {host}/fire/admin/workspaces/{wsId}/meeting-types/{id}/guest-form | |
| {scheduling link} | .../chilical/scheduling-links/{type}/{linkId}/edit | {bookingUrl from the create call} |
| {distribution} | .../distributions/{distributionId} | |
| {rule} | .../rules/edit/{ruleId} | |
| {router} | see build-patterns.md route table | {public router link, if Concierge} |

### Standing defaults

Built here:
- [ ] Reminders on every meeting type (cadence AND copy agreed with the customer; reschedule link on each)
- [ ] Meeting logged against the record, if the chain supports it
- [ ] Ownership update on routed records, if the customer wants it

In-app setup, links to hand over (unless the live tool list says otherwise).
In the workspace:
- [ ] No-show recovery: /workspaces/{wsId}/orchestrator/flows
- [ ] Meeting Prep brief: /workspaces/{wsId}/chili-agents/meeting-prep-agent
- [ ] Spam Checker scoring settings: /workspaces/{wsId}/chili-agents/spam-checker - the step itself is built into the router; only the thresholds are in-app, and they are shared with Chat
- [ ] Distro Lead Conversion node, if conversion was asked for - in-app only

In Command Center (org level):
- [ ] Enrichment provider: Integrations > Data Providers - **a prerequisite, not a follow-up, if any segment routes on enriched data**
- Credit note given: {yes | n/a}

### Other defaults applied (see shared-assets.md)
- {e.g. round-robin with capping, ownership routing, business hours}

### If the customer chose plan-only
- Reason: {pausing / prerequisite | going for sign-off}
- Pausing -> the build sequence above is the deliverable: ordered, [MANUAL] marked, tool names exact
- Sign-off -> add a rationale per piece: what it does, what changes for the reps, what the alternatives were

### Handoffs (human / CSM)
- [ ] Write-scoped API key (if read-only session)
- [ ] OAuth enablement (if browser login wanted)
- [ ] End-user training with CSM (rep calendar + availability + ChiliCal extension)
- [ ] Tier upgrade for: {unlicensed use cases}

### Prerequisites and watch-outs
- {anything to connect or enable first: MCP/API key, CRM, calendar, an Admin for key generation, licensed products}

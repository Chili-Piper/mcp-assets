# Where routing data comes from

Which data source a rule reads decides which population it actually covers. Read before any segment on a Concierge or Chat motion.

Rule conditions carry a `DataSource`. Which one you can use decides which population the rule actually covers.

| Source | What it is | Objects |
|---|---|---|
| `DF` | Data Fields: the form data layer | Person, Company, DeanonymizedPerson, DeanonymizedCompany |
| `SF` | Salesforce CRM values | Lead, Contact, Account, Opportunity, Case |
| `HS` | HubSpot CRM values | Contact, Company, Deal, Ticket, User |
| `MK` | Marketo | data fields map to Marketo as well as Salesforce and HubSpot |
| `CP` | Chili Piper's own records, not the form layer | User, Meeting, Booker, Assignee, MappedSalesforceUser, MappedHubspotUser |
| `AT` | Assignment Table: the columns of the row being evaluated, injected per row at execution time rather than fetched from a connector | referenced by an `AssignmentTableRule` via `assignmentTableId` |

Two of these are easy to confuse. **`DF` is what the visitor gave you** (form fields, enrichment, deanonymised firmographics). **`CP` is Chili Piper's own state**: the meeting, who booked it, who it was assigned to, and the CP user record including its mapped Salesforce or HubSpot user. Use `CP` to route on the internal side of a booking (for example the assignee's mapped CRM user); use `DF` to route on what the lead submitted. Command Center labels both as "Chili Piper", so a rule that reads `chiliPiper` in the UI could be either, and the builder writes `DF` by default.

**This mostly matters for Concierge**, where an anonymous visitor submits a form and the routing decision runs immediately:

- A `DF` condition evaluates what the form carried, so it works for **every** submitter.
- An `SF` or `HS` condition evaluates CRM values, so it works only when the submitter **matched an existing record**. Ownership routing is the familiar case: it fires when there is a record to own, and not otherwise.
- Enriching a record in the CRM *after* a form submits is too late for the routing decision that already happened.

So when a customer names a segmenting field for a Concierge router, establish which population it has to cover:

- **Known prospects** (already in the CRM at submit time): route on any CRM field, exactly as you would on account owner.
- **Net-new**: only what is on the form, or enriched live on the form before routing. Nothing else exists yet.

A segment meant to cover both needs either the field on the form, live enrichment, or an explicit net-new path that lands somewhere sensible. Never leave net-new falling through to catch-all by accident.

**Chat** hits the same thing when a visitor is anonymous, though a journey can collect and enrich during the conversation before it routes, so there is more room to fill the gap.

**Distro is not affected.** It fires off a CRM record that already exists, so CRM values are there when the decision runs; route on whatever field the customer wants.

**Handoff mostly is not.** There is no form, so `DF` rules have nothing to read, and a rep booking a prospect already in the CRM routes on any CRM field. But the trigger is just a guest email, so a rep can book someone the CRM has never seen, and that prospect matches no `SF` / `HS` rule. Give them a destination at the catch-all (`handoff.md`).

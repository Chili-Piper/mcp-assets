# Shared assets

**Read this before any product file.** Teams, rules, distributions, meeting types and data fields are workspace assets, not product assets. One of each serves several products at once, which is why the build sequence puts them first and sizes them for every motion the interview surfaced, not just the first one to go live.

If a sentence would be true for two products, it belongs here rather than in a product file.

## Contents
- What shares with what
- Reuse or create
- Data fields
- Meeting types and reminders
- Merge tags
- Distributions
- Teams
- Universal routing pattern
- Segment starting points

## What shares with what

**Distributions share by assignment type, not by product** (help 29260564275603):

| Distribution type | Used by |
|---|---|
| Meeting | Concierge, Chat, Handoff, ChiliCal |
| Prospect/Record | Distro, Concierge |
| Conversation | Chat |

So one Meeting distribution can serve an inbound Concierge router, an SDR-to-AE Handoff and a ChiliCal round-robin link. Ask which of those the pool is for before you set `assignmentType` on `distribution-create`, because the type is what limits reuse.

**Rules are reusable across every product, but reuse is limited by data source, not by product.** Help 30080073275027: "Any Rule can be reused on multiple Journeys or Routers across your products (Chat, Concierge, Distro, and Handoff)." The MCP agrees: `rule.product` is optional and `rule-list` filters by workspace, not product. That is true of the rule as an object, and it is the part that misleads: **a rule attaches anywhere, and then evaluates against whatever data that motion actually has.**

So check the rule's `DataSource` before reusing it, not just its conditions (`routing-data.md`):

- **`DF` rules do not travel.** They read the form layer, so they only evaluate where a form submission exists. Attach a `DF` rule to a Distro router, which fires from a CRM record with no submission behind it, and it matches nothing. No error, no warning, just a path that never fires.
- **`SF` / `HS` and ownership rules travel everywhere.** They read the CRM record, which every motion has by the time it routes.

The practical consequence for the build: a Concierge router segmenting on form values cannot hand those rules to Distro, so the second product needs its own rules reading the CRM equivalents of the same idea. Say that when it comes up, because "we already built the segmentation" is exactly what a customer will reasonably assume.

Name rules for the *condition* they express (`ENT by revenue`, `Owned by an AE`), not for the router that first used one, or the second product to need it will not find it. Where the same idea exists in both layers, put the source in the name (`ENT by revenue (form)` vs `ENT by revenue (SF)`), so the one that cannot travel is obvious at a glance.

**Meeting types and teams** are workspace assets under Assets, reused by whatever references them.

**One workspace by default.** A workspace is the container for teams, meeting types and routing rules, and assets are ring-fenced to it. CP recommends starting with one, and most companies do; add another later only to deliberately separate teams or BUs, accepting duplicated assets (help 27155073608723).

**Consequence for sequencing.** Build the shared layer wide, then layer products onto it. The second product costs a router and little else, which is what makes "which would you like to set up next?" a cheap question rather than a new project.

## Reuse or create

The skill's default is to read what exists and reuse it. That is right on a tidy tenant and wrong on a cluttered one. Judge it:

- **Reuse** a rule or meeting type whose name and conditions clearly match what you need, in the workspace you are building in.
- **Create** when what exists is unnamed, empty, orphaned, or you cannot tell what it was for. Adopting an asset nobody can explain makes the build harder to explain and harder to maintain. Say plainly that you are creating rather than reusing, and why.
- Never reuse across workspaces. Assets are ring-fenced to their workspace.

## Data fields

**Some standard fields are normally present**, among them `PersonEmail`, `PersonFirstName`, `PersonLastName`, `PersonTitle`, `PersonState`, `PersonCountry`, `CompanyName`, `CompanyEmployees`. **Confirm with `data-field-list` before referencing any of them.** The names vary between tenants: the phone field can be plain `Phone` rather than `PersonPhone`, and an unknown `dataField` fails the create with a 400. Anything not in that read is a custom field and must exist before a router or rule references it.

**Gate before `data-field-create`:** which CRM object and field does this write to? Do the picklist values match the source's **submitted** values exactly, not its labels? An unmapped field is accepted silently and populates nothing.

Source: help 27607845025555 (Setting up Data Fields), 48593999839635 (Standard Data Fields List).

- **Map the fields you route on and write back, or nothing reaches the CRM.** A Data Field captures visitor data against a type and syncs to the CRM field(s) it is mapped to. Both routing on a field and writing it back depend on that mapping.
- **CP's auto-created fields are not all mapped.** CP ships the default five and auto-creates a standard set (UTM original/recent, Spam Score, chat URLs, firmographics); several land unmapped and populate nothing until an Admin maps them.
- **Create and map in one call.** `data-field-create` / `data-field-update` take per-system mappings and publish automatically; `data-field-list` shows what already exists. Read the exact mapping shape with `describe-tools` on `data-field-create` before the first write.
- **Ask which CRM field it maps to before you create it, every time.** `mappings` is optional on the create call, so an unmapped field is accepted silently and then populates nothing. Creating one and noting the gap afterwards is not the same as asking: it leaves the customer a field that routes but never writes back, which is the failure this whole section exists to prevent. The question is small and concrete ("which Salesforce field should company size write to?") and the customer usually knows it offhand.
- **Match the picklist values to the source, exactly.** Where the value comes from a form, the data field's values are the form's submitted **option values**, not the labels shown to the visitor. A `<select>` whose option reads `51-100` and submits `50-100` will break both the mapping and any rule written from the label, and nothing will report an error.
- **Profile the CRM field before you route on it or map into it.** The gate above checks the form side; this checks the other end, and it is where a build that passed every earlier check still falls over. Read the field's **type** and **group its existing values by count**. Three things to look for:
  - **Free text wearing a picklist's clothes.** A field holding 150 distinct values across 40,000 records is not a set of bands, whatever its name suggests. Canonical-looking values may cover most rows while the tail is raw numbers and junk.
  - **Two spellings of one value.** `United States`, `United States of America` and `USA` as separate values means a rule naming one of them silently covers a fraction of the intended population.
  - **A vocabulary that does not line up with the source.** Form bands of `500-1000` mapped into a CRM field that thinks in `251-1K` will write values nothing else in the CRM understands, and a threshold the customer agreed to may have no clean expression on the CRM side at all.
  Where the field fails this, look for a **typed** alternative and use operators instead of a value list: an integer employee-count field with `>=` beats a string field with seven hand-listed bands, and it covers the whole population rather than the rows that happen to match a spelling. Raise the mismatch with the customer rather than mapping into a field you have just found to be dirty.
- `data-field-list` has no filter and returns every field in the org, which on a mature tenant can be hundreds. Expect a large read, and do not adopt a near-match: a field whose values differ even slightly from the source is worse than a new one.
- `data-field-update` only edits **custom** fields. The default five and CP's managed standard fields are mapped by hand in Command Center at `/fire/admin/data-fields`. Data fields are org level, not per workspace, so one mapping serves every workspace.
- **Gotchas:** picklist / checkbox / radio need a non-empty values list, and picklist values must match the CRM's exactly or the mapping will not resolve. Set the per-mapping Overwrite flag deliberately (Enabled always updates, Disabled preserves an existing non-null value).
- **Smart parameters** are URL aliases on any field: a booking or Concierge link carrying `?<alias>=<value>` pre-fills it (`data-field-set-smart-parameters`). Useful for passing campaign or segment values into routing without adding a visible form field.

## Meeting types and reminders

**Gate before `meeting-type-create` and `meeting-type-reminder-create`:** has the customer given you the name, the length, the guest-facing invite copy, the agenda, and the reminder cadence and wording? These are the only assets a prospect reads. Nothing here gets written by you alone.

- Standard set: demo, discovery, follow-up. Reusable templates under Assets (help 29154678237459).
- **Ask before you build, not in the plan.** A meeting type and its reminders are the only assets in this build whose contents a prospect reads, so the customer sees the words before they ship. Ask for the name and length, the guest-facing invite title and body, and the agenda. A suggested cadence sitting in the plan as a default to strike is not asking, and it ends with the agent having written every word the prospect receives.
- **Ask what cadence they want**, suggesting 1 day, 1 hour and 1 minute before as a starting point. Make the day-before conditional on the meeting being booked at least a day ahead, and add an extra one when booked two or more weeks out.
- **`meeting-type-create` seeds a reminder by itself.** The create response comes back with a reminder already attached ("Email 1 hour before") whose body carries **no reschedule link**. Read the response's `reminders` array and fix or replace it with `meeting-type-reminder-update`; adding your own on top leaves a half-conforming one in place.
- **Always send `others: []` on a `location`.** Both `meeting-type-create` and `meeting-type-update` reject a location without it. It is the shared location type rather than one endpoint, so the same omission fails on an update you make later.
- Build them as reusable assets: `meeting-type-reminder-create`, then `meeting-type-attach-reminder`.
- Include an agenda customised per meeting type, personalise with dynamic tags, and **always include a reschedule link**.
- **Vary the trigger kind rather than building three timed reminders.** A nudge to someone who has not responded belongs on `BeforeMeetingNoResponse`, not on a third `BeforeMeeting`.
- Start from an in-app template rather than writing from scratch (help 28030135101971).
- **Conditional sending is not settable here.** "Send the day-before only when the meeting was booked more than a day ahead" is a real in-app setting and a good idea, but the reminder tool leaves advanced send behaviour to the backend. Suggest it as something for the customer to switch on in the app, not as something you are building.

## Merge tags

Guest-facing copy takes merge tags, and **the syntax is `{!CP.Object.Field}`**, with the `!`. Other forms, such as `{CP.Company}`, `{{Company}}` or `{Company}`, render as literal text in the prospect's calendar invite, so correct them if a customer suggests one.

| Tag | What it renders |
|---|---|
| `{!CP.DataField.FirstName}` | a value the guest submitted, by data-field name |
| `{!CP.DataField.CompanyName}` | as above; multi-word field names close up, so Company Size is `{!CP.DataField.CompanySize}` |
| `{!CP.Host.FirstName}` / `{!CP.Host.FullName}` / `{!CP.Host.Title}` | the meeting host |
| `{!CP.Meeting.RescheduleUrl}` / `{!CP.Meeting.CancelUrl}` | the links every reminder should carry |
| `{!CP.Meeting.ShortRescheduleUrl}` / `{!CP.Meeting.ShortCancelUrl}` | shortened forms, for SMS |
| `{!CP.Meeting.Location}` | where the meeting happens |
| `{!CP.Question.FieldName}` | an answer to a booking-form question |

Two rules worth knowing before you write copy: a multi-word data field closes up into one token, and **Question tags do not work in reminders**, only on the booking page. Check the tag against `data-field-list` the same way you would a routing field, because a tag naming a field that does not exist renders as literal text with no error.

## Distributions

**Gate before `distribution-create`:** is `assignmentType` set for every motion in the plan, not just the one you are building? Is Flexible or Strict a decision you made per product rather than a default? Does the team behind it have members?

- `distribution-create` needs a `teamRef`, so the team exists first.
- Set `assignmentType` from the table above. Getting this wrong is what blocks reuse later.
- **Flexible or Strict** is the `handling` field on a Meeting distribution. Flexible shows the combined availability of everyone in the pool and assigns whoever has fewest meetings; Strict shows only the calendar of the rep with fewest, which distributes more evenly but can leave very few slots to choose from (help 29260564275603). Which to pick depends on who is doing the booking, so it is a per-product call: see the product file.
- **Capping** is per-user with a reset period (Daily / Weekly / Monthly / HourlyRolling). Pair a cap with a fallback owner so a capped rep does not stall the queue.
- **Weights** are 0 to 10000, default 100; 0 disables a user without removing them.
- Distribution weight adjustments over the MCP are **additive, not absolute**: a +50 on a weight of 100 gives 150.
- Set business hours, or availability looks broken across time zones.
- `distribution-list-put` returns per-user state that is worth reading before you declare a build done: `Active`, `Capped`, `Disabled`, `NoLicense` (still on the team but lost their licence, so receiving nothing), `Removed`. `prioritization.queue` is the authoritative next-up order; the level numbers are informational.

## Teams

- `team-create`, then `team-add-users`. **A team cannot be usefully empty**: an empty team produces a distribution that routes to nobody and a router path that resolves to nothing. If the real membership is not known yet, add the licensed admin running the session and say so. That is a real, bookable user who can be removed later, which is different from inventing test users, which this skill never does.
- Job function (SDR / AE / CSM) is **not** on the Chili Piper user record. The record carries permission role (Admin / WorkspaceManager / TeamManager / User), licences and membership. Function comes from the customer or from their CRM.

## Rules

**Gate before `rule-create`:** does every field in the conditions exist in a system the customer controls, and are the values the ones that system actually sends? A rule on a field you created for the purpose can never fire, and it will pass any test where you supply the value yourself. The call is live immediately with no dry run, and `product` comes back server-assigned (usually `Distro`) whatever the rule is for, which is cosmetic and not worth correcting.

An **ownership** rule needs more than the others: `CreateOwnershipRuleRequest` requires a `teamId`, and the owner is resolved against that team's members, so it needs a team holding every possible owner. Where the router row assigns through a distribution, that team needs one too.

**Every `OwnershipCondition` needs its `ownership` reference**: `{source, object, field}`, for example `{source: "SF", object: "Account", field: "OwnerId"}`. Omitting it is rejected with a 400 and `OwnershipConditionMissingReference`, so check any example you adapt.

**The owner is matched on email, so unmapped CRM users are not a blocker.** `searchOwnershipBy` accepts `CrmIdOrEmail`, which resolves the CRM record's owner to the Chili Piper user with the same address. A tenant where most users have no `salesforce` link still routes ownership correctly, so do not report that as a gap and do not reach for `integration-salesforce-set-mappings` to close it: that call is a **strict full-tenant replace**, so a partial fix means sending every user in one payload, which is a large destructive write to solve a problem that is not there. Email is also the version a customer can read and debug in the app, where an id tells them nothing.

## Universal routing pattern

Applies to Concierge, Distro, Handoff and Chat. Build the router as:

1. **Segment** by a firmographic field. Check the source first (`routing-data.md`): a segment on a CRM field only covers known prospects.
2. **Ownership-first with round-robin fallback**: an owned record goes to its owner, otherwise round-robin across the segment pool.
3. **Ownership override**: owned prospects route to the owner regardless of segment.
4. **A catch-all at the end, set deliberately**: everyone who matches no rule ends up here, so it decides the default outcome for the router. Two valid answers, and the customer picks: disqualify them (the common choice on inbound, which makes the router read as an allow-list), or hand them to an SDR or fallback pool. What is not valid is leaving it unset, which drops people silently.
5. **Blank / missing value fallback**: when the segmenting field is empty, flag for manual review rather than misassigning. On a Concierge router this is also where net-new prospects land when the segment reads from the CRM.
6. **Capping where needed**, with a fallback owner when the cap is reached.
7. **Preview / dry-run before going live**, then check the router logs and verify the write landed in the CRM.

## Segment starting points

Customers often know they want to split by size or region and have not settled where the lines go. Offering a starting point moves that along; presenting it as the answer produces a router built on our numbers rather than theirs. So **suggest, then take whatever they say back**, including a flat "no, ours are different", which is the common and correct response.

Ask the open question first. Only reach for these if they are stuck or explicitly ask what most people do.

**Company size**, by employees:

| Segment | Employees |
|---|---|
| SMB | 1 to 250 |
| Mid-Market | 251 to 1,500 |
| Enterprise | 1,501+ |

**Regions**, as country lists:

- **NA**: United States, Canada, Mexico
- **EMEA**: United Kingdom, Germany, France, Spain, Italy, Netherlands, Sweden, Norway, Denmark, Finland, Ireland, Belgium, Switzerland, Austria, Portugal, Poland, Czech Republic, Romania, Hungary, Greece, Turkey, Israel, United Arab Emirates, Saudi Arabia, South Africa, Nigeria, Kenya, Egypt
- **APAC**: Australia, New Zealand, Japan, South Korea, Singapore, India, China, Hong Kong, Taiwan, Thailand, Philippines, Indonesia, Malaysia, Vietnam
- **LATAM**: Brazil, Argentina, Colombia, Chile, Peru, Costa Rica, Panama, Dominican Republic, Puerto Rico, Ecuador

Four things to hold onto when you use these:

- **They are a prompt, not a plan.** A customer who accepts them wholesale without looking has not really answered, so read the numbers back and check they match how the team is actually carved.
- **Whose vocabulary?** The lists above are display strings. If the segment reads from a form, the values must match what the form *submits*; if it reads from the CRM, they must match what that field actually holds, spellings and all. A country list naming "United States" misses every record that says "United States of America" (§ Data fields).
- **Add the unknown path.** Whatever the bands are, some records have no size and no country. Decide where those land before the catch-all, rather than letting the catch-all absorb them by accident.
- **Coverage before elegance.** Bands only work if there is a rep behind each one. A carve that produces a segment nobody covers is worse than a coarser one that everybody does.

Segment thresholds anywhere else in this skill are **an illustration, not a default**. Every customer brings their own, so ask. Reuse the pattern, not the numbers.

Take the customer's segmentation at face value. Regions and sizes are often worked by more than one rep, and a carve that looks thin from the outside is usually deliberate. Build what they describe; anything worth revisiting is a conversation for their CSM, not a blocker here.

# Distro

CRM-triggered record routing. **Salesforce only.** A HubSpot org uses Concierge / Handoff / ChiliCal / Chat instead. Read `shared-assets.md` first.

Note the scope of that gate: it applies to Distro, the router product. Distributions are CRM-agnostic and every motion on every CRM assigns through one.

## Routing data is always there

Distro fires off a CRM record that already exists, so every CRM field is available to the routing decision. "Route on company size" needs no conversation about where the value comes from. That question belongs to Concierge, where an anonymous form submission may have no record behind it (`routing-data.md`).

## What blocks a publish

Three rules that stop a Distro build and are not obvious from the Concierge experience:

- **`catchAll` is mandatory.** Concierge's is optional; Distro's is not. Every record reaching the end of the matrix gets routed somewhere, which is why the entry gate below matters so much.
- **Every route and the catch-all needs at least one action.** A row that assigns a distribution but carries no action fails to publish. The distribution decides *who*; the actions decide *what happens to them*.
- **`trigger.evaluation` is the entry gate, and it is the only way to not route something.** A ruleId whose failures are dropped before the matrix runs. With a mandatory catch-all, records that fail it are the only ones that go nowhere. This is the most important structural idea in a Distro build: disqualification happens at the entrance, not at the end.

The reassuring half: **create is all-or-nothing.** Unlike a Concierge 422, a failed Distro create leaves nothing behind, so there is no orphan to hunt and a retry is safe once the cause is fixed.

## Build

- **Set the trigger**: which Salesforce object and which field change fires it (new Lead, Opportunity flipping to Closed/Won, an account signal). Get this to the object-and-field level in the interview; "new leads" is not a trigger.
- Apply the universal routing pattern from `shared-assets.md`: segments, ownership-first, capping with a fallback owner, blank-value to manual review.
- Distribution `assignmentType` here is **Prospect/Record**, not Meeting. That is what makes a Distro distribution non-reusable by Concierge's booking flow, so if the customer wants both, they need one of each.
- **Chained routers**: a `Send to Router` node fires the next one (CSM Router then AM Router); the downstream router is set to "When started by another flow".
- Add an SLA on at least one path.
- Understand Lead-to-Account (L2A) matching; it decides which account a lead resolves to and therefore who owns it.

Routers can be created inactive and activated separately (`distro-router-activate` / `-deactivate`), so a build can be reviewed before it starts firing on live records. Prefer that over publishing straight into production; it is the one product where you get to stage.

**Actions: send every field, and do not take the ownership defaults.** `UpdateOwnership` takes `respectWorkingHours`, `sendSlackNotification`, `sendEmailNotification` and `matchBy`. Any you omit get defaults: **both notifications on**, so every routed record pings its assignee twice, and **`matchBy: Id`**, which resolves nothing on a tenant where users have no CRM id linked. Send all four explicitly, and use `matchBy: {type: "Email"}` unless you have confirmed the CRM ids are actually mapped.

**Routing steps exist here too, in different shapes from Concierge's.** `{type: "Enrichment", fieldMappings: [{variableId, field, waterfallId, overwriteExisting?, relation?}]}` and `{type: "SpamCheck", salesforceWrite}`. A step copied across from a Concierge router is a 400.

**Lead conversion is an in-app node.** The Lead Conversion node is real, it is what a customer means when they ask about converting on routing, and it has its own settings including which Lead Status performs the conversion. It is not one of the actions the API exposes, so it is a handover: build the rest, give them the router link, and say it is a couple of minutes in the app. The audit trail is the `Distro_Converted_CP` checkbox the Distro for Salesforce package adds to the Contact, which auto-checks when Distro converts a Lead and therefore needs the package installed (help 34424043095443).

**Naming a Record distribution:** a router row needs a `distributionId` even where the row routes by ownership and the distribution only supplies the team to resolve the owner against. So one distribution often serves two rows that mean different things, and a name describing either path fits the other badly. Name it after the team rather than the path (`Accounts - All Reps`, not `Unowned Accounts`).

## Verify

**There is no Distro equivalent of `concierge-route-by-slug`.** Concierge can be verified by running the router against a synthetic lead; Distro cannot, so verification here is a config read-back plus Preview Mode in the app. Say that rather than implying the same standard of proof: it is an honest asymmetry, and a customer who watched the Concierge router get tested will expect the same.

**Read the trigger back with `distro-list-routers`, not `distro-router-get`.** `distro-router-get` and both the create and update responses omit `trigger` entirely: object type, event types, and `evaluation`, which is the entry gate and the only way this product declines to route something. `distro-list-routers` carries it, but it takes **no arguments at all** (no router id, no workspace filter), so confirming one trigger means listing every router in the org. On a mature tenant that is a large read: pull it once, find your router by id, and do not repeat it per asset.

**A read-back can look lossy without anything being wrong.** A router containing app-only nodes reads back as `routing: {known: true, representable: false, rows: [{ruleId, outcome: {kind: "side-effect", type: "Unrepresentable"}}], catchAll: null}`. That is a reporting limit, not data loss. `distro-router-update` is an overlay matched by `ruleId`, and it preserves matchers, SLAs, campaign addition, lead-to-contact conversion, send-to-routers, duplicate matching and any app-only actions on that route. Say both halves if a customer sees it: the config is intact, the API just cannot render those nodes.

Run in Preview Mode before going live, then verify both records in the CRM and the chain in `distro-logs`.

**Assigned no one:** check the trigger fired; check for a blank segmenting value (it should have hit the manual-review path); check the router chain and Preview; check L2A.

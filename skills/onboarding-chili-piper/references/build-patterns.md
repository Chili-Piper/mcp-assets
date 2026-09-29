# Build patterns

Config and diagnosis patterns that apply across products.

Cross-product only. Shared assets (teams, rules, distributions, meeting types, data fields, the universal routing pattern) are in `shared-assets.md`.

## Contents
- Reading the account without blowing up the context
- Deep-linking what you build
- Access and prerequisites
- One CRM
- Between sessions
- MCP (connecting an AI assistant)
- Diagnosis playbook
- Baseline spine

## Reading the account without blowing up the context

Two failure modes, same cause: fetching everything when you needed a number or a slice.

**Responses.** `distribution-list-put` and `rule-list` both default to `pageSize` 200. On a tenant with history that response can be too large to return. Both take filters, so use them:

- `distribution-list-put`: `workspaceIds[]`, `pagination {page, pageSize}`, `name`, `assignmentType`.
- `rule-list`: `pagination`, `filter.workspaceId`, `filter.name`, `filter.type[]`, `filter.ruleBuilderVersion` (required).

In Phase 0 you want **counts, not bodies**. `rule-list` returns `total`, so `pageSize: 1` gives you the count for free. `distribution-list-put` returns only `items` with no `total`, so probe with a small page rather than assuming a count is available. Once the target workspace is known, scope every subsequent read to it and fetch bodies only for what you are about to reuse.

**Schemas.** `search-tools` returns `_meta` with `chilipiper.com/schemaTokens`. This is a namespaced `_meta` key, not a URL. **Read it before calling `describe-tools`.** Some list and log tools are very large to describe, and the number tells you which.

That number is the **whole `describe-tools` payload**, not the input shape. Most of it is `outputSchema`, which you do not need to construct a call. So a big number means the response is expensive, not that the call is hard. Three rules follow.

- **One name per `describe-tools` call.** Batching sums the payloads, and several tools share one huge output schema: `meeting-get`, `meeting-patch`, `meeting-list-put`, `meeting-cancel-post`, `meeting-noshow-post`, `crm-get`, `crm-cancel-post` and `crm-noshow-post` each carry the same ~75KB meeting record, so a batch of eight returns those bytes eight times.
- **Do not describe a read, list or log tool.** Their payloads are almost entirely output schema, and their inputs are a few obvious fields. `concierge-logs` takes `workspaceId`, `routerId`, `start`, `end` (all required, ISO-8601, 30-day max window) plus optional `page` and `pageSize`; `concierge-list-routers` and `handoff-router-list` take `workspaceId` plus pagination. Per the capability rule these shapes are a starting point and not authority: if a call 4xxs, describe the tool then and accept the cost.
- **Describe the write tools freely.** Their input schemas are small; `web-experience-create` / `-update` and the router creates are the largest. A write tool quoting an unusually large number is worth a second look before you call it.

In a client that cannot save large tool results to a file (Claude Desktop, ChatGPT), an oversized result cannot be recovered, so these rules are what keep the skill working in every client.

## Deep-linking what you build

**Every asset you create or update gets a link.** Create tools return the new id; on an update you already hold the id you passed in. Either way, never say "it's in Command Center under Meeting Types" and leave the customer to find it. Give them the URL.

**The MCP does not return admin URLs.** No create tool hands back a Command Center link, so the admin link is always constructed. It does return two public URLs, and those you use as-given rather than building:

- **Scheduling links**: `bookingUrl` on every `scheduling-link-create-*` response is the live guest-facing booking page. Use it verbatim; do not assemble one from the slug.
- **Concierge routers**: `concierge-router-create` returns `slug`, and the public router link is `https://<subdomain>.chilipiper.com/concierge-router/link/<slug>` with the subdomain from `tenant-get`. (`routerLink` in that same response is the form's field mapping, not a URL. The name misleads.)

Everything else is constructed. Two ids build any admin link: the `workspaceId` you built into, and the id the create call returned. Most create responses carry both (`meeting-type-create`, `team-create`, `rule-create`, `concierge-router-create`, `distro-router-create`, `handoff-router-create`, `web-experience-create` all return `id` + `workspaceId`). Two exceptions worth knowing: `distribution-create` returns only `distributionId`, so pair it with the workspace id you passed in, and the scheduling-link creates return `linkId` plus a ready-made public `bookingUrl`, so give the customer both the admin link and the live booking link.

**Two levels, and they are not interchangeable.** Everything sits under `/fire/admin`, but it splits in two:

- **Command Center is the org level.** Integrations, user management (inviting, adding, assigning licences), workspace management, data fields, billing, branding, org settings. There is one of each per tenant.
- **A workspace holds everything else**, and that is where most of the MCP's writes land: teams, rules, distributions, meeting types, all the routers, Chili Agents, Orchestrator flows, logs and reporting. Each is scoped to one `workspaceId` and ring-fenced from the others.

Use the words accordingly. "Configure it in Command Center" is wrong for Spam Checker or an Orchestrator flow, because those live inside a workspace. Say "in your workspace, under Chili Agents" and give the link.

**Host: always `https://fire.chilipiper.com/fire/admin/...`.** A logged-in user hitting `fire.chilipiper.com` is resolved to their own tenant host (`calendar.chilipiper.com` and the rest), so you never need the subdomain for an admin link. Do not spend a `tenant-get` call to build one, and do not ask which host they are on. `tenant-get` is only needed for the *public* URLs, where the subdomain is genuinely in the path.

**Routes you built**, all relative to `<host>/fire/admin`. Every one is inside a workspace:

| What you built | Link |
|---|---|
| Meeting type | `/workspaces/<wsId>/meeting-types/<id>/guest-form` |
| Team | `/workspaces/<wsId>/teams/edit/<id>` |
| Distribution | `/workspaces/<wsId>/distributions/<distributionId>` |
| Rule | `/workspaces/<wsId>/rules/edit/<id>` |
| Concierge router | `/workspaces/<wsId>/form-router/<id>/flow-builder` |
| Distro router | `/workspaces/<wsId>/crm-router/edit/<id>` |
| Handoff router | `/workspaces/<wsId>/handoff/handoff-router/<id>/flow-builder` |
| Scheduling link | `/workspaces/<wsId>/chilical/scheduling-links/<type>/<linkId>/edit`, where `<type>` is `one-on-one`, `round-robin`, `group` or `ownership` |
| Chat journey / web experience | `/workspaces/<wsId>/chat/journeys/edit/<id>/version/latest` |
| Orchestrator flow | `/workspaces/<wsId>/orchestrator/flows/edit/<flowId>` |
| Meeting Prep brief | `/workspaces/<wsId>/chili-agents/meeting-prep-agent/edit/<briefId>` |

**Workspace pages**, for when you have no id or want to point at a section:

| Page | Link |
|---|---|
| Meeting types / distributions / rules / teams | `/workspaces/<wsId>/meeting-types`, `/distributions`, `/rules`, `/teams` |
| Scheduling links | `/workspaces/<wsId>/chilical/scheduling-links` |
| Concierge logs / Distro logs | `/workspaces/<wsId>/concierge-logs`, `/workspaces/<wsId>/distro-logs` |
| Chili Agents hub / Spam Checker / Meeting Prep | `/workspaces/<wsId>/chili-agents`, `/chili-agents/spam-checker`, `/chili-agents/meeting-prep-agent` |
| Orchestrator flows / logs | `/workspaces/<wsId>/orchestrator/flows`, `/orchestrator/logs` |
| Meetings activity | `/workspaces/<wsId>/reporting/meetings-activity` |
| CRM matching settings | `/workspaces/<wsId>/settings/crm-matching` |

**Command Center pages**, org level, no `workspaceId` in the path:

| Page | Link |
|---|---|
| Workspaces (and creating one) | `/workspaces` |
| Users / a single user | `/users/active`, `/users/active/<userId>/personal-details` |
| Integrations / API tokens | `/integrations/built-in`, `/integrations/credentials/access-tokens` |
| Data fields | `/data-fields` |
| Billing and credits | `/billing` |

Where a route is not in this table, link the list page rather than guessing a deep link, and say that is what you did. A wrong URL costs the customer more time than no URL.

## Access and prerequisites

- **Set up the MCP.** Steps per client are in help article 50430350863635. OAuth (Claude Desktop, claude.ai, Claude Code, ChatGPT) needs an Admin on a paid account and stores no key. API key (Cursor, Codex, Gemini CLI, CI, or a narrower scope) is generated at `fire.chilipiper.com/fire/admin/integrations/credentials`, Credentials tab, API Access Tokens sub-tab (not HTTP Auth), scoped to what that session needs and shown once.
- **Connect a CRM.** Salesforce or HubSpot at `fire.chilipiper.com/fire/admin/integrations/built-in`. If both are connected, use the sales reps' source of truth (Salesforce when sales runs Salesforce and marketing runs HubSpot).
- **Entitlement.** Read the `tier` on the per-user `licenses` object; `tenant-get` does not carry it. The tier is a bundle and is the entitlement, so the per-product booleans are not the check and a false one is not a gap. Offer what the tier covers; anything else is a tier-upgrade handoff.
- **Licence the Admin running the session, first.** An operator with no tier cannot be a host, has no availability, and cannot be booked, so nothing you build can be tested end to end. `user-update-licenses` **replaces** a user's full licence set rather than patching it (`chiliCalOrg` and `handoff` are required in the payload), so read the current set with `user-find` and send it back with the additions, or you will silently strip licences. A downgrade takes effect immediately, and the call fails if the org has no free seats: if it does, that is a seat-count conversation for the CSM, not a retry.
- **Distro requires Salesforce.** A HubSpot org uses Concierge / Handoff / ChiliCal / Chat, not Distro. This applies to Distro the CRM-triggered router product only. Distributions are CRM-agnostic: every motion, on any CRM, assigns through one.
- **Data fields are the CRM mapping layer.** Routing on a field and writing it back to the CRM both require the field to exist *and* be mapped; CP's auto-created standard fields (UTM, Spam Score, firmographics) populate nothing until mapped (help 27607845025555, 48593999839635). Custom fields are created and mapped in one MCP call (`data-field-create` / `data-field-update`, with a `mappings[]` array per CRM: Salesforce `object`+`field`+`overwrite`, HubSpot `object`+`property`+`overwrite`); publish is automatic. `data-field-update` only edits custom fields, so the default five and CP's managed standard fields are mapped in Command Center (`fire.chilipiper.com/fire/admin/data-fields`). Picklist values must match the CRM's exactly for the mapping to resolve.
- **What breaks routing.** No connected CRM means no ownership or territory routing. No connected calendar means no availability, so check `availabilityConfigured` per user before declaring a booking surface done.
- **Write capability cannot be probed.** Nothing returns "this key can write". The only signal is that write tools carry `readOnlyHint: false` in `search-tools`, and that describes the catalogue rather than the key. Say so honestly ("write tools are exposed; unconfirmed until the first write succeeds") rather than reporting a check that did not happen. The first write either succeeds or gives you a 4xx, and a 4xx on a newer capability can mean a missing token scope rather than an unsupported feature.

## One CRM

**An org has exactly one CRM connection.** Salesforce or HubSpot, never both. Everything follows from that:

- **A form platform is not an integration.** A HubSpot or Marketo form posts field values to CP; routing on them needs only the `thirdPartyForm` mapping. A Salesforce-connected org routes a HubSpot form perfectly well with no HubSpot connection anywhere.
- **Write-back goes to the connected CRM only.** Use only the CRM action family that matches it. `concierge-router-create` exposes both Salesforce and HubSpot action families, and rule conditions accept `SF`, `HS` and `MK` data sources, so the API surface will not stop you choosing wrong.
- **Never raise "connect HubSpot" as a handoff for a Salesforce customer.** "Nothing writes back into HubSpot until that integration is connected" is a wrong sentence to say to a Salesforce org, not a helpful caveat. Their marketing platform is not waiting on a connection; it is not the CRM.
- If both somehow appear connected, do not infer which is authoritative. Ask which system the reps work out of. Marketing running HubSpot while sales runs Salesforce means Salesforce is the CRM and HubSpot is the MAP.
- **Distro is Salesforce only.** That gate is about Distro the router product. Distributions are CRM-agnostic.
- **Workspace creation.** Search the `workspace` category for it before sending anyone to the UI. If your search comes back empty, it is a Command Center job (`/fire/admin/workspaces`) and it gates the whole build, so sequence it first. Why one workspace is the default, and what is ring-fenced to it, is in `shared-assets.md`.

## Between sessions

- **Review config between sessions** and flag issues before they block. The validate instinct, applied to work you did not do yourself.
- **Document routing logic as it is finalized** in the onboarding plan, so the next session and the customer's own admins can follow it.

## MCP (connecting an AI assistant)

Per-client setup steps are in help article 50430350863635. Give the customer that link rather than reciting the steps. What the article will not tell you:

- **Prefer OAuth where the client supports it and the person is an Admin**: no stored key, and it grants everything the account can use. Claude Desktop, claude.ai and ChatGPT are OAuth only; Cursor, Codex and Gemini CLI are API key only; Claude Code does both. A non-Admin has no OAuth path on any client, and a key's scopes cap what can be built.
- Every MCP tool returns typed structured output (`outputSchema` + `structuredContent`).
- **Gemini needs `X-MCP-Schema-Dialect: gemini`.** Without the header, rules, distributions, routers, meeting types and Handoff fail to load, and one failed tool takes the whole list down; simple tools still answer, so it looks connected. Same requirement for the Gen AI SDK, ADK and Gemini Enterprise. Gemini's web and mobile apps and Gems do not currently accept custom MCP servers, so Gemini users go through the CLI.
- **ChatGPT**: the MCP connects as a plugin (Plugins - + - Server URL + OAuth), which reaches every tool the account can use; scope it down with an API-key client instead if that is too broad. Custom GPTs are a different mechanism, calling the REST API through GPT Actions rather than this server.
- Limits: OAuth is Admin-only on paid accounts; some Claude accounts need Owner approval before a connector can be used; writes require approval; all calls are org-scoped; distribution weight adjustments are additive not absolute (a +50 on a weight of 100 gives 150).

## Typed errors

What a failure code means and what to do about it. Check here before hypothesising.

| Error | HTTP | What it means, and the move |
|---|---|---|
| Invalid `dataField` | 400 | The field does not exist. Use a standard default or a real UUID; never invent one. |
| Missing `teamId` on an ownership rule | 400 | `teamId` is required. An ownership rule without a team can never match. |
| Missing `ownership` on an `OwnershipCondition` | 400 `OwnershipConditionMissingReference` | Every OwnershipCondition needs `{source, object, field}`, e.g. `{source: "SF", object: "Account", field: "OwnerId"}`. Send it even where the schema shows it as optional. |
| Publish failure | 422 | The router is saved as an **unpublished draft**, so nothing is live. **Do not retry the create**: each retry mints another draft. Fix the cause, then delete the leftover draft in the Concierge app. |
| `RouterWorkspaceNotManageable` | 4xx | The workspace is not a team workspace, or this credential cannot manage it. |
| Rule revision conflict | 409 | Re-fetch with `rule-list` and retry that one rule. Revisions go stale fast. |
| `DecodingFailure at .x.y` | 400 | Input validation, rejected before anything was created. Nothing left behind, safe to retry. Often a missing `type` discriminator on a union branch: **`type` equals the variant's schema title**; set it explicitly on every union branch. |
| `Proxied call error: <business rule>` on `web-experience-create` | 4xx | **The draft was already created and survived the rejection.** Retrying mints a second one. It does not show in `web-experience-list` and `web-experience-get` errors on it, so stop, tell the customer, and give them the workspace journeys link. |
| Rename rejected while someone is editing | 423 | A lock, not a failure to retry around. Someone has the draft open in the app's builder. |
| Missing scope | 403 | **The response names the operation it wanted.** That is the one place the API tells you what a credential can do, so read it rather than guessing. Fixed in Command Center under API keys. |

## Diagnosis playbook

Per-product symptoms are in each product file. These are the ones that are not about a single product:

- **A router built fine but segments nobody.** Check the rule's data source. On Concierge, a rule on `SF`/`HS` fields only matches submitters who already exist in the CRM, so net-new fall through (`shared-assets.md`).
- **A distribution routes to nobody.** Check the team has members, that they hold licences (`distribution-list-put` reports `NoLicense` per user), and that their availability is configured.
- **Orchestrator ran but the CRM field did not update.** Check the field action, permissions, and the journey activity log, in the workspace under Orchestrator.
- **MCP returns no data.** Check the credential (Bearer literal present, scopes), the endpoint URL, and that the client shows the server connected; run the tenant test.

## Baseline spine

Mirrors Chili Piper's official Admin Setup order (help article 37194718584211, "Welcome to Chili Piper").

**Before each step, search the live tool list.** Build it over the MCP where a tool exists. Guide the in-app path only where your search comes back empty, and say that is what happened. Do not carry an assumption from one session into the next.

Most of what you build lands **inside a workspace**: teams, rules, distributions, meeting types, routers, links. The **Command Center** layer above it (integrations, users and licences, workspaces) has historically needed a person, which is why steps 0 to 2 below lean manual while steps 5 onwards are tool calls. Search before you assume that still holds for any given step.

Steps 1 to 5 are built once and serve every product. Steps 6 and 7 are per-product, and they are the loop: after verifying one, ask which motion is next and run them again.

0. **A workspace to build in, if there is not a usable one.** This gates everything after it, so settle it first rather than discovering it at step 4. Search the `workspace` category for a create tool; if your search comes back empty, the customer creates one at `/fire/admin/workspaces` and gives you the id.
1. **Connect CRM** (Salesforce or HubSpot) at `fire.chilipiper.com/fire/admin/integrations/built-in`. Sets the motion branch decided in Phase 0.
2. **Connect calendar and meeting location** (Google/Microsoft; Zoom/Teams/Meet). Availability comes from each rep's own calendar connection, which is end-user setup, so for this session get one connected calendar you can test against, usually the Admin's. The company-level calendar integration is optional and view-only: do not treat it as a prerequisite (Phase 0).
3. **Map data fields to the CRM.** Routing on a field and writing it back both depend on the field existing *and* being mapped, so nothing lands in the CRM without this, and several of CP's auto-created standard fields arrive unmapped. Tools, mapping shapes, and gotchas → `shared-assets.md` § Data fields.
4. **Users, starting with a licensed host.** **Licence the Admin running the session first** if the Phase 0 ladder found they need it: without a licence they have no availability, cannot host, and cannot test what you are about to build. Then source and add the rest per the customer's chosen method (Phase 1): `user-invite` with `sendInvite`, then `team-create`, `workspace-add-users`, `team-add-users`, `user-update-licenses`. Note `user-update-licenses` replaces a user's whole licence set rather than patching it, so read the current set first and send it back with the additions; it fails outright when the org has no free seats, which is a CSM conversation rather than a retry (§ Access and prerequisites above).
5. **Build the shared assets, sized for every motion in the plan.** Teams (`team-create`) and Meeting Types with reminders (`meeting-type-create` + `meeting-type-reminder-create`) first, then Rules (`rule-create`) and Distributions (`distribution-create`). These are workspace assets reused across products, so build them for the whole plan rather than for the first router: one Meeting distribution serves Concierge, Chat, Handoff and ChiliCal, and any rule can be reused by all of them. Set `assignmentType` deliberately, because that is what decides whether the next product reuses a distribution or needs its own. Read what already exists in the chosen workspace and reuse what clearly matches, but do not adopt unnamed or empty assets (`shared-assets.md` § Reuse or create). **Distributions and rules are CRM-agnostic**, not Salesforce-only.
6. **Set up the product for the current motion.** Read that product's reference file now. Concierge, Distro (Salesforce only), and Handoff routers build over the MCP, as do chat journeys, playbooks, and web experiences. Search the live list for Chat and Orchestrator rather than assuming either has to be built in-app. A Concierge build also needs a deployment snippet on the customer's page and, for a third-party form, a field mapping.
7. **One booking surface, chosen rather than defaulted.** Which surface is right falls out of the Phase 1 answers: a round-robin link for a shared pool, an ownership link where the CRM already holds an owner, a group link where several people must attend, an admin one-on-one link for a named person. Check the assumption before building: an ownership link needs an owner field that is actually populated, and any link needs hosts whose availability is configured. If Concierge is the priority motion, the router's form is already the booking surface.
8. **Verify.** Confirm it routes and has availability coverage.
9. **Ask which motion is next**, then return to step 6. The shared assets are already there, so say so: the next product is a router and a verify, not a rebuild.

End-user setup (each rep connects calendar and meeting location, sets availability, installs the ChiliCal Co-Pilot extension) is a separate track, usually CSM-led training (Phase 4 handoff).

Spam Checker, enrichment, no-show recovery and Meeting Prep are not "depth": they belong in the plan from the start (Phase 2). The first two are `routingSteps` on the router, so they are part of the build; the other two are workspace links to hand over. Enrichment **providers** are a Command Center integration, so a waterfall needs one in place first.

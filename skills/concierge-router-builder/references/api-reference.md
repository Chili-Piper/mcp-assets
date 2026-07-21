# API reference — concierge-router-builder

Tool and field truth verified against the live Chili Piper MCP / Edge API, 2026-07-21. The
tools' own text descriptions are unreliable — treat this file as the truth for this skill.
`workspaceId`/`teamId`/`userId`/`distributionId` are UUID strings; resolve every ID from a
live call before using it.

## Tools

| Tool | What it does |
|------|-------------|
| `tenant-get` | Current tenant context |
| `workspace-list` | Workspaces → items use `id` (not `workspaceId`) |
| `concierge-list-routers` | Existing Concierge routers → `{routers: [...]}`; read their form/trigger fields to discover valid `dataField` references |
| `user-find` | Email/name → user; bare array of `{id, name, email, …}` |
| `team-create` | Create a team (routing target) |
| `team-add-users` | Add members to a team |
| `meeting-type-create` | Create a team meeting type (**not atomic** — see below) |
| `rule-create` | Create an ownership or segment rule (live immediately, revision 1) |
| `rule-list` | Existing rules — copy conditions/`workspaceId`; filter `{ruleBuilderVersion: ["ExplicitV1"], workspaceId}` |
| `distribution-create` | Create + publish a distribution (assignment pool) |
| `distribution-list-put` | Existing distributions → **top-level array**; name = `published.name`, ID = `id` |
| `meeting-type-list` | Existing meeting types (verify names) |
| `concierge-router-create` | Create + **publish live** the router (no draft state via API) |
| `concierge-router-get` | Read back for verification → `ConciergeRouter` (no `status` field) |

## Data fields (the API gap)

There is **no MCP/Edge tool to list, read, create, or map data fields**, and **no way to
map a web form** via the API — both are UI-only (Settings → Data Fields; Concierge Form
Mapping). The builder only *references* data fields:

- **Standard defaults** (`PersonEmail`, `PersonFirstName`, `PersonLastName`, `CompanyName`,
  `CompanyEmployees`, `PersonCountry`, `PersonPhone`, `PersonTitle`, `PersonState`) are
  always valid.
- **Custom fields** must be created in the UI first; reference them by their **UUID**.
- Discover what a tenant already uses by reading existing routers' `form`/trigger fields
  (`concierge-list-routers` → `concierge-router-get`).
- An unknown `dataField` fails `concierge-router-create` with **400** — never invent one.

## Teams

`team-create` → `{workspaceId*, name*, members?}` (members = seed `userId`s). Returns
`{id, workspaceId, name, members, metadata}`. Add more later: `team-add-users` →
`{teamId*, userIds*[]}` (already-members skipped). **Teams can't be empty** — seed at least
the admin as a placeholder.

## Meeting types

`meeting-type-create` → `{workspaceId*, name*, duration*}` + optional `description`,
`inviteTitle`, `inviteDescription`, `location`, `sharedWith`. `duration` is a Scala
duration string: `"30 minutes"`, `"1 hour"`.

- **Not atomic:** create sets only name / duration / default location; other fields are
  applied by follow-up calls. If a follow-up fails, the meeting type exists without them —
  fix with `meeting-type-update`, don't re-create (that duplicates). Prefer creating with
  the fields you need up front.
- `description` is **internal**; guest-facing invite text is `inviteTitle` /
  `inviteDescription` (both accept `{CP.*}` merge tags).
- `sharedWith` = `{type: "Workspace"}` or `{type: "Teams", teamIds}`; supplying it
  provisions the sharing scope. Omit `location` to inherit the workspace default.

## Rules

`rule-create` → `{dto}` where `dto` is one variant (choose by kind):

- **Segment (non-ownership):** `{type: "CreateRuleRequest", workspaceId*, name*, conditions*}`
- **Ownership:** `{type: "CreateOwnershipRuleRequest", workspaceId*, name*, conditions*, teamId?}`

Every conditions node carries a `type` discriminator. Typical segment shape (OR of
per-source groups; AND within a group):

```
conditions: {type: "ConditionGroup", id: "<any>", operator: "or", conditions: [
  {type: "ConditionGroup", id: "<any>", operator: "and", conditions: [
    {type: "StaticValueCondition", conditionId: "<any>",
     dataReference: {source: "DF", object: "Person", field: "NumberOfEmployees"},
     operator: "<=", value: 250},
    {type: "StaticValueCondition", conditionId: "<any>",
     dataReference: {source: "DF", object: "Person", field: "Country"},
     operator: "isAnyOf", value: ["United States","Canada","Mexico"]}
  ]}
]}
```

Ownership rule condition (routes to the record owner; optionally a custom owner field):

```
conditions: {type: "ConditionGroup", id: "<any>", operator: "or", conditions: [
  {type: "OwnershipCondition", conditionId: "<any>",
   ownership: {source: "SF", object: "Account", field: "OwnerId"},
   searchOwnershipBy: "CrmIdOrEmail"}   # or a custom field, e.g. field: "CSM__c"
]}
```

- `source` (`DataSource`): `SF` | `DF` | `CP` | `HS` | `MK`. `operator` incl. `equal`,
  `notEqual`, `isAnyOf`, `isNotAnyOf`, `contains`, `<`, `>`, `<=`, `>=`, `startsWith`, …;
  `SingleParameterCondition` uses `empty` | `notEmpty` (no `value`).
- `searchOwnershipBy`: `CrmIdOrEmail` (default) | `SalesforceIdOrEmail` | `TeamMemberFullNames`.
- `id`/`conditionId` are any non-blank strings unique within the rule. Fastest safe path:
  copy conditions from a `rule-list` result (they already carry the discriminators).
- ⚠ Live immediately with no dry-run — a misconfigured rule misroutes in every router that
  references it. Match objects (`MatchedAccount`, etc.) are for matching-config references,
  not ordinary CRM objects.

## Distributions

`distribution-create` → `{teamId*, workspaceId*, name*, assignmentTypeConfig*, weights?, …}`.
`name` is **required** (a nameless distribution is legacy/unusable). Default meeting pool:

```
assignmentTypeConfig: {type: "Meeting",
  handling: {type: "Flexible", reassignmentType: "AnyTeamMember", allowPickingAssignee: false},
  limits: {type: "MeetingLimitUnset"}}
```

Returns `{distributionId}`. `weights: [{userId, weight}]` optional (round-robin balance);
tune caps later with `distribution-adjust-v3`. Other `type`s: `Record`, `Conversation`.

## Router

`concierge-router-create` → `{workspaceId*, name*, routing*}` + optional `form`,
`inAppButton`, `routerLink`, `branding`, `localizations`. **Publishes live on success**;
the URL `slug` is derived from `name` and returned. `workspaceId` must be a **team**
workspace.

```
routing: {routes: [{ruleId*, outcome*}], catchAll*}        # catchAll REQUIRED; routes ordered top-down
outcome = {type: "Schedule", assignment*, meetingTypeId*, timeout?, crmActions?}
        | {type: "Redirect", url*}
assignment = {type: "Distribution", distributionId} | {type: "User", userId}
timeout    = {minutes*, onTimeout*: {type: "Landing"} | {type: "Url", url}}   # omit → default 10 min → Landing
crmActions = [{type: "ConvertLead"} | {type: "Notify", slackChannel?}]        # ConvertLead is the ONLY API CRM action
form[]        = {dataField*, label*, required*, description?, hidden?}         # MUST include PersonEmail; hidden = a prefilled value
inAppButton[] = {dataField*}                                                  # MUST include PersonEmail
routerLink[]  = {dataField*, label*, required*, hidden?}                       # MUST include PersonEmail; gives a shareable Router Link URL
branding      = {coverImage?, headingText?, language?}
```

Omitting all trigger kinds auto-generates a minimal email-only Chili webform. If the final
publish step fails, the router is left as an **unpublished draft (422)** — retrying mints
another; fix/delete the leftover in the Concierge app.

## Typed errors

| Error | HTTP | Meaning / behavior |
|-------|:---:|--------------------|
| invalid `dataField` | 400 | Field doesn't exist — use a standard default or a real UUID; create custom fields in the UI first |
| publish-failure | 422 | Router saved as an unpublished draft — nothing live; fix/delete the draft in the Concierge app, don't blind-retry |
| `RouterWorkspaceNotManageable` | 4xx | Workspace can't be managed by this key / isn't a team workspace |
| rule revision conflict | 409 | Re-fetch the rule (`rule-list`) and retry |
| 403 | 403 | Missing scope — name the operation; fix in Admin Center → API Keys |

## Permissions

Needs create scopes for team, meeting-type, rule/distribution, and concierge on the API
key, plus read scopes for discovery. A 403 names the missing scope.

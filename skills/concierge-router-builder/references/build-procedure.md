# Build procedure — concierge-router-builder

> ⚠️ **Runs only after the Phase 2 confirmation and `dry_run=false`.** The build creates
> many objects and publishes a **live** Concierge router. It is **not transactional** — a
> failure partway leaves earlier objects behind (see § Partial-build recovery). All field
> shapes → `api-reference.md`.

Build in **dependency order** — an object must exist (and its ID be captured) before the
object that references it. Within a step, independent creates can run in parallel; across
steps, respect the dependencies below.

## Step 1 — Resolve the admin's user

`user-find` with the admin's email/name → capture `userId` (the placeholder team member and
the fallback for `assignment: {type: "User"}` outcomes).

## Step 2 — Teams  *(parallel)*

`team-create` `{workspaceId, name, members}` for each planned team. Seed `members` with the
chosen reps' `userId`s, or the admin's `userId` as a placeholder — **teams can't be empty**.
Capture each `teamId`. Add extra reps with `team-add-users` if needed. Resolve rep emails to
`userId`s via `user-find` first.

## Step 3 — Meeting types  *(parallel, can overlap Step 2)*

`meeting-type-create` `{workspaceId, name, duration}` per planned meeting type (reuse one
across all rules if the admin chose "same for all"). Set `inviteTitle`/`inviteDescription`
and `sharedWith` in the same call where possible — **create is not atomic**, so avoid
follow-up calls that could half-configure it; if one is unavoidable and fails, repair with
`meeting-type-update` (never re-create — that duplicates). Capture each `meetingTypeId`.

## Step 4 — Rules  *(parallel; needs team IDs for ownership rules)*

`rule-create` per rule, in the planned order:

- **Ownership** rule: `dto.type = "CreateOwnershipRuleRequest"`, carry the owner team's
  `teamId`; conditions use `OwnershipCondition` (OwnerId, or the customer custom owner field).
- **Customer** rule: usually a non-ownership rule that filters the customer-defining field
  (or an ownership rule on a custom owner field).
- **Segment** rules: `dto.type = "CreateRuleRequest"` with the OR-of-groups conditions from
  `segment-presets.md`.

Capture each `ruleId`. Rules are **live immediately** — order matters only in the router's
`routes`, but a wrong condition misroutes everywhere the rule is used.

## Step 5 — Distributions  *(parallel; needs team IDs)*

`distribution-create` `{teamId, workspaceId, name, assignmentTypeConfig}` for each team that
a scheduling outcome routes to, using the default Meeting/Flexible/MeetingLimitUnset config
(→ `api-reference.md` § Distributions). Add `weights` only if the admin specified balance.
Capture each `distributionId`.

## Step 6 — Router  *(last; needs rule + distribution + meeting-type IDs)*

`concierge-router-create` `{workspaceId, name, routing, form?, inAppButton?, routerLink?}`:

- `routing.routes` in order — ownership → customer → segments — each `{ruleId, outcome}`
  with `outcome: {type: "Schedule", assignment: {type: "Distribution", distributionId},
  meetingTypeId, timeout?, crmActions?}`. Use `{type: "User", userId}` only for a specific host.
- `routing.catchAll` — **required**; Schedule (fallback team) or Redirect per the plan.
- `form` — planned fields, each `{dataField, label, required}`, **including `PersonEmail`**.
  Add `routerLink` / `inAppButton` if requested (each must include `PersonEmail`).
- `crmActions` settable here is `[{type: "ConvertLead"}]` and/or `[{type: "Notify", slackChannel?}]`
  (ConvertLead is the only CRM-mutating one; Notify posts to Slack). Other CRM actions are
  UI-only — captured for the hand-off, not sent.
- On invalid `dataField` (400): re-check valid references via `concierge-list-routers` and
  retry with a corrected reference — do not invent names.

## Step 7 — Verify

`concierge-router-get` → confirm the routing rows, catch-all, and form match the plan; read
the returned `slug` for the booking URL. Then present Phase 4 output → `output-format.md`.

## Partial-build recovery

The build is not transactional. If any step fails:

1. **Stop** — do not continue creating dependent objects.
2. Report exactly what was created so far (with IDs) and what failed (with the error).
3. Offer to (a) fix the cause and resume from the failed step reusing already-created
   objects, or (b) leave it for manual cleanup — never silently abandon a half-built router.
4. A router-publish 422 leaves an **unpublished draft**; tell the admin it must be fixed or
   deleted in the Concierge app (retrying `create` mints another draft).
5. Rule revision conflict (409) → re-fetch via `rule-list` and retry just that rule.

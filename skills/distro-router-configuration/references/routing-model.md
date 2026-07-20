# Routing model — distro-router-configuration

Distro routing is **lead routing**: rows pair a rule (conditions) with a **distribution** (the assignee pool). There is no meeting type on rows — that's Concierge/Handoff. The catch-all is a distribution too.

## The write shape (`routing` on create/update)

```
routing: {
  trigger: {                       # REQUIRED
    objectType: Lead | Contact | Account | Opportunity | Case | CustomObject
              | DuplicateLead | DuplicateContact | AccountTeamMember,
    eventTypes: [ {type: NewRecord} | {type: UpdateField} | {type: NewRecordOrUpdateField}
                | {type: Scheduled} | {type: Signal} ],   # at least one
    evaluation?: string,           # advanced; omit unless copying from an existing router
    delay?: {type: BeforeRecordEval | AfterRecordEval, ...}
  },
  routes: [                        # evaluated in order
    {ruleId?: string,              # rule = the conditions; from rule-list
     distributionId: string,       # REQUIRED — where matching records go
     actions?: [...]}              # optional side effects, see below
  ],
  catchAll: {distributionId, actions?},   # REQUIRED — records matching no rule
  routingSteps?: [ {type: Enrichment, fieldMappings?} | {type: SpamCheck} ]
}
```

## Resolving IDs (never invent them)

- **Rules** → `rule-list` with `filter: {ruleBuilderVersion: ["ExplicitV1"], workspaceId}` (per QA ground truth — don't pass `routerId`). Match by rule name; put the rule's ID in `ruleId`.
- **Distributions** → `distribution-list-put` (returns a **top-level array**). Name lives in `published.name`, ID in `id`.
- When `changes` names a rule or distribution that doesn't resolve, list the closest candidates and ask — never guess an ID.

## Row actions (optional, per row and on the catch-all)

`ReassignRecord`, `SendEmailReminderToAssignee`, `SendSlackToAssignee`, `UpdateField`, `UpdateFieldDynamic`, `UpdateOwnership` — each a discriminated object (`{type: ...}` plus type-specific fields). Only plan actions the human asked for; copying existing rows' actions verbatim from a `get` is safe.

## The read shape is NOT the write shape

`distro-router-get` returns a summary: `rows: [{ruleId?, outcome}]` where `outcome` is `{type: "Route", distributionId, actions?}` or `{type: "Unrepresentable"}`. To update, convert summary rows back to write rows (`{ruleId, distributionId, actions}` from each `Route` outcome). Any `Unrepresentable` outcome (or `representable: false` at the top) → abort the update; the router must be edited in the UI.

## Rendering rows for humans

Always show routing as a table before/after:

```
| # | Rule | → Distribution | Actions |
|---|------|----------------|---------|
| 1 | EMEA - MQL (rule_8f…) | EMEA SDRs (dist_2a…) | — |
| 2 | (catch-all) | Global Queue (dist_9c…) | Slack assignee |
```

Resolve IDs to names in the table; keep the raw IDs in parentheses so the plan is auditable.

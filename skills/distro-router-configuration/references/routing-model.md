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
    {ruleId: string,               # REQUIRED — rule = the conditions; from rule-list
     distributionId: string,       # REQUIRED — where matching records go
     actions: [...]}               # ≥1 action required to publish, see below
  ],
  catchAll: {distributionId, actions},    # REQUIRED — records matching no rule; also needs ≥1 action
  routingSteps?: [ {type: Enrichment, id?, fieldMappings} | {type: SpamCheck, id?, salesforceWrite} ]
}
```

## Resolving IDs (never invent them)

- **Rules** → `rule-list` with `filter: {ruleBuilderVersion: ["ExplicitV1"], workspaceId}` (per QA ground truth — don't pass `routerId`). Match by rule name; put the rule's ID in `ruleId`.
- **Distributions** → `distribution-list-put` (returns a **top-level array**). Name lives in `published.name`, ID in `id`.
- When `changes` names a rule or distribution that doesn't resolve, list the closest candidates and ask — never guess an ID.

## Row actions (per row and on the catch-all)

`ReassignRecord`, `SendEmailReminderToAssignee`, `SendSlackToAssignee`, `UpdateField`, `UpdateFieldDynamic`, `UpdateOwnership` — each a discriminated object (`{type: ...}` plus type-specific fields). The distribution picks WHO; actions decide WHAT — **at least one action per route and on the catch-all is required to publish** (an actionless route fails). On update, a `ruleId`-matched row **keeps its existing actions**, so supply actions only where you change them or on new rows; copying existing rows' actions verbatim from a `get` is safe.

## Updates are an overlay, not a full replace

`distro-router-get` returns a summary: `rows: [{ruleId?, outcome}]` where `outcome` is `{type: "Route", distributionId?, actions}` or `{type: "Unrepresentable", kind}`. `distro-router-update` **overlays** your `routing` onto the router's current routing:

- Each sent route is matched to an existing row by `ruleId` (catch-all to catch-all) and only its **distribution + actions** are swapped in. App-only config on that row — SLAs, matchers, campaign addition, lead-to-contact conversion, send-to-routers, duplicate-matching, app-only actions — is **preserved**.
- A sent row whose `ruleId` matches nothing is **appended** as a new route.
- The **trigger and `routingSteps` are replaced** from what you send — an empty or absent `routingSteps` **clears** them, so read them back from the `get` and resend them (carrying each step's `id` keeps it, and variables referencing it, stable).
- `Unrepresentable` outcomes (or `representable: false` at the top) **no longer block updates** — the flag only means the lossy summary doesn't round-trip exactly. The overlay edits such routers safely, changing only what you address by `ruleId`.
- The overlay applies to the router's editable **draft** (unpublished edits made in the Distro app are part of the base) and the result is republished.

To update: start from the current summary, build write rows (`{ruleId, distributionId, actions}` from each `Route` outcome), apply the changes, and send the **complete row set** — don't rely on omitted rows surviving the overlay.

## Rendering rows for humans

Always show routing as a table before/after:

```
| # | Rule | → Distribution | Actions |
|---|------|----------------|---------|
| 1 | EMEA - MQL (rule_8f…) | EMEA SDRs (dist_2a…) | — |
| 2 | (catch-all) | Global Queue (dist_9c…) | Slack assignee |
```

Resolve IDs to names in the table; keep the raw IDs in parentheses so the plan is auditable.

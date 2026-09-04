# Write procedures — handoff-router-configuration

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Handoff routers are
> **always-live**: there is no Inactive state and no separate activation step, so every
> write below changes live handoff routing the moment it succeeds. Run these only after
> the dry-run plan is confirmed by the human (see SKILL.md § Checkpoint):
> - **`handoff-router-create`** — the new router starts routing live handoffs on success.
> - **`handoff-router-update`** — live immediately. On a representable router it is a
>   full replace (any row not in the payload is **gone**); on an app-built router it is
>   an overlay patch (untouched rows preserved) — see api-reference § Representability.
>   Every update also publishes the router's current draft, unpublished app edits included.
> - **`handoff-router-delete`** — permanently removes the router and its routing.

## Building routing rows

1. Parse `changes` into rows: each row = a rule (condition) → an outcome.
2. Resolve every ID from live calls — never invent:
   - rule names → `rule-list` (`filter: {ruleBuilderVersion: ["ExplicitV1"], workspaceId}`) → `ruleId`
   - distribution names → `distribution-list-put` (`{results: [...], total, page, pageSize}` — iterate `results`, CEH-11548; `published.name` / `id`)
   - rep names/emails → `user-find` → `userId`
   - meeting type names → `meeting-type-list` → `meetingTypeId`
3. Every `Schedule` outcome needs **both** an `assignment` (`{type: Distribution, distributionId}` or `{type: User, userId}`) **and** a `meetingTypeId`. If the human didn't name a meeting type, ask — don't default silently.
4. The only optional per-row extra is `crmActions`, which accepts any combination of `{type: "ConvertLead"}`, `{type: "AddToCampaign", campaignId, memberStatus}` (CEH-11141), `{type: "SalesforceUpdateFields", ...}` / `{type: "HubspotUpdateFields", ...}`, `{type: "SalesforceUpdateOwnership", ...}` / `{type: "HubspotUpdateOwnership", ...}` (CEH-11302/CEH-11303), and `{type: "SalesforceCreateEvent", ...}` / `{type: "HubspotCreateEngagement", ...}` (CEH-11588/11589) — shapes and defaults → api-reference § Write shapes. Handoff writes accept **no** `Redirect` outcome, **no** `timeout`, **no** `Notify`, and **no** Upsert variants — the API rejects them (400); those belong to concierge routers. A `SalesforceCreateEvent.relatedTo` of `ExplicitObject`/`RelationDisabled` is a typed 400. `Other{kind}` appears only on read and is rejected on write. Resolve `campaignId` from the CRM (never invent it) and confirm the intended `memberStatus` with the human.
5. `catchAll` is **optional** on create and update (CEH-11358) — omitting it on create produces a router with no fallback path; on update it preserves the current catch-all. If the human didn't specify one, ask what unmatched handoffs should do and state the choice in the plan.
6. When a name resolves to nothing or to several candidates, list the closest matches and ask.

## Create

1. Payload: `{workspaceId, name, routing}` (routing per above).
2. `handoff-router-create` → on success the router is **live**. Say so.
3. Verify: `handoff-router-get` → rows/catch-all match the plan (`representable: true` expected for API-created routers).

## Update

1. `handoff-router-get` → read `known` (must be `true`) and `routing.representable` → the write **mode** (api-reference § Representability).
2. **Full replace** (`representable: true`): reconstruct the **complete** desired `routing` from the current summary + requested changes. Convert each read row (`outcome: Schedule{distributionId|userId, meetingTypeId}`) back to a write row; the plan lists every row as kept / changed / added / removed.
   **Overlay** (`representable: false`): build `routing.routes` from **only** the rows to change (existing `ruleId`s) or add (new `ruleId`s), plus the `catchAll` outcome; the plan marks every unlisted existing row "(preserved — app-built config untouched)". If the request needs a row removed or reordered, stop: that part must be done in the Handoff app.
3. `handoff-router-update` with `{name?, routing}` — omit `routing` entirely for a rename-only update (the current routing is kept).
4. Verify by re-`get`; compare to plan. After an overlay, expect changed rows to read back as `Schedule` and preserved rows to keep their previous (possibly unrepresentable) outcomes.

## Delete

1. Show the router's current routing in the plan (it disappears with the router).
2. `handoff-router-delete` → verify with `handoff-router-list` (gone).
3. There is no deactivate step to soften this — deletion is the only removal, and it is irreversible.

## Error handling

- Typed 400s (`HandoffRouterConversionError`) name the offending part — surface verbatim, fix the plan, re-present; never blind-retry a write.
- `RouterPublishRejected` — the config was structurally valid but publish refused it; report the message and stop.
- Publish-failure `422` — the changes were **saved on an unpublished draft**; nothing went live. Tell the human the draft must be fixed or deleted in the Handoff app, and verify with `handoff-router-get` what is actually live.
- 403 → missing `handoff.*` permission; name the operation and the fix (Admin Center → API Keys).
- After any failure mid-apply, re-read (`handoff-router-get`) and report the actual current state — never assume.

# Write procedures — concierge-router-configuration

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Concierge routers are
> **always-live**: there is no Inactive state or activation step, so every write below
> changes the live public form the moment it succeeds. Run these only after the dry-run
> plan is confirmed by the human (see SKILL.md § Checkpoint):
> - **`concierge-router-create`** — the router's form goes live on success.
> - **`concierge-router-update`** — full-replace routing: any row not in the payload is
>   **gone**, and the new config serves form submissions immediately.
> - **`concierge-router-delete`** — permanently removes the router; **its public form
>   URL (slug) stops working instantly** — anything embedding or linking it breaks.

## Building routing rows

1. Parse `changes` into rows: each row = a rule (condition) → an outcome.
2. Resolve every ID from live calls — never invent:
   - rule names → `rule-list` (`filter: {ruleBuilderVersion: ["ExplicitV1"], workspaceId}`) → `ruleId`
   - distribution names → `distribution-list-put` (top-level array; `published.name` / `id`)
   - rep names/emails → `user-find` → `userId` · meeting types → `meeting-type-list` → `meetingTypeId`
3. Every `Schedule` outcome needs **both** an `assignment` and a `meetingTypeId` — ask rather than default.
4. Optional per-row extras only when asked: `timeout: {minutes, onTimeout: Landing|Url}`, `crmActions: [ConvertLead | Notify{slackChannel}]`.
5. `catchAll` is **required** — if unspecified, ask what unmatched submissions should do.
6. Form changes: each field is `{dataField, label, required, description?, hidden?}` — `dataField` must reference a real workspace data field; keep existing fields unless the human asked to change them. Branding: `{coverImage?, headingText?, language?}`.

## Create

1. Payload: `{workspaceId, name, routing}` + optional `form`/`branding`/`localizations`.
2. `concierge-router-create` → on success the router (and its form URL) is **live**. Report the returned `slug`.
3. Verify: `concierge-router-get` → rows/catch-all match the plan (`representable: true` expected for API-created routers).

## Update (full-replace routing)

1. `concierge-router-get` → representability gate (api-reference § Representability).
2. Reconstruct the **complete** desired `routing` from the current summary + requested changes; the plan lists every row as kept / changed / added / removed. `form`/`branding` are included only when they change.
3. `concierge-router-update` with `{name?, routing, form?, branding?, localizations?}` — `routing` always included when routing changes; never send a partial routes list.
4. Verify by re-`get`; compare to plan.

## Delete

1. The plan shows the router's `slug` (the public URL that dies) and its current routing.
2. `concierge-router-delete` → verify with `concierge-list-routers` (gone).
3. There is no deactivate step — deletion is the only removal, and it is irreversible.

## Error handling

- `ConciergeRouterNotFound` (404) → re-resolve the router via `concierge-list-routers`; the ID was stale.
- `RouterPublishRejected` — structurally valid but publish refused; report the message and stop.
- `RouterRoutingNotRepresentable` → abort with the edit-in-UI guidance (should have been caught in the preflight gate).
- 403 → missing concierge scope; name the operation and the fix (Admin Center → API Keys).
- After any failure mid-apply, re-read (`concierge-router-get`) and report the actual current state — never assume.

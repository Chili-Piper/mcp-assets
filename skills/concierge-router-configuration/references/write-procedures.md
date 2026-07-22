# Write procedures — concierge-router-configuration

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Concierge routers are
> **always-live**: there is no Inactive state or activation step, so every write below
> changes the live public form the moment it succeeds. Run these only after the dry-run
> plan is confirmed by the human (see SKILL.md § Checkpoint):
> - **`concierge-router-create`** — the router's form goes live on success.
> - **`concierge-router-update`** — live immediately. Routing is a full replace on a
>   representable router (any row not in the payload is **gone**) or an overlay patch on
>   an app-built one (untouched rows preserved) — see api-reference § Representability.
>   Every update also publishes the router's current draft, unpublished app edits included.
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
6. Form changes: each field is `{dataField, label, required, description?, hidden?}` — `dataField` must reference a real, **already-existing** data field (no API lists or creates them: standard defaults like `PersonEmail` are always valid, custom fields need their UUID from the app, and an unknown reference fails the write with 400 → api-reference § Data fields); keep existing fields unless the human asked to change them; the field list must include `PersonEmail`. Trigger changes: `inAppButton` (`[{dataField}]`) and `routerLink` (`[{dataField, label, required?, hidden?}]`) are each writable and replace **only their own kind** — writing one never destroys the others; both must include `PersonEmail`. Branding: `{coverImage?, headingText?, language?}` — merged per sub-field (omitted sub-fields preserved).

## Create

1. Payload: `{workspaceId, name, routing}` + optional `form`/`inAppButton`/`routerLink`/`branding`/`localizations`. Supplying no trigger kind auto-generates a minimal email-only Chili webform; a `routerLink` gives the router a shareable Router Link URL.
2. `concierge-router-create` → on success the router (and its form URL) is **live**. Report the returned `slug` — since DISTRO-4626 the create response carries the derived published slug, so the booking URL comes straight back (no follow-up get needed).
3. Verify: `concierge-router-get` → rows/catch-all match the plan (`representable: true` expected for API-created routers).

## Update

1. `concierge-router-get` → read `known` (must be `true`), `routing.representable` → the routing write **mode**, and `form.representable` if a form write is planned (api-reference § Representability).
2. **Full replace** (`representable: true`): reconstruct the **complete** desired `routing` from the current summary + requested changes; the plan lists every row as kept / changed / added / removed.
   **Overlay** (`representable: false`): build `routing.routes` from **only** the rows to change (existing `ruleId`s) or add (new `ruleId`s), plus the `catchAll` outcome; the plan marks every unlisted existing row "(preserved — app-built config untouched)". If the request needs a row removed or reordered, stop: that part must be done in the Concierge app.
3. `concierge-router-update` with `{name?, routing?, form?, inAppButton?, routerLink?, branding?, localizations?}` — send only the dimensions that change (omitted dimensions are preserved). A `name` change re-derives the slug: state the new public URL in the plan.
4. Verify by re-`get`; compare to plan. After an overlay, expect changed rows to read back as written and preserved rows to keep their previous (possibly unrepresentable) outcomes.

## Delete

1. The plan shows the router's `slug` (the public URL that dies) and its current routing.
2. `concierge-router-delete` → verify with `concierge-list-routers` (gone).
3. There is no deactivate step — deletion is the only removal, and it is irreversible.

## Error handling

- `ConciergeRouterNotFound` (404) → re-resolve the router via `concierge-list-routers`; the ID was stale.
- `RouterPublishRejected` — structurally valid but publish refused; report the message and stop.
- `RouterRoutingNotRepresentable` (409) → only expected from a `form` write on a third-party webform (routing updates stopped returning it with DISTRO-4614); abort with the edit-in-UI guidance.
- Publish-failure `422` — the changes were **saved on an unpublished draft**; nothing went live. Tell the human the draft must be fixed or deleted in the Concierge app, and verify with `concierge-router-get` what is actually live.
- 403 → missing concierge scope; name the operation and the fix (Admin Center → API Keys).
- After any failure mid-apply, re-read (`concierge-router-get`) and report the actual current state — never assume.

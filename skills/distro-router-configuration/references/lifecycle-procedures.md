# Lifecycle procedures — distro-router-configuration

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Run these only after the
> dry-run plan is confirmed by the human (see SKILL.md § Checkpoint), and only on the
> resolved IDs in that plan:
> - **`distro-router-delete`** — permanently removes the router and its routing config.
> - **`distro-router-update`** — overlay, but the **trigger and `routingSteps` are
>   replaced** from what you send (an empty/absent `routingSteps` **clears** them), and
>   omitted rows should not be relied on to survive — send the complete row set.
> - **`distro-router-activate`** — the router starts routing **live CRM records
>   immediately**; requires its own explicit confirmation.

## State machine

```
create → [Inactive] —activate→ [Activating] → [Active]
[Active] —deactivate→ [Deactivating] → [Inactive] —delete→ (gone)
any transition can land in [Error{message}] → surface message, escalate
```

## Create

1. Build the full payload: `{workspaceId, name, routing}` — `routing` per `references/routing-model.md` (requires `trigger` + `catchAll`).
2. `distro-router-create` → returns the router **`Inactive`**. Tell the human explicitly: *"Created but not routing — activation is a separate step."*
3. On `422 RouterCreationFailed`: the API rolled back everything (all-or-nothing) — nothing was left behind. Fix the cause from the error message and retry the same create.
4. Verify: `distro-router-get` → `status.type === "Inactive"`, routing matches the plan.

## Activate

1. Confirm separately with the human (live-routing warning).
2. `distro-router-activate` → response may already show `Active`, or `Activating`.
3. If `Activating`: poll `distro-router-get` every ~5 s, up to 2 minutes. Stop at `Active` (done), or `Error` (surface `status.message`, escalate). Report polling progress.
4. Idempotent — re-calling on an `Active` router is safe.

## Update (overlay)

1. `distro-router-get` → read the current rows, catch-all, trigger, and `routingSteps` — this summary is the base the overlay addresses. `representable: false` / `Unrepresentable` rows do **not** block the update (→ api-reference § Representability (advisory)); note in the plan which app-only config the overlay preserves on those rows.
2. Reconstruct the **complete** desired `routing` (every row, the catch-all, the trigger, the current `routingSteps` with their `id`s) — start from the current summary, apply the changes. Rows are matched by `ruleId` (only distribution + actions swap in; a matched row keeps its existing actions unless you send new ones); an unmatched `ruleId` is appended as a new route; the trigger and `routingSteps` are **replaced** (empty/absent `routingSteps` clears them). New rows and the catch-all need ≥1 action.
3. `distro-router-update` with `{name?, description?, routing}` — `routing` always included (400 `RouterRoutingRequired` without it).
4. **Activation state is preserved**: an `Active` router stays active and the new config goes live immediately (say so in the plan); an `Inactive` one stays inactive. The overlay applies to the router's editable **draft**, so unpublished app edits are part of what gets published — mention this if the `get` looks different from what the human expects.
5. Verify: re-`get`, compare rows/catch-all to the plan.
6. On a typed 422: the update is **NOT rolled back**. Publish failure → changes sit on an unpublished draft, prior config still live. Re-activation failure → new config published but router `Inactive`. Surface the message and direct the human to fix/activate in the Distro app.

## Deactivate (async)

1. `distro-router-deactivate` → returns `{status: {type: "Deactivating"}}` immediately.
2. Poll `distro-router-get` every ~5 s (≤2 min) until `Inactive`. On `Error`, surface the message.
3. Never pass `force`. Idempotent on an already-`Inactive` router.

## Delete

1. Gate: `distro-router-get` → if `status.type !== "Inactive"`, the plan must include deactivate → poll-until-Inactive as numbered steps before the delete. A delete on a non-Inactive router returns `409 RouterDeleteRejected`.
2. `distro-router-delete` (takes only `routerId` — the `force` param exists on deactivate, not delete).
3. Verify: `distro-list-routers` — the router is gone.

## Polling etiquette

- Interval ~5 s, budget 2 minutes; after the budget, report the last observed status and hand off to the human (do not loop forever).
- Every poll result feeds the `status` output so the human sees progress.

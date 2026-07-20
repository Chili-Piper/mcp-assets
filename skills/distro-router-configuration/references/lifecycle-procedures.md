# Lifecycle procedures — distro-router-configuration

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Run these only after the
> dry-run plan is confirmed by the human (see SKILL.md § Checkpoint), and only on the
> resolved IDs in that plan:
> - **`distro-router-delete`** — permanently removes the router and its routing config.
> - **`distro-router-update`** — full-replace: any row not in the payload is **gone**.
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

## Update (full-replace)

1. `distro-router-get` → require `routing.representable === true` (else abort → api-reference § Representability).
2. Reconstruct the **complete** desired `routing` (every row, the catch-all, the trigger) — start from the current summary, apply the changes. Any row omitted from the payload is deleted.
3. `distro-router-update` with `{name?, description?, routing}` — `routing` always included (400 `RouterRoutingRequired` without it).
4. **Activation state is preserved**: an `Active` router stays active and the new config goes live immediately (say so in the plan); an `Inactive` one stays inactive.
5. Verify: re-`get`, compare rows/catch-all to the plan.

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

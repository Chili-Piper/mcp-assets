# Output format — handoff-router-configuration

## Router list

```
## Handoff routers — <workspace>

| Router | Rows | Catch-all |
|--------|-----:|-----------|
| AE Handoff | 3 | Global AE Queue (distribution) |
| CS Escalation | 1 | maria@acme.com (user) |
```

(No status column — Handoff routers are always live.)

## Router detail / dry-run plan (Checkpoint)

```
## Plan — update "AE Handoff" (rtr_7b3c…) · DRY RUN, nothing written

Representability check: ✅ routing.representable = true
⚠️ Always-live: this routing goes LIVE the moment it is applied.

### Routing (current → proposed)
| # | Rule | Outcome (current) | Outcome (proposed) |
|---|------|-------------------|--------------------|
| 1 | Enterprise | Schedule → EMEA AEs · Handoff Call | (unchanged) |
| 2 | Mid-market | Schedule → NA Pod A · Handoff Call | Schedule → NA Pod B · Handoff Call ← change |
| — | (catch-all) | Schedule → Global AE Queue · Handoff Call | (unchanged) |

### Write calls that would run
1. handoff-router-update rtr_7b3c… (full routing object — 2 rows + catch-all)

⚠️ Handoff routers are always-live — apply publishes immediately. Apply?
```

Delete plans show what disappears:

```
## Plan — delete "CS Escalation" (rtr_9d1e…) · DRY RUN
This removes the router AND its routing (1 row + catch-all, shown above). Irreversible.
```

## Result (after apply, dry_run=false)

```
## Applied — "AE Handoff" (rtr_7b3c…) · LIVE

Routing verified via handoff-router-get: 2 rows + catch-all match the plan ✅

Audit trail:
1. handoff-router-get rtr_7b3c… (pre-read, representable ✅)
2. handoff-router-update rtr_7b3c… → 200 (live immediately)
3. handoff-router-get rtr_7b3c… (verify)
```

## Rules

- Every plan and result carries the **always-live** warning — there is no inactive staging state to fall back on.
- Outcomes render as `Schedule → <assignee> · <meeting type>` or `Redirect → <url>`; resolved names with raw IDs in parentheses on first mention.
- Read-only outcome variants (`OwnerAssign`, `ContactOptions`, `CrmAction`, `Other`) render as-is with a note that they can't be edited via this API.

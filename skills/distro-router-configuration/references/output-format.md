# Output format — distro-router-configuration

## Router list

```
## Distro routers — <workspace>

| Router | Status | Trigger |
|--------|--------|---------|
| Inbound MQL | 🟢 Active | Lead · NewRecord |
| EMEA expansion | ⚪ Inactive | Contact · NewRecordOrUpdateField |
| Legacy 2024 | 🔴 Error: <message> | Lead · UpdateField |
```

Status badges: 🟢 Active · ⚪ Inactive · 🟡 Activating/Deactivating · 🔴 Error.

## Dry-run plan (Checkpoint)

```
## Plan — update "Inbound MQL" (rtr_4f2a…) · DRY RUN, nothing written

Summary coverage: ✅ routing.representable = true (no app-only config on these rows)
Current status: 🟢 Active — the new routing goes LIVE immediately on apply.

### Routing (current → proposed)
| # | Rule | → Distribution (current) | → Distribution (proposed) |
|---|------|--------------------------|---------------------------|
| 1 | EMEA - MQL | EMEA SDRs | EMEA SDRs (unchanged) |
| 2 | NA - MQL | NA Pod A | NA Pod B ← change |
| — | (catch-all) | Global Queue | Global Queue (unchanged) |

### Write calls that would run
1. distro-router-update rtr_4f2a… (overlay — 3 rows + catch-all resent; routingSteps carried over)

Apply it? (Reply 'apply' or re-run with dry_run=false.)
```

Lifecycle plans show the transition and its pre-steps:

```
## Plan — delete "Legacy 2024" (rtr_9c1b…) · DRY RUN

Current status: 🟢 Active → delete requires Inactive.
1. distro-router-deactivate rtr_9c1b…   (async)
2. poll distro-router-get every 5s until Inactive (≤2 min)
3. distro-router-delete rtr_9c1b…       ⚠️ irreversible
```

## Status polling (during apply)

```
Deactivating… 5s → Deactivating · 10s → Deactivating · 15s → ✅ Inactive (14s)
```

## Result (after apply, dry_run=false)

```
## Applied — "Inbound MQL" (rtr_4f2a…)

Final status: 🟢 Active (verified via distro-router-get)
Routing verified: 3 rows + catch-all match the plan ✅

Audit trail:
1. distro-router-get rtr_4f2a… (pre-read: overlay base)
2. distro-router-update rtr_4f2a… → 200
3. distro-router-get rtr_4f2a… (verify)
```

## Rules

- Create results always state: **"Router is Inactive — it will not route records until activated."**
- When `routing.representable = false`, the Summary coverage line lists the `Unrepresentable` rows and their `kind`s, and states that the overlay preserves that app-only config — never present it as a blocker.
- IDs render with resolved names; raw IDs stay in parentheses for auditability.
- On a typed error, show the error name + verbatim message and the specific recovery from api-reference § Typed errors.

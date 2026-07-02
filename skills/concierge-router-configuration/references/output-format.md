# Output format — concierge-router-configuration

## Router list

```
## Concierge routers — <workspace>

| Router | Slug | Rows | Catch-all |
|--------|------|-----:|-----------|
| Inbound Demo | inbound-demo | 4 | AE Queue · Demo (Schedule) |
| Pricing Contact | pricing-contact | 2 | Redirect → /thanks |
```

(No status column — Concierge routers are always live.)

## Dry-run plan (Checkpoint)

```
## Plan — update "Inbound Demo" (rtr_2c8a…, slug: inbound-demo) · DRY RUN, nothing written

Representability check: ✅ routing.representable = true
⚠️ Always-live: this publishes to the live form the moment it is applied.

### Routing (current → proposed)
| # | Rule | Outcome (current) | Outcome (proposed) |
|---|------|-------------------|--------------------|
| 1 | Enterprise domains | Schedule → EMEA AEs · Demo | (unchanged) |
| 2 | Mid-market | Schedule → NA Pod A · Demo | Schedule → NA Pod B · Demo ← change |
| — | (catch-all) | Schedule → AE Queue · Demo | (unchanged) |

### Form / branding changes
(none)

### Write calls that would run
1. concierge-router-update rtr_2c8a… (full routing object — 4 rows + catch-all)

⚠️ Concierge routers are always-live — apply publishes immediately. Apply?
```

Delete plans lead with the dying URL:

```
## Plan — delete "Pricing Contact" (rtr_9e4b…, slug: pricing-contact) · DRY RUN
⚠️ The public form URL /pricing-contact stops working instantly. Irreversible.
Current routing (2 rows + catch-all) shown above disappears with it.
```

## Result (after apply, dry_run=false)

```
## Applied — "Inbound Demo" (rtr_2c8a…) · LIVE

Routing verified via concierge-router-get: 4 rows + catch-all match the plan ✅

Audit trail:
1. concierge-router-get rtr_2c8a… (pre-read, representable ✅)
2. concierge-router-update rtr_2c8a… → 200 (live immediately)
3. concierge-router-get rtr_2c8a… (verify)
```

## Rules

- Every plan and result carries the **always-live** warning; delete plans lead with the slug/URL that dies.
- Outcomes render as `Schedule → <assignee> · <meeting type>` or `Redirect → <url>`; resolved names with raw IDs in parentheses on first mention.
- Read-only outcome variants (`OwnerAssign`, `ContactOptions`, `CrmAction`, `Other`) render as-is with a note that they can't be edited via this API.
- After an inspect-then-fix flow, cite the concierge-debugger/routing-audit finding the change addresses.

# Output format — scheduling-link-management

## Link audit / list

```
## Scheduling links — <workspace or "all workspaces">

### Round-robin (2)
| Link | Slug | Meeting types | Distributions | Booking URL |
|------|------|---------------|---------------|-------------|
| EMEA Demo RR | emea-demo | Demo | EMEA SDRs | …/emea-demo |
| Global Intro | global-intro | Intro Call | Global Queue | …/global-intro |

### Group (1)
| Link | Slug | Host | Required / optional members | Booking URL |
|------|------|------|-----------------------------|-------------|
| Exec Briefing | exec-brief | maria@… | 2 / 1 | …/exec-brief |
```

Personal-link audits list per user: `| slug | meeting type | bookingUrl |`.

## Dry-run plan (Checkpoint)

```
## Plan — create round-robin link "EMEA Demo RR" · DRY RUN, nothing written

| Field | Value |
|-------|-------|
| workspace | Sales (ws_1a2b…) — team workspace ✅ |
| slug | emea-demo → bookingUrl will be …/emea-demo |
| meetingTypeIds | Demo (mt_4f2a…) |
| distributionIds | EMEA SDRs (dist_2c8a…) |
| sharedWith | (default: workspace) |

### Write calls that would run
1. scheduling-link-create-round-robin

Apply it? (Reply 'apply' or re-run with dry_run=false.)
```

Delete plans lead with the dying URL:

```
## Plan — delete group link "Exec Briefing" (lnk_9d4e…) · DRY RUN
⚠️ Booking URL …/exec-brief stops working instantly — every embed/signature using it breaks.
```

Slug-change updates carry the same warning for the old URL.

## Result (after apply, dry_run=false)

```
## Applied — round-robin link "EMEA Demo RR"

Created lnk_7b3c… · live booking URL: …/emea-demo ✅ (from the create response)

Audit trail:
1. meeting-type-list / distribution-list-put (ID resolution)
2. scheduling-link-create-round-robin → 200
3. scheduling-link-list-round-robin filterLinkSlugs=[emea-demo] (verify)
```

## Rules

- Every plan/result quotes the `bookingUrl` affected; deletes and slug changes lead with it.
- Resolved names with raw IDs in parentheses on first mention.
- Array fields shown as complete desired lists (they replace, not merge, on update).
- Personal links render in audits but never appear in write plans (list-only).

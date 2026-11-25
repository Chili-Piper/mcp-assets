# Output format — meeting-type-management

## List / audit view

```
## Meeting types — <workspace or "all workspaces">

| Meeting type | Workspace | Status | Duration | Limit | Invite title |
|--------------|-----------|--------|---------:|-------|--------------|
| Demo Call | Sales | Active | 30 minutes | 3/day (domain) | "Demo with {CP.Host.FullName}" |
| Intro Call | Sales | Inactive | 15 minutes | — | (defaults to name) |
```

## Dry-run plan (Checkpoint)

```
## Plan — update "Demo Call" (mt_4f2a…) · DRY RUN, nothing written

### Guest-visible changes 👁
| Field | Current | Proposed |
|-------|---------|----------|
| inviteDescription | "Join us…" | "Join {CP.Host.FullName} for a demo…" |

### Internal-only changes
| Field | Current | Proposed |
|-------|---------|----------|
| duration | 30 minutes | 45 minutes |

### Write calls that would run
1. meeting-type-update mt_4f2a… {inviteDescription, duration}

Apply it? (Reply 'apply' or re-run with dry_run=false.)
```

Delete plans additionally list dependents:

```
⚠️ 2 scheduling links use this meeting type and will break immediately:
   sales-demo-rr, emea-demo-group
Reversible alternative: set status: Inactive instead.
```

## Result (after apply, dry_run=false)

```
## Applied — "Demo Call" (mt_4f2a…)

| Field | Before | After (verified via meeting-type-get) |
|-------|--------|--------------------------------------|
| inviteDescription | "Join us…" | "Join {CP.Host.FullName}…" ✅ |
| duration | 30 minutes | 45 minutes ✅ |

Audit trail:
1. meeting-type-get mt_4f2a… (pre-read)
2. meeting-type-update mt_4f2a… → 200
3. meeting-type-get mt_4f2a… (verify)
```

## Rules

- Guest-visible changes always render in their own section, first, marked 👁.
- Every write is followed by a verify re-read; the After column cites verified values, not the request payload.
- Partial failures: show exactly which steps landed and which didn't, then the recovery step (per write-operations § Non-atomic create recovery).

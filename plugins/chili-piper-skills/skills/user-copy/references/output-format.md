# User Copy — Output Format

Exact layout for the dry-run plan (always shown before any write), the confirmation
prompt, and the post-write result.

---

## Plan template (always shown before writes)

### Copy plan: `<sourceEmail>` → `<targetEmail>`

**Workspaces to add**

| Workspace | Action |
|-----------|--------|
| ... | ADD / SKIP (already member) |

**Teams to add**

| Team | Workspace | Action |
|------|-----------|--------|
| ... | | ADD / SKIP (already member) |

**Licenses to grant** *(only when `copy_licenses=true`)*

| License | Source | Target | Action |
|---------|--------|--------|--------|
| ... | ✓ / ✗ | ✓ / ✗ | GRANT / SKIP (already has) |

> ⚠️ Granting licenses consumes paid seats. This is additive only — the target keeps everything it already has; nothing is revoked.

**Not copied (manual setup required):**
- Admin role (`isSuperAdmin`) — set manually if the target should be a super admin
- Meeting types — configure individually in each workspace
- Routing rule assignments — update router distributions manually
- Scheduling link settings — create new links for this user

---

## Dry-run stop / confirmation prompt

If `dry_run=true`: stop after the plan. Ask:

*"Does this plan look right? Re-run with `dry_run=false` to apply the changes."*

This is the human decision point — no write happens until the human confirms by re-running
with `dry_run=false`.

---

## Result template (only when dry_run=false)

### Result: `<targetEmail>` added to `N` workspaces and `N` teams (and granted `N` licenses)

| Added to | Type | Confirmed |
|----------|------|-----------|
| ... | Workspace / Team / License | ✓ / ⚠ |

Report any writes that did not reflect in the confirmation fetch.

**Human decision point**

*"User copy complete. Manual follow-up required: add the user to any distribution (round-robin) queues in the router builder, and create their personal scheduling links. Want me to run `/user-details` to confirm the new user's full configuration?"*

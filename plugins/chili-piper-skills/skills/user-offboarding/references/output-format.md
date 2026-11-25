# User Offboarding — Output Format

The exact layout for the offboarding plan (the dry-run diff shown before any write) and
the completion audit trail (shown after writes). Render these verbatim — the plan is the
glass-box artifact a human approves before any destructive action.

---

## Offboarding plan (always shown before writes)

This is the dry-run diff. It MUST be produced and shown before any mutation.

### Offboarding Plan: `<name>` (`<email>`)

**Open meetings (`N` upcoming)**

| Date | Guest | Meeting type | Action |
|------|-------|-------------|--------|
| ... | | | Reassign to `<reassign_to>` / ⚠ Flag for manual reassignment |

**Workspace removals**

| Workspace | Action |
|-----------|--------|
| ... | REMOVE |

**Team removals**

| Team | Workspace | Action |
|------|-----------|--------|
| ... | | REMOVE |

**Distribution memberships (manual action required)**

> These distributions must be updated manually in the Chili Piper router builder — MCP
> cannot modify distribution membership directly:

| Distribution | Workspace | Action needed |
|-------------|-----------|---------------|
| ... | | Remove from distribution queue |

**Not handled by this skill (manual):**
- Ownership of existing Salesforce leads/contacts — re-assign in Salesforce
- Personal scheduling links — deactivate or transfer in Chili Piper admin
- Meeting types — archive if not needed by other reps
- Router rule ownership conditions — audit routers that reference this user explicitly

---

## Dry-run stop prompt

If `dry_run=true`: stop here and ask:

*"Does this plan look right? Set `dry_run=false` to apply. Reminder: distribution queue
removal and scheduling link deactivation require manual steps in the Chili Piper UI."*

---

## Completion audit trail (shown after writes)

### Offboarding Complete: `<name>`

| Action | Count | Status |
|--------|-------|--------|
| Open meetings cancelled/flagged | N | ✓ / ⚠ |
| Workspaces removed | N | ✓ |
| Teams removed | N | ✓ |
| Distributions requiring manual removal | N | ⚠ Manual |

**Human decision point**

*"Manual steps still required: distribution queue removal and scheduling link deactivation
in the CP admin UI. Should I run `/routing-audit` to check whether the rep's absence
creates any routing gaps?"*

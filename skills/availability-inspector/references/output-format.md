# Availability Inspector — Output Format

Exact result layout for the final step of the availability-inspector skill. Fill in all
fields; use "—" for unavailable data.

---

## Template

### Availability Inspector: `<user name>` (`<email>`)

**User profile**

| Check | Status |
|-------|--------|
| Scheduling license | Active (chiliCalOrg / concierge / handoff) / ⚠ None |
| Calendar status | Not readable from user-read — confirm with rep or admin |

**Availability query result**

| Field | Value |
|-------|-------|
| Window checked | `<today>` to `<today + N days>` |
| Slots found | N |
| Earliest slot | |

**Availability per day**

> Include this whenever slots are returned. One row per day in the window (including 0-slot
> days). Mark days truncated by the query window boundary as *partial*.

| Date | Day | Slots |
|------|-----|-------|
| `<YYYY-MM-DD>` | Mon | N *(partial — window started midday)* |
| ... | | |
| `<YYYY-MM-DD>` | Sat | 0 |
| **Total** | | **N** |

**Diagnosis**

> [One-paragraph explanation of the specific blocker, based on user profile and the
> common-causes checklist. Note: the API no longer returns per-user failure codes — verify
> the exact cause in Chili Piper admin.]

**Fix**

> **Step 1:** [Specific action for the user or admin]
> **Step 2:** [If multiple steps]
> **Verify:** Re-run `/availability-inspector` after the fix to confirm slots appear.

**Human decision point**

*"Should I check the rest of the team, or does this fix cover the routing issue you're
seeing?"*

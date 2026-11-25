# Org Meeting Snapshot — Output Format

Exact template for the output step of the org-meeting skill. Fill in all values; use "—" for unavailable data.

---

## Template

### Org Meeting Snapshot | `<date range>` | Grouped by `<dimension>`

**Org Summary**

| Metric | Value |
|--------|-------|
| Total meetings (completed + no-show) | |
| Completed | |
| No-shows | |
| Org no-show rate | |
| Cancelled (excl. from rate) | |
| Upcoming (Scheduled) | |

**Breakdown**

| `<Dimension>` | Meetings | No-shows | Rate | Flag |
|---------------|---------|----------|------|------|
| ... | | | | ⚠ / ✓ |

**Flags**

For each flagged group:
> `<Workspace/Rep>` — `N%` no-show rate vs `N%` org average. Run `/analyze-no-shows workspace="<name>"` or `/user-meetings user="<email>"` for root-cause analysis.

**Human decision point**

*"Should I send this to the summary view, or drill into any of the flagged groups?"*

---

## Caveat line

Surface a caveat when past-Active is a significant share of total:

> *"N meetings were not formally closed (Active status, past start time) — included in denominator as informally completed."*

---

## Suggested follow-up skills

- `/analyze-no-shows` — drill into a flagged workspace with root-cause hypotheses
- `/user-meetings` — inspect a specific rep's meeting health
- `/inspect-meeting` — investigate a single anomalous meeting

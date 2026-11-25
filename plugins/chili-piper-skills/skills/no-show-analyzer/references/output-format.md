# No-Show Analyzer — Output Format

The exact report layout. Render in this order.

---

## Template

### No-Show Analysis: [Date Range] | [Workspace or Org-wide] | Grouped by [Dimension]

**Summary**

| Metric | Value |
|--------|-------|
| Total meetings analyzed | N |
| No-shows | N |
| Org no-show rate | N% |
| Flagged segments (>[threshold]%) | N |

**Breakdown**

| [Dimension] | Meetings | No-shows | Rate | Flag |
|-------------|---------|----------|------|------|
| ... | | | | ⚠ / ✓ |

**Flagged segments + hypotheses**

[One section per flagged segment — see `references/analysis-methodology.md` § Root-cause hypotheses for flagged segments for the per-hypothesis shape]

**Recommended actions**

[2-4 actions — see `references/analysis-methodology.md` § Recommended actions]

**Human decision point**

Ask: *"Which action do you want to test? I can help you document the baseline and set a 30-day review reminder."*

---

## Caveats to surface in the output

- When the past-Active count is significant, include the informally-completed caveat from `references/analysis-methodology.md` § No-show rate formula.
- When a group has fewer than 10 meetings, note low sample size next to the rate rather than flagging it.

# User Meetings — Output Format

The exact result layout, the classification rules and metric formulas that feed it, and
the anomaly thresholds.

---

## Classify meetings

Use the `Status` column. Split `Active` on the `When` time vs. now:

| Status | When | Classification |
|--------|------|----------------|
| `Completed` | any | Completed — include in rate |
| `NoShow` | any | No-Show — include in rate (numerator) |
| `Canceled` | any | Cancelled — exclude from rate |
| `Active` | future | Upcoming — exclude from rate |
| `Active` | past | Informally Completed — include in denominator only |

Surface a caveat when past-Active count is significant: *"N past meetings show as Active
(not formally closed). No-show rate treats these as completed; actual no-shows may be
undercounted."*

---

## Calculate metrics

**No-show rate:** `NoShow / (Completed + NoShow + past-Active)`

**Completion rate:** `(Completed + past-Active) / (Completed + NoShow + past-Active)`

---

## Detect anomalies

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| High no-show rate | > 30% (with ≥ 10 meetings) | High |
| Very high no-show rate | > 50% | High |
| Low volume | < 5 meetings in period | Medium — may be routing gap |
| Zero meetings | 0 meetings | High — check router membership |
| Many cancellations | Cancelled > 50% of total | Medium |

---

## Output template

### Meetings for `<name>` (`<email>`) | `<date range>` | Timezone: `<tz>`

**Summary**

| Metric | Value |
|--------|-------|
| Total meetings (completed + no-show) | |
| Completed | |
| No-shows | |
| No-show rate | |
| Past Active (informally completed) | |
| Cancelled (excluded from rate) | |
| Upcoming | |

**Anomalies**

| Flag | Severity | Note |
|------|----------|------|
| ... | | |

*(or: "No anomalies detected.")*

**Meeting list** (most recent first, sorted by `When`)

| Scheduled (`When`) | Booked (`Booked At`) | Status | Primary Guest | Workspace |
|--------------------|----------------------|--------|--------------|----------|
| ... | | | | |

> All times in `<tz>`. The **Booked** column comes from the `Booked At` CSV column (added
> in DISTRO-4483); lead time = `When` − `Booked At`.

**Human decision point**

*"Does this look like a coaching opportunity, a routing adjustment, or is the rep
performing as expected? I can pull their routing assignments or compare them to the team
average."*

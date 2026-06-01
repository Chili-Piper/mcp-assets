# Distribution Analysis — Output Format

Lead with config + rep breakdown so the "who's getting more/fewer meetings" answer is visible immediately, then patterns, then recommendations.

```
## Distribution Analysis — <Distribution Name>
**Workspace:** <workspace name>  ·  **Period:** <start> – <end>
**Handling:** <Strict|Flexible>  ·  **Active members:** <N>

> Note: meetings are attributed by host rep. <Rep X> also belongs to other
> distributions, so their counts here include meetings routed elsewhere.
> (Include this line only when a member is in multiple distributions.)

---

### Rep Breakdown

| Rep | Weight | Total | Completed | Cancelled | No-show | Cancel % |
|-----|-------:|------:|----------:|----------:|--------:|---------:|
| Alice Smith | 2 | 28 | 22 | 6 | 0 | 21.4% |
| Bob Jones   | 1 | 14 | 12 | 2 | 1 | 14.3% |
| ...         |   |    |    |   |   |        |

**Imbalance ratio:** 2.0× (top rep vs. median)
**Vs. weights:** Alice has 50% of meetings on a 67% weight share (slightly under); Bob is on target.

---

### Patterns Found

**Booking source:** <e.g. Alice's meetings are mostly from scheduling links; Bob's from concierge routing — read actual scheduleOrigin/meetingSource values>

**Day-of-week:** <e.g. Alice dominates Monday mornings; Bob skews to Fridays>

**Weekly trend:** <e.g. the gap widened the week of May 12>

**Cancellations:** <e.g. Alice's cancels are mostly guest-initiated; Bob's are calendar-sync driven — based on history[] actorRef/origin>

---

### Recommendations

| Finding | Likely cause | What to check / do |
|---------|-------------|--------------------|
| One rep gets ~2× the meetings | Weight skew | Compare `published.weights`; rebalance in the router builder |
| A member has 0 meetings | Calendar/availability blocker | Run `/check-availability` for that rep |
| Gap opened on a specific date | A config or availability change | Check the router builder change log; confirm working hours |
| High calendar-driven cancels for one rep | Calendar sync issue | Check that rep's calendar integration |
| Share far from configured weight | Capping, availability, or source mix | Review `capping` and booking-source skew above |

**Human decision point**

*"Want me to outline the weight changes to rebalance this distribution? Applying them requires the router builder, or `distribution-adjust-v3` with your explicit go-ahead since it publishes immediately."*
```

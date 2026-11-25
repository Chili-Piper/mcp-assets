# No-Show Analyzer — Analysis Methodology

How to classify records, compute the no-show rate, build the breakdown, and form root-cause hypotheses. Field names and status values live in `references/api-reference.md`.

---

## Classify each merged meeting record

After merging and deduplicating on `meetingId`, classify each record by `meetingStatus` and start time:

- `Completed` -> completed
- `NoShow` -> no-show
- `Canceled` -> excluded (shouldn't appear given the filter, but discard if present)
- `Active` + start in future -> upcoming, exclude
- `Active` + start in past -> informally completed, include in denominator only

Build a map of `meetingId -> effective-status` for the join. (Key the map on `item.meetingId`.)

---

## No-show rate formula

```
no_show_rate = NoShow / (Completed + NoShow + past-Active)
```

`Canceled` and future-`Active` meetings are excluded from the denominator. Surface a caveat when the past-Active count is significant:

> "N meetings were not formally closed (status Active, start in past) - included in denominator as informally completed. Actual no-shows within this group may be undercounted."

---

## Build the breakdown by dimension

Group by the selected dimension:

- **`group_by=trigger`** - group by the `trigger` field from concierge-logs
- **`group_by=route`** - group by `matchedPath` from concierge-logs
- **`group_by=rep`** - group by `hostId` from meeting-list-put (`hostName`/`hostEmail` are already present for display)
- **`group_by=workspace`** - group by workspace (requires per-workspace calls or export)

For each group calculate:

- Total meetings (Completed + NoShow + past-Active — the same denominator as the no-show rate formula above)
- No-show count
- No-show rate (%)

Sort highest no-show rate first. Flag any group where `no_show_rate >= flag_threshold`.

If a group has fewer than 10 meetings, note low sample size next to the rate - don't flag purely on low-volume segments.

---

## Root-cause hypotheses for flagged segments

For each flagged segment, produce 1-3 hypotheses. Use what you know about GTM + CP.

**By trigger type:**

- `ThirdPartyForm` - high no-show often means no SMS confirmation or booking window is too long (> 3-4 days)
- `Direct` - lower intent signal; prospect clicked a link but may not remember context by meeting day
- `Email` - usually lowest no-show of the trigger types; if high, check whether links are hitting spam filters or the wrong audience
- `RouterLink` - similar to Direct; check lead time and whether a reminder sequence is configured
- `InApp` - typically high-intent; if high no-show, check if the in-app trigger fires at a low-intent moment in the product flow

**By route (`matchedPath.route.type`):**

- `RuleRoute` with high no-show - a specific rule matched; check whether the assigned rep is right (e.g. stale Salesforce ownership pointing leads at the wrong rep) and whether distribution is balanced
- `CatchAllRoute` with high no-show - leads that hit the catch-all had no specific rule match; lower intent and lower rep accountability. If catch-all volume is high, run `/audit-routing` to find the coverage gap

**By rep:**

- Individual reps with >40% no-show - check if they have calendar hygiene issues, or are being assigned leads outside their territory
- Clusters of reps with high no-show - likely a team-level issue (process, ICP, territory)

Format each hypothesis as:

```
Hypothesis: [cause]
Check: [what to verify in CP or Salesforce]
Fix: [specific change to make]
```

---

## Recommended actions

Give 2-4 specific, testable actions ranked by expected impact:

```
Action [n] — [title]
Change: [exact setting/config change in Chili Piper]
Expected effect: [what moves and by how much]
Measure: [the signal to watch after 30 days]
Owner: RevOps / Demand Gen / Rep manager
```

---

## Measurement loop

This skill reads data - it does not write anything. After the human selects an action:

1. The human makes the change in Chili Piper
2. Document baseline: current no-show rate for the flagged segment
3. Re-run `/no-show-analyzer` in 30 days with same parameters
4. Compare new rate to baseline

This is the optimization loop.

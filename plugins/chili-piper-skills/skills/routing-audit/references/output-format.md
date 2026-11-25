# Routing Audit — Output Format

The exact layout for the audit report. Lead with the router summary, then gaps sorted by
severity, then prioritized recommendations, then the human decision point.

---

## Report layout

### Routing Audit | `<Workspace(s)>` | Last `<N>` days

**Router summary**

| Router | Rules | Catch-all outcome | Leads (N days) | Catch-all rate |
|--------|-------|-------------------|----------------|----------------|
| ... | | Schedule: team/distribution / User / ⚠ MISSING \| Redirect: `<url>` | | |

**Gaps found** (sorted by severity)

**[CRITICAL]** Missing catch-all or no valid outcome
> Router `<name>` has no catch-all, or its catch-all has no valid `outcome`. Leads matching no rule are dropped with no fallback.
> Fix: set the catch-all to a `Schedule` outcome (assign via a distribution or user + book a meeting type) or a `Redirect` outcome (send leads to a URL fallback).

**[INFO]** Catch-all redirects to URL (no booking)
> Router `<name>`'s catch-all uses a `Redirect` outcome: leads falling through all rules are sent to `<url>` rather than being booked.
> Confirm this is intentional. If these leads should be bookable, update the catch-all to a `Schedule` outcome.

**[HIGH]** High catch-all rate
> Router `<name>`: `N%` of leads hit the catch-all. Top unmatched profiles: `<field values>`.
> Fix: add a rule covering `<top unmatched profiles>`.

**[MEDIUM]** Empty distribution
> Distribution `<name>` in workspace `<name>` has 0 active members.
> Fix: add at least one rep with a non-zero weight.

**[MEDIUM]** Single-member distribution
> Distribution `<name>` has only 1 active member. If they're unavailable, the route stops working.
> Fix: add a backup rep or configure a fallback distribution.

**[LOW]** Potentially stale ownership rule
> Rule `<name>` (`OwnershipRule`) in router `<name>` had 0 matches in the last `N` days.
> Check: is this rule still needed? Is ownership data in Salesforce up to date?

**[LOW]** Assignment imbalance vs. configured weight
> Distribution `<name>`: rep `<name>` received `N%` of assignments but their weight share is `N%` (ideal: `N` assignments). Check capping config, recent calendar outages, or reassignment churn.

**Recommendations** (prioritized)

1. Fix critical gaps (catch-all missing or no valid outcome) — these drop leads silently
2. Investigate high catch-all rates — add rules for top unmatched profiles
3. Fill empty distributions — any distribution with 0 active members is currently routing nothing
4. Review single-member distributions before the next vacation or departure
5. Investigate assignment imbalance — if actual share deviates > 2× from weight share, check capping, availability, or reassignment activity

**Human decision point**

*"Which gap do you want to fix first? I can help draft the rule conditions or pull the lead profile data to understand what's hitting the catch-all."*

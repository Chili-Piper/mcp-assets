# Routing Audit — Output Format

The exact layout for the audit report. Lead with the router summary, then gaps sorted by
severity, then prioritized recommendations, then the human decision point.

---

## Report layout

### Routing Audit | `<Workspace(s)>` | Last `<N>` days

**Router summary**

| Router | Rules | Catch-all routes to | Leads (N days) | Catch-all rate |
|--------|-------|---------------------|----------------|----------------|
| ... | | team/distribution / ⚠ NO ONE | | |

**Gaps found** (sorted by severity)

**[CRITICAL]** Catch-all routes to no one
> Router `<name>`'s catch-all does not route to any team/distribution. Leads matching no rule are dropped with no fallback.
> Fix: point the catch-all at a fallback distribution in the router builder.

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

1. Fix critical gaps (catch-all routing to no one) — these drop leads silently
2. Investigate high catch-all rates — add rules for top unmatched profiles
3. Fill empty distributions — any distribution with 0 active members is currently routing nothing
4. Review single-member distributions before the next vacation or departure
5. Investigate assignment imbalance — if actual share deviates > 2× from weight share, check capping, availability, or reassignment activity

**Human decision point**

*"Which gap do you want to fix first? I can help draft the rule conditions or pull the lead profile data to understand what's hitting the catch-all."*

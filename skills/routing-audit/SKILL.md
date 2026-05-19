---
name: routing-audit
description: Audits all Chili Piper concierge routers for coverage gaps — unmapped lead sources, stale ownership rules, unbalanced distributions, and catch-all overflows — before they show up as lost pipeline
version: 0.1.0
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID to audit. Omit for org-wide audit of all workspaces."
    required: false
  - name: log_days
    type: number
    description: "Number of days of concierge logs to analyze for catch-all overflow and no-match rates (max 30)."
    required: false
    default: 7
outputs:
  - name: router_summary
    description: All routers found with rule count, catch-all type, and recent no-match rate
  - name: gaps
    description: Specific routing gaps detected — stale rules, unbalanced distributions, high catch-all rates
  - name: recommendations
    description: Prioritized list of fixes with expected impact
tools_required: [chili-piper-mcp]
human_decision_point: "Review gaps and decide which to fix first — routing gaps silently leak pipeline, so prioritize by volume before severity"
writes_to: "Nothing — read-only diagnostic. Use the Chili Piper router builder to apply fixes."
api_note: "concierge-logs requires a routerId and has a hard 30-day maximum window. Rule details come from rule-list per router. Distribution membership comes from distribution-list-put per workspace."
---

# Routing Audit

You are a RevOps systems auditor. Your job is to systematically inspect all Chili Piper concierge routers, identify coverage gaps and balance issues, and give the human a prioritized fix list before silent pipeline leaks show up in the numbers.

## API reference

| Tool | What it returns |
|------|----------------|
| `workspace-list` | All workspaces → `workspaceId`, `name` |
| `concierge-list-routers` | Routers in a workspace → array `routers[N]` where `routers[N].router.id` (routerId), `routers[N].router.name`, `routers[N].router.slug`, `routers[N].workspaceId` |
| `rule-list` | All rules for a router → `id`, `name`, `type`, `conditions`, `revision` |
| `concierge-logs` | Routing decisions → `status`, `matchedPath`, `guestEmail`, `triggeredAt` |
| `distribution-list-put` | Distributions in a workspace → `{results: [{distributionId, name, teamId, assignees, assignmentTypeConfig, capping}]}` (items use `distributionId` not `id`; assignees contain weights/calibration) |

---

## Step 1 — Resolve workspace(s)

If `workspace` specified: resolve name to ID via `workspace-list`.
If no workspace: fetch all workspaces and audit each.

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Workspace items use `workspaceId` (not `id`) — use this field when passing workspace IDs to subsequent calls.

---

## Step 2 — List all routers

For each workspace (using its `workspaceId` field):

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.workspaceId>
```

Response shape: `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`.
For each router store: `routers[N].router.id` (routerId), `routers[N].router.name`, `routers[N].router.slug`, `routers[N].workspaceId`.

---

## Step 3 — Inspect rules per router

For each router:

```
tool: rule-list
args:
  routerId: <routers[N].router.id>
```

Inspect each rule:
- **Type:** `CrmOwnership` / `WithoutOwnership` / `CatchAll`
- **Conditions:** What fields/values trigger this rule?
- **Missing catch-all:** every router MUST have a CatchAll as the last rule. Flag any router without one as a critical gap.

Detect potentially stale rules:
- Ownership rules that reference users not recently seen in logs (proxy: check distribution membership)
- Rules with no matching logs in the analysis window (possible dead code)

---

## Step 4 — Analyze logs for catch-all overflow

For each router:

```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601, log_days ago>
  end: <ISO-8601, now>
```

Calculate:
- **Total leads processed:** count of all log entries
- **No-match rate:** entries where `status = NoMatch` or `matchedPath = null`
- **Catch-all rate:** entries where matched rule is the catch-all (matchedPath = last rule)

**Flag thresholds:**
- Catch-all rate > 20%: routing rules may not cover important lead profiles
- No-match rate > 5%: leads are falling through entirely (no catch-all or router error)

---

## Step 5 — Check distribution balance

For each workspace:

```
tool: distribution-list-put
args:
  workspaceId: <workspace id>
```

For each distribution inspect:
- **Member count:** distributions with 0 members will route no leads
- **Members with 0 weight:** effectively excluded from routing
- **Algorithm:** Strict / Flexible / Weighted / Working Hours

Flag:
- Any distribution with 0 or 1 active member (no redundancy — single rep absence blocks the route)
- Weighted distributions where one rep has > 5× the weight of others (may be intentional, but worth flagging)

---

## Step 6 — Output format

### Routing Audit | `<Workspace(s)>` | Last `<N>` days

**Router summary**

| Router | Rules | Has catch-all | Leads (N days) | Catch-all rate | No-match rate |
|--------|-------|--------------|----------------|---------------|--------------|
| ... | | ✓ / ⚠ MISSING | | | |

**Gaps found** (sorted by severity)

**[CRITICAL]** Missing catch-all
> Router `<name>` has no catch-all rule. Leads that match no rules are dropped with no fallback.
> Fix: add a catch-all in the router builder as the last rule.

**[HIGH]** High catch-all rate
> Router `<name>`: `N%` of leads hit the catch-all. Top unmatched profiles: `<field values>`.
> Fix: add a rule covering `<top unmatched profiles>`.

**[MEDIUM]** Empty distribution
> Distribution `<name>` in workspace `<name>` has 0 active members.
> Fix: add at least one rep with a non-zero weight.

**[MEDIUM]** Single-member distribution
> Distribution `<name>` has only 1 member. If they're unavailable, the route stops working.
> Fix: add a backup rep or configure a fallback distribution.

**[LOW]** Potentially stale ownership rule
> Rule `<name>` in router `<name>` references ownership but had 0 matches in the last `N` days.
> Check: is this rule still needed? Is ownership data in Salesforce up to date?

**Recommendations** (prioritized)

1. Fix critical gaps (missing catch-all) — these drop leads silently
2. Investigate high catch-all rates — add rules for top unmatched profiles
3. Fill empty distributions — any distribution with 0 members is currently routing nothing
4. Review single-member distributions before the next vacation or departure

**Human decision point**

*"Which gap do you want to fix first? I can help draft the rule conditions or pull the lead profile data to understand what's hitting the catch-all."*

---

## Data handling

- **PII present:** guest emails in concierge logs used for counting only, not displayed
- **Storage:** ephemeral
- **Writes:** none — read-only. All fixes applied manually in the Chili Piper router builder.

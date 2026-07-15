---
name: routing-audit
description: Audits all Chili Piper concierge routers for coverage gaps — unmapped lead sources, stale ownership rules, unbalanced distributions, and catch-all overflows — before they show up as lost pipeline
version: 0.2.3
api_note: "concierge-logs: optional page/pageSize pagination added (DISTRO-4576, max 500 per page); Step 4 and preflight updated to paginate for complete log coverage on high-volume routers. As of DISTRO-4549 (PR #898, 2026-06-18): routing.rules[] entries and routing.catchAll each carry a discriminated outcome field — Schedule{assignment: {type: Distribution, distributionId} | {type: User, userId}, meetingTypeId, timeout?: {minutes, onTimeout: Landing|{url}}, crmActions?: [...]} or Redirect{url}. Treat Redirect as a valid catch-all outcome (leads are sent to a URL, not dropped); only flag the catch-all as critical when routing.catchAll is absent or its outcome is null/missing. As of DISTRO-4623 (PR #962, 2026-07-09): concierge-list-routers now returns `inAppButton` and `routerLink` trigger fields on each router's read view (in addition to `form`); button/link are no longer present in `form.readOnlyTriggers`. Flag routers where all three trigger kinds are absent/empty as a configuration gap — no trigger means the router cannot receive inbound leads."
references:
  - api-reference
  - audit-procedure
  - output-format
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
---

# Routing Audit

You are a RevOps systems auditor. Systematically inspect all Chili Piper concierge routers, identify coverage gaps and balance issues, and give the human a prioritized fix list before silent pipeline leaks show up in the numbers.

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill (`concierge-logs` requires a routerId + has a 30-day max window;
> per-router rules + catch-all come from the router object, not `rule-list`; etc.).

## When to use

- Someone wants a health check across all concierge routers before pipeline leaks surface.
- Someone suspects leads are falling through to the catch-all or being dropped.
- Someone wants to find stale ownership rules or unbalanced distributions.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | — | all workspaces | Workspace name or ID to audit. Omit for an org-wide audit. |
| `log_days` | — | `7` | Days of `concierge-logs` to analyze for catch-all overflow and no-match rates (max 30). |

If a required input is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Resolve workspace(s)

If `workspace` is specified, resolve its name to ID via `workspace-list`. If not, fetch
all workspaces and audit each.

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Workspace items use `id` (NOT `workspaceId`) — use `workspace.id` when passing workspace
IDs to subsequent calls. Field-name gotchas → `references/api-reference.md`
§ Critical field name differences.

### Step 2 — List all routers

For each workspace (using its `id`):

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.id>
```

For each router store `routers[N].router.id` (routerId), `.name`, `.slug`,
`routers[N].workspaceId`, and the routing config at `routers[N].router.routing`. Response
shape → `references/api-reference.md` § concierge-list-routers — router object shape.

### Step 3 — Inspect rules per router

The ordered rules (`router.routing.rules[]`) and the catch-all (`router.routing.catchAll`,
a separate object) are already on each router from Step 2. For richer rule detail across a
workspace, call `rule-list`. Confirm each catch-all has a valid `outcome` (`Schedule` or
`Redirect` — flag as critical only when the catch-all is absent or has no outcome; surface
a `Redirect` catch-all as informational) and detect potentially stale rules. Full procedure
→ `references/audit-procedure.md`
§ Inspecting rules per router and § Detecting stale rules.

Also check trigger configuration: if `form`, `inAppButton`, and `routerLink` are all absent
or empty on a router, flag it as a **[HIGH]** configuration gap — no trigger means the
router cannot receive inbound leads. (`inAppButton` and `routerLink` are top-level fields
on the router object as of DISTRO-4623; they are no longer reported inside
`form.readOnlyTriggers`.)

### Step 4 — Analyze logs for catch-all overflow

For each router, pull `concierge-logs` over the `log_days` window and compute total leads,
catch-all rate (`matchedPath.route.type == "CatchAllRoute"`), and rule-match rate
(`RuleRoute`). The tool returns at most 500 logs per page; paginate by incrementing `page`
from 0 until the response array is empty or shorter than `pageSize` to capture all activity
on high-volume routers. Full procedure + flag thresholds → `references/audit-procedure.md`
§ Analyzing logs for catch-all overflow. The 30-day limit + required `routerId` →
`references/api-reference.md` § Hard API limits.

### Step 5 — Check distribution balance

For each workspace, pull `distribution-list-put` (a top-level array) and inspect active
members, weights, handling, and assignment `statistics`. Full procedure + flag thresholds
→ `references/audit-procedure.md` § Checking distribution balance.

### Step 6 — Output

Lead with the router summary, then gaps sorted by severity, then prioritized
recommendations. Exact layout → `references/output-format.md` § Report layout.

## Preflight audit

Verify before writing output:

- [ ] Required inputs resolved (`workspace` → `id`, or all workspaces fetched).
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] `concierge-logs` calls each pass `workspaceId` + `routerId`, span ≤ 30 days, and are paginated until the response is empty or shorter than `pageSize`.
- [ ] `log_days` respected (default 7, capped at 30).
- [ ] Each catch-all checked for a valid `outcome` — `Schedule` or `Redirect` (critical only when absent/no outcome; `Redirect` surfaced as informational).
- [ ] Each router checked for at least one active trigger (`form`, `inAppButton`, or `routerLink`); absence of all three flagged as [HIGH].
- [ ] Distribution imbalance derived from `statistics.assigned` vs. configured weights.

## Checkpoint

This is a read-only diagnostic. Present the router summary, gaps (sorted by severity), and
prioritized recommendations, then stop and let the human decide which gap to fix first —
routing gaps silently leak pipeline, so prioritize by volume before severity. All fixes
are applied manually in the Chili Piper router builder.

## Data handling

- **PII present:** guest emails in concierge logs — used for counting only, not displayed
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only. All fixes applied manually in the Chili Piper router builder.

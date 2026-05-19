---
name: no-show-analyzer
description: Analyzes Chili Piper meeting no-show patterns by trigger type, routing path, rep, or workspace using meeting-list-put and concierge-logs to surface actionable optimization opportunities
version: 0.3.0
inputs:
  - name: date_range
    type: string
    description: "Period to analyze: 'last-7-days', 'last-30-days', or 'YYYY-MM-DD:YYYY-MM-DD'. For trigger/route breakdown, concierge-logs caps at 30 days. Meeting data can go further but loses routing context."
    required: false
    default: "last-30-days"
  - name: workspace
    type: string
    description: "Workspace name or ID to scope the analysis. Omit for org-wide."
    required: false
  - name: group_by
    type: string
    description: "Primary dimension: 'trigger' (lead source type) | 'route' (matched routing path) | 'rep' (assignee) | 'workspace'"
    required: false
    default: "trigger"
  - name: flag_threshold
    type: number
    description: "No-show rate (%) above which a segment is flagged. Default: 30."
    required: false
    default: 30
outputs:
  - name: summary
    description: Overall no-show rate and meeting volume for the period
  - name: breakdown
    description: No-show rate by the selected dimension, sorted highest to lowest
  - name: flagged_segments
    description: Segments above the threshold with root-cause hypotheses
  - name: recommended_actions
    description: Specific routing or confirmation flow changes to test
tools_required: [chili-piper-mcp]
human_decision_point: "Review flagged segments and decide which routing rule or confirmation flow change to test first"
writes_to: "Salesforce task (optional) — created by human after reviewing recommendations"
api_note: "meeting-list-put has a strict 7-day maximum window per call — the skill chunks longer ranges automatically. concierge-logs has a separate 30-day maximum window and requires a routerId. Only log entries with status=Booked have a meetingId to join against meeting-list-put; Offered/NoMatch/NotQualified/Timeout/Error entries never became meetings and must be excluded from the join. meeting-list-put response envelope is {data: {list: [...]}, hasMore: 'Yes'|'No'}; meeting items use 'meetingId' (not 'id'); paginate by checking hasMore === 'Yes' (string, not boolean). concierge-list-routers nests routerId at routers[N].router.id, workspaceId at routers[N].workspaceId, name at routers[N].router.name."
---

# No-Show Analyzer

You are a GTM data analyst with deep knowledge of Chili Piper's meeting and routing model. Your job is to pull meeting data and routing context for a given period, calculate no-show rates, flag problem segments, and surface specific actions for the human to test.

## API reference (actual MCP tool names)

| Tool | Method | What it returns |
|------|--------|----------------|
| `meeting-list-put` | POST | Paginated meetings by time range — response envelope `{data: {list: [...]}, hasMore: "Yes"\|"No"}`. Items in `data.list[]`: `meetingId`, `status`, `scheduledAt`, `assignedUserId`, `workspaceId`, `attendees` (array). Paginate by checking `hasMore === "Yes"` (string). |
| `concierge-list-routers` | GET | All routers — response: `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. Access: `routerId` at `routers[N].router.id`, `name` at `routers[N].router.name`, `workspaceId` at `routers[N].workspaceId`. |
| `concierge-logs` | POST | Routing decisions per router — `status`, `trigger`, `guestEmail`, `triggeredAt`, `matchedPath`, `assignments`, `meetingId`, `sourceUrl` |
| `workspace-list` | GET | All workspaces — `id`, `name`, `userCount` |

**Key constraint — two separate windows:**
- `meeting-list-put` has a **7-day maximum window per call**. For ranges longer than 7 days, you must make multiple sequential calls and merge the results.
- `concierge-logs` requires a `routerId` and has a **30-day maximum window**. For grouping by `trigger` or `route`, loop over routers and call once per router, then join on `meetingId`.

**Status values in meeting-list-put:**
| Status | Include in no-show rate? |
|--------|------------------------|
| `Completed` | ✓ Yes — denominator and numerator |
| `NoShow` | ✓ Yes — numerator only |
| `Cancelled` | ✗ No — exclude entirely |
| `Scheduled` | ✗ No — not yet occurred |

**Status values in concierge-logs (critical for the join):**
| Status | Has `meetingId`? | Meaning |
|--------|----------------|---------|
| `Booked` | ✓ Yes | Lead completed booking — this `meetingId` joins to meeting-list-put |
| `Offered` | ✗ No | Calendar was shown but lead did not book |
| `NoMatch` | ✗ No | No routing rule matched the lead |
| `NotQualified` | ✗ No | Lead was disqualified (spam, ICP filter, explicit disqualify rule) |
| `Timeout` | ✗ No | Session expired before the lead booked |
| `Error` | ✗ No | Technical routing error |

Only `Booked` log entries have a `meetingId` to join with meeting-list-put. All others represent leads that never became meetings — they are a separate "booking conversion" funnel and must be excluded from no-show calculations.

**Trigger types in concierge-logs:**
| Value | What it means |
|-------|--------------|
| `ThirdPartyForm` | Web form submission (Marketo, HubSpot, Pardot, HTML form) |
| `Direct` | Prospect visited the router URL directly |
| `Email` | Scheduling link embedded in an email |
| `RouterLink` | Router link shared via a direct URL |
| `InApp` | In-product trigger (SaaS product-embedded booking) |

**No-show rate formula:**
```
no_show_rate = NoShow / (Completed + NoShow)
```
Scheduled and Cancelled meetings are excluded from the denominator.

---

## Step 1 — Resolve inputs and validate

Parse the user's request for `date_range`, `workspace`, `group_by`, and `flag_threshold`.

**Date range constraint check:** If the requested range exceeds 30 days AND `group_by` is `trigger` or `route`, warn the user:
> "concierge-logs has a 30-day maximum window. I'll analyze the most recent 30 days for trigger/route breakdown. For longer periods, use `group_by=rep` instead."

If `workspace` is provided as a name (not ID), call `workspace-list` first to resolve it to an ID.

---

## Step 2 — Fetch meeting data

`meeting-list-put` accepts at most a **7-day window per call**. Split the requested date range into 7-day (or shorter) chunks and issue one call per chunk.

For each chunk:

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  pagination:
    page: 0
    pageSize: 200
```

Results are in `response.data.list[]`. Paginate each chunk if needed — continue incrementing `pagination.page` while `response.hasMore === "Yes"` (string comparison, not boolean). Merge all results into a single list and deduplicate on `meetingId`.

Filter the merged list:
- **Include:** status `Completed` or `NoShow`
- **Exclude:** status `Scheduled`, `Cancelled`

If `workspace` was specified, note that `meeting-list-put` does not support workspace filtering. Use `meeting-export-v2-put` with `workspaceId` instead (returns CSV — parse accordingly).

Build a map of `meetingId → status` for the join in Step 3. (The field name in each meeting-list-put item is `meetingId`, so key the map on `item.meetingId`.)

---

## Step 3 — Fetch routing context (only for `trigger` or `route` grouping)

Skip this step if `group_by=rep` — rep is available directly from `meeting-list-put` via the `assignedUserId` field (resolve to name/email via `user-find-by-ids` if needed).

**3a. List all routers:**
```
tool: concierge-list-routers
args:
  workspaceId: <resolved workspace ID, or omit for all>
```

The response is `{routers: [{router: {id, name, slug, ...}, dataFields: [...], workspaceId}]}`. When iterating routers use `routers[N].router.id` as the routerId, `routers[N].router.name` for display, and `routers[N].workspaceId` for the workspaceId.

**3b. For each router, fetch routing logs:**
```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601 start>
  end: <ISO-8601 end>
```

From the logs, **first filter to entries where `status = Booked`** — only these have a `meetingId` to join on. Then extract:
- `meetingId` — used to join with meeting status
- `trigger` — the lead source type (see trigger types table above)
- `matchedPath` — the routing rule matched (e.g. `CrmOwnership`, `WithoutOwnership`, `CatchAll`)
- `sourceUrl` — the page the lead came from (useful for inferring campaign/channel)
- `assignments[0].name` — the rep the router assigned

Join on `meetingId` to get the meeting's actual status (`Completed` or `NoShow`).

Note: concierge-logs entries with status `Offered`, `NoMatch`, `NotQualified`, `Timeout`, or `Error` never produced a meeting and will not appear in meeting-list-put. Do not attempt to join these — discard them from this analysis.

---

## Step 4 — Calculate the breakdown

Group by the selected dimension:

**`group_by=trigger`** — group by the `trigger` field from concierge-logs
**`group_by=route`** — group by `matchedPath` from concierge-logs
**`group_by=rep`** — group by `assignedUserId` from meeting-list-put (resolve to name/email via `user-find-by-ids` if display is needed)
**`group_by=workspace`** — group by workspace (requires per-workspace calls or export)

For each group calculate:
- Total meetings (Completed + NoShow)
- No-show count
- No-show rate (%)

Sort highest no-show rate first. Flag any group where `no_show_rate >= flag_threshold`.

If a group has fewer than 10 meetings, note low sample size next to the rate — don't flag purely on low-volume segments.

---

## Step 5 — Root-cause hypotheses for flagged segments

For each flagged segment, produce 1–3 hypotheses. Use what you know about GTM + CP:

**By trigger type:**
- `ThirdPartyForm` — high no-show often means no SMS confirmation or booking window is too long (> 3–4 days)
- `Direct` — lower intent signal; prospect clicked a link but may not remember context by meeting day
- `Email` — usually lowest no-show of the trigger types; if high, check whether links are hitting spam filters or the wrong audience
- `RouterLink` — similar to Direct; check lead time and whether a reminder sequence is configured
- `InApp` — typically high-intent; if high no-show, check if the in-app trigger fires at a low-intent moment in the product flow

**By matchedPath (routing rule type):**
- `CrmOwnership` with high no-show — check if the Salesforce ownership data is stale; wrong rep gets assigned, lead goes cold
- `WithoutOwnership` (territory/segment rules) with high no-show — check if round-robin distribution is balanced; overloaded reps may under-prepare
- `CatchAll` with high no-show — leads that hit the catch-all had no specific rep match; lower intent and lower rep accountability
- Any route with `matchedPath = null` — leads falling through entirely; run `/routing-audit` to find the gap

**By rep:**
- Individual reps with >40% no-show — check if they have calendar hygiene issues, or are being assigned leads outside their territory
- Clusters of reps with high no-show — likely a team-level issue (process, ICP, territory)

Format each hypothesis as:
```
Hypothesis: [cause]
Check: [what to verify in CP or Salesforce]
Fix: [specific change to make]
```

---

## Step 6 — Recommended actions

Give 2–4 specific, testable actions ranked by expected impact:

```
Action [n] — [title]
Change: [exact setting/config change in Chili Piper]
Expected effect: [what moves and by how much]
Measure: [the signal to watch after 30 days]
Owner: RevOps / Demand Gen / Rep manager
```

---

## Step 7 — Output format

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
[One section per flagged segment]

**Recommended actions**
[2–4 actions]

**Human decision point**
Ask: *"Which action do you want to test? I can help you document the baseline and set a 30-day review reminder."*

---

## Measurement

This skill reads data — it does not write anything. After the human selects an action:

1. The human makes the change in Chili Piper
2. Document baseline: current no-show rate for the flagged segment
3. Re-run `/no-show-analyzer` in 30 days with same parameters
4. Compare new rate to baseline

This is the optimization loop.

---

## Data handling

- **PII present:** guest emails and rep emails used for grouping only, not displayed in output unless explicitly requested
- **Storage:** ephemeral — no data persists after the skill completes
- **Scope:** reads only your org's data via your API key

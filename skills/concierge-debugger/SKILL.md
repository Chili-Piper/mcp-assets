---
name: concierge-debugger
description: Debugs why a specific lead did not book — traces the concierge routing session, identifies the rule that fired (or why none did), and recommends a targeted fix
version: 0.2.2
api_note: "concierge-logs: optional page/pageSize pagination added (DISTRO-4576, max 500 per page); Step 2 and preflight updated to paginate when searching for a lead in high-volume routers. As of DISTRO-4623 (PR #962, 2026-07-09): concierge-list-routers now returns `inAppButton` and `routerLink` trigger fields on each router's read view (separate from `form`; no longer present in `form.readOnlyTriggers`). Note which trigger kinds are active when diagnosing non-bookings — a missing trigger kind means leads cannot arrive via that channel (e.g., no `routerLink` means no one could have booked via the router's shareable URL)."
references:
  - api-reference
  - diagnosis
  - output-format
inputs:
  - name: guest_email
    type: string
    description: "Email address of the lead who did not book"
    required: true
  - name: router
    type: string
    description: "Router name or slug to search in. Omit to search all routers."
    required: false
  - name: date_range
    type: string
    description: "When the lead submitted: 'today', 'last-7-days', or 'YYYY-MM-DD:YYYY-MM-DD'"
    required: false
    default: "last-7-days"
outputs:
  - name: routing_session
    description: The concierge log entry for this lead — trigger, matched route, assignee, status
  - name: diagnosis
    description: Plain-language explanation of what happened and why
  - name: fix
    description: Specific change to make in the router to prevent recurrence
tools_required: [chili-piper-mcp]
human_decision_point: "Review the diagnosis and decide: fix the routing rule, rebook the lead manually, or escalate to engineering"
writes_to: "Nothing — read-only diagnostic"
---

# Concierge Debugger

You are a Chili Piper routing specialist. A lead submitted a form but did not book — your job is to find their concierge log entry, explain exactly what happened at each step, and give the human one specific thing to fix.

> **Prefer live data over training.** MCP field names and tool signatures change. Load `references/api-reference.md` before making MCP calls — it is the canonical field-name truth for this skill (the tools' own descriptions are unreliable).

## When to use

- A lead submitted a form but no meeting was booked, and you need to know why.
- You need to confirm whether a specific lead was routed at all, and to whom.
- Deciding whether a non-booking is a routing-rule problem, an availability problem, or a UX/delivery problem.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `guest_email` | ✅ | — | Email address of the lead who did not book. |
| `router` | — | all routers | Router name or slug to search in. Omit to search all routers. |
| `date_range` | — | `last-7-days` | When the lead submitted: `today`, `last-7-days`, or `YYYY-MM-DD:YYYY-MM-DD`. |

If `guest_email` is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Find the router(s) to search

If `router` is specified, call `concierge-list-routers` and find the matching router by name or slug.

If no `router` specified, fetch all routers across all workspaces:

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

```
tool: concierge-list-routers
args:
  workspaceId: <workspace.id>
```

Router ID is at `routers[N].router.id`; workspace at `routers[N].workspaceId`. Workspace items from `workspace-list` use `id`. Response shapes and identifier fields → `references/api-reference.md` § Tools and what they return.

The router object also carries `form`, `inAppButton`, and `routerLink` trigger fields. Note which are active — if a trigger kind is absent the lead could not have arrived via that channel, which may itself explain a non-booking.

### Step 2 — Search logs for the lead

For each router (or the specified router):

```
tool: concierge-logs
args:
  workspaceId: <routers[N].workspaceId>
  routerId: <routers[N].router.id>
  start: <ISO-8601 start of date_range>
  end: <ISO-8601 end of date_range>
  page: 0
  pageSize: 500
```

Paginate: increment `page` by 1 until the response array is empty or shorter than `pageSize` (max 500). Most debug windows won't exceed a single page; high-volume routers may.

Search results for entries where `guestEmail` matches `guest_email` (case-insensitive). The 30-day window and `routerId` requirement → `references/api-reference.md` § Hard API limits.

If found: store the log entry and stop searching other routers.
If not found in any router: use the "no session found" report → `references/output-format.md` § If no session found.

### Step 3 — Diagnose the outcome

Read the outcome signals (`meetingId`, `status`, `matchedPath.route.type`) → `references/api-reference.md` § Reading the outcome and § matchedPath. Then branch to the matching case (booked / CatchAllRoute / RuleRoute / TimedOut / Cancelled-or-unknown) → `references/diagnosis.md`. Resolve any `assignments[].userId` to a name with `user-find-by-ids`.

### Step 4 — Output

Exact layout → `references/output-format.md` § Template.

## Preflight audit

Verify before writing output:

- [ ] `guest_email` present.
- [ ] Field names taken from `references/api-reference.md`, not guessed.
- [ ] `concierge-logs` window ≤ 30 days, every call carried a `routerId`, and paginated until empty or short page.
- [ ] Outcome interpreted from the literal `status` + `matchedPath` (no assumed status enum).
- [ ] Any reported assignee `userId` resolved to a name via `user-find-by-ids`.

## Checkpoint

Present the routing session, diagnosis, root cause, and fix, then stop for the human:

*"Should I make the fix in the router, or would you like to manually rebook this lead first?"*

The human decides: fix the routing rule, rebook the lead manually, or escalate to engineering.

## Data handling

- **PII present:** guest email used for lookup and display
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only diagnostic

---
name: chat-conversation-inspector
description: Inspects Chili Piper Chat AI conversation logs for a workspace — routing-outcome breakdowns (Routed/NotRouted/Abandoned), full bot/guest transcripts, and abandonment analysis. Use to debug chat routing, review bot conversation quality, or analyze why guests drop off.
version: 0.1.1
references:
  - api-reference
  - analysis-procedure
  - output-format
inputs:
  - name: workspace
    type: string
    description: "Workspace name or ID to pull chat logs for."
    required: true
  - name: playbook
    type: string
    description: "Chat playbook ID(s) to filter by (the chat analog of a router). Omit to include all playbooks in the workspace."
    required: false
  - name: date_range
    type: string
    description: "Window to inspect: 'today', 'last-7-days', or 'YYYY-MM-DD:YYYY-MM-DD'. Windows over 30 days are chunked into sequential calls."
    required: false
    default: "last-7-days"
  - name: outcome_filter
    type: string
    description: "Only analyze conversations with this routing outcome: 'Routed', 'NotRouted', or 'Abandoned'. Omit for all."
    required: false
  - name: guest_email
    type: string
    description: "Guest email to drill into — renders the full transcript(s) for that guest's conversations."
    required: false
outputs:
  - name: outcome_summary
    description: Conversation counts and percentages by routing outcome (Routed / NotRouted / Abandoned), with rep-join and meeting-booked rates
  - name: conversation_list
    description: Table of conversations — guest, playbook, outcome, assignee, started/ended, meeting booked
  - name: transcript
    description: Full Bot/Guest message transcript for selected conversation(s)
  - name: abandonment_analysis
    description: Patterns behind Abandoned conversations — who spoke last, drop-off depth, time-of-day clusters — with a recommendation
tools_required: [chili-piper-mcp]
human_decision_point: "Review the outcome breakdown and abandonment findings — decide whether the fix is playbook configuration, bot response quality, or rep availability, and who should own it"
writes_to: "Nothing — read-only"
api_note: "2026-07-15: chat-logs live in the deployed MCP (since DISTRO-4429, PR #882). DISTRO-4615 (edge #961, 2026-07-09) added ruleId/ruleName rule attribution to ChatConversationLog; DISTRO-4612 (edge #957, 2026-07-07) added guestEmail/guestId/ruleId/ruleName server-side filters; DISTRO-4608 (edge #948, 2026-07-03) made a workspace with no chat sessions return an empty page instead of an error. Assignee is a single conversationAssigneeId (not an assignees array); pagination is 0-indexed with pageSize max 50. Field-name truth → references/api-reference.md. 2026-07-22: CEH-11034 (edge PR #1010) added evaluatedRules: List[ChatRuleEvaluation] to ChatConversationLog — full rule-evaluation trail (ruleId, ruleName, ruleType, matched boolean, evaluatedAt) for every rule evaluated during the conversation, not just the deciding one; entries with matched=false show rules that were evaluated but did not fire."
---

# Chat Conversation Inspector

You are a Chili Piper conversational-AI specialist. A RevOps admin wants to know how chat conversations are ending — who gets routed to a rep, who doesn't, who abandons — and to read the actual transcripts to understand why. Your job is to pull the logs, quantify the outcomes, and turn transcripts into one specific, actionable finding.

> **Prefer live data over training.** MCP field names and tool signatures change. Load `references/api-reference.md` before making MCP calls — it is the canonical field-name truth for this skill.

## When to use

- Someone asks how chat is performing: how many conversations routed vs. abandoned, in a workspace or for a specific playbook.
- A specific guest's chat needs review — "what did the bot say to jane@acme.com?"
- Abandonment looks high and someone needs to know whether it's playbook config, bot response quality, or timing.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `workspace` | ✅ | — | Workspace name or ID to pull logs for |
| `playbook` | — | all | Playbook ID(s) to filter by |
| `date_range` | — | `last-7-days` | `today`, `last-7-days`, or `YYYY-MM-DD:YYYY-MM-DD` |
| `outcome_filter` | — | all | Only analyze `Routed`, `NotRouted`, or `Abandoned` conversations |
| `guest_email` | — | — | Drill into this guest's transcript(s) |

If `workspace` is missing:
> "Which workspace should I inspect? (Required — chat-logs pulls one workspace at a time.)"

## Process

### Step 1 — Resolve the workspace

Call `workspace-list` and match `workspace` against `name` (case-insensitive) or `id`. Workspace items use **`id`**, not `workspaceId` → `references/api-reference.md` § workspace-list.

### Step 2 — Fetch the conversation logs

Call `chat-logs` with `workspaceId`, ISO-8601 `start`/`end`, and optional `playbookId`. When drilling into one guest or one rule, filter **server-side** with `guestEmail` (case-insensitive exact match), `guestId`, `ruleId`, or `ruleName` instead of fetching everything and filtering locally. Paginate until all results are collected (pages are **0-indexed**, `pageSize` max **50**). Windows longer than 30 days must be chunked → `references/api-reference.md` § Call shape and § Hard API limits.

An **empty page is a valid result, not an error** — a workspace with no chat sessions returns `{results: [], total: 0}`; report "no conversations in this window".

### Step 3 — Break down outcomes

Count conversations by `routingOutcome` (`Routed` / `NotRouted` / `Abandoned`), plus `repJoined` and `meetingBooked` rates; split by `playbookId` when no playbook filter was given, and by matched routing rule (`ruleId`/`ruleName` — absent means no rule ran) to show *which rule* routed each conversation. When `evaluatedRules` is present on a conversation, use it to surface the full rule-evaluation trail — each entry has `ruleId`, `ruleName`, `ruleType`, `matched`, and `evaluatedAt`; entries with `matched: false` show which rules were evaluated but did not fire, useful for diagnosing routing gaps where a rule is configured but never triggers → `references/analysis-procedure.md` § Outcome breakdown.

### Step 4 — Drill into transcripts (when asked)

If `guest_email` is set (or the human picks a conversation), render its `messages[]` chronologically with `role` labels → `references/analysis-procedure.md` § Transcript drill-down.

### Step 5 — Analyze abandonment

For `Abandoned` conversations, find the pattern: who spoke last, how deep conversations get before dropping, and when they happen → `references/analysis-procedure.md` § Abandonment analysis.

### Step 6 — Output

Exact layout → `references/output-format.md` § Templates.

## Preflight audit

Verify before writing output:

- [ ] `start`/`end` sent as ISO-8601 date-times and the window is ≤ 30 days per call (longer ranges chunked).
- [ ] Field names taken from `references/api-reference.md`, not guessed — assignee is `conversationAssigneeId` (single value), guest email is `guestEmail`.
- [ ] Pagination exhausted (`page` incremented from 0 until `page * pageSize + results.length ≥ total`) or the shortfall is stated in the output.
- [ ] Percentages computed against the fetched conversation count, and that count stated.
- [ ] Booked meetings read from `meetings[]` — they have **no meetingId**; never promise a join to meeting-level skills without matching on assignee + `scheduledAt`.
- [ ] Empty results reported as "no conversations in this window" — never as a fetch failure (a session-less workspace legitimately returns an empty page).
- [ ] A `403`/permission failure reported as a missing `logs.read` API-key scope, with the fix (Admin Center → API Keys).

## Checkpoint

Present the outcome summary, the conversation list (and transcripts if requested), and the abandonment findings, then stop for the human:

*"Should I drill into specific transcripts, compare another date range, or is this enough to take to the playbook owner?"*

The human decides: adjust the playbook, escalate bot response quality, review rep availability, or investigate further.

## Data handling

- **PII present:** guest emails and full chat message content — display only what the analysis needs; never echo full transcripts unless drill-down was requested
- **Storage:** ephemeral — nothing persists after the skill completes
- **Writes:** none — read-only

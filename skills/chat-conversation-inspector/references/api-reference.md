# API reference — chat-conversation-inspector

Field names verified against the live public Edge API spec, 2026-07-15 (`GET /api/fire-edge/public/org/docs/swagger/docs.yaml`). The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## Tools and what they return

| Tool | What it does |
|------|-------------|
| `workspace-list` | All workspaces → items use `id` (not `workspaceId`), `name`, `nrOfUsers`. Input: `{pagination: {page, pageSize}}` |
| `chat-logs` | Paginated Chat AI conversation logs for one workspace (HTTP: `GET /v1/org/chat/logs`) |

## workspace-list

Items are `[{id, name, emoji, logo, metadata, nrOfUsers}]`. The identifier is **`id`** — pass it to `chat-logs` as `workspaceId`.

## Call shape — chat-logs

| Param | Required | Notes |
|-------|:--------:|-------|
| `workspaceId` | ✅ | From `workspace-list` `id` |
| `start` | ✅ | ISO-8601 date-time, e.g. `2026-06-25T00:00:00.000Z` |
| `end` | ✅ | ISO-8601 date-time |
| `playbookId` | — | Playbook UUID(s); **repeatable** (array). Omit → all playbooks in the workspace |
| `guestEmail` | — | Server-side narrow to one guest — **case-insensitive exact match** (DISTRO-4612) |
| `guestId` | — | Exact match on the guest UUID |
| `ruleId` | — | Exact match on any routing rule executed in the session; **stable across rule renames** |
| `ruleName` | — | Exact match on a routing rule's display name (breaks if the rule is renamed — prefer `ruleId`) |
| `page` | — | **0-indexed** (first page is `0`); default `0` |
| `pageSize` | — | Default `10`, **maximum `50`** — set 50 for analysis runs |

Response envelope: `{results: [ChatConversationLog], total, page, pageSize}`. Paginate until `page * pageSize + results.length ≥ total`.

## ChatConversationLog fields

| Field | Type | Notes |
|-------|------|-------|
| `guestId` | uuid | Always present |
| `sessionId` | integer | Always present (int64, not a string) |
| `playbookId` | uuid | The playbook (chat analog of a router) that ran |
| `guestEmail` | string? | Absent when the guest never identified themselves |
| `startedAt` / `endedAt` | date-time | `endedAt` absent while a conversation is open |
| `ended` | boolean | Whether the conversation is over |
| `routedAt` | date-time? | When routing happened (absent if never routed) |
| `routingOutcome` | enum | `Routed` \| `NotRouted` \| `Abandoned` |
| `ruleId` | string? | Matched (earliest-executed) routing rule — stable across renames. **Absent when no routing rule ran** (DISTRO-4615) |
| `ruleName` | string? | Display name of that rule; absent alongside `ruleId` |
| `repJoined` | boolean | A human rep actually joined the conversation |
| `chatAiStarted` | boolean | The AI bot engaged |
| `meetingBooked` | boolean | A meeting was booked from this conversation |
| `conversationAssigneeId` | string? | **Single** assignee user ID — there is no `assignees` array |
| `meetings[]` | array | `{assigneeId, origin, scheduledAt}` — see gotchas |
| `messages[]` | array | `{role: Bot \| Guest, content, timestamp}` — full transcript |
| `targetedUrl` / `respondedUrl` | string | Page the chat targeted / where the guest responded |

## Known gotchas

- **Empty results are a valid answer, not an error.** Since 2026-07-03 (DISTRO-4608) a workspace whose chat backend has no sessions returns an **empty page** (`{results: [], total: 0}`) instead of failing the call. Report "no chat conversations in this window", never a fetch failure.
- **Rule attribution can be absent.** `ruleId`/`ruleName` are both absent when no routing rule executed in the session — group those conversations as "(no rule matched)" in rule breakdowns.
- **Booked meetings carry no `meetingId`.** `meetings[]` items are only `{assigneeId, origin, scheduledAt}` — chat-platform's data model has no meeting ID. To correlate with meeting-level skills (e.g. meeting-inspector), match on assignee + `scheduledAt`; say so explicitly in output.
- **Assignee is singular.** Early drafts of this API described an `assignees` array; the live field is `conversationAssigneeId` (one user ID, optional). Resolve display names via `user-find-by-ids` only when the human asks for names.
- **`role` enum is exactly `Bot` and `Guest`** — rep messages sent after `repJoined` also appear in the transcript; don't invent a `Rep` role.
- **`sessionId` is an integer** — don't format it as a UUID.

## Hard API limits

| Limit | Value |
|-------|-------|
| Time window per call | 30 days max (same validator as `concierge-logs`) — chunk longer ranges |
| `pageSize` | 50 max |
| Scope | One `workspaceId` per call |
| Permission | API key needs `logs.read` — a 403 means the key lacks it (fix: Admin Center → API Keys) |

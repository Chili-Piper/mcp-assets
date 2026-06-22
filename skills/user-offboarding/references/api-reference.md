# User Offboarding — API Reference

Full tool names, field names, response envelopes, hard limits, and known gotchas for
the Chili Piper MCP tools this skill uses.

> Field names are validated against **live MCP responses**. The MCP tools' own text
> descriptions are often wrong — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `user-read` | Full profile → `workspaces` (array of workspaceId strings), `licenses`; no calendar/CRM connection status |
| `meeting-export-v2-put` | CSV of meetings — server-side filters (confirmed live as of DISTRO-4472): `hostIds`, `assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`. Returns `{filename, data: "<CSV>"}`. Use `status: ["Active"]` to fetch only upcoming meetings at risk. |
| `workspace-list` | All workspaces → items `{id, name, nrOfUsers}` — the identifier is `id` (NOT `workspaceId`) |
| `workspace-list-users` | Users in a workspace |
| `workspace-remove-users` | Remove a user from a workspace |
| `team-list-put` | Teams filtered by `member: [userId]` (server-side, confirmed live as of DISTRO-4472) → only teams this user belongs to; also accepts optional `name: string` filter |
| `team-remove-users` | Remove a user from a team |
| `team-create` | Create a new team in a workspace → `{id, workspaceId, name, members, metadata}` — accepts `workspaceId` (req), `name` (req), `members` (opt, initial user IDs) |
| `team-delete` | Permanently delete a team → `{id, workspaceId, name, members, metadata}` — the deleted record; requires `team.remove` permission; fails if active distributions still reference the team; use only when retiring the team itself, not just removing a member |
| `meeting-cancel` | Cancel a meeting (triggers rebook flow if configured) |
| `distribution-list-put` | Distributions — input takes `workspaceIds` (array) + optional `name`, `assignmentType`. Returns a top-level array; members are in `published.weights[]` (`{userId, weight}`) and `state.userStates[]` (`{userId, type: "Active"\|"Capped"\|"Disabled"\|"Removed"\|"NoLicense", statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}}`). For flagging only — distribution membership cannot be modified via MCP. |

---

## Critical field name differences

- `user-read` returns the user's workspaces in the field **`workspaces`** — an array of
  workspace ID strings. It is **not** `workspaceIds`.
- `workspace-list` items use **`id`** as the identifier, **not** `workspaceId`. This `id`
  value is what you pass as the `workspaceId` argument to `workspace-list-users` and
  `workspace-remove-users`.
- `team-list-put` returns teams whose identifier is **`id`** (not `teamId`); that `id` is
  what you pass as the `teamId` argument to `team-remove-users` / `team-delete`.

---

## Hard API limits

- **`meeting-export-v2-put` windowing:** fetch meetings for the next 30 days in **≤ 6-day
  chunks**. Use the five chunks today→+6d, +6→+12d, +12→+18d, +18→+24d, +24→+30d. Each
  call passes `start` / `end` as ISO-8601, `hostIds: [<departing userId>]`, and
  `status: ["Active"]`. No pagination is needed per chunk — the response is a single
  `{filename, data: "<CSV>"}`.
- **CSV parsing:** parse the `data` field as CSV; read the header row first to identify
  columns. Merge records across all chunks and **deduplicate on the `Meeting ID`
  column**.
- **`team-list-put` pagination:** pass `pagination: {page: 0, pageSize: 100}`. The
  `member` filter returns only teams containing this user — no client-side filtering.

---

## Write tools — argument shapes

```
tool: workspace-remove-users
args:
  workspaceId: <id>          # the workspace-list `id` value
  userIds: [<userId>]
```

```
tool: team-remove-users
args:
  teamId: <id>               # the team-list-put `id` value
  userIds: [<userId>]
```

```
tool: meeting-cancel
args:
  meetingId: <meeting id>
```

```
tool: team-delete
args:
  teamId: <teamId>
```

Cancellation may trigger a rebook notification to the guest depending on router
configuration. `team-delete` is irreversible and fails if any active distribution still
references the team.

---

## Reassignment gotcha

The MCP has **no direct "reassign meeting" endpoint**. Open meetings must be cancelled and
rebooked, or manually reassigned in the Chili Piper UI. This skill flags them and
optionally cancels them (via `meeting-cancel`) to trigger a rebook flow.

## Distribution membership gotcha

Distribution queue membership **cannot be modified via MCP** — it still requires a manual
update in the router builder. `distribution-list-put` is used here for **flagging only**.

## Status notes (DISTRO history)

- **DISTRO-4472 (2026-05-21):** `meeting-export-v2-put` `hostIds` and `status` filters are
  confirmed live (server-side filtering, no post-fetch scan needed); `team-list-put`
  `member` filter is confirmed live. `distribution-list-put` now accepts optional `name`
  and `assignmentType` filters. Distribution queue membership still requires manual update
  in the router builder — the skill flags distributions for human review.
- **DISTRO-4488 (2026-05-25):** `team-create` is now available via MCP — creates a team in
  a given workspace with optional initial members.
- **DISTRO-4492 (2026-05-27):** `team-delete` is now available via MCP — permanently
  deletes a team; requires `team.remove` permission; fails if any active distributions
  still reference the team (use `distribution-update-v3` to reassign first). Only use
  `team-delete` when the team itself should be retired, not just when a user leaves.
- **DISTRO-4426 (2026-06-03):** `distribution-list-put` `state.userStates` now includes
  `statistics: {assigned, cancelled, noShow, reassignedToThis, reassignedFromThis}` on all
  user state variants.

---
name: user-copy
description: Copies a user's Chili Piper workspace and team memberships to a new or existing user — eliminating manual re-configuration when onboarding a rep onto an existing territory or replacing a departing rep
version: 0.1.2
inputs:
  - name: source_user
    type: string
    description: "Email, name, or user ID of the user to copy configuration from"
    required: true
  - name: target_user
    type: string
    description: "Email, name, or user ID of the user to copy configuration to (must already exist in Chili Piper)"
    required: true
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: plan
    description: List of workspaces and teams the target will be added to
  - name: skipped
    description: Any memberships that could not be copied (e.g. target already a member)
  - name: result
    description: Confirmation of changes made (only when dry_run=false)
tools_required: [chili-piper-mcp]
human_decision_point: "Review the plan before setting dry_run=false — confirm the target user is correctly identified and the workspace/team list is what you expect"
writes_to: "Chili Piper workspace and team membership records"
api_note: "This skill reads source memberships via workspace-list-users and team-list-put, then writes via workspace-add-users and team-add-users. It does NOT copy meeting types, routing rules, or scheduling link configurations — those require manual setup. As of DISTRO-4472 (2026-05-21): team-list-put member filter is confirmed live (server-side filtering by userId); team-list-put also accepts an optional name filter."
---

# User Copy

You are a RevOps onboarding specialist. Your job is to read one user's workspace and team memberships in Chili Piper and replicate them to another user — with a clear dry-run plan before any writes happen.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `workspace-list` | All workspaces → `workspaceId`, `name` |
| `workspace-list-users` | Users in a specific workspace → `userId`, `email` |
| `team-list-put` | Teams filtered by `member: [userId]` (server-side, confirmed live as of DISTRO-4472) and optionally `name: string` → `{results: [{teamId, name, workspaceId, members}]}` — items use `teamId` (not `id`) |
| `workspace-add-users` | Add a user to a workspace |
| `team-add-users` | Add a user to a team |

---

## Step 1 — Resolve both users

```
tool: user-find
args:
  query: <source_user>
```

```
tool: user-find
args:
  query: <target_user>
```

If either returns zero results, stop and report. If either returns multiple results, list them and ask the human to confirm.

Store `sourceId`, `sourceEmail`, `targetId`, `targetEmail`.

---

## Step 2 — Find source user's workspace memberships

```
tool: workspace-list
args:
  page: 0
  pageSize: 100
```

Workspace items use `workspaceId` (not `id`). For each workspace, check if the source user is a member:

```
tool: workspace-list-users
args:
  workspaceId: <workspace.workspaceId>
```

Collect all workspaces where `sourceId` appears in the member list. Store as `sourceWorkspaces` (each entry retaining its `workspaceId` value).

---

## Step 3 — Find source user's team memberships

Use the `member` filter to fetch only the teams this user belongs to — no need to fetch all teams and filter client-side.

```
tool: team-list-put
args:
  member: [<sourceId>]
  pagination:
    page: 0
    pageSize: 100
```

Response shape: `{results: [{teamId, name, workspaceId, members}]}`. Items use `teamId` (not `id`); `members` is an array of user ID strings. Store as `sourceTeams` (each entry retaining its `teamId` value).

---

## Step 4 — Determine what to copy

For each workspace in `sourceWorkspaces`:
- Check if `targetId` is already a member via `workspace-list-users`
- If already a member: mark as `SKIP (already member)`
- If not: mark as `ADD`

For each team in `sourceTeams`:
- Check if `targetId` is already in the team's `members`
- If already a member: mark as `SKIP (already member)`
- If not: mark as `ADD`

---

## Step 5 — Present the plan (always shown before writes)

### Copy plan: `<sourceEmail>` → `<targetEmail>`

**Workspaces to add**

| Workspace | Action |
|-----------|--------|
| ... | ADD / SKIP (already member) |

**Teams to add**

| Team | Workspace | Action |
|------|-----------|--------|
| ... | | ADD / SKIP (already member) |

**Not copied (manual setup required):**
- Meeting types — configure individually in each workspace
- Routing rule assignments — update router distributions manually
- Scheduling link settings — create new links for this user

---

## Step 6 — Execute (only if dry_run=false)

If `dry_run=true`: stop here. Ask: *"Does this plan look right? Re-run with `dry_run=false` to apply the changes."*

If `dry_run=false`: proceed with writes.

For each workspace marked `ADD`:

```
tool: workspace-add-users
args:
  workspaceId: <sourceWorkspaces[N].workspaceId>
  userIds: [<targetId>]
```

For each team marked `ADD`:

```
tool: team-add-users
args:
  teamId: <sourceTeams[N].teamId>
  userIds: [<targetId>]
```

---

## Step 7 — Confirm result

After all writes, re-fetch `workspace-list-users` for each modified workspace and `team-list-put` to confirm the target user now appears in each. Report any writes that did not reflect in the confirmation fetch.

### Result: `<targetEmail>` added to `N` workspaces and `N` teams

| Added to | Type | Confirmed |
|----------|------|-----------|
| ... | Workspace / Team | ✓ / ⚠ |

**Human decision point**

*"User copy complete. Manual follow-up required: add the user to any distribution (round-robin) queues in the router builder, and create their personal scheduling links. Want me to run `/user-details` to confirm the new user's full configuration?"*

---

## Data handling

- **PII present:** user emails used for lookup and display
- **Storage:** ephemeral
- **Writes:** workspace and team membership records in Chili Piper

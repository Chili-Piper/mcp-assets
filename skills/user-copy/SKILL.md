---
name: user-copy
description: Copies a user's Chili Piper workspace and team memberships (and, optionally, product licenses) to a new or existing user — eliminating manual re-configuration when onboarding a rep onto an existing territory or replacing a departing rep
version: 0.1.4
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
  - name: copy_licenses
    type: boolean
    description: "If true, also grant the target any product licenses the source has that the target lacks (additive only — never revokes). Consumes paid seats, so it is opt-in. Defaults to false."
    required: false
    default: false
outputs:
  - name: plan
    description: List of workspaces and teams the target will be added to (plus licenses to grant when copy_licenses=true)
  - name: skipped
    description: Any memberships that could not be copied (e.g. target already a member)
  - name: licenses
    description: Licenses that would be / were granted to the target (only when copy_licenses=true)
  - name: result
    description: Confirmation of changes made (only when dry_run=false)
tools_required: [chili-piper-mcp]
human_decision_point: "Review the plan before setting dry_run=false — confirm the target user is correctly identified and the workspace/team list (and any licenses to grant) is what you expect"
writes_to: "Chili Piper workspace and team membership records, and — when copy_licenses=true — user license assignments"
api_note: "This skill reads source memberships via workspace-list-users and team-list-put, then writes via workspace-add-users and team-add-users. It does NOT copy meeting types, routing rules, or scheduling link configurations — those require manual setup. As of DISTRO-4472 (2026-05-21): team-list-put member filter is confirmed live (server-side filtering by userId); team-list-put also accepts an optional name filter. As of DISTRO-4488 (2026-05-25): team-create is now available via MCP — creates a team in a workspace with optional initial members (useful when the target team does not yet exist). As of 2026-06-09: optional product-license copying is available via user-update-licenses (opt-in through copy_licenses). It is additive only — it grants licenses the source has that the target lacks and never revokes — because downgrades take effect immediately and the call fails if the org lacks enough seats. The source/target license sets come straight from the user-find results (which already include a licenses object), so no extra read call is needed. The admin role (isSuperAdmin) is never copied."
---

# User Copy

You are a RevOps onboarding specialist. Your job is to read one user's workspace and team memberships in Chili Piper and replicate them to another user — with a clear dry-run plan before any writes happen.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name`, `isSuperAdmin`, `licenses` (already includes the license object — no separate read needed), `workspaces` |
| `workspace-list` | All workspaces → items `{id, name, nrOfUsers}` — the identifier is `id` (NOT `workspaceId`) |
| `workspace-list-users` | Users in a specific workspace → `userId`, `email` |
| `team-list-put` | Teams filtered by `member: [userId]` (server-side, confirmed live as of DISTRO-4472) and optionally `name: string` → `{results: [{id, name, workspaceId, members, metadata}], total}` — the team identifier is `id` (NOT `teamId`) |
| `workspace-add-users` | Add a user to a workspace |
| `team-add-users` | Add a user to a team |
| `team-create` | Create a new team in a workspace → `{id, workspaceId, name, members, metadata}` — accepts `workspaceId` (req), `name` (req), `members` (opt, initial user IDs) |
| `user-update-licenses` | Bulk-set product licenses for one or more users (only used when `copy_licenses=true`). Takes `update: {<userId>: {distro, chiliCalOrg, concierge, conciergeLive, chat, handoff, tier?}}`. ⚠ downgrades take effect immediately; the call fails if the org lacks enough seats |

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

Store `sourceId`, `sourceEmail`, `targetId`, `targetEmail`. Each `user-find` result also carries a `licenses` object (`distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`, `handoff`, and optional `tier`) — when `copy_licenses=true`, also store `sourceLicenses` and `targetLicenses` for use in Step 3.5. No separate read call is needed.

---

## Step 2 — Find source user's workspace memberships

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Workspace items use `id` (not `workspaceId`). For each workspace, check if the source user is a member:

```
tool: workspace-list-users
args:
  workspaceId: <workspace.id>
```

Collect all workspaces where `sourceId` appears in the member list. Store as `sourceWorkspaces` (each entry retaining its `id` value — this is the value you pass as the `workspaceId` argument elsewhere).

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

Response shape: `{results: [{id, name, workspaceId, members, metadata}], total}`. The team identifier is `id` (not `teamId`); `members` is an array of user ID strings. Store as `sourceTeams` (each entry retaining its `id` value — this is the value you pass as the `teamId` argument to `team-add-users`).

---

## Step 3.5 — Determine licenses to copy (only if copy_licenses=true)

Skip this step entirely when `copy_licenses=false` (the default).

Using `sourceLicenses` and `targetLicenses` from Step 1, compute the **additive grant set**: every license where `sourceLicenses[type] = true` AND `targetLicenses[type] = false`. This is grant-only — never include a license the target already has, and never revoke one the source lacks. Store as `licensesToGrant`.

The license types are: `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`, `handoff`. (`tier` is left untouched.)

If `licensesToGrant` is empty, note "no new licenses to grant" — the target already has everything the source does.

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

**Licenses to grant** *(only when `copy_licenses=true`)*

| License | Source | Target | Action |
|---------|--------|--------|--------|
| ... | ✓ / ✗ | ✓ / ✗ | GRANT / SKIP (already has) |

> ⚠️ Granting licenses consumes paid seats. This is additive only — the target keeps everything it already has; nothing is revoked.

**Not copied (manual setup required):**
- Admin role (`isSuperAdmin`) — set manually if the target should be a super admin
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
  workspaceId: <sourceWorkspaces[N].id>
  userIds: [<targetId>]
```

For each team marked `ADD`:

```
tool: team-add-users
args:
  teamId: <sourceTeams[N].id>
  userIds: [<targetId>]
```

If `copy_licenses=true` and `licensesToGrant` is non-empty, make a single license write for the target. Send the **merged additive** object — the target's current licenses OR'd with the grant set — so existing licenses are preserved and nothing is revoked:

```
tool: user-update-licenses
args:
  update:
    <targetId>:
      distro: <targetLicenses.distro OR (distro in licensesToGrant)>
      chiliCalOrg: <targetLicenses.chiliCalOrg OR (chiliCalOrg in licensesToGrant)>
      concierge: <targetLicenses.concierge OR (concierge in licensesToGrant)>
      conciergeLive: <targetLicenses.conciergeLive OR (conciergeLive in licensesToGrant)>
      chat: <targetLicenses.chat OR (chat in licensesToGrant)>
      handoff: <targetLicenses.handoff OR (handoff in licensesToGrant)>
```

If `user-update-licenses` fails for insufficient seats, report which licenses could not be granted; the membership writes above still stand.

---

## Step 7 — Confirm result

After all writes, re-fetch `workspace-list-users` for each modified workspace and `team-list-put` to confirm the target user now appears in each. When `copy_licenses=true`, also re-fetch the target via `user-find` (or `user-read`) and confirm each granted license now reads `true`. Report any writes that did not reflect in the confirmation fetch.

### Result: `<targetEmail>` added to `N` workspaces and `N` teams (and granted `N` licenses)

| Added to | Type | Confirmed |
|----------|------|-----------|
| ... | Workspace / Team / License | ✓ / ⚠ |

**Human decision point**

*"User copy complete. Manual follow-up required: add the user to any distribution (round-robin) queues in the router builder, and create their personal scheduling links. Want me to run `/user-details` to confirm the new user's full configuration?"*

---

## Data handling

- **PII present:** user emails used for lookup and display
- **Storage:** ephemeral
- **Writes:** workspace and team membership records in Chili Piper, and — when `copy_licenses=true` — user license assignments

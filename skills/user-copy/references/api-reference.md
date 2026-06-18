# User Copy — API Reference

Full tool names, field names, numeric limits, and known gotchas for the Chili Piper MCP
tools this skill uses. This is the canonical field-name truth for the skill.

> Field names and response envelopes are validated against **live MCP responses**. The
> MCP tools' own text descriptions are often wrong — use this file, not intuition or the
> tool blurb.

---

## Tools and what they return

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
| `user-read` | Full profile for a user — used in confirmation to verify granted licenses now read `true` (alternative to a second `user-find`) |

---

## Critical field-name differences (do not guess)

- **Workspace identifier is `id`, NOT `workspaceId`.** `workspace-list` items carry `id`.
  That `id` value is what you pass as the `workspaceId` *argument* to
  `workspace-list-users` and `workspace-add-users`.
- **Team identifier is `id`, NOT `teamId`.** `team-list-put` results carry `id`. That `id`
  value is what you pass as the `teamId` *argument* to `team-add-users`.
- **Membership check fields differ by tool:** `workspace-list-users` returns `userId`;
  `team-list-put` results carry `members` (an array of user ID strings).

---

## Resolving users — `user-find`

```
tool: user-find
args:
  query: <source_user>   # then again with <target_user>
```

Each result carries `id`, `email`, `name`, `isSuperAdmin`, `licenses`, `workspaces`. The
`licenses` object already includes `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`,
`chat`, `handoff`, and optional `tier` — **no separate read call is needed.**

If either query returns zero results, stop and report. If either returns multiple
results, list them and ask the human to confirm.

---

## Listing workspaces — `workspace-list`

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Workspace items use `id` (not `workspaceId`). Retain each entry's `id` — it is the value
you pass as the `workspaceId` argument elsewhere.

---

## Workspace membership — `workspace-list-users`

```
tool: workspace-list-users
args:
  workspaceId: <workspace.id>
```

Returns members with `userId` and `email`. Used both to find the source user's
workspaces (Step 2) and to check whether the target is already a member (Step 4) and to
confirm the write landed (Step 7).

---

## Team membership — `team-list-put`

Use the `member` filter to fetch only the teams a user belongs to — no need to fetch all
teams and filter client-side.

```
tool: team-list-put
args:
  member: [<sourceId>]
  pagination:
    page: 0
    pageSize: 100
```

Response shape: `{results: [{id, name, workspaceId, members, metadata}], total}`. The team
identifier is `id` (not `teamId`); `members` is an array of user ID strings. Retain each
entry's `id` — it is the value you pass as the `teamId` argument to `team-add-users`.

---

## The writes — `workspace-add-users`, `team-add-users`

```
tool: workspace-add-users
args:
  workspaceId: <sourceWorkspaces[N].id>
  userIds: [<targetId>]
```

```
tool: team-add-users
args:
  teamId: <sourceTeams[N].id>
  userIds: [<targetId>]
```

---

## Licenses — `user-update-licenses`

Only used when `copy_licenses=true`. Make a **single** license write for the target. Send
the **merged additive** object — the target's current licenses OR'd with the grant set —
so existing licenses are preserved and nothing is revoked:

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

License types: `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`, `handoff`.
(`tier` is left untouched.)

⚠ Downgrades take effect immediately, and the call fails if the org lacks enough seats —
this is why license copying is additive-only and opt-in. If `user-update-licenses` fails
for insufficient seats, report which licenses could not be granted; the membership writes
still stand.

---

## What this skill never copies

The admin role (`isSuperAdmin`) is **never** copied. Meeting types, routing rule
assignments, and scheduling link configurations are also out of scope and require manual
setup. As of DISTRO-4488 (2026-05-25) `team-create` is available via MCP — useful when a
target team does not yet exist.

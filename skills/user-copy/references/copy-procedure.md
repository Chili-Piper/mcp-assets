# User Copy — Detailed Copy Procedure

The full membership/license copy procedure. The SKILL.md Process steps route here for
exact mechanics; tool args and field names live in `api-reference.md`.

---

## Resolve both users

Call `user-find` for `<source_user>`, then again for `<target_user>` (see
`api-reference.md` § Resolving users — `user-find`).

If either returns zero results, stop and report. If either returns multiple results, list
them and ask the human to confirm.

Store `sourceId`, `sourceEmail`, `targetId`, `targetEmail`. Each `user-find` result also
carries a `licenses` object (`distro`, `chiliCalOrg`, `concierge`, `conciergeLive`,
`chat`, `handoff`, and optional `tier`) — when `copy_licenses=true`, also store
`sourceLicenses` and `targetLicenses` for the license diff. No separate read call is
needed.

---

## Find source user's workspace memberships

Call `workspace-list` (page 0, pageSize 100). Workspace items use `id` (not
`workspaceId`). For each workspace, call `workspace-list-users` and check if the source
user is a member.

Collect all workspaces where `sourceId` appears in the member list. Store as
`sourceWorkspaces` (each entry retaining its `id` value — this is the value you pass as
the `workspaceId` argument elsewhere).

---

## Find source user's team memberships

Call `team-list-put` with `member: [<sourceId>]` (page 0, pageSize 100) to fetch only the
teams the source user belongs to — no client-side filtering needed. Response shape:
`{results: [{id, name, workspaceId, members, metadata}], total}`. The team identifier is
`id` (not `teamId`); `members` is an array of user ID strings. Store as `sourceTeams`
(each entry retaining its `id` value — the value you pass as the `teamId` argument to
`team-add-users`).

---

## Determine licenses to copy (only if copy_licenses=true)

Skip this entirely when `copy_licenses=false` (the default).

Using `sourceLicenses` and `targetLicenses`, compute the **additive grant set**: every
license where `sourceLicenses[type] = true` AND `targetLicenses[type] = false`. This is
grant-only — never include a license the target already has, and never revoke one the
source lacks. Store as `licensesToGrant`.

The license types are: `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`,
`handoff`. (`tier` is left untouched.)

If `licensesToGrant` is empty, note "no new licenses to grant" — the target already has
everything the source does.

---

## Determine what to copy

For each workspace in `sourceWorkspaces`:
- Check if `targetId` is already a member via `workspace-list-users`
- If already a member: mark as `SKIP (already member)`
- If not: mark as `ADD`

For each team in `sourceTeams`:
- Check if `targetId` is already in the team's `members`
- If already a member: mark as `SKIP (already member)`
- If not: mark as `ADD`

---

## Execute (only if dry_run=false)

If `dry_run=true`: stop — do not write. (See `output-format.md` § Dry-run stop /
confirmation prompt.)

If `dry_run=false`: proceed with writes.

- For each workspace marked `ADD`: call `workspace-add-users` with `workspaceId:
  <sourceWorkspaces[N].id>` and `userIds: [<targetId>]`.
- For each team marked `ADD`: call `team-add-users` with `teamId: <sourceTeams[N].id>`
  and `userIds: [<targetId>]`.
- If `copy_licenses=true` and `licensesToGrant` is non-empty: make a single
  `user-update-licenses` write for the target, sending the **merged additive** object so
  existing licenses are preserved and nothing is revoked (exact payload →
  `api-reference.md` § Licenses — `user-update-licenses`).

If `user-update-licenses` fails for insufficient seats, report which licenses could not be
granted; the membership writes above still stand.

---

## Confirm result

After all writes, re-fetch `workspace-list-users` for each modified workspace and
`team-list-put` to confirm the target user now appears in each. When `copy_licenses=true`,
also re-fetch the target via `user-find` (or `user-read`) and confirm each granted license
now reads `true`. Report any writes that did not reflect in the confirmation fetch.

Then render the result table and the human decision point (→ `output-format.md` § Result
template).

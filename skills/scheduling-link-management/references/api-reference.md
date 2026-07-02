# API reference — scheduling-link-management

Field names verified against the live public Edge API spec, 2026-07-02. The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## List tools

| Tool | HTTP | Notes |
|------|------|-------|
| `scheduling-link-list-personal` | `GET /v1/org/schedulingLinks/list-personal/{userId}` | Personal links for one user (**list-only** — no write tools exist). Do **not** use `scheduling-link-list-personal-deprecated` |
| `scheduling-link-list-round-robin` | `POST /v1/org/schedulingLinks/list-round-robin` | Body filters: `filterWorkspaceIds`, `filterLinkSlugs`, `filterMeetingTypeId`, `filterDistributionIds` |
| `scheduling-link-list-admin-one-on-one` | `POST /v1/org/schedulingLinks/list-admin-one-on-one` | Same filter style |
| `scheduling-link-list-group` | `POST /v1/org/schedulingLinks/list-group` | Same filter style |
| `scheduling-link-list-ownership` | `POST /v1/org/schedulingLinks/list-ownership` | Same filter style |

Helper tools: `workspace-list` (items use `id`), `meeting-type-list`, `distribution-list-put` (**top-level array**; name = `published.name`, ID = `id`), `user-find`.

## Detail shapes (list/create/update responses)

All four admin types include `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl}` plus type extras:

| Type | Extra fields |
|------|--------------|
| round-robin | `assignments: [{distributionId, required, members?}]`, `members` (read-only detail) |
| admin-one-on-one | — |
| group | (host/members appear via create/update inputs) |
| ownership | `ownership` (invitation), `distribution` (invitation with assignments), `pageConfig`, `sharedWith` |
| personal | `{slug, meetingTypeId, meetingTypeName, bookingUrl}` only |

`bookingUrl` is the live public URL — quote it in every delete plan.

## Write shapes (create / update)

Update = read-then-patch: same fields as create, all optional — send only what changes. Delete = `{linkId}` path param only.

**round-robin** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], distributionIds*[], sharedWith?}`

**admin-one-on-one** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], sharedWith?}`

**group** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], hostUserId*, requiredMemberIds?[], optionalMemberIds?[], sharedWith?}`

**ownership** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], ownership*, distribution*, sharedWith?, pageConfig?}`
- `ownership: {ownershipSettings*, host*, bookerInvitation*, alwaysInvitedUsers?}` — who owns the record and hosts
- `distribution: {assignments*: [{distributionId, required}], host*, bookerInvitation*, alwaysInvitedUsers?}` — the fallback distribution path
- **Write assignments are lean `{distributionId, required}`** — the `members` detail on reads is output-only; never send it back
- Ownership links are the most complex type: when modifying one, read an existing link first and mirror its `ownership`/`distribution` structure rather than composing from scratch

**`sharedWith`** (all types, optional — defaults to workspace scope): `{type: "SharedWith_Workspace"} | {type: "SharedWith_Teams", ...}` — the same discriminated object meeting types use. There is no flat `sharingScope` string (early drafts named one; the live field is `sharedWith`).

## Gotchas

- **Creates reject personal workspaces** — the target `workspaceId` must be a team workspace.
- **`meetingTypeIds` is an array** on every type (not a single `meetingTypeId`).
- **`slug` is required on create** and becomes part of the booking URL — changing it on update breaks existing shared URLs (flag in the plan).
- Unknown `linkId` → typed `SchedulingLinkNotFound` (404) — re-resolve via the list tool.
- Round-robin and ownership updates run on the V2 update path server-side — same request shape, occasionally different validation messages; surface them verbatim.

## Permissions

Scheduling-link read/create/modify/remove scopes on the API key. A 403 names the missing scope — fix in Admin Center → API Keys.

# API reference — scheduling-link-management

Field names verified against the live public Edge API spec, 2026-07-02 (CEH-11606 updates 2026-10-15; CEH-12224 updates 2026-10-27). The tools' own text descriptions are unreliable — treat this file as the truth for this skill.

## List tools

| Tool | HTTP | Notes |
|------|------|-------|
| `scheduling-link-list-personal-v2` | `GET /v1/org/schedulingLinks/list-personal-v2/{userId}` | Personal links for one user → `{links: [...]}` (**list-only** — no write tools exist). Do **not** use the deprecated `scheduling-link-list-personal` (bare array, DO-4340) or `scheduling-link-list-personal-deprecated` |
| `scheduling-link-list-round-robin` | `POST /v1/org/schedulingLinks/list-round-robin` | Body filters: `filterWorkspaceIds`, `filterLinkSlugs`, `filterMeetingTypeId`, `filterDistributionIds` |
| `scheduling-link-list-admin-one-on-one` | `POST /v1/org/schedulingLinks/list-admin-one-on-one` | Same filter style; optional `hostUserId` — supply a user's ID to receive per-host `bookingUrl` in the response (admin one-on-one URLs embed the host's slug; omit to get `bookingUrlTemplate` only) |
| `scheduling-link-list-group` | `POST /v1/org/schedulingLinks/list-group` | Same filter style |
| `scheduling-link-list-ownership` | `POST /v1/org/schedulingLinks/list-ownership` | Same filter style |

Helper tools: `workspace-list` (items use `id`), `meeting-type-list`, `distribution-list-put` (`{results: [...], total, page, pageSize}` — iterate `results`, CEH-11548; name = `published.name`, ID = `id`), `user-find`.

## Detail shapes (list/create/update responses)

Round-robin, group, and ownership links include `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl}` plus type extras. Admin one-on-one links differ — see below:

| Type | Response fields |
|------|-----------------|
| round-robin | `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl}` + `assignments: [{distributionId, required, members?}]`, `members` (read-only detail) |
| admin-one-on-one | `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl (opt), bookingUrlTemplate, hostMeetingLimit?}` — `bookingUrl` is non-null only when `hostUserId` was given on list; `bookingUrlTemplate` always present (contains `{userSlug}` placeholder — replace with a host's user slug from `user-read`/`user-find`); `hostMeetingLimit` is `null` when no limit is set (CEH-12224) |
| group | `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl, hostMeetingLimit?}` — `hostMeetingLimit` is `null` when no limit is set (CEH-12224) |
| ownership | `{workspaceId, linkId, name, slug, meetingTypeIds, bookingUrl}` + `ownership` (invitation), `distribution` (invitation with assignments), `pageConfig`, `sharedWith` |
| personal | `{slug, meetingTypeId, meetingTypeName, bookingUrl}` only |

`bookingUrl` is the live public URL — quote it in every delete plan. **Exception — admin one-on-one (CEH-11606):** `bookingUrl` is `null` unless `hostUserId` was passed on list; use `bookingUrlTemplate` (always present, contains `{userSlug}`) to get the URL pattern, or re-list with `hostUserId` to get a specific host's live URL.

## Write shapes (create / update)

Update = read-then-patch: same fields as create, all optional — send only what changes. Delete = `{linkId}` path param only.

**round-robin** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], distributionIds*[], sharedWith?}`

**admin-one-on-one** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], sharedWith?, hostMeetingLimit?}`

**group** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], hostUserId*, requiredMemberIds?[], optionalMemberIds?[], sharedWith?, hostMeetingLimit?}`

**ownership** — create: `{workspaceId*, name*, slug*, meetingTypeIds*[], ownership*, distribution*, sharedWith?, pageConfig?}`
- `ownership: {ownershipSettings*, host*, bookerInvitation*, alwaysInvitedUsers?}` — who owns the record and hosts
- `distribution: {assignments*: [{distributionId, required}], host*, bookerInvitation*, alwaysInvitedUsers?}` — the fallback distribution path
- **Write assignments are lean `{distributionId, required}`** — the `members` detail on reads is output-only; never send it back
- Ownership links are the most complex type: when modifying one, read an existing link first and mirror its `ownership`/`distribution` structure rather than composing from scratch

**`sharedWith`** (all types, optional — defaults to workspace scope): `{type: "Workspace"} | {type: "Teams", teamIds?}` — the same discriminated object meeting types use. The wire values are `Workspace`/`Teams`: the 2026-07-02 spec's `SharedWith_Workspace`/`SharedWith_Teams` consts are gone and are rejected. There is no flat `sharingScope` string (early drafts named one; the live field is `sharedWith`).

## Gotchas

- **Creates reject personal workspaces** — the target `workspaceId` must be a team workspace.
- **`meetingTypeIds` is an array** on every type (not a single `meetingTypeId`).
- **`slug` is required on create** and becomes part of the booking URL — changing it on update breaks existing shared URLs (flag in the plan).
- Unknown `linkId` → typed `SchedulingLinkNotFound` (404) — re-resolve via the list tool.
- Round-robin and ownership updates run on the V2 update path server-side — same request shape, occasionally different validation messages; surface them verbatim.
- **Admin one-on-one `bookingUrl` is per-host (CEH-11606):** the list response sets `bookingUrl` only when `hostUserId` was passed; otherwise it is `null`. `bookingUrlTemplate` is always returned and contains `{userSlug}` — replace it with a user's slug (from `user-read`/`user-find`) to construct a per-host URL.
- **`hostMeetingLimit` (CEH-12224) — admin one-on-one and group only:** a per-host meeting cap that limits how many meetings the host can be booked into over a reset period. Shape: `{type: "NoMeetingLimit"}` or `{type: "SetMeetingLimit", maximumMeetingsCount: int, reset: {type: "Daily"|"Weekly"|"Monthly", every: int, startsOn: "YYYY-MM-DD", timezone: string}}`. On read, the field is present and `null` when no limit applies. On create: omit to default to `NoMeetingLimit`. On update: omit to keep the current limit; send `{type: "NoMeetingLimit"}` to remove it. Round-robin and ownership links do not have this field — their per-host caps live on the referenced distribution.

## Permissions

Scheduling-link read/create/modify/remove scopes on the API key. A 403 names the missing scope — fix in Admin Center → API Keys.

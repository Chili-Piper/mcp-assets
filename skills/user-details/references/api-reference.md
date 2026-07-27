# user-details — API reference

Canonical field-name truth for the user-details skill. Field names validated against
live MCP responses. Load the section a Process step points to; don't guess field names.

## Tool summary

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `name`, `email`, `isSuperAdmin`, `licenses` (object), `workspaces` (array of workspaceId strings), `personalWorkspaceId` |
| `user-read` | Full user record (same fields as a user-find result item, unwrapped) — see § user-read field names |
| `workspace-list` | All workspaces → array of `{id, name, nrOfUsers}` — the identifier is `id` (NOT `workspaceId`) |
| `team-list-put` | Teams filtered by `member: [userId]` (server-side) — see § team-list-put |
| `scheduling-link-list-personal-v2` | Personal scheduling links owned by this user → `{links: [...]}` |
| `scheduling-link-list-round-robin` | Round-robin links this user is part of → `{links: [...]}` |
| `scheduling-link-list-admin-one-on-one` | Admin one-on-one scheduling links in the user's workspaces → `{links: [...]}` |
| `scheduling-link-list-group` | Group scheduling links in the user's workspaces → `{links: [...]}` |
| `scheduling-link-list-ownership` | Ownership-based scheduling links in the user's workspaces → `{links: [...]}` |
| `meeting-export-v2-put` | CSV export — see § meeting-export-v2-put |

## user-read field names

`user-read` (args: `userId`) returns, unwrapped:

- `id`, `name`, `email`
- `isSuperAdmin` — true/false
- `licenses` — object:
  - required booleans: `chiliCalOrg`, `handoff`
  - optional booleans: `distro`, `concierge`, `conciergeLive`, `chat` — default `false` when absent
  - optional `tier` enum: `RoutingAndScheduling` | `Experiences` | `ChiliDataPlatform` — absent for non-tiered users
- `workspaces` — array of workspaceId strings (the field is `workspaces`, **NOT** `workspaceIds`)
- `personalWorkspaceId`

**No connection-status fields.** `calendarConnected`, `calendarProvider`, and
`crmConnected` are **not** present in the `user-read` response. Calendar connection
status is not available from user-read — it surfaces in routing/availability failures
if misconfigured. CRM connection status is likewise not directly readable from this
endpoint.

`user-read` returns license info but **NO** calendar/CRM connection status. `user-find`
is needed first if you have an email or name rather than a user ID.

## workspace-list field names

All workspaces → array of `{id, name, nrOfUsers}`. The identifier is `id` (**NOT**
`workspaceId`). Map the user's `workspaces` (list of workspaceId strings) to workspace
names by joining to the `id` field of each workspace-list item.

## team-list-put

Teams filtered by `member: [userId]` — server-side filtering, confirmed live as of
DISTRO-4472 (2026-05-21). Returns only teams this user belongs to; also accepts an
optional `name: string` filter.

Response: `{results: [{id, name, workspaceId, members, metadata}], total}`. The team
identifier is `id` (**NOT** `teamId`) and includes `workspaceId`.

## Scheduling-link list tools

Query all five link types to enumerate every scheduling link this user is part of:

- `scheduling-link-list-personal-v2` — personal links owned by this user
- `scheduling-link-list-round-robin` — round-robin links this user is part of
- `scheduling-link-list-admin-one-on-one` — admin one-on-one links in the user's workspaces
- `scheduling-link-list-group` — group links in the user's workspaces
- `scheduling-link-list-ownership` — ownership-based links in the user's workspaces

All five accept `userId`. As of DISTRO-4548 (2026-06-16):
`scheduling-link-list-admin-one-on-one`, `scheduling-link-list-group`, and
`scheduling-link-list-ownership` are now live.

**Response envelope:** All five tools return `{links: [...]}` — read scheduling links
from the `links` array.

**Deprecation note:** `scheduling-link-list-personal` (bare-array response) was deprecated
on 2026-07-23 (DO-4340, edge PR #982) in favour of `scheduling-link-list-personal-v2`.
Do not call the deprecated tool — it is excluded from the MCP tool list and will return
a "tool not found" error.

## meeting-export-v2-put

CSV export. Server-side filters (all confirmed live as of DISTRO-4472): `hostIds`,
`assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`.

Response: `{filename, data: "<CSV>"}` — parse the header row for column names.

**Hard limit:** strict **≤ 7-day** window per call. No pagination needed; all matching
records for the window are returned in one response.

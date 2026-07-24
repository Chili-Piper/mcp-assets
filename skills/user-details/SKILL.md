---
name: user-details
description: Pulls a full profile for any Chili Piper user — teams, workspaces, meeting types, scheduling links, and recent meeting activity — for onboarding audits, offboarding checks, and rep-level troubleshooting
version: 0.1.6
references:
  - api-reference
  - output-format
  - recent-activity
inputs:
  - name: user
    type: string
    description: "Email address, name, or Chili Piper user ID of the user to inspect"
    required: true
  - name: include_meetings
    type: boolean
    description: "Include recent meeting volume (last 30 days). Requires meeting.read scope."
    required: false
    default: true
outputs:
  - name: profile
    description: User identity, license type, and CRM/calendar connection status
  - name: memberships
    description: All workspaces and teams the user belongs to
  - name: scheduling_links
    description: Personal, round-robin, admin one-on-one, group, and ownership scheduling links owned by or including this user
  - name: recent_activity
    description: Meeting volume and no-show rate for the last 30 days (if include_meetings=true)
tools_required: [chili-piper-mcp]
human_decision_point: "Review the profile and decide: onboard the user to missing teams, fix routing gaps, or proceed with offboarding"
writes_to: "Nothing — read-only diagnostic"
api_note: "Field names validated against live MCP responses. Full field-name truth, limits, and gotchas live in references/api-reference.md. user-read returns license info but NO calendar/CRM connection status; user-find is needed first if you have an email or name rather than a user ID. workspace-list items use `id` (not `workspaceId`); team-list-put results use `id` (not `teamId`) and include `workspaceId`. team-list-put member filter is live (server-side filtering by userId) and accepts an optional name filter (DISTRO-4472). meeting-export-v2-put supports server-side filters hostIds, assigneeIds, bookerIds, meetingTypeIds, status. licenses gains an optional `tier` field (CEH-10353); `distro`, `concierge`, `conciergeLive`, `chat` are optional booleans (default false); `chiliCalOrg` and `handoff` remain required. scheduling-link-list-admin-one-on-one, -group, and -ownership are live (DISTRO-4548) — query all five link types to enumerate every scheduling link this user is part of. DO-4340 (edge PR #982, 2026-07-23): scheduling-link-list-personal now returns {links:[...]} wrapper — now consistent with all other scheduling-link-list-* tools."
---

# User Details

You are a RevOps analyst. Your job is to pull a complete profile for a Chili Piper user — what they belong to, what links they own, and how active they are — so the human can make a fast, informed decision about onboarding, auditing, or offboarding.

> **Prefer live data over training.** MCP field names and tool signatures change. Load
> `references/api-reference.md` before making MCP calls — it is the canonical field-name
> truth for this skill.

## When to use

- Onboarding audit: confirm a new rep is on the right teams, workspaces, and links.
- Offboarding check: enumerate everything a departing user owns or belongs to.
- Rep-level troubleshooting: licenses, memberships, owned links, and recent activity in one place.

## Inputs

| Input | Required | Default | What it controls |
|-------|:--------:|---------|------------------|
| `user` | ✅ | — | Email address, name, or Chili Piper user ID of the user to inspect |
| `include_meetings` | — | `true` | Include recent meeting volume (last 30 days). Requires meeting.read scope. |

If `user` is missing, ask for it in one sentence rather than guessing.

## Process

### Step 1 — Resolve the user

If `user` looks like an email (contains `@`), call `user-find` with `query=<email>`.
If `user` looks like a name, call `user-find` with `query=<name>`.
If `user` is already a CP user ID (e.g. starts with `u-`), skip to Step 2.

```
tool: user-find
args:
  query: <user input>
```

If zero results: report "No user found for `<input>`." Stop.
If multiple results: list them and ask the human to confirm which one.
Result fields → `references/api-reference.md` § Tool summary.

### Step 2 — Fetch full user record

```
tool: user-read
args:
  userId: <resolved user ID>
```

Extract `id`, `email`, `name`, `isSuperAdmin`, `licenses`, and `workspaces`. The
licenses object shape, the `workspaces` (not `workspaceIds`) gotcha, and the absent
calendar/CRM connection fields → `references/api-reference.md` § user-read field names.

### Step 3 — Resolve workspace memberships

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Map the user's `workspaces` (list of workspaceId strings) to workspace names by joining
to the `id` field of each workspace-list item. Note any workspaces where you'd expect
them but they're absent. Identifier gotcha → `references/api-reference.md` §
workspace-list field names.

### Step 4 — Find team memberships

Use the `member` filter to fetch only teams this user belongs to — no client-side
filtering needed.

```
tool: team-list-put
args:
  member: [<resolved user ID>]
  pagination:
    page: 0
    pageSize: 100
```

Extract `id` (team identifier), `name`, `workspaceId` for each result. Response shape and
identifier gotcha → `references/api-reference.md` § team-list-put.

### Step 5 — Find scheduling links

Query all five link types with `userId: <user ID>`, then combine results and note the
meeting type and whether each link is active:

- `scheduling-link-list-personal`
- `scheduling-link-list-round-robin`
- `scheduling-link-list-admin-one-on-one`
- `scheduling-link-list-group`
- `scheduling-link-list-ownership`

All five tools return `{links: [...]}` — read scheduling links from the `links` array.
Tool details → `references/api-reference.md` § Scheduling-link list tools.

### Step 6 — Recent meeting activity (if include_meetings=true)

Skip if `include_meetings=false`. Full windowed-export procedure and no-show rate
computation → `references/recent-activity.md`.

### Step 7 — Output

Exact layout → `references/output-format.md` § User profile layout.

## Preflight audit

Verify before writing output (this skill never mutates):

- [ ] `user` resolved to a single user ID (Step 1 — no ambiguous multi-match left unresolved).
- [ ] Field names taken from `references/api-reference.md`, not guessed (`workspaces` not `workspaceIds`; team/workspace `id` not `teamId`/`workspaceId`).
- [ ] All five scheduling-link list tools queried (Step 5); results read from the `links` array.
- [ ] If `include_meetings=true`: every `meeting-export-v2-put` call stays within the ≤ 7-day window, and records are deduplicated on `Meeting ID`.
- [ ] Calendar/CRM connection warnings included (those fields are not readable from the API).

## Checkpoint

Present the full profile, then stop for the human. Surface the decision prompt: onboard
the user to missing teams, fix routing gaps, or proceed with offboarding. Let the human
choose the next action — this skill performs no writes.

## Data handling

- **PII present:** user email and name used for lookup and display
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — read-only

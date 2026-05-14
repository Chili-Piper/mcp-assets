---
name: user-details
description: Pulls a full profile for any Chili Piper user — teams, workspaces, meeting types, scheduling links, and recent meeting activity — for onboarding audits, offboarding checks, and rep-level troubleshooting
version: 0.1.0
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
    description: Personal and round-robin scheduling links owned by this user
  - name: recent_activity
    description: Meeting volume and no-show rate for the last 30 days (if include_meetings=true)
tools_required: [chili-piper-mcp]
human_decision_point: "Review the profile and decide: onboard the user to missing teams, fix routing gaps, or proceed with offboarding"
writes_to: "Nothing — read-only diagnostic"
api_note: "user-read returns full license and calendar connection status. user-find is needed first if you have an email or name rather than a user ID."
---

# User Details

You are a RevOps analyst. Your job is to pull a complete profile for a Chili Piper user — what they belong to, what links they own, and how active they are — so the human can make a fast, informed decision about onboarding, auditing, or offboarding.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `name`, `email`, `isSuperAdmin`, `licenses` (object), `workspaces` (array of workspaceId strings), `personalWorkspaceId` |
| `user-read` | Full user record (same fields as user-find result item, unwrapped) → `id`, `name`, `email`, `isSuperAdmin`, `licenses` (object with boolean fields: `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`, `handoff`), `workspaces` (array of workspaceId strings, NOT `workspaceIds`), `personalWorkspaceId`. No `calendarConnected`, `calendarProvider`, or `crmConnected` fields. |
| `workspace-list` | All workspaces → array of `{workspaceId, name, settings}` — items use `workspaceId` (NOT `id`) |
| `team-list-put` | All teams → filter for teams containing this user |
| `scheduling-link-list-personal` | Personal scheduling links owned by this user |
| `scheduling-link-list-round-robin` | Round-robin links this user is part of |
| `meeting-list-put` | Recent meetings assigned to this user |

---

## Step 1 — Resolve the user

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

---

## Step 2 — Fetch full user record

```
tool: user-read
args:
  userId: <resolved user ID>
```

Extract:
- `id`, `email`, `name`
- `isSuperAdmin` — true/false
- `licenses` — object with boolean fields: `distro`, `chiliCalOrg`, `concierge`, `conciergeLive`, `chat`, `handoff`
- `workspaces` — list of workspaceId strings (field is `workspaces`, NOT `workspaceIds`)

Note: `calendarConnected`, `calendarProvider`, and `crmConnected` are **not** present in the `user-read` response. Calendar connection status is not available from user-read — it will surface in routing/availability failures if misconfigured. CRM connection status is likewise not directly readable from this endpoint.

---

## Step 3 — Resolve workspace memberships

Call `workspace-list` to get all workspace names.

```
tool: workspace-list
args:
  page: 0
  pageSize: 100
```

Map the user's `workspaces` (list of workspaceId strings) to workspace names using the `workspaceId` field (not `id`) from the workspace-list response. Note any workspaces where you'd expect them but they're absent.

---

## Step 4 — Find team memberships

```
tool: team-list-put
args:
  page: 0
  pageSize: 100
```

Filter the results for teams where this user appears as a member. Extract `id`, `name`, `workspaceId` for each matching team.

---

## Step 5 — Find scheduling links

```
tool: scheduling-link-list-personal
args:
  userId: <user ID>
```

```
tool: scheduling-link-list-round-robin
args:
  userId: <user ID>
```

Combine results. Note the meeting type and whether the link is active.

---

## Step 6 — Recent meeting activity (if include_meetings=true)

The `meeting-list-put` API has a strict **< 7-day** window per call. Split the 30-day range into chunks of at most 6 days each (5 or 6 calls). For each chunk:

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  pagination:
    page: 0
    pageSize: 200
```

Paginate each chunk if needed: check `hasMore === "Yes"` (string comparison) and increment `pagination.page` until `hasMore === "No"`.

Merge all results from `data.list` across all chunks. Deduplicate on `meetingId`.

Filter for meetings where `assignedUserId === <resolved user ID>`.

Calculate:
- Total meetings (Completed + NoShow)
- No-show count and rate
- Cancelled count

---

## Step 7 — Output format

### User Profile: `<name>` (`<email>`)

**Identity**

| Field | Value |
|-------|-------|
| User ID | |
| Super Admin | true / false |
| Licenses | distro, chiliCalOrg, concierge, … (list enabled ones) |

**Warnings** (if any)
- ⚠ Calendar connection status is not available from the API — check routing/availability failures if scheduling issues are reported
- ⚠ CRM connection status is not available from the API — ownership-based routing failures will surface at routing time

**Workspace memberships**

| Workspace | ID |
|-----------|----|
| ... | |

**Team memberships**

| Team | Workspace |
|------|-----------|
| ... | |

**Scheduling links**

| Link name | Type | Meeting type |
|-----------|------|-------------|
| ... | Personal / Round-robin | |

**Recent activity (last 30 days)**

| Metric | Value |
|--------|-------|
| Meetings (completed + no-show) | |
| No-shows | |
| No-show rate | |
| Cancelled | |

**Human decision point**

*"What would you like to do with this user? I can check missing workspace memberships, look at their routing assignments, or start an offboarding flow."*

---

## Data handling

- **PII present:** user email and name used for lookup and display
- **Storage:** ephemeral — no data persists after the skill completes
- **Writes:** none — read-only

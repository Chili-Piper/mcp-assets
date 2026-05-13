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
| `user-find` | Search by email or name → `id`, `email`, `name`, `role` |
| `user-read` | Full user record → license, calendar provider, calendar connected, CRM connected, `workspaceIds` |
| `workspace-list` | All workspaces → resolve IDs to names |
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
- `role` — Admin, User, or similar
- `licenseType` — which products they're licensed for
- `calendarProvider` — Google / Outlook / None
- `calendarConnected` — true/false
- `crmConnected` — true/false
- `workspaceIds` — list of workspace IDs

Flag if `calendarConnected = false` — this user cannot appear in any scheduling flow.
Flag if `crmConnected = false` — ownership routing will not work for this user.

---

## Step 3 — Resolve workspace memberships

Call `workspace-list` to get all workspace names.

```
tool: workspace-list
args:
  page: 0
  pageSize: 100
```

Map the user's `workspaceIds` to workspace names. Note any workspaces where you'd expect them but they're absent.

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

```
tool: meeting-list-put
args:
  start: <30 days ago, ISO-8601>
  end: <today, ISO-8601>
  page: 0
  pageSize: 200
```

Filter for meetings where `assignee.email` matches the user's email.

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
| Role | |
| License | |
| Calendar | Connected (Google/Outlook) / ⚠ Not connected |
| CRM | Connected / ⚠ Not connected |

**Warnings** (if any)
- ⚠ Calendar not connected — this user will not appear in any scheduling flow
- ⚠ CRM not connected — ownership-based routing will not resolve to this user

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

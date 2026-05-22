---
name: user-offboarding
description: Safely removes a departing Chili Piper rep — surfaces open meetings that need reassignment, removes them from workspaces and teams, and produces an audit trail — making rep offboarding repeatable and zero-leak
version: 0.1.2
inputs:
  - name: user
    type: string
    description: "Email, name, or Chili Piper user ID of the departing rep"
    required: true
  - name: reassign_to
    type: string
    description: "Email, name, or user ID of the rep who should receive open meetings. If omitted, upcoming meetings are flagged for manual reassignment."
    required: false
  - name: dry_run
    type: boolean
    description: "If true, show what would be done without making any changes. Always recommended before first run."
    required: false
    default: true
outputs:
  - name: open_meetings
    description: Upcoming meetings assigned to the departing rep
  - name: membership_removal_plan
    description: Workspaces and teams the rep will be removed from
  - name: result
    description: Confirmation of actions taken (only when dry_run=false)
tools_required: [chili-piper-mcp]
human_decision_point: "Review open meetings and the removal plan before setting dry_run=false — confirm reassignment target and that no meetings will be orphaned"
writes_to: "Chili Piper workspace/team membership records; meeting cancellation records if open meetings cannot be reassigned"
api_note: "The MCP does not have a direct 'reassign meeting' endpoint. Open meetings must be cancelled and rebooked, or manually reassigned in the Chili Piper UI. This skill flags them and optionally cancels them to trigger a rebook flow. As of DISTRO-4472 (2026-05-21): meeting-export-v2-put hostIds and status filters are confirmed live (server-side filtering, no post-fetch scan needed); team-list-put member filter is confirmed live. distribution-list-put now accepts optional name and assignmentType filters. Distribution queue membership still requires manual update in the router builder — the skill flags distributions for human review."
---

# User Offboarding

You are a RevOps offboarding specialist. Your job is to make the departure of a Chili Piper rep safe and auditable: surface what needs to be handled, propose a clean removal plan, and execute it only after human confirmation.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `user-read` | Full profile → workspaceIds, license, calendar status |
| `meeting-export-v2-put` | CSV of meetings — server-side filters (confirmed live as of DISTRO-4472): `hostIds`, `assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`. Returns `{filename, data: "<CSV>"}`. Use `status: ["Active"]` to fetch only upcoming meetings at risk. |
| `workspace-list` | All workspaces → `workspaceId`, `name` |
| `workspace-list-users` | Users in a workspace |
| `workspace-remove-users` | Remove a user from a workspace |
| `team-list-put` | Teams filtered by `member: [userId]` (server-side, confirmed live as of DISTRO-4472) → only teams this user belongs to; also accepts optional `name: string` filter |
| `team-remove-users` | Remove a user from a team |
| `meeting-cancel` | Cancel a meeting (triggers rebook flow if configured) |
| `distribution-list-put` | Distributions — optional filters: `name: string`, `assignmentType` (for flagging — manual removal required) |

---

## Step 1 — Resolve the departing user

```
tool: user-find
args:
  query: <user input>
```

If multiple results: list and ask human to confirm. If zero: stop.

If `reassign_to` is provided, resolve that user too via a second `user-find` call.

---

## Step 2 — Find open meetings

Fetch meetings for the next 30 days in ≤ 6-day chunks using `meeting-export-v2-put` with `hostIds` and `status: ["Active"]`. This returns only this rep's upcoming meetings — no client-side filtering needed.

For each chunk (today→+6d, +6→+12d, +12→+18d, +18→+24d, +24→+30d):

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<departing user's userId>]
  status: ["Active"]
```

Response: `{filename: "...", data: "<CSV>"}`. Parse `data` as CSV — read the header row first to identify columns. No pagination needed per chunk.

Merge records across all chunks. Deduplicate on meetingId. These are the meetings at risk.

---

## Step 3 — Find workspace and team memberships

```
tool: user-read
args:
  userId: <userId>
```

Extract `workspaces` (array of workspace ID strings — the field is `workspaces`, not `workspaceIds`). For each workspace confirm membership via `workspace-list-users`.

```
tool: team-list-put
args:
  member: [<userId>]
  pagination:
    page: 0
    pageSize: 100
```

The `member` filter returns only teams containing this user — no client-side filtering needed.

---

## Step 4 — Find distribution memberships (flag only)

```
tool: distribution-list-put
args:
  workspaceId: <each workspace id>
```

Filter distributions where this user appears as a member. Optionally use the `name` filter if looking for a specific distribution by name. These cannot be updated via MCP — flag them for manual removal in the router builder.

---

## Step 5 — Present the offboarding plan (always shown before writes)

### Offboarding Plan: `<name>` (`<email>`)

**Open meetings (`N` upcoming)**

| Date | Guest | Meeting type | Action |
|------|-------|-------------|--------|
| ... | | | Reassign to `<reassign_to>` / ⚠ Flag for manual reassignment |

**Workspace removals**

| Workspace | Action |
|-----------|--------|
| ... | REMOVE |

**Team removals**

| Team | Workspace | Action |
|------|-----------|--------|
| ... | | REMOVE |

**Distribution memberships (manual action required)**

> These distributions must be updated manually in the Chili Piper router builder — MCP cannot modify distribution membership directly:

| Distribution | Workspace | Action needed |
|-------------|-----------|---------------|
| ... | | Remove from distribution queue |

**Not handled by this skill (manual):**
- Ownership of existing Salesforce leads/contacts — re-assign in Salesforce
- Personal scheduling links — deactivate or transfer in Chili Piper admin
- Meeting types — archive if not needed by other reps
- Router rule ownership conditions — audit routers that reference this user explicitly

---

## Step 6 — Execute (only if dry_run=false)

If `dry_run=true`: stop here and ask: *"Does this plan look right? Set `dry_run=false` to apply. Reminder: distribution queue removal and scheduling link deactivation require manual steps in the Chili Piper UI."*

**Cancel open meetings** (if no reassign_to, or if meeting API does not support reassignment):

For each open meeting:
```
tool: meeting-cancel
args:
  meetingId: <meeting id>
```

Note: cancellation may trigger a rebook notification to the guest depending on router configuration.

**Remove from workspaces:**
```
tool: workspace-remove-users
args:
  workspaceId: <id>
  userIds: [<userId>]
```

**Remove from teams:**
```
tool: team-remove-users
args:
  teamId: <id>
  userIds: [<userId>]
```

---

## Step 7 — Confirm and produce audit trail

Re-check memberships after removal. Report any that failed.

### Offboarding Complete: `<name>`

| Action | Count | Status |
|--------|-------|--------|
| Open meetings cancelled/flagged | N | ✓ / ⚠ |
| Workspaces removed | N | ✓ |
| Teams removed | N | ✓ |
| Distributions requiring manual removal | N | ⚠ Manual |

**Human decision point**

*"Manual steps still required: distribution queue removal and scheduling link deactivation in the CP admin UI. Should I run `/routing-audit` to check whether the rep's absence creates any routing gaps?"*

---

## Data handling

- **PII present:** user email, guest emails in meeting list
- **Storage:** ephemeral — no data persists; keep a copy of the audit output if needed
- **Writes:** workspace/team removals; meeting cancellations (if dry_run=false)

# User Offboarding — Procedure

The detailed, step-by-step offboarding procedure. The SKILL.md Process section routes
here for the full mechanics of each step. Tool argument shapes, field names, and limits
live in `api-reference.md`; the plan/audit output layout lives in `output-format.md`.

---

## Resolve the departing user

```
tool: user-find
args:
  query: <user input>
```

If multiple results: list and ask the human to confirm. If zero: stop.

If `reassign_to` is provided, resolve that user too via a second `user-find` call.

---

## Find open meetings

Fetch meetings for the next 30 days in ≤ 6-day chunks using `meeting-export-v2-put` with
`hostIds` and `status: ["Active"]`. This returns only this rep's upcoming meetings — no
client-side filtering needed.

For each chunk (today→+6d, +6→+12d, +12→+18d, +18→+24d, +24→+30d):

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<departing user's userId>]
  status: ["Active"]
```

Response: `{filename: "...", data: "<CSV>"}`. Parse `data` as CSV — read the header row
first to identify columns. No pagination needed per chunk.

Merge records across all chunks. Deduplicate on the `Meeting ID` column. These are the
meetings at risk.

---

## Find workspace and team memberships

```
tool: user-read
args:
  userId: <userId>
```

Extract `workspaces` (array of workspace ID strings — the field is `workspaces`, not
`workspaceIds`). For each workspace confirm membership via `workspace-list-users`.

```
tool: team-list-put
args:
  member: [<userId>]
  pagination:
    page: 0
    pageSize: 100
```

The `member` filter returns only teams containing this user — no client-side filtering
needed.

---

## Find distribution memberships (flag only)

```
tool: distribution-list-put
args:
  workspaceIds: [<workspace id>]
```

The response is `{results: [...], total, page, pageSize}` — iterate `results` (CEH-11548).
Flag distributions where this user's `userId` appears
in `published.weights[]` or in `state.userStates[]` with `type: "Active"`. Optionally use
the `name` filter to look for a specific distribution. Distribution membership cannot be
updated via MCP — flag these for manual removal in the router builder.

---

## Execute (only if dry_run=false)

If `dry_run=true`: stop at the plan and ask: *"Does this plan look right? Set
`dry_run=false` to apply. Reminder: distribution queue removal and scheduling link
deactivation require manual steps in the Chili Piper UI."*

**Cancel open meetings** (if no reassign_to, or if meeting API does not support
reassignment):

For each open meeting:
```
tool: meeting-cancel
args:
  meetingId: <meeting id>
```

Note: cancellation may trigger a rebook notification to the guest depending on router
configuration.

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

> **Optional — retire empty teams:** If removing this user leaves a team with zero members
> and the team should be retired (not just emptied), you can delete it with `team-delete`.
> Ask the human to confirm before doing so — deletion is irreversible and will fail if any
> active distribution still references the team.
>
> ```
> tool: team-delete
> args:
>   teamId: <teamId>
> ```

---

## Confirm and produce audit trail

Re-check memberships after removal. Report any that failed. Render the completion audit
trail per `output-format.md` § Completion audit trail.

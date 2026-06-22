# Org Meeting Snapshot — API Reference

Full field names, status values, hard limits, and known gotchas for the Chili Piper MCP tools used by this skill.

> Field names and response envelopes are validated against **live MCP responses**. The MCP tools' own text descriptions are often wrong — use this file, not intuition or the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `meeting-list-put` | Meetings in a window < 7 days → response: `{data: {list: [{meetingId, meetingStatus, dateTime: {start, end}, attendees, hostId, hostEmail, hostName, workspaceId}]}, hasMore: "Yes"\|"No"}`. Accepts a `status` filter (confirmed live as of DISTRO-4472). |
| `workspace-list` | All workspaces → array of `{id, name, nrOfUsers}` — the identifier is `id` (NOT `workspaceId`) — join `meeting.workspaceId` to `workspace.id` to get the workspace name |

---

## Hard API limits

| Tool | Limit |
|------|-------|
| `meeting-list-put` | **strict 7-day maximum window** per call — chunk `date_range` into ≤6-day slices (each chunk must be strictly less than 7 days). For 30-day ranges the skill makes multiple paginated calls. |

---

## meeting-list-put — pagination and chunking

```
tool: meeting-list-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  status: ["Completed", "NoShow", "Active"]   # always include Active — past-Active meetings count in denominator; Canceled excluded server-side
  workspaceIds: [<resolved workspaceId>]          # optional: only if a workspace filter is desired
  pagination:
    page: 0
    pageSize: 200
```

- Each chunk must be strictly less than 7 days (use at most 6-day chunks).
- Results are in `data.list`.
- Paginate each chunk: check `hasMore === "Yes"` (string comparison) and increment `pagination.page` until `hasMore === "No"`.
- Merge all results from `data.list` across all chunks, deduplicate on `meetingId`.
- Pass `workspaceIds` for server-side workspace scoping.

### The status filter

The status filter on `meeting-list-put` is confirmed live as of DISTRO-4472 (2026-05-21).

Always include `"Active"` in the status filter. Past-Active meetings (start time in the past) must be included in the no-show rate denominator — omitting them inflates the apparent no-show rate. Future-Active meetings are separated client-side and shown as "Upcoming" in the summary.

For historical analysis (entire date range in the past), pass `status: ["Completed","NoShow","Canceled"]` to skip Active/upcoming meetings and reduce data returned.

---

## Meeting status values (`meetingStatus`)

| Value | Meaning | Treatment in rates |
|-------|---------|--------------------|
| `Completed` | explicitly marked as completed | numerator (completed) + denominator |
| `NoShow` | explicitly marked as no-show | no-show numerator + denominator |
| `Canceled` | meeting was cancelled (single-`l` spelling) | **exclude from no-show rate entirely** |
| `Active` (start in future) | upcoming | exclude from rate — shown as "Upcoming" |
| `Active` (start in past) | meeting likely happened but never formally closed; treat as informally completed | include in denominator but NOT the no-show numerator |

**Important:** meetings not explicitly closed stay `Active` indefinitely. Excluding past-`Active` from the denominator inflates the apparent no-show rate. Always split `Active` on start time vs. now.

---

## workspace-list — resolving workspace names

```
tool: workspace-list
args:
  pagination:
    page: 0
    pageSize: 100
```

Build a map of `id → name` from each workspace-list item (the workspace identifier is `id`), then join each meeting's `workspaceId` to that `id` to get the workspace name.

Note: meeting items from `meeting-list-put` include a `workspaceId` field — use it directly for grouping.

---

## Grouping fields by dimension

| `group_by` | Group key (on each meeting item) | Name source |
|-----------|----------------------------------|-------------|
| `workspace` | `workspaceId` | resolve via `workspace-list` (`id → name`) |
| `rep` | `hostId` | `hostName` / `hostEmail` already present on each meeting — no separate lookup needed |
| `status` | `meetingStatus` | n/a (simple count of each status) |

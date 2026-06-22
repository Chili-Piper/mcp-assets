# User Meetings — API Reference

Tool field names, CSV columns, status values, and hard limits for the Chili Piper MCP
tools this skill uses.

> Field names and the export CSV schema are validated against **live MCP responses**.
> The MCP tools' own text descriptions are often wrong — use this file, not intuition or
> the tool blurb.

---

## Tools and what they return

| Tool | What it returns |
|------|----------------|
| `user-find` | Search by email or name → `id`, `email`, `name` |
| `meeting-export-v2-put` | CSV export with server-side filters (all confirmed live as of DISTRO-4472): `hostIds`, `assigneeIds`, `bookerIds`, `meetingTypeIds`, `status`. Response: `{filename, data: "<CSV>"}`. Parse `data` as CSV; read header row to identify columns. No pagination — all matching records in one response per chunk. |
| `workspace-list` | All workspaces — needed to resolve workspace ID to display name |

---

## meeting-export-v2-put CSV columns

Columns (verified live): `Title`, `When` (scheduled start), `End`, `Meeting Type`,
`Status`, `Source`, `Host`, `Assignee`, `Booker`, `Primary Guest`, UTM columns,
`CRM Event Id`, `Meeting ID`, `Booked At`.

Status values: `Active` | `Canceled` | `NoShow` | `Completed`.

**`Meeting ID` and `Booked At` columns were added in DISTRO-4483 (production
2026-05-29).** Dedupe on the `Meeting ID` column and populate the Booked column from the
`Booked At` column. Lead time = `When` − `Booked At`.

---

## Hard API limits

**`meeting-export-v2-put` accepts at most a 7-day window per call.** For a 30-day range
issue multiple sequential calls and merge the results. Each chunk must be strictly ≤ 6
days. No pagination is needed per chunk — all matching records come back in one response.

Suggested slicing:
- `last-7-days` → one call
- `last-30-days` → 5 calls (days 0–6, 7–13, 14–20, 21–27, 28–30)
- `YYYY-MM-DD:YYYY-MM-DD` → calculate the slices needed

Merge records across all chunks. Deduplicate on the `Meeting ID` column.

---

## meeting-export-v2-put call shape

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<resolved userId>]
  status: ["Active", "Completed", "NoShow", "Canceled"]
  workspaceIds: [<resolved workspaceId>]   # only if workspace was specified
```

Response: `{filename, data: "<CSV>"}`. Parse `data` as CSV — read the header row first to
identify columns.

---

## Workspace resolution

Always call `workspace-list` at the start. Build a `workspaceId → name` map. Never invent
or guess workspace names.

---

## Local timezone detection

```bash
cat /etc/timezone 2>/dev/null || readlink /etc/localtime 2>/dev/null | sed 's|.*zoneinfo/||'
```

Store the IANA result (e.g. `America/Chicago`). Convert **all timestamps** in output to
this timezone. If the command fails, fall back to `date +%z` and note the UTC offset
used.

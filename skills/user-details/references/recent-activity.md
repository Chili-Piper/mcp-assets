# user-details — recent meeting activity

Procedure for computing the last-30-day meeting volume and no-show rate. Runs only when
`include_meetings=true`. Tool field names → `api-reference.md` § meeting-export-v2-put.

## Windowed export

`meeting-export-v2-put` has a strict **≤ 7-day** window per call. Split the 30-day range
into chunks of at most 6 days each (5 or 6 calls). For each chunk:

```
tool: meeting-export-v2-put
args:
  start: <chunk start, ISO-8601>
  end: <chunk end, ISO-8601>
  hostIds: [<resolved user ID>]
  status: ["Active", "Completed", "NoShow", "Canceled"]
```

Response: `{filename: "...", data: "<CSV>"}`. Parse `data` as CSV — read the header row
first to identify column names. No pagination needed; all matching records for the chunk
are returned in one response.

Merge records across all chunks. Deduplicate on the `Meeting ID` column.

## No-show rate computation

Calculate from the status column. **Note on `Active`:** meetings not explicitly closed
stay `Active` even after the meeting time passes. Split `Active` on the `When` column vs.
now:

- `Active` + start in future → Upcoming (exclude from rate)
- `Active` + start in past → informally completed (include in denominator, not numerator)

Counts:

- Total in rate: Completed + NoShow + past-Active
- No-show rate: `NoShow / (Completed + NoShow + past-Active)`
- Cancelled count (excluded from rate)
- Surface caveat if past-Active is significant

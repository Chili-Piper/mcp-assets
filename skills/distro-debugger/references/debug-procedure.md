# Distribution Debugger — Debug Procedure

The full search, fetch, stage-walk, and status-based diagnosis decision tree. Field names
and limits → `references/api-reference.md`.

---

## Search by Salesforce ID

Convert `date_range` to ISO8601:

- `today` → `from`: start of today UTC, `to`: now
- `last-7-days` → `from`: 7 days ago UTC, `to`: now
- `YYYY-MM-DD:YYYY-MM-DD` → `from`: first date T00:00:00Z, `to`: second date T23:59:59Z

Resolve workspace name to ID via `workspace-list` if a name was provided. Search distro
logs using the Salesforce ID as a text search:

```
tool: distro-logs
args:
  workspaceId: <workspace id>
  page: 0
  pageSize: 20
body:
  search: <salesforce_id>
  from: <ISO8601 start>
  to: <ISO8601 end>
```

- Multiple results: present a summary table (record name, status, triggeredAt, assignee) and ask which to inspect.
- Exactly one result: proceed directly with that entry's `logId` and `routerId`.
- No results: report "No distribution log found for `<salesforce_id>` in workspace `<workspace>` for the requested period."

---

## Search by record name

First resolve the name to a Salesforce ID:

```
tool: salesforce-query
args:
  query: "SELECT Id, Name, Email FROM Lead WHERE Name = '<record_name>' LIMIT 5"
```

If no Lead match, try Contact:

```
tool: salesforce-query
args:
  query: "SELECT Id, Name, Email FROM Contact WHERE Name = '<record_name>' LIMIT 5"
```

- Multiple Salesforce records returned: present them and ask the human to confirm which one.
- No Salesforce record found: report "No Lead or Contact found matching `<record_name>`. Check spelling or use `salesforce_id` directly."

Once you have the Salesforce ID, search distro logs using both the ID and name:

```
tool: distro-logs
args:
  workspaceId: <workspace id>
  page: 0
  pageSize: 20
body:
  search: <salesforce_id or record_name>
  from: <ISO8601 start>
  to: <ISO8601 end>
```

Handle multiple or zero results the same as "Search by Salesforce ID".

---

## Fetch the full evaluation trace

```
tool: distro-log-get
args:
  logId: <log_id>
  routerId: <router_id>
```

If not found: "Log entry `<log_id>` not found for router `<router_id>`. Verify the IDs
are correct and that the log is within the retention window."

Extract the trace fields → `references/api-reference.md` § Evaluation trace fields.

---

## Enrich with router context

Fetch the router's name and check its activation state:

```
tool: distro-list-routers
args:
  workspaceId: <workspace id>
```

Match `router_id` against `id` to surface the human-readable router name. Capture `status`
and check it immediately (status values → `references/api-reference.md` § Router status values):

- `Active` → router is live; proceed to stage walk.
- `Inactive` → **stop and flag as root cause**: the router is not active and is not routing records. Routers created via MCP/API start as Inactive by default and require explicit activation. Report this as the diagnosis — the fix is to activate the router via `distro-router-activate`.
- `Activating` / `Deactivating` → transient state; inform the human that routing may be temporarily unavailable and to retry in a few minutes.
- `Error{message}` → escalate to engineering with the router ID and the error message.

If the router is not found in `distro-list-routers` (e.g., it was deleted or is from an older pre-CRUD architecture), fall back to `distribution-list-put` to resolve the display name:

```
tool: distribution-list-put
args:
  workspaceId: <workspace id>
```

Match `router_id` against `distributionId` to surface the human-readable router name.

---

## Walk the evaluation stages

For each stage in `stages[]`, in order:

1. Note whether `matched` is true or false
2. For each condition in `conditions[]`:
   - `passed = false` → failure point: record `field`, `operator`, `expected`, `actual`
   - `passed = true` → note briefly
3. If a stage `matched = true`: this is the firing rule — note `assignee`
4. If no stage matched: record hit catch-all or was dropped

| Stage | Rule | Matched | First failing condition |
|-------|------|---------|------------------------|
| 1 | … | ✅ / ❌ | field `X` was `Y`, expected `Z` |

---

## Diagnose by status

**`Finished` or `SlaFinished`:**
> Record was assigned to `<assignee>` via `<distributionMethod>`.
> If the assignment seems wrong: check whether the correct rule fired, or whether enrichment altered a key field before evaluation. `SlaFinished` means the record waited through an SLA window first — check if the delay was expected.

**`NotMatchedEntryRule`:**
> No entry rule matched this record. Walk through each stage's failing conditions.
> Common causes: field is null/empty, CRM field name mismatch, enrichment failed to populate a required field.
> Fix: identify the first failing condition and either update the rule or correct the field mapping.

**`NotRouted`:**
> The record entered the router and matched an entry rule, but no assignment was made.
> Check `distributionMethod`: `NoUserAvailable` means all reps were at capacity; `NoDistribution` means the matched rule has no distribution configured.
> Fix: add a distribution to the rule, or adjust rep capping/availability.

**`NotTriggered`:**
> The router flow did not fire. First check the router `status` from Step 3:
> - **`Inactive`** → root cause: the router is not active. Routers created via MCP/API start as Inactive by default and must be explicitly activated via `distro-router-activate`. Fix: activate the router.
> - **`Activating` / `Deactivating`** → transient; ask the human to retry after the state transition completes.
> - **`Error{message}`** → escalate to Chili Piper support with the router ID and error message.
> If the router is `Active`, check the router trigger configuration against the record's source, object type, or entry conditions.

**`DelayInProgress` / `WorkingHours` / `SlaInProgress`:**
> The record is still in-flight — it hasn't failed, it's waiting.
> Inform the human: routing is not complete. Come back after the delay/SLA window or working hours resume.

**`Error`:**
> Technical error. Escalate: provide `router_id`, `log_id`, `triggeredAt` to Chili Piper support.

**distributionMethod context for `Finished`:**

- `FallbackTeam` / `FallbackUser`: the primary distribution had no available rep — verify rep capacity and working hours
- `NoUserAvailable`: all reps at capacity — increase capping or add reps
- `FromOwnershipArs` / `DuplicateMatchOwner`: assigned by CRM ownership — verify this is the intended behavior for this rule

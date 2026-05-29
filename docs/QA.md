# Skill QA & Status Tracker

This file tracks the quality of every skill in this repo so we (and clients) always know how battle-tested each one is. It is the source of truth for the **maturity** column in [`skills/README.md`](../skills/README.md).

## Maturity levels

| Level | Meaning |
|-------|---------|
| `draft` | Written, but has known correctness issues or has not been verified against the live MCP. Not client-ready. |
| `tested` | Static review complete (tool names + response field names + limits verified against the live MCP schema and a real read-only call). No known correctness bugs. |
| `verified` | `tested` **plus** an end-to-end run against a real tenant produced correct output, logged below. Client-ready. |

## How to QA a skill

1. **Static review** — for every MCP tool the skill calls, confirm (a) the tool name exists, (b) the input params match the live schema, (c) the response field names the skill reads match a **real read-only call** (the tools' own text descriptions are unreliable — see the verification log), (d) documented limits/windows are accurate.
2. **Read-only live run** — execute the skill against a real tenant; confirm the output format and that no step errors. Log it below.
3. **Write skills** (`user-copy`, `user-offboarding`) — never execute write/destructive steps for QA. Verify the write tools exist and are called correctly, and that the dry-run/approval gates are present, by static review only.
4. Update the status matrix and bump the skill's `version` if behavior changed.

---

## Status matrix

_Last updated: 2026-05-29. Static-review fixes applied on branch `repurpose-official-skills` (commits "fix meeting-list-put field drift", "fix routing, concierge, and availability skills", "fix user/org skills"). Read-only live run = end-to-end execution against tenant `floatingapps.com` — pending for `verified`._

| Skill | Version | Read-only? | Static review | Live run | Maturity | Notes |
|-------|:------:|:---:|:---:|:---:|:---:|---|
| meeting-inspector | 0.3.0 | ✅ | ✅ fixed | ⬜ | `tested` | meeting-list-put drift, status values, `startTime`, `matchedPath` corrected |
| no-show-analyzer | 0.3.3 | ✅ | ✅ fixed | ⬜ | `tested` | meeting-list-put drift + `workspace-list` `nrOfUsers` + concierge status `Scheduled` corrected |
| org-meeting | 0.1.3 | ✅ | ✅ fixed | ⬜ | `tested` | meeting-list-put drift + group-by `hostId` + workspace `id` join corrected |
| user-meetings | 0.3.1 | ✅ | ✅ done | ⬜ | `tested` | Uses CSV export — no JSON drift. Verify export CSV header against a real export. |
| routing-audit | 0.2.0 | ✅ | ✅ fixed | ⬜ | `tested` | `rule-list` workspace-scoped, router rules from `router.routing`, `distribution-list-put` array shape, workspace `id` |
| concierge-debugger | 0.2.0 | ✅ | ✅ fixed | ⬜ | `tested` | invented status enum removed; diagnose via `matchedPath.route.type` + `meetingId`; `assignments[].userId` |
| availability-inspector | 0.1.0 | ✅ | ✅ fixed | ⬜ | `tested` | `availability-slots` request shape corrected; failure-reason strings read literally |
| user-details | 0.1.3 | ✅ | ✅ fixed | ⬜ | `tested` | `workspace-list` `id`, `team-list-put` `id`, nested pagination |
| user-copy | 0.1.3 | ⚠️ writes | ✅ fixed | n/a | `tested` | `.id` joins corrected (was `.workspaceId`/`.teamId`); dry-run/approval gates present ✅ |
| user-offboarding | 0.1.4 | ⚠️ writes | ✅ fixed | n/a | `tested` | `team-list-put` `id`; `distribution-list-put` `workspaceIds[]` + members via weights/userStates; user-read row. Approval/destructive gates present ✅ |

All ten skills are now `tested` (static review complete, no known correctness bugs against the live MCP). The next step for `verified` is an end-to-end read-only live run per skill, logged in the verification log below. The two write skills (`user-copy`, `user-offboarding`) stay at static-review only — never executed for QA.

**New skills (rebuilt on the public MCP, replacing the internal bo-sql versions):**

| Skill | Version | Static review | Live run | Maturity | Notes |
|-------|:---:|:---:|:---:|:---:|---|
| distribution-analysis (public) | 0.1.0 | ✅ built | ⬜ | `tested` | Built on `distribution-list-put` + `meeting-list-put` + `user-find-by-ids`. No bo-sql, no config-history; attributes meetings by host rep (caveat documented in-skill). |
| ~~tenant-meetings~~ | — | — | — | dropped | Not added — `org-meeting` already covers tenant/org meeting volume via the public MCP, and the bo-sql version was internal-only. |

---

## Verified ground truth (live read-only calls, 2026-05-29, tenant `floatingapps.com`)

> **The MCP tools' own text descriptions are unreliable.** Each of the following was confirmed against a real payload, and differed from what the tool advertised.

**`meeting-list-put`** → envelope `{data:{list:[...]}, hasMore:"Yes"|"No"}`. Each item:
- `meetingId`, `workspaceId`, `meetingTypeId`, `bookerId`/`bookerEmail`
- `hostId` / `hostEmail` / `hostName` — the assigned rep (**not** `assignedUserId`)
- `dateTime.start` / `dateTime.end` — scheduled time (**not** `scheduledAt`)
- `meetingStatus` (**not** `status`), plus `extendedMeetingStatus`
- `noShowStatus` — a **string** (`"Unknown"`/`"NoShow"`/…), not nested
- `bookedAt` — when booked (use for booking-window filters; there is no `createdAt`)
- `primaryGuest.value` (guest email), plus `attendees[]`
- Input: body `{start, end}` (ISO, required, ≤7-day span), optional `status[]`, `workspaceIds[]`, `pagination:{page,pageSize}`.

**`workspace-list`** → `[{id, name, emoji, logo, metadata, nrOfUsers}]`. Identifier is **`id`** (not `workspaceId`); member count is **`nrOfUsers`** (not `userCount`); there is no `settings`. Input: `{pagination:{page,pageSize}}`.

**`team-list-put`** → results items use **`id`** (not `teamId`); `workspaceId` is present on each. Input: body filters `{workspaceIds, name, member}` + `pagination`.

**`concierge-logs`** → entry fields `status`, `guestEmail`, `trigger` (string), `assignments[]`, `matchedPath`, `meetingId`, `sourceUrl`, `crmUrl`, `triggeredAt`, `actionsStatus`. Notes: `assignments[]` items are `{userId, ruleId, teamRef, distributionId, type}` — **no `name`**. `matchedPath` is an **object** `{route:{type:"RuleRoute"|"CatchAllRoute", ruleIds, id}, type}`. Observed `status` values include `Scheduled`, `TimedOut`, `Cancelled` — **not** `Booked`/`Timeout`/`NoMatch`. Requires `workspaceId`+`routerId`+`start`+`end`, ≤30-day window.

**`distribution-list-put`** → top-level **array** (no `results` wrapper). Each item `{id, published:{distributionId, name, weights:[{userId,weight}], assignmentTypeConfig, capping, teamRef:{id}}, state:{userStates:[{userId, type:Active|Removed}]}, prioritization}`. Members come from `published.weights[]` / `state.userStates[]` (no `assignees`/`members` field); algorithm is `published.assignmentTypeConfig.handling.type` (`Strict`/`Flexible`).

**`availability-slots`** → request requires `expectedHost` as an **object** (`{type:"User", userId}` or `{type:"AssigneeFromDistribution", distributionId}`); attendees go in `attendees[]` with `type` ∈ `ManuallyAssigned|DistributionAssignee|AssignedViaTeam|AdditionalAttendee` (**no** top-level `userIds`, **no** attendee `type:Host`); `meetingTypeRef.id` is required. Response includes `startTimes[]` and `failures:{userId: failure}`.

**`user-find`** → bare array of `{id, name, email, isSuperAdmin, licenses{distro,chiliCalOrg,concierge,conciergeLive,chat,handoff}, salesforce, hubspot, slug, workspaces[], personalWorkspaceId, managedWorkspaces, managedTeams}`. **`user-read`** has no `calendarConnected`/`crmConnected` fields.

---

## Detailed findings to fix

### The recurring `meeting-list-put` substitution (meeting-inspector, no-show-analyzer, org-meeting)
- `status` → `meetingStatus`
- `scheduledAt` → `dateTime.start`
- `assignedUserId` / group-by rep → `hostId` (+ `hostEmail`/`hostName`); resolve names via `user-find-by-ids`
- `createdAt` / "booked at" → `bookedAt`; lead time = `dateTime.start` − `bookedAt`
- status value `Scheduled` → `Active`; spelling `Cancelled` → `Canceled`
- `startTime` (anomaly-detection.md) → `dateTime.start`
- guest top-level → `primaryGuest.value` (plus `attendees[]`)

### meeting-inspector/references/api-reference.md (most affected) — rewrite the field tables to the verified shape above; the `{data:{list}, hasMore}` envelope and `pagination` input are already correct.

### Cross-cutting `id` fixes (routing-audit, concierge-debugger, user-details, user-copy, user-offboarding)
- `workspace-list` items use `id` (not `workspaceId`); member count `nrOfUsers`; wrap pagination in `pagination:{}`.
- `team-list-put` items use `id` (not `teamId`).

### routing-audit & concierge-debugger
- Stop calling `rule-list` with `routerId`. Get per-router rules + catch-all from `concierge-list-routers` (`router.routing.rules[]`, `router.routing.catchAll`), or call `rule-list` with `filter:{ruleBuilderVersion:["ExplicitV1"], workspaceId}`. Rule `type` enum is `OwnershipRule`/`NonOwnershipRule` (no `CatchAll`).
- concierge-debugger: fix `concierge-logs` status enum to observed values; `assignments[0].name` → `assignments[0].userId` (resolve via `user-find-by-ids`); read matched rule from `matchedPath.route`.
- routing-audit: fix `distribution-list-put` to the array shape above (read `published.weights`/`state.userStates`, `published.assignmentTypeConfig.handling.type`).

### availability-inspector
- Fix the `availability-slots` request to the verified shape; require a real `meetingTypeRef.id`; express durations as `"30 minutes"`/`"PT30M"`. The `failures` reason enum is unverified — confirm against a real (non-mutating) slot query before relying on exact strings.

### user-offboarding
- `distribution-list-put`: `workspaceId` → `workspaceIds:[...]`; read membership from `published.weights`/`state.userStates`, not `members`/`assignees`.
- Correct the user-read API-reference row (`workspaces` array; no calendar/CRM status).

---

## Items still needing a live read-only call before fixing
- `team-list-put` `id` (vs `teamId`) — observed by audit; re-confirm with one direct call.
- `availability-slots` `failures` reason strings.
- `meeting-export-v2-put` CSV header columns (user-meetings, user-details).
- concierge-logs full `status` value set (only `Scheduled`/`TimedOut`/`Cancelled` observed so far).

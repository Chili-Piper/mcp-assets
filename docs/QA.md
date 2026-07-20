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
3. **Write skills** (`user-copy`, `user-offboarding`, `meeting-type-management`, `distro-router-configuration`, `handoff-router-configuration`, `concierge-router-configuration`) — never execute write/destructive steps for QA. Verify the write tools exist and are called correctly, and that the dry-run/approval gates are present, by static review only.
4. Update the status matrix and bump the skill's `version` if behavior changed.

---

## Status matrix

_Last updated: 2026-07-02. Backfilled the missing `distro-debugger` row (shipped in #35 after the 2026-05-29 QA run — enters at `draft` until a static review + live run are logged). Prior update 2026-05-29: static-review fixes applied across the skills, then an end-to-end read-only live run against a connected test tenant (9/9 read-only skills PASS). Write skills stay at static-review only — never executed for QA._

| Skill | Version | Read-only? | Static review | Live run | Maturity | Notes |
|-------|:------:|:---:|:---:|:---:|:---:|---|
| meeting-inspector | 0.3.0 | ✅ | ✅ fixed | ✅ pass | `verified` | meeting-list-put + meeting-get + concierge shapes confirmed live |
| no-show-analyzer | 0.3.3 | ✅ | ✅ fixed | ✅ pass | `verified` | `noShowStatus` + concierge `trigger`/`matchedPath`/`meetingId` confirmed |
| org-meeting | 0.1.3 | ✅ | ✅ fixed | ✅ pass | `verified` | meeting `workspaceId` + workspace `id` join + `user-find-by-ids` confirmed |
| user-meetings | 0.4.0 | ✅ | ✅ done | ✅ pass | `verified` | CSV export confirmed; real headers are `Meeting ID` + `Booked At` (DISTRO-4483) |
| routing-audit | 0.2.0 | ✅ | ✅ fixed | ✅ pass | `verified` | rule-list (702 rules), router.routing, distribution-list-put array all confirmed |
| concierge-debugger | 0.2.0 | ✅ | ✅ fixed | ✅ pass | `verified` | `matchedPath.route.{type,ruleIds}` + `assignments[].userId` confirmed |
| availability-inspector | 0.1.0 | ✅ | ✅ fixed | ✅ pass | `verified` | corrected request returned 12 live slots; `{startTimes, failures}` confirmed |
| user-details | 0.1.3 | ✅ | ✅ fixed | ✅ pass | `verified` | user-read (no calendar/CRM), `team-list-put` `id`, scheduling-link shapes confirmed |
| distribution-analysis | 0.1.0 | ✅ | ✅ built | ✅ pass | `verified` | distribution-list-put array (weights/userStates/handling) + meeting attribution confirmed |
| distro-debugger | 0.3.1 | ✅ | ⏳ pending | ⏳ pending | `draft` | Shipped in #35 without a QA log entry — static review + live run needed to promote |
| chat-conversation-inspector | 0.1.0 | ✅ | ⏳ pending | ⏳ pending | `draft` | New (issue #41) — field names taken from the live Edge spec 2026-07-02; needs a real read-only call + live run |
| user-copy | 0.1.3 | ⚠️ writes | ✅ fixed | n/a | `tested` | `.id` joins corrected; dry-run/approval gates present ✅ (write skill — not live-run) |
| user-offboarding | 0.1.4 | ⚠️ writes | ✅ fixed | n/a | `tested` | `team-list-put` `id`; `distribution-list-put` `workspaceIds[]` + weights/userStates; approval/destructive gates present ✅ (write skill — not live-run) |
| meeting-type-management | 0.1.0 | ⚠️ writes | ⏳ pending | n/a | `draft` | New (issue #34) — schema from live Edge spec 2026-07-02; dry-run/approval gates present; needs static review via real read-only calls |
| distro-router-configuration | 0.1.0 | ⚠️ writes | ⏳ pending | n/a | `draft` | New (issue #44) — DISTRO-4581 lifecycle encoded (Inactive create, async deactivate, Inactive-only delete); dry-run/approval gates present |
| handoff-router-configuration | 0.1.0 | ⚠️ writes | ⏳ pending | n/a | `draft` | New (issue #42) — always-live model (no status/activate); representability gate; dry-run/approval gates present |
| concierge-router-configuration | 0.1.0 | ⚠️ writes | ⏳ pending | n/a | `draft` | New (issue #38) — always-live model; representability gate; write complement to concierge-debugger/routing-audit |

9 of the 11 read-only skills are `verified` (static review + a passing end-to-end read-only run against a real tenant); `distro-debugger` and `chat-conversation-inspector` are `draft` pending their first logged QA pass. The 2 write skills (`user-copy`, `user-offboarding`) are `tested` (static review complete; intentionally never executed for QA).

> `tenant-meetings` was **not** added — `org-meeting` already covers tenant/org meeting volume via the public MCP, and the earlier internal version was internal-only.

## Verification log

**2026-05-29 — read-only live run (connected test tenant), 9/9 PASS.** Window 2026-05-22→05-28. Exercised each skill's core MCP calls; all corrected response shapes held. Highlights:
- `meeting-export-v2-put` CSV header confirmed; the new columns are **`Meeting ID`** and **`Booked At`** (DISTRO-4483) — title-case with spaces, not `meetingId`/`bookedAt`. Skills updated to the exact header names.
- `availability-slots` with the corrected request shape returned live slots; `meetingTypeRef.{meetingTypeId,timestamp}` on a meeting item is the easiest source for the required `{id,timestamp}`.
- `concierge-logs` `matchedPath.route.type` has more values than `RuleRoute`/`CatchAllRoute` in live data (e.g. `SpamCheckRoute`); `matchedPath.type` varies (`RoutePathLive`/`RoutePathWithCalendar`/`RoutePathWithoutCalendar`). routing-audit + concierge-debugger updated to treat unknown route types as fall-through.

---

## Verified ground truth (live read-only calls, 2026-05-29, connected test tenant)

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

## Recent API changes to track

Endpoint changes that affect these skills — note them here so skills stay in sync and so we can add CHANGELOG entries at release.

| Date | Change | JIRA | Affected skills | Status |
|------|--------|------|-----------------|--------|
| 2026-05-29 | `meeting-export-v2-put` CSV now includes **`bookedAt`** and **`meetingId`** columns | DISTRO-4483 (Production) | user-meetings (now uses both; was stubbing `bookedAt`), user-details & user-offboarding (dedupe on `meetingId` now valid) | ✅ user-meetings updated v0.4.0; verify exact header strings against a live export |
| 2026-05-21 | `meeting-export-v2-put` + `meeting-list-put` server-side `status` filter; `team-list-put` `member` filter | DISTRO-4472 | no-show-analyzer, org-meeting, user-details, user-meetings, user-copy, user-offboarding | ✅ reflected in skills |

## Items still needing a live read-only call before fixing
- `team-list-put` `id` (vs `teamId`) — observed by audit; re-confirm with one direct call.
- `availability-slots` `failures` reason strings.
- `meeting-export-v2-put` CSV header columns — including the new `bookedAt` / `meetingId` columns from DISTRO-4483 (confirm exact header strings) — used by user-meetings, user-details, user-offboarding.
- concierge-logs full `status` value set (only `Scheduled`/`TimedOut`/`Cancelled` observed so far).

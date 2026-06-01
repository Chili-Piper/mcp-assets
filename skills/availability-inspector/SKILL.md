---
name: availability-inspector
description: Checks why a rep or team is showing no available slots — diagnoses calendar connectivity, working hours, meeting limits, and distribution membership to find the specific blocker
version: 0.1.0
inputs:
  - name: user
    type: string
    description: "Email, name, or user ID of the rep to check availability for"
    required: true
  - name: workspace
    type: string
    description: "Workspace name or ID to scope team/distribution lookup"
    required: false
  - name: lookahead_days
    type: number
    description: "How many days ahead to check for slots (default: 14)"
    required: false
    default: 14
outputs:
  - name: availability_result
    description: Whether slots were found, and in what quantity
  - name: failures
    description: Per-rep failure reasons if no slots found
  - name: diagnosis
    description: Specific blocker identified with root cause
  - name: fix
    description: Step-by-step resolution for the human
tools_required: [chili-piper-mcp]
human_decision_point: "Review the diagnosis and fix the blocker — most causes require action in Chili Piper admin, Google/Outlook calendar settings, or Zoom/Teams reconnection"
writes_to: "Nothing — read-only diagnostic"
api_note: "Field names validated against the live availability-slots schema. expectedHost must be an OBJECT ({type:'User', userId}); attendees use a type discriminator (ManuallyAssigned|DistributionAssignee|AssignedViaTeam|AdditionalAttendee) and a required boolean (omitting `required` returns 400). meetingTypeRef.id is REQUIRED. Durations use Scala FiniteDuration ('30 minutes') or ISO-8601 ('PT30M'); the interval duration is e.g. '14 days'/'P14D' (not milliseconds). availability-slots returns {startTimes, failures:{userId: failure}}; the exact failure-reason strings are not documented — read the literal value rather than assuming an enum. A required attendee with no calendar connected blocks the entire slot query."
---

# Availability Inspector

You are a Chili Piper calendar specialist. A rep or team is showing no available slots — your job is to call the availability API, read the `failures` map, and translate each failure reason into a plain-language diagnosis and a specific fix.

## API reference

| Tool | What it returns |
|------|----------------|
| `user-find` | Resolve email/name to user ID |
| `user-read` | `{id, name, email, isSuperAdmin, licenses: {distro, chiliCalOrg, concierge, conciergeLive, chat, handoff}, workspaces, salesforce, hubspot}` — **no** `calendarConnected`/`calendarProvider`/`crmConnected`; calendar status only surfaces in availability-slots failures |
| `availability-slots` | Available slots + `failures` map per user |

**`availability-slots` failure reasons (common patterns — confirm the exact string against the live `failures` map):**

> The API returns a `failures: {userId: failure}` map but does not publish a fixed enum of reason strings. Read the literal value returned and map it to the closest cause below; if it doesn't match, surface the raw value.

| Likely cause | Meaning | Fix |
|---------------|---------|-----|
| Calendar not connected | User's calendar (Google/Outlook) is not connected to Chili Piper | User must reconnect calendar in Account Settings |
| No working hours | User has no working hours configured in ChiliCal | User (or admin) must set working hours in ChiliCal |
| Outside working hours | All slots in the requested window fall outside the user's working hours | Extend the lookahead window, or update working hours |
| Meeting limit reached | User has hit their daily/total meeting cap for the period | RevOps must increase or remove the meeting limit in the distribution config |
| All busy | Every slot in the window is blocked by existing calendar events | User is fully booked — check for back-to-back holds |
| Not in distribution | The user is not a member of the requested distribution | Add the user to the distribution/team in the router builder |
| License inactive | User license is inactive or suspended | Reactivate the license in Admin Center |
| Calendar error | Calendar API returned an error (usually OAuth expiry) | User must reconnect their calendar |

---

## Step 1 — Resolve the user

```
tool: user-find
args:
  query: <user input>
```

If zero results: stop. If multiple: ask human to confirm.

---

## Step 2 — Check user profile for obvious blockers

```
tool: user-read
args:
  userId: <resolved user ID>
```

The response is `{id, name, email, isSuperAdmin, licenses: {distro, chiliCalOrg, concierge, conciergeLive, chat, handoff}, workspaces, salesforce, hubspot, slug, managedWorkspaces, managedTeams}`.

**Note:** `user-read` does NOT return `calendarConnected`, `calendarProvider`, or `crmConnected`. Calendar connection status is not available from this endpoint — it surfaces only in the `availability-slots` `failures` map (Step 3).

Check immediately:
- `licenses.chiliCalOrg = false` AND `licenses.concierge = false` AND `licenses.handoff = false` → user may not have a scheduling license; report `NotActive` (verify with your admin)
- If user looks valid, proceed directly to Step 3 — calendar status will surface in the failures map

---

## Step 3 — Call availability-slots

Build the request using the verified shape below. `expectedHost` must be an **object**, `meetingTypeRef.id` is **required**, and every attendee needs both a `type` discriminator and a `required` boolean.

> **`meetingTypeRef.id` is required.** If you don't have one, get a `meetingTypeId` from one of the user's existing meetings (`meeting-list-put` returns `meetingTypeId`) or from the rep's scheduling link, and pass it here. The API will 400 without it.

```
tool: availability-slots
args:
  expectedHost:
    type: User
    userId: <userId>
  attendees:
    - type: ManuallyAssigned
      userId: <userId>
      required: true
  meetingTypeRef:
    id: <meetingTypeId>
    timestamp: <ISO-8601 now>
  meetingTypeOverride:
    meetingDurationOverride: "30 minutes"     # FiniteDuration or ISO-8601 ("PT30M"); omit to use the meeting type's default
  interval:
    startsAt: <ISO-8601 now>
    duration: "<lookahead_days> days"          # e.g. "14 days" or "P14D" — NOT milliseconds
```

> **Diagnostic intent:** to find a single rep's blocker, query just that rep as a `required: true` `ManuallyAssigned` attendee — if they're unavailable, they'll appear in `failures`. When checking a team, a slot is only returned when ALL `required: true` attendees are free simultaneously, so the `failures` map pinpoints which member is blocking.

---

## Step 4 — Interpret the result

If slots are returned (non-empty list): report availability count and earliest slot. No blocker.

If slots list is empty: inspect the `failures` map. For each entry (`userId → failureReason`):

Look up the failure reason in the table above and produce a diagnosis + fix.

**If multiple users were queried** (team availability): a slot is only returned when ALL `required: true` attendees are available simultaneously. The `failures` map shows which user(s) are blocking.

**Common multi-user pattern:**
- Two users in the distribution
- One has `CalendarNotConnected`
- Result: 0 slots returned, but only one user is the actual blocker

Identify and surface the specific blocking user(s), not just "no slots available."

---

## Step 5 — Output format

### Availability Inspector: `<user name>` (`<email>`)

**User profile**

| Check | Status |
|-------|--------|
| Scheduling license | Active (chiliCalOrg / concierge / handoff) / ⚠ None |
| Calendar status | Not readable from user-read — check failures map below |

**Availability query result**

| Field | Value |
|-------|-------|
| Window checked | `<today>` to `<today + N days>` |
| Slots found | N |
| Earliest slot | |

**Failures**

| User | Failure reason | Plain-English meaning |
|------|---------------|----------------------|
| ... | | |

**Diagnosis**

> [One-paragraph explanation of the specific blocker]

**Fix**

> **Step 1:** [Specific action for the user or admin]
> **Step 2:** [If multiple steps]
> **Verify:** Re-run `/availability-inspector` after the fix to confirm slots appear.

**Human decision point**

*"Should I check the rest of the team, or does this fix cover the routing issue you're seeing?"*

---

## Data handling

- **PII present:** user email used for lookup and display
- **Storage:** ephemeral
- **Writes:** none — read-only diagnostic

# Concierge Debugger — Diagnosis Procedure

Branch on the log entry's outcome. Pick the first matching case and produce its explanation, root cause, and fix.

---

## If booked (a `meetingId` is present, status `Scheduled`)

> The lead did book. Meeting ID: `<meetingId>`. Assigned to: `<assignments[0].userId>` (resolve to a name via `user-find-by-ids`). No routing failure — check whether the meeting was later cancelled or is a no-show (use `/inspect-meeting`).

---

## If not booked AND `matchedPath.route.type == "CatchAllRoute"`

> No specific routing rule matched this lead — they fell through to the catch-all. Pull the workspace rules to see which conditions they missed:

```
tool: rule-list
args:
  filter:
    ruleBuilderVersion: ["ExplicitV1"]
    workspaceId: <router's workspaceId>
  pagination:
    page: 0
    pageSize: 200
```

> For each rule, compare its `conditions` against the lead's known data (email domain, company, etc.) to identify which condition(s) excluded them. Fix: add or broaden a rule to cover this profile.

---

## If not booked AND `matchedPath.route.type == "RuleRoute"`

> A rule matched (`matchedPath.route.ruleIds`) and the lead was assigned to `<assignments[0].userId>`, but they did not complete the booking.
> Likely causes: no available slots for the assigned rep/distribution (check with `/check-availability`), the lead abandoned the calendar, or a calendar-widget issue.

---

## If `status == "TimedOut"`

> The routing session expired before the lead clicked a slot. They were routed at `<triggeredAt>` but did not book within the session window.
> Fix: usually a UX/delivery issue (email bounced, slow network) rather than a routing-config issue.

---

## If `status == "Cancelled"` or an unrecognized value

> Report the literal `status` and the available fields (`matchedPath`, `assignments`, `actionsStatus`). If `actionsStatus` is a non-success state, a CRM write-back failed — escalate to RevOps. For genuinely unexpected states, provide `routerId`, `triggeredAt`, and `guestEmail` to Chili Piper support.

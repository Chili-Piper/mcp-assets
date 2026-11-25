# Availability Inspector — Diagnostics

The "why no slots" cause/meaning/fix checklist and the multi-user interpretation rules for
Step 4 of the availability-inspector skill.

> `availability-slots-v2` does not return a per-user failure reason. When the results list
> is empty, use the table below as a diagnostic checklist and verify each cause in the
> Chili Piper admin.

---

## Common-causes checklist (check manually — not returned by the API)

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

## Interpreting the result

If `results` is non-empty: report total availability count (`total`) and earliest slot.
No blocker.

If `results` is empty: the v2 API returns **no** `failures` map. Work through the
common-causes checklist in order:

1. **License check** (already done in Step 2): if no scheduling license, report that as the primary cause.
2. **Calendar connection**: ask the rep or RevOps admin to confirm their Google/Outlook calendar is connected in Chili Piper Account Settings.
3. **Working hours**: confirm working hours are set in ChiliCal and that the requested window overlaps.
4. **Meeting limits**: verify per-distribution capping settings for this rep.
5. **Calendar events**: look for back-to-back holds or out-of-office blocks in the rep's calendar.

## Multi-user (team) availability

When multiple users were queried, a slot is only returned when ALL `required: true`
attendees are available simultaneously — so an empty team result may reflect any one member
blocking.

**Common multi-user pattern:**

- Two users in the distribution
- One has no calendar connected
- Result: 0 slots returned, but only one user is the actual blocker

If the team result is empty, re-query each member individually with the same window to
identify which specific member(s) produce empty results — surface the blocking user(s), not
just "no slots available."

## Per-day breakdown signals

When slots ARE returned, bucket every entry in `results` by the calendar date of its
`startTime` and count slots per day across the whole window (include zero-slot days so gaps
are visible). This turns a raw "180 slots" into a pattern a human can act on:

- **Weekends / holidays showing 0** confirm working-hours config, not a bug.
- **A weekday at 0** in an otherwise-full week is a real signal (day off, fully booked, or
  a calendar block) — worth calling out.
- **A later first slot on some weekdays** (e.g. Mondays starting 09:30 vs 08:30 elsewhere)
  points to day-specific working hours.
- **First/last day partials** are usually just the query window boundaries (a midday
  `startsAt` truncates day 1; the window end truncates the last day) — label them as
  partial, not as a drop. To get full first/last days, anchor `interval.startsAt` to
  start-of-day (00:00).

Times come back in **UTC** — state the timezone, and convert to the rep's working timezone
if the human needs local hours.

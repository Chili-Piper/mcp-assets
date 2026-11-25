# Meeting Inspector — Anomaly Detection

Full anomaly table and severity definitions for Step 4 of the meeting-inspector skill.

---

## Anomaly table

Check every row. Flag any condition that is true.

| Anomaly | Condition | Severity |
|---------|-----------|----------|
| **No-show** | `meetingStatus = NoShow` (or `noShowStatus = NoShow`) | High |
| **Late cancellation** | `meetingStatus = Canceled` AND cancellation within 2 hours of `dateTime.start` | Medium |
| **Long lead time + no-show** | Lead time > 5 days AND `meetingStatus = NoShow` | High — recency decay likely |
| **Rep assignment mismatch** | `assignments[0].userId` (routing log) ≠ `hostId` (meeting record) | High — meeting was reassigned after routing |
| **Routing fallthrough** | `matchedPath.route.type == "CatchAllRoute"` | Medium — no specific rule matched; the lead hit the catch-all |
| **Unrouted meeting** | No routing log found at all, or the log's `matchedPath` is null/blank | Low — likely manual or direct-link booking |
| **CRM write-back failure** | `actionsStatus` is not a success state | Medium — meeting not visible in Salesforce |

---

## Plain-language explanations per anomaly

Use these in the output for clarity:

**No-show**
The guest did not attend the meeting. Common causes: too long a lead time, no reminder sequence, low-intent booking.

**Late cancellation**
The meeting was cancelled within 2 hours of the scheduled start. Often indicates the guest forgot they booked or had a last-minute conflict. Check whether the booking confirmation included a clear agenda.

**Long lead time + no-show**
Lead time over 5 days significantly increases no-show risk due to recency decay — the guest forgets why they booked. Shortening the booking window or adding an SMS reminder can reduce recurrence.

**Rep assignment mismatch**
The router assigned a different rep than the one on the meeting record. Most common cause: stale Salesforce ownership data. The meeting was probably manually reassigned after routing completed.

**Routing fallthrough**
No specific routing rule matched this lead's profile — `matchedPath.route.type` is `CatchAllRoute`, so the lead was handled by the catch-all. Review the `sourceUrl` to see which page triggered the router and whether a rule should cover that source.

**Unrouted meeting**
No concierge-log was found for this meeting (or the log carries no `matchedPath` at all). It was likely booked via a direct scheduling link, a handoff, or a manual booking by a rep. Not necessarily a problem, but worth confirming if ownership and CRM write-back behaved correctly.

**CRM write-back failure**
The meeting exists in Chili Piper but the post-routing CRM actions (Salesforce task, campaign association) did not complete successfully. The deal may not reflect this meeting activity. Escalate to the RevOps admin.

---

## Severity definitions

| Severity | Meaning |
|----------|---------|
| **High** | Likely pipeline impact — act promptly |
| **Medium** | Process gap — should be investigated, may not have immediate deal impact |
| **Low** | Informational — context for understanding the booking, not necessarily a problem |

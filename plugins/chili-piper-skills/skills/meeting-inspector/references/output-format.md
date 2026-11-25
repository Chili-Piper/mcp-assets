# Meeting Inspector — Output Format

Exact template for Step 6 of the meeting-inspector skill. Fill in all fields; use "—" for unavailable data.

---

## Template

### Meeting Inspector: `<guest_email or meeting_id>`

**Meeting Summary**

| Field | Value |
|-------|-------|
| Meeting ID | |
| Status | |
| Scheduled | |
| Booked at | |
| Lead time | |
| Guest | |
| Assigned rep | |

---

**Routing Trace**

| Field | Value |
|-------|-------|
| Trigger | |
| Router | |
| Matched rule | |
| Source URL | |
| Router assigned | |
| Routed at | |
| CRM actions status | |

If the routing trace is unavailable, replace this table with one of:
- *"Routing trace unavailable — meeting is older than 30 days."*
- *"No routing log found — meeting was likely booked via direct scheduling link, handoff, or manual booking."*

---

**Anomalies**

| Flag | Severity | Detail |
|------|----------|--------|
| | | |

If no anomalies: *"No anomalies detected."*

---

**Recommended action**

> [One paragraph. See SKILL.md Step 5 for the recommendation decision tree.]

---

**Human decision point**

*"What would you like to do — rebook the guest, follow up, or look at the underlying routing rule?"*

---

## Tone guidance

- Use plain language. Avoid jargon like "CRM attribution propagation failure" — say "the meeting may not appear in Salesforce."
- Keep the recommended action to one paragraph. The human wants a decision, not a report.
- Surface individual emails only when diagnosing a specific case — use counts in summaries.

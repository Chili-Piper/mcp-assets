# Concierge Debugger — Output Format

Exact template for the output step. Fill in all fields; use "—" for unavailable data.

---

## Template

### Concierge Debug: `<guest_email>`

**Routing session found**

| Field | Value |
|-------|-------|
| Router | |
| Triggered at | |
| Trigger type | |
| Source URL | |
| Status | |
| Matched route | RuleRoute / CatchAllRoute |
| Assigned rep | (from `assignments[0].userId`) |
| Meeting booked | |

**Diagnosis**

> [Plain-language explanation of what happened]

**Root cause**

> [Specific cause: which condition failed, why the session expired, etc.]

**Fix**

> [One specific change to make: add a routing rule condition, add a fallback, fix availability, etc.]

**Human decision point**

*"Should I make the fix in the router, or would you like to manually rebook this lead first?"*

---

## If no session found

Report: *"No routing session found for `<guest_email>` in the requested window. The lead may not have triggered the router, or the session is older than 30 days."*

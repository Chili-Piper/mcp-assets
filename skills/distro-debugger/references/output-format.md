# Distribution Debugger — Output Format

The exact layout for the final diagnostic report.

---

## Template

### Distribution Debug: `<record name or ID>`

**Log summary**

| Field | Value |
|-------|-------|
| Router | |
| Triggered at | |
| Salesforce record | |
| Status | |
| Assigned to | |
| Assignment method | |

**Enrichment**

> [Fields enriched before rule evaluation, any failures — or "No enrichment ran"]

**Stage-by-stage evaluation**

| Stage | Rule | Matched | Notes |
|-------|------|---------|-------|
| 1 | | ✅/❌ | |

**Condition detail for failing stages**

- Rule: `<ruleName>` — field `<field>` was `<actual>`, expected `<operator> <expected>`

**Diagnosis**

> [What happened, which rule fired or why none did, whether enrichment or SLA played a role]

**Root cause**

> [The specific condition, field value, or config gap]

**Fix**

> [One specific change: update condition X, add fallback distribution, fix enrichment mapping, adjust capping]

**Human decision point**

*"Should I open the router builder to apply this fix, or would you like to manually reassign the record first?"*

---
title: "Router Coverage Audit: find and fix routing gaps before they cost you pipeline"
contributor: chili-piper
stage: orchestration
tool_category: [routing, analytics, crm]
persona: [rev-ops]
stack: [claude-code, chili-piper-mcp]

humans_in_loop:
  - role: RevOps
    does: "reviews gap report, decides which rules to add or modify, makes changes in the router builder"
    joy: high

agent_does:
  - "lists all concierge routers across all workspaces"
  - "fetches routing rules per router and checks for missing catch-alls"
  - "analyzes concierge logs for catch-all overflow rate and no-match patterns"
  - "checks distributions for empty or single-member queues"
  - "produces a prioritized gap report with specific fix recommendations"

human_decision_points:
  - custom

data_sources:
  - name: chili-piper
    type: live-api

data_handling:
  pii_present: []
  storage: ephemeral
  outputs_go_to: human-review

revenue_impact:
  optimizes_for: [win_rate, pipeline_velocity]
  expected_lift: "Closing routing gaps that cause 10%+ catch-all overflow typically recovers 5–10% of form submissions that were being routed to a generic SDR pool or dropped"
  evidence_strength: anecdotal
  measurement_horizon: "30 days"

measurement:
  writes_to: []
  attribution_signal: "Track catch-all rate in concierge logs before and after fixing — target <10% catch-all rate per router"
  optimization_loop: "Re-run monthly or after any major territory or segment change"

maturity: draft
---

# Router Coverage Audit

**The problem:** Routing gaps are silent. A lead fills out a form, hits a catch-all because no rule matches their profile, and gets routed to a generic pool — or dropped entirely. No alert fires. The SDR who should have owned that account never sees it.

**What this does:** Runs a systematic audit of every concierge router — checks for missing catch-alls, high catch-all rates, empty distributions, and stale ownership rules — and gives RevOps a prioritized fix list.

**Why it matters:** One uncovered territory or one empty distribution queue silently leaks pipeline. A monthly audit catches these before they compound.

---

## Prerequisites

- Chili Piper account with API access
- Chili Piper MCP installed (see `mcp-servers/chili-piper/README.md`)
- Claude Code

---

## Human-agent loop

```
Agent                               RevOps
─────────────────────────────────   ────────────────────────────────────────
Lists all workspaces + routers      
Fetches rules per router            
Checks for missing catch-alls       
Analyzes logs for catch-all rates   
Checks distribution membership      
Produces gap report                 
                                    ← Reviews prioritized gaps
                                    ← Opens router builder in CP
                                    ← Adds missing rules, fills empty queues
                                    ← Re-runs audit to confirm
```

---

## How to run it

### Org-wide audit (recommended monthly)

```
/routing-audit
```

### Single workspace audit

```
/routing-audit workspace="Inbound US"
```

### With extended log analysis

```
/routing-audit log_days=30
```

---

## Example output

*(Synthetic data — Acme Corp)*

### Routing Audit | All Workspaces | Last 7 days

**Router summary**

| Router | Workspace | Rules | Catch-all | Leads | Catch-all rate | No-match |
|--------|-----------|-------|-----------|-------|---------------|---------|
| Inbound US | AMER | 6 | ✓ Round-robin | 284 | 8% | 0% |
| Inbound EMEA | EMEA | 4 | ✓ Round-robin | 91 | 31% ⚠ | 0% |
| Enterprise Fast Lane | AMER | 3 | ⚠ MISSING | 22 | — | 14% ⚠ |
| Event Capture | Global | 2 | ✓ Redirect | 47 | 2% | 0% |

**Gaps found**

**[CRITICAL] Inbound US — Enterprise Fast Lane: no catch-all**
> 14% of leads (3 in 7 days) triggered no rule and were dropped with no fallback.
> Fix: add a catch-all rule in the router builder as the final node. Route to the general SDR team or redirect to a "we'll be in touch" page.

**[HIGH] Inbound EMEA: 31% catch-all rate**
> 28 of 91 leads hit the catch-all in the last 7 days. These leads are being routed to the general EMEA pool rather than a territory-specific rep.
> Top unmatched profiles (estimated from log sourceUrls): `/de/` and `/fr/` landing pages (DACH + France traffic).
> Fix: add territory rules for DACH and France before the catch-all. Route to the DACH team and France team distributions respectively.

**[MEDIUM] Inbound US — "SMB West" distribution has 0 active members**
> The SMB West distribution has been configured but no reps are assigned. Any lead matching the SMB West rule is currently being dropped.
> Fix: add at least 2 reps to the SMB West distribution in the router builder.

**Recommendations**

1. Add catch-all to Enterprise Fast Lane — 3 leads dropped this week, unknown cumulative loss
2. Add DACH + France rules to Inbound EMEA — 28 leads/week going to generic pool
3. Populate SMB West distribution — routing rule exists but goes nowhere

**Human decision point**

*"Which gap should we fix first? I can help draft the rule conditions for the EMEA territory rules, or open the Enterprise Fast Lane router to add the catch-all."*

---

## Measurement

1. Before fixing: note catch-all rates for each flagged router (from this report)
2. Make the changes in the Chili Piper router builder
3. Re-run `/routing-audit log_days=7` one week later
4. Compare catch-all rates — target < 10% per router

---

## Local setup

```
recipes/orchestration/routing/router-coverage-audit/
├── router-coverage-audit.md   ← this file
└── local/                     ← GITIGNORED
    ├── README.md
    └── .env                   ← CHILI_PIPER_API_KEY
```

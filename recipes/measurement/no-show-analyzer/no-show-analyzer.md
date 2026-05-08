---
title: "No-Show Analyzer: find and fix your booking leak by source, route, or rep"
contributor: chili-piper
stage: measurement
tool_category: [scheduling, analytics, crm]
persona: [rev-ops, demand-gen]
stack: [claude-code, chili-piper-mcp, salesforce-mcp]

humans_in_loop:
  - role: RevOps
    does: "reviews flagged segments, selects which action to test, creates the tracking task in Salesforce"
    joy: high
  - role: Demand Gen
    does: "reviews lead-source breakdown, deprioritizes or redirects budget from high-no-show sources"
    joy: medium

agent_does:
  - "fetches all meeting records for the period from Chili Piper MCP"
  - "calculates no-show rate by lead source, route, rep, or workspace"
  - "flags segments above threshold with root-cause hypotheses"
  - "recommends 2–4 specific, testable routing or confirmation changes"
  - "offers to create a Salesforce tracking task for the chosen experiment"

human_decision_points:
  - before-send

data_sources:
  - name: chili-piper
    type: live-api
  - name: salesforce
    type: live-api

data_handling:
  pii_present: [email]
  storage: ephemeral
  outputs_go_to: salesforce-tasks

revenue_impact:
  optimizes_for: [win_rate, pipeline_velocity]
  expected_lift: "5–15pp reduction in no-show rate on flagged segments within 30 days"
  evidence_strength: anecdotal
  measurement_horizon: "30 days"

measurement:
  writes_to: [salesforce-tasks]
  attribution_signal: "Salesforce task on lead source campaign or rep record with baseline rate + 30-day follow-up date"
  optimization_loop: "Re-run skill after 30 days with same parameters to compare no-show rate against baseline"

maturity: draft
---

# No-Show Analyzer

**The problem:** No-show rates vary enormously by lead source, routing rule, and rep — but most teams look at a single blended org-wide number and miss the real story.

**What this does:** Pulls your Chili Piper meeting data for a period, calculates no-show rates across the dimension that matters to you (source, route, rep, or workspace), flags the outliers, and gives RevOps a prioritized list of specific changes to test.

**Why it matters:** A 10pp reduction in no-show rate on your highest-volume source has the same pipeline effect as a significant increase in booking rate — at zero additional spend.

---

## Prerequisites

- Chili Piper account with API access
- Chili Piper MCP installed and configured (`mcp-servers/chili-piper/`)
- Salesforce MCP (optional — for writing the tracking task)
- Claude Code

---

## Human-agent loop

```
Agent                               Human (RevOps / Demand Gen)
─────────────────────────────────   ────────────────────────────────────────
Fetches meeting records             
Calculates no-show rates            
Flags problem segments              
Generates root-cause hypotheses     
Recommends 2–4 test actions         
                                    ← Reviews flagged segments
                                    ← Selects 1 action to test
                                    ← Confirms Salesforce task creation
Agent creates Salesforce task       
                                    ← Runs change in Chili Piper
                                    ← (30 days later) re-runs skill
Agent compares new vs baseline      
```

The human owns the diagnosis and the fix. The agent owns the data gathering and pattern recognition.

---

## How to run it

### Option A — defaults (last 30 days, grouped by lead source)

```
/no-show-analyzer
```

### Option B — custom date range and dimension

```
/no-show-analyzer date_range=last-90-days group_by=route workspace="Inbound US"
```

### Option C — tighten the flag threshold

```
/no-show-analyzer flag_threshold=20
```

---

## Example output

*(Synthetic data — Acme Corp)*

### No-Show Analysis: Jan 1–Jan 31 | Org-wide | Grouped by Lead Source

**Summary**

| Metric | Value |
|--------|-------|
| Total meetings (excl. cancelled) | 412 |
| No-shows | 98 |
| Org no-show rate | 23.8% |
| Flagged segments (>30%) | 2 |

**Breakdown**

| Lead Source | Meetings | No-shows | No-show rate | Status |
|-------------|---------|----------|-------------|--------|
| Paid Social — LinkedIn | 87 | 41 | 47.1% | ⚠ Flagged |
| Content Download (gated) | 63 | 22 | 34.9% | ⚠ Flagged |
| Inbound Demo Request | 148 | 21 | 14.2% | ✓ OK |
| Partner Referral | 44 | 7 | 15.9% | ✓ OK |
| Event — Webinar | 70 | 7 | 10.0% | ✓ OK |

**Flagged: Paid Social — LinkedIn (47.1%)**

> **Hypothesis:** LinkedIn paid leads often book impulsively and have low intent at the moment of the meeting.
> **Signal to check:** Time between booking and meeting for this source. If median > 4 days, recency decay is the problem.
> **Likely fix:** Add a 24h SMS reminder sequence to this route, and reduce the booking window to 3 days max.

**Flagged: Content Download (34.9%)**

> **Hypothesis:** Content downloads have no stated intent signal — prospect may not remember why they booked.
> **Signal to check:** Whether this route has a pre-meeting confirmation email with agenda. If not, that's the gap.
> **Likely fix:** Add a "here's what we'll cover" confirmation email 48h before the meeting.

**Recommended actions**

**Action 1 — Add SMS reminder to LinkedIn Paid route**
What to change: Enable SMS reminder sequence on the "Paid Social — LinkedIn" route in Chili Piper, 24h before meeting
Expected effect: 10–15pp reduction in no-show rate for this source within 30 days
How to measure: Re-run this skill in 30 days, filter to LinkedIn Paid, compare to 47.1% baseline
Owner: RevOps

**Action 2 — Cap booking window on LinkedIn Paid to 3 days**
What to change: Set max booking advance on "Paid Social — LinkedIn" route from 14 days to 3 days
Expected effect: Reduces low-intent bookings that decay before the meeting
How to measure: Booking volume vs no-show rate tradeoff — watch both metrics
Owner: RevOps

---

## Measurement

1. RevOps selects an action and the agent creates a Salesforce task on the lead source campaign record:
   - **Subject:** `[No-Show Test] LinkedIn Paid: SMS reminder sequence`
   - **Description:** Baseline no-show rate: 47.1% (Jan 1–31). Testing: SMS reminder 24h pre-meeting. Follow-up: Feb 28.
   - **Due date:** 30 days from change date

2. On the due date, re-run `/no-show-analyzer date_range=<test period> group_by=lead-source`

3. Compare flagged segment rate to baseline. If improved: make permanent, increase scope. If not: try Action 2.

---

## Local setup

```
recipes/measurement/no-show-analyzer/
├── no-show-analyzer.md    ← this file
└── local/                 ← GITIGNORED — put your real API keys here
    ├── README.md
    └── .env               ← CHILI_PIPER_API_KEY, SALESFORCE_TOKEN
```

`local/README.md` contents:
```
# Local config for no-show-analyzer

Set these in .env (gitignored):
  CHILI_PIPER_API_KEY=your_api_key
  SALESFORCE_TOKEN=your_sf_token (optional)

Never commit these. Never.
```

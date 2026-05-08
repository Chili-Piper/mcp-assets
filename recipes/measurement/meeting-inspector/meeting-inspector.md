---
title: "Meeting Inspector: reconstruct any booking's full lifecycle in one command"
contributor: chili-piper
stage: measurement
tool_category: [scheduling, analytics, crm]
persona: [rev-ops, ae]
stack: [claude-code, chili-piper-mcp]

humans_in_loop:
  - role: RevOps
    does: "reviews anomaly flags, decides whether to rebook, follow up, or fix a routing rule"
    joy: high
  - role: AE
    does: "uses to investigate a specific no-show or late cancel on their own pipeline"
    joy: medium

agent_does:
  - "resolves meeting by ID or guest email"
  - "reconstructs the full routing path — trigger, router, matched rule, assigned rep"
  - "detects anomalies: no-show, late cancel, rep reassignment, routing fallthrough"
  - "recommends one specific next action based on what it found"

human_decision_points:
  - before-send

data_sources:
  - name: chili-piper
    type: live-api

data_handling:
  pii_present: [email]
  storage: ephemeral
  outputs_go_to: human-review

revenue_impact:
  optimizes_for: [win_rate, pipeline_velocity]
  expected_lift: "Faster response to no-shows — rebooking within 2h of a missed meeting recovers 20–40% of lost meetings"
  evidence_strength: anecdotal
  measurement_horizon: "immediate"

measurement:
  writes_to: []
  attribution_signal: "Manual — RevOps notes the outcome in Salesforce after acting on the recommendation"
  optimization_loop: "Use no-show-analyzer to track whether single-meeting interventions accumulate into a lower segment-level no-show rate"

maturity: draft
---

# Meeting Inspector

**The problem:** When a meeting no-shows, is reassigned, or gets a late cancel, you have no quick way to understand *why*. Did the wrong rep get assigned? Did the lead come from a low-intent source with a 10-day booking window? Did the router fall through to a catch-all? You're left guessing.

**What this does:** Give it a meeting ID or guest email and it reconstructs the full story — how the lead arrived, which routing rule fired, who got assigned (and whether that changed), and what the outcome was. It flags anything that looks wrong and tells you what to do next.

**Why it matters:** The first 2 hours after a no-show are the highest-leverage recovery window. This skill gives you everything you need to act fast — without digging through CP logs and Salesforce manually.

---

## Prerequisites

- Chili Piper account with API access
- Chili Piper MCP installed and configured (`mcp-servers/chili-piper/`)
- Claude Code

---

## Human-agent loop

```
Agent                               Human (RevOps / AE)
─────────────────────────────────   ────────────────────────────────────────
Resolves meeting by ID or email     
Fetches meeting record              
Pulls routing log from concierge    
Detects anomalies                   
Recommends next action              
                                    ← Reviews anomaly flags
                                    ← Decides: rebook / follow up / fix rule
                                    ← Takes action (outside this skill)
```

The human owns the decision and the fix. The agent owns the reconstruction.

---

## How to run it

### Option A — by meeting ID

```
/meeting-inspector meeting_id=abc123
```

### Option B — by guest email (finds most recent meeting)

```
/meeting-inspector guest_email=prospect@company.com
```

### Option C — guest email with a specific date window

```
/meeting-inspector guest_email=prospect@company.com date_range=2025-04-01:2025-04-30
```

---

## Example output

*(Synthetic data — Acme Corp)*

### Meeting Inspector: `jordan.lee@prospect.io`

**Meeting Summary**

| Field | Value |
|-------|-------|
| Meeting ID | mtg_8f3k2p |
| Status | NoShow |
| Scheduled | Apr 14, 2025 at 2:00 PM PT |
| Booked at | Apr 7, 2025 at 11:22 AM PT |
| Lead time | 6 days, 2 hours |
| Guest | jordan.lee@prospect.io |
| Assigned rep | Sarah Chen (sarah@acme.com) |

**Routing Trace**

| Field | Value |
|-------|-------|
| Trigger | ThirdPartyForm |
| Router | Inbound US — Demo Request |
| Matched rule | Round Robin |
| Source URL | acme.com/pricing |
| Router assigned | Sarah Chen |
| Routed at | Apr 7, 2025 at 11:22 AM PT |

**Anomalies**

| Flag | Severity | Detail |
|------|----------|--------|
| No-show | High | Guest did not attend the scheduled meeting |
| Long lead time + no-show | High | 6-day booking window — intent likely decayed before the meeting date |

**Recommended action**

> This is a classic recency-decay no-show: the lead came in from a pricing page form fill, got routed to round robin, and booked 6 days out. By the time the meeting arrived, they'd moved on. Send a rebook link within the next 2 hours with a personal note referencing the pricing page — something like "I noticed you were looking at our pricing, I'd love to pick up where we left off." If you're seeing this pattern repeatedly on this route, consider capping the booking window to 3 days for form fills from high-intent pages.

**Human decision point**

*"What would you like to do — rebook the guest, follow up, or look at the Round Robin routing rule?"*

---

## Recovery playbook (after the skill runs)

| Anomaly | What to do |
|---------|-----------|
| No-show, lead time > 5 days | Rebook within 2h; note the source URL and route for no-show-analyzer |
| No-show, lead time < 2 days | High-urgency lead — call first, then rebook |
| Late cancel (< 2h before) | Check if guest or rep cancelled; send rebook link either way |
| Rep assignment mismatch | Check Salesforce ownership; if mismatch was wrong, fix and reassign |
| Routing fallthrough | Open the router in CP and audit which rule should have matched |

---

## Pairing with no-show-analyzer

Meeting Inspector is a single-meeting diagnostic. When you find a pattern — multiple no-shows from the same route, rep, or trigger — use `/no-show-analyzer` to quantify it at the segment level and get a prioritized list of fixes.

```
/no-show-analyzer group_by=route flag_threshold=25
```

---

## Local setup

```
recipes/measurement/meeting-inspector/
├── meeting-inspector.md    ← this file
└── local/                  ← GITIGNORED — put your real API keys here
    ├── README.md
    └── .env                ← CHILI_PIPER_API_KEY
```

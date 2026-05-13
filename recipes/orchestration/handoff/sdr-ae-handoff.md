---
title: "SDR-to-AE Handoff: book the AE meeting before the SDR call ends"
contributor: chili-piper
stage: orchestration
tool_category: [scheduling, handoff, crm]
persona: [sdr, ae, rev-ops]
stack: [claude-code, chili-piper-mcp, salesforce-mcp]

humans_in_loop:
  - role: SDR
    does: "runs the discovery call, confirms AE fit, triggers the handoff from within the call"
    joy: high
  - role: AE
    does: "receives the booked meeting with full context, reviews the SDR's handoff notes before joining"
    joy: high
  - role: RevOps
    does: "configures the handoff router and distribution once; monitors handoff completion rate"
    joy: medium

agent_does:
  - "queries AE availability for the next N days via availability-slots"
  - "initiates a handoff session with the lead's CRM context (account, opportunity, lead source)"
  - "presents available slots to the SDR during the live call"
  - "books the AE meeting and writes the activity back to Salesforce"
  - "sends a confirmation with meeting context to both SDR and AE"

human_decision_points:
  - before-meeting

data_sources:
  - name: chili-piper
    type: live-api
  - name: salesforce
    type: live-api

data_handling:
  pii_present: [email, name, company]
  storage: ephemeral
  outputs_go_to: salesforce-activities

revenue_impact:
  optimizes_for: [win_rate, pipeline_velocity]
  expected_lift: "SDRs who book the AE meeting while the prospect is live convert at 2–4× the rate of email follow-up scheduling"
  evidence_strength: one-team
  measurement_horizon: "30 days"

measurement:
  writes_to: [salesforce-activities, salesforce-opportunities]
  attribution_signal: "Chili Piper activity on the Lead/Contact record with handoff type and SDR name"
  optimization_loop: "Track handoff completion rate (handoff initiated vs meeting completed) weekly in Salesforce reports"

maturity: draft
---

# SDR-to-AE Handoff

**The problem:** The best moment to book the AE meeting is while you're on the phone with the prospect. Every hour between "I'll send you a calendar link" and the prospect actually booking reduces conversion. Cold handoffs with email follow-up scheduling convert at a fraction of live handoffs.

**What this does:** During or immediately after a qualified SDR call, the agent queries AE availability, presents slots in real time, and books the meeting before the SDR hangs up. The AE receives a meeting with full context — account, opportunity stage, what the SDR learned — already populated from Salesforce.

**Why it matters:** Speed-to-AE is a leading indicator of win rate. Live handoffs are the highest-leverage intervention in the SDR→AE motion.

---

## Prerequisites

- Chili Piper account with a **Handoff router** configured (workspace, AE team, meeting type)
- Chili Piper MCP installed (see `mcp-servers/chili-piper/README.md`)
- Salesforce MCP (optional — for writing activity post-booking)
- Claude Code
- SDR must know the lead's email address

---

## Human-agent loop

```
SDR (on call with prospect)        Agent                    AE
──────────────────────────────   ─────────────────────    ────────────────
Qualifies prospect                
Confirms AE meeting interest      
Triggers: /sdr-ae-handoff         
  guest_email=prospect@co.com     
  workspace=inbound-us            
                                  Queries AE availability  
                                  → Returns next 5 slots   
SDR reads slots to prospect       
Prospect picks slot               
SDR: "confirm slot 2"             
                                  Books meeting            
                                  Writes Salesforce task   
SDR gets confirmation link        
                                                           ← Receives invite
                                                           ← Sees SDR notes
```

---

## How to run it

### During a live call (fastest)

```
/sdr-ae-handoff guest_email=prospect@company.com workspace=inbound-us
```

The agent returns 5 available slots. Read them to the prospect, confirm their choice, then:

```
/sdr-ae-handoff confirm slot=2
```

### With full context pre-loaded

```
/sdr-ae-handoff \
  guest_email=prospect@company.com \
  workspace=inbound-us \
  crm_record_id=0031X00002abc123 \
  notes="ICP fit, budget confirmed, evaluating Q2. Pain: manual lead routing."
```

---

## What the agent does (MCP calls)

**Step 1 — Resolve workspace and find the handoff router:**

```
tool: workspace-list
```

Resolve workspace name to ID. Then:

```
tool: concierge-list-routers
args:
  workspaceId: <workspace id>
```

Find the handoff router (or the routing configured for AE booking).

**Step 2 — Check AE availability:**

```
tool: availability-slots
args:
  expectedHost: <AE team distribution ID>
  userIds: <AE team member IDs>
  meetingTypeOverride:
    meetingDurationOverride: "2700000 milliseconds"   # 45 minutes
  interval:
    startsAt: <now, ISO-8601>
    duration: "604800000 milliseconds"                # 7 days
```

Returns combined availability across the AE team (Flexible round-robin: most slots visible to SDR).

**Step 3 — Initiate handoff session:**

```
tool: handoff-init
args:
  workspaceId: <workspace id>
  bookerId: <SDR's user ID>
  body:
    guestEmail: <prospect email>
    crmExplicits:
      leadId: <Salesforce Lead ID if known>
      contactId: <Salesforce Contact ID if known>
    interval:
      startsAt: <now, ISO-8601>
      duration: "604800000 milliseconds"
```

Returns a `sessionId` and available meeting slots.

**Step 4 — Book the selected slot:**

```
tool: handoff-schedule
args:
  sessionId: <from handoff-init>
  slotId: <selected slot ID>
  body:
    notes: <SDR's handoff notes>
```

Returns a confirmation with meeting ID and calendar invite details.

---

## Example output

*(Synthetic data — Acme Corp)*

**Availability for prospect@company.com | Next 7 days**

| # | Date | Time | AE |
|---|------|------|----|
| 1 | May 15 | 10:00 AM PT | Sarah Chen |
| 2 | May 15 | 2:00 PM PT | Marcus Williams |
| 3 | May 16 | 11:00 AM PT | Sarah Chen |
| 4 | May 16 | 3:00 PM PT | Marcus Williams |
| 5 | May 17 | 9:00 AM PT | Sarah Chen |

*"Which slot works best? I'll book it immediately."*

---

**After slot 2 confirmed:**

> ✓ Meeting booked: May 15, 2:00 PM PT with Marcus Williams
> Confirmation sent to prospect@company.com and marcus@acme.com
> Salesforce activity logged on Lead record

---

## Measurement

What to track:
1. **Handoff initiation rate:** How often SDRs trigger the handoff vs email follow-up
2. **Handoff completion rate:** `meetings booked / handoffs initiated` — target >80%
3. **Win rate by handoff type:** Live handoff vs email follow-up scheduling

Salesforce report: filter Chili Piper Activities where `Type = Handoff` and track opportunity stage progression at 30/60/90 days.

---

## Pairing with other skills

- `/availability-inspector` — if AE shows no slots, diagnose before the call
- `/meeting-inspector` — investigate a no-show on a booked handoff meeting
- `/user-meetings` — check an AE's handoff meeting volume and no-show rate

---

## Local setup

```
recipes/orchestration/handoff/sdr-ae-handoff/
├── sdr-ae-handoff.md      ← this file
└── local/                 ← GITIGNORED
    ├── README.md
    └── .env               ← CHILI_PIPER_API_KEY
```

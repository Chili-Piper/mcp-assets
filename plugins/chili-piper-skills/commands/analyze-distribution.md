---
description: Analyzes a Chili Piper distribution (round-robin queue) for imbalance vs. configured weights, booking-source and day-of-week skew, and cancellation breakdown.
argument-hint: "<workspace> <distribution> <start-date> <end-date>"
allowed-tools: [Read]
---

# /analyze-distribution

Analyze round-robin distribution balance using the `distribution-analysis` skill.

## Steps

1. Read `skills/distribution-analysis/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs (all four are **required** — prompt for any that are missing):
   - `workspace` — workspace name or ID containing the distribution.
   - `distribution` — distribution name (substring) or `distributionId`.
   - `start_date` — start of range, inclusive (e.g. `2026-05-01`).
   - `end_date` — end of range, exclusive (e.g. `2026-06-01` = through May 31).
4. Load `skills/distribution-analysis/references/output-format.md` before producing the report.
5. Execute the skill's steps in order.
6. Output the distribution config, the per-rep breakdown with imbalance ratios, the booking-source/day-of-week/cancellation patterns, and the recommendations.
7. Ask: *"Want to rebalance weights, fix availability for an under-booked rep, or leave as-is?"*

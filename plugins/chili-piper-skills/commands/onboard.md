---
description: Guided Chili Piper onboarding, reads your account, interviews you, agrees a plan, then builds your routing and scheduling baseline with a confirmation before anything is created.
argument-hint: "[workspace]"
allowed-tools: [Read]
---

# /onboard

Run a guided Chili Piper setup using the `onboarding-chili-piper` skill.

> ⚠️ This skill **writes to Chili Piper**: users and team membership, teams, meeting types,
> rules, distributions, routers and scheduling links. It reads your account and agrees a plan
> with you first, and nothing is created until you confirm. The build is **not transactional**,
> and Concierge routers publish **live** on create.

## Steps

1. Read `skills/onboarding-chili-piper/SKILL.md`.
2. Check that the Chili Piper MCP is connected, call `health-ping`. If it fails, output the
   setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. If the user provided a workspace name as the argument, pass it as the `workspace` input.
   Otherwise the skill reads it from the account.
4. Execute the phases in order, Phase 0 baseline, Phase 1 interview, Phase 2 plan (STOP for
   confirmation), Phase 3 build, Phase 4 handoffs.
5. Tip: to build a single Concierge router without the full onboarding, use
   `/build-concierge-router`.

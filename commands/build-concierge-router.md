---
description: Guides you through building a complete Concierge web-form router from scratch — teams, meeting types, rules, distributions, and the live router — with a confirmation checkpoint before anything is created.
argument-hint: "[workspace] [requirements] [--build]"
allowed-tools: [Read]
---

# /build-concierge-router

Build a new Concierge router end to end using the `concierge-router-builder` skill.

> ⚠️ This skill **writes to Chili Piper** and publishes a **live** router. It creates many
> objects (teams, meeting types, rules, distributions) and is **not transactional** — a
> mid-build failure leaves earlier objects behind. It always runs the interview and presents
> a full plan first; nothing is created until you confirm. Data fields and web-form mapping
> are **UI-only prerequisites** the API cannot do.

## Steps

1. Read `skills/concierge-router-builder/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the
   setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `workspace` (optional; asked if missing).
   - Remaining text → `requirements` (optional free-text to pre-fill the interview).
   - `--build` → `dry_run: false`. **Without `--build`, always run with `dry_run: true`.**
4. Execute the phases in order — Phase 0 prerequisites, Phase 1 interview, Phase 2
   confirmation checkpoint (STOP for confirmation), Phase 3 build, Phase 4 verify & hand off.
5. Output the build plan (dry run) or the built objects + booking slug + go-live checklist
   (after `--build`).
6. Tip: to *edit* an existing router use `/configure-concierge-router`; to *diagnose* one use
   `/debug-concierge` or `/audit-routing`.

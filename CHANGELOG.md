# Changelog

All notable changes to the official Chili Piper Skills are recorded here. The repo follows [Keep a Changelog](https://keepachangelog.com/); each skill also carries its own `version` in its `SKILL.md` (and matching `GPT.md`).

## [Unreleased]

### Added
- **`handoff-router-configuration` skill (new, writes) + paired GPT +
  `/configure-handoff-router` command.** CRUD for Handoff (rep-to-rep) routers via the
  new `handoff-router-*` MCP tools (DISTRO-4550). Always-live model — no Inactive state
  or activation step exists, so the skill leads every plan with a live-on-apply warning;
  full-replace updates with a representability gate; Schedule outcomes require an
  assignment (distribution or user) plus a meeting type. Closes #42.
- **`distro-router-configuration` skill (new, writes) + paired GPT +
  `/configure-distro-router` command.** Full lifecycle for Distro lead-routing routers
  via the new `distro-router-*` MCP tools (DISTRO-4551/4581) — create (starts Inactive),
  update (full-replace with representability guard), activate/deactivate (async with
  status polling), delete (Inactive-only gate). Defaults to `dry_run: true` with a
  mandatory checkpoint plus a separate activation confirmation. Closes #44.
- **`meeting-type-management` skill (new, writes) + paired GPT + `/manage-meeting-types`
  command.** Full lifecycle for team meeting types and their email/SMS reminders via the
  new `meeting-type-*` MCP tools (DISTRO-4546/4547/4560/4583) — list/get/create/update/
  delete, reminder CRUD, and attach/detach. Defaults to `dry_run: true` with a mandatory
  confirmation checkpoint; prominently separates guest-visible invite fields
  (`inviteTitle`/`inviteDescription`) from the internal `description` label
  (the DISTRO-4583 fix). Closes #34.
- **`chat-conversation-inspector` skill (new, read-only) + paired GPT + `/inspect-chats`
  command.** Inspects Chat AI conversation logs via the new `chat-logs` MCP tool
  (DISTRO-4429) — routing-outcome breakdowns (Routed/NotRouted/Abandoned), per-playbook
  abandonment ranking, full Bot/Guest transcripts, and abandonment analysis. Field names
  taken from the live Edge spec (notably: single `conversationAssigneeId`, booked
  meetings carry no `meetingId`, 0-indexed pages, `pageSize` ≤ 50). Closes #41.
- **`/debug-distro` slash-command wrapper** for the `distro-debugger` skill, matching the
  wrapper convention every other skill already had.

### Fixed
- **Registered `distro-debugger` in the catalog indexes it was missing from** —
  `skills/README.md` (skill index, at `draft` maturity), `gpts/README.md` (GPT table),
  and `docs/QA.md` (status matrix row; pending static review + live run). The skill
  shipped in #35 after the last QA pass and these entries were never backfilled.

## [1.2.0]

### Added
- **Progressive-disclosure authoring standard.** Documented the convention every skill
  follows — Anthropic's Agent Skills progressive disclosure (load only what the current
  step needs) — in `docs/methodology.md` (the principles, the loading stages, file
  budgets, the required SKILL.md shape), with `docs/SKILL.template.md` (a copy-to-start
  stage contract) and an `AGENTS.md` repo-orientation file. Linked from the README,
  `CONTRIBUTING.md`, and `skills/README.md`.

### Changed
- **Structural pass over every skill** to match the standard — each SKILL.md is now a
  lean Inputs → Process → Outputs contract with deep detail (API field names, output
  formats, procedures) split into on-demand `references/*.md` via selective section
  routing, plus a preflight audit and an explicit checkpoint. Behavior, MCP tool calls,
  and field names are unchanged; per-skill `version`s are unchanged (so SKILL↔GPT parity
  holds).
- **`validate_skill_frontmatter.py` now also checks skill structure** — fails CI on
  reference⇄frontmatter mismatch or any `references/*.md` over the 200-line load budget;
  warns (non-failing) on oversized SKILL.md files and over-long descriptions.
- Bumped the **plugin version** (`1.1.0 → 1.2.0`) so org distribution pushes this update
  to installed clients.

## [1.1.0]

### Added
- **Slash-command wrappers for all 11 skills.** Added 9 new commands
  (`/check-availability`, `/debug-concierge`, `/analyze-distribution`,
  `/analyze-no-shows`, `/org-meeting-report`, `/user-details`, `/user-meetings`,
  `/copy-user`, `/offboard-user`) alongside the existing `/inspect-meeting` and
  `/audit-routing`. Skills are model-loaded and don't surface in the `/` menu;
  these thin wrappers make every skill discoverable and runnable under `/chili…`
  (the plugin namespace) in Claude Code. The two write-action wrappers
  (`/copy-user`, `/offboard-user`) default to a dry run and confirm before applying.

## [1.0.0]

Initial public release of the official Chili Piper Skills repository (formerly the internal `gtm-clawllective` cookbook).

### Added
- **11 official skills** for the Chili Piper MCP, each with a matching ChatGPT GPT:
  meeting-inspector, no-show-analyzer, routing-audit, concierge-debugger,
  availability-inspector, org-meeting, distribution-analysis, user-details,
  user-meetings, user-copy, user-offboarding.
- `distribution-analysis` skill (new) — round-robin imbalance analysis on the public MCP.
- Claude Code **plugin + marketplace** (`chili-piper-skills`) for one-step install and auto-update.
- ChatGPT **GPT Actions** generated directly from the live Chili Piper Edge API spec.
- MCP setup guide (API key + OAuth), QA tracker (`docs/QA.md`), and org-deployment guide (`docs/org-deployment.md`).

### Fixed
- Corrected response field-name drift across all skills against the live MCP
  (e.g. `meetingStatus`/`dateTime.start`/`hostId` for meetings; `id` for
  workspaces and teams; real `concierge-logs` status values and `matchedPath`
  object; valid `availability-slots` request shape; `rule-list` workspace
  scoping; `distribution-list-put` array shape).
- Updated `user-meetings` for **DISTRO-4483** — `meeting-export-v2-put` CSV now
  includes `bookedAt` and `meetingId` columns (in production 2026-05-29).

### Changed
- **`user-copy` 0.1.4** — added optional, opt-in product-license copying via
  `user-update-licenses` (new `copy_licenses` input, default `false`). It is
  additive only — grants licenses the source has that the target lacks and never
  revokes (downgrades apply immediately and the call fails on insufficient seats).
  Licenses are read from the existing `user-find` results, surfaced in the dry-run
  plan, and confirmed after the write. Paired `gpts/user-copy/` bumped to 0.1.4
  and its `openapi.yaml` regenerated to expose `userUpdateLicenses`.
- Repurposed the repository from a community GTM cookbook to Chili Piper's
  official, first-party skills; removed community scaffolding.
- GPT Action OpenAPI specs now target the real Edge API
  (`https://fire.chilipiper.com/api/fire-edge`, Bearer auth) instead of a
  placeholder URL, and are kept in sync via CI (`check_gpt_sync.py`).

---

*Versioning: skill changes bump the skill's `SKILL.md` `version` and the paired `GPT.md` `version` (parity enforced in CI). Release tags will be cut from this changelog once the repo is public.*

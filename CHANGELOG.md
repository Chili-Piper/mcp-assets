# Changelog

All notable changes to the official Chili Piper Skills are recorded here. The repo follows [Keep a Changelog](https://keepachangelog.com/); each skill also carries its own `version` in its `SKILL.md` (and matching `GPT.md`).

## [Unreleased]

### Added
- **Cursor plugin (`.cursor-plugin/plugin.json` + root `mcp.json`).** Makes this repo
  installable as a first-party [Cursor](https://cursor.com) plugin (also surfaced in the
  Grok bot plugin list), reusing the same `skills/` and `commands/` as the Claude plugin.
  The plugin points at the same hosted MCP
  (`https://fire.chilipiper.com/api/fire-edge/v1/org/mcp`) and uses the existing one-click
  OAuth flow — no JSON to paste, API key optional. Ships the official Chili Piper logo
  (`assets/chili-piper-logo.svg`) and a Cursor install path in the README, ready for
  submission to the Cursor Marketplace.
- **`concierge-router-builder` skill (new, writes) + paired GPT +
  `/build-concierge-router` command.** A guided, end-to-end builder that stands up a
  complete Concierge web-form router from scratch — teams, meeting types, rules
  (ownership / customer / segment), distributions, and the live router — via a discovery
  interview, a confirmation checkpoint, then a dependency-ordered build over
  `team-create`, `meeting-type-create`, `rule-create`, `distribution-create`, and
  `concierge-router-create`. The build is not transactional and the router publishes live,
  so it defaults to `dry_run: true` and stops for confirmation before creating anything.
  Complements the CRUD `concierge-router-configuration` skill (build-from-scratch vs edit).
  Documents the current API gap: **data fields and web-form
  mapping are UI-only** (no MCP/Edge tool to list, create, or map them) — the router can
  only reference data fields that already exist.
- **Google Gemini support guide** (`gemini/README.md`) — how to connect the Chili Piper
  MCP from Gemini CLI (`~/.gemini/settings.json`), the Google Gen AI SDK / ADK
  (`McpToolset` over streamable HTTP), and Gemini Enterprise (custom MCP data store),
  including the explicit caveat that the consumer Gemini app and Gems do not support
  custom MCP servers. Added a Gemini CLI config snippet to
  `mcp-servers/chili-piper/README.md` and a `gemini/` row to the root README index.

### Changed
- **`distro-router-configuration` 0.2.0** (SKILL + paired GPT + regenerated
  `openapi.yaml`) — **`distro-router-update` is now an overlay; the
  abort-on-unrepresentable rule is retired** (live spec v1.311.1, the DISTRO-4621
  deferral of DISTRO-4614's opaque-preserve overlay has landed for Distro). Sent routes
  are matched to the router's existing routing by `ruleId` (catch-all to catch-all) and
  only their distribution + actions swap in — app-only config (SLAs, matchers, campaign
  addition, lead-to-contact conversion, send-to-routers, duplicate-matching) is
  preserved, so **any router can be edited**; `routing.representable` is advisory only.
  Documented the sharp edges that come with it: the trigger and `routingSteps` are
  still **replaced** from what you send (empty/absent `routingSteps` **clears** them —
  read them back first, carry step `id`s); ≥1 action per route and on the catch-all is
  required to publish (`ruleId`-matched rows keep their existing actions); the overlay
  applies to the router's editable **draft** (unpublished app edits included); and a
  failed update is **not rolled back** — publish failure leaves the changes on an
  unpublished draft, re-activation failure leaves the new config published but the
  router `Inactive` (typed 422 either way). `routing` remains required on every update
  and name/description keep their CEH-11002 PATCH semantics.
- **`concierge-router-configuration` 0.1.1** (SKILL + paired GPT) — documented the
  **data-field API gap** surfaced while building `concierge-router-builder` (#65): no
  MCP/Edge tool lists, reads, creates, or maps data fields, and web-form mapping is
  UI-only, so `form`/trigger writes may only *reference* existing data fields (standard
  defaults like `PersonEmail` always valid; custom fields by their UUID from the app) —
  an unknown `dataField` fails the write with **400** (new typed-error row + preflight
  check). Also noted that `concierge-router-create` requires a **team** workspace, added
  a grammar sync note pointing at `concierge-router-builder`'s api-reference, and
  cross-linked "When to use" both ways (edit/CRUD here; guided build-from-scratch →
  `concierge-router-builder`).
- **Setup guide: API token permissions are now editable in place** (Edge release
  2026-07-21) — noted in `mcp-servers/chili-piper/README.md` § Getting your API key
  that a token's permissions can be edited without regenerating it (the token value
  doesn't change), so a missing-scope 403 no longer means minting a new key.

## [1.3.0]

### Added
- **`scheduling-link-management` skill (new, writes) + paired GPT +
  `/manage-scheduling-links` command.** Lifecycle for scheduling links across all four
  admin link types — round-robin, admin one-on-one, group, ownership — via the new
  `scheduling-link-*` create/update/delete MCP tools (DISTRO-4548), plus cross-type
  audits including personal links (list-only). Dry-run first; every plan quotes the
  affected booking URL (deletes and slug changes kill it instantly). Closes #37.
- **`concierge-router-configuration` skill (new, writes) + paired GPT +
  `/configure-concierge-router` command.** CRUD for Concierge web-form routers via the
  new `concierge-router-*` MCP tools (DISTRO-4549) — routing rows, form fields, and
  branding. Always-live (no inactive state; delete kills the public form slug instantly);
  full-replace updates with a representability gate. The write complement to the
  read-only `concierge-debugger` and `routing-audit` skills. Closes #38.
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

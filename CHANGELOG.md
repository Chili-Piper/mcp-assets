# Changelog

All notable changes to the official Chili Piper Skills are recorded here. The repo follows [Keep a Changelog](https://keepachangelog.com/); each skill also carries its own `version` in its `SKILL.md` (and matching `GPT.md`).

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

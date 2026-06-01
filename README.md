# Chili Piper Skills

**Official, first-party Skills and ChatGPT GPTs for the [Chili Piper](https://chilipiper.com) MCP server.**

Maintained by Chili Piper. These are ready-to-use AI specialists — meeting diagnostics, routing audits, user onboarding/offboarding, no-show analysis, and more — that run against your own Chili Piper account through the official Chili Piper MCP.

> **Sponsored and maintained by Chili Piper.** This repository lives under the verified [`Chili-Piper`](https://github.com/Chili-Piper) GitHub organization.

---

## What's in here

| Folder | What it is |
|--------|-----------|
| [`skills/`](skills/) | **Claude Code / Claude Skills** — drop-in specialists that call the Chili Piper MCP. One job each, done well. |
| [`gpts/`](gpts/) | **ChatGPT Custom GPTs** — the ChatGPT equivalent of each skill, with a GPT Actions schema. |
| [`mcp-servers/chili-piper/`](mcp-servers/chili-piper/) | **MCP setup guide** — connect the Chili Piper MCP via API key or OAuth. |
| [`docs/`](docs/) | QA status tracker and org-level deployment guide. |

A **Skill** is a small, self-contained instruction set that teaches an AI agent how to do one Chili Piper task correctly — which MCP tools to call, in what order, and how to format the result. A **GPT** is the same capability packaged for ChatGPT.

### Available skills

| Skill | What it does | Read-only? |
|-------|-------------|:---:|
| [meeting-inspector](skills/meeting-inspector/) | Deep-dive a single meeting — booking trigger, routing path, rep assignment, outcome | ✅ |
| [no-show-analyzer](skills/no-show-analyzer/) | Analyze no-show patterns by trigger, route, rep, or workspace | ✅ |
| [routing-audit](skills/routing-audit/) | Audit all concierge routers for coverage gaps and stale rules | ✅ |
| [availability-inspector](skills/availability-inspector/) | Diagnose why a rep or team shows no available slots | ✅ |
| [concierge-debugger](skills/concierge-debugger/) | Trace why a specific lead didn't book | ✅ |
| [org-meeting](skills/org-meeting/) | Org-wide meeting volume and health snapshot | ✅ |
| [user-details](skills/user-details/) | Full profile for any Chili Piper user | ✅ |
| [user-meetings](skills/user-meetings/) | Rep-level meeting volume and health metrics | ✅ |
| [user-copy](skills/user-copy/) | Copy a user's workspace/team memberships to another user | ⚠️ writes |
| [user-offboarding](skills/user-offboarding/) | Safely remove a departing rep, with an audit trail | ⚠️ writes |

See [`skills/README.md`](skills/README.md) for the full index with QA/maturity status, and [`gpts/README.md`](gpts/README.md) for the ChatGPT versions.

---

## Get started

### 1. Connect the Chili Piper MCP

Every skill talks to your Chili Piper account through the official MCP server. Set it up once — **API key** or **OAuth** — following [`mcp-servers/chili-piper/README.md`](mcp-servers/chili-piper/README.md).

### 2. Install the skills — pick your surface

**Option A — Claude Code CLI (plugin; auto-updates):**

In the standalone Claude Code terminal CLI:

```
/plugin marketplace add Chili-Piper/mcp-assets
/plugin install chili-piper-skills@chili-piper-skills
```

This installs every skill, the bundled slash commands, and the Chili Piper MCP config in one step. Updating later is a single command (see [Staying up to date](#staying-up-to-date)).

> **Note:** `/plugin` is **only** available in the Claude Code **terminal CLI** — not in the Claude Desktop app or claude.ai. If you're on Desktop/web, use Option B.

**Option B — Claude Desktop / claude.ai (upload a skill):**

Skills install through Claude's **Customize → Skills** panel (no `/plugin` needed):

1. Download the skill's `.zip` from the [latest release](https://github.com/Chili-Piper/mcp-assets/releases/latest) — e.g. [`meeting-inspector.zip`](https://github.com/Chili-Piper/mcp-assets/releases/latest/download/meeting-inspector.zip). Each skill is a separate `.zip`.
2. Open **Customize → Skills → ＋** and upload the `.zip`. It's added as a **Personal skill** (just you — local to your account).
3. Make sure the **Chili Piper MCP** connector is connected with your own API key or OAuth ([setup](mcp-servers/chili-piper/README.md)).

> **Org admins:** to roll a skill out to your whole team, upload it under **Organization skills** and turn on **Share**. Personal (local) and Organization (org-wide) are both supported — users can self-serve either way.

**Option C — ChatGPT:** deploy the matching Custom GPT — see [`gpts/README.md`](gpts/README.md).

### 3. Run a skill

In Claude Code:

```
/inspect-meeting guest@example.com
/audit-routing "APAC Sales"
```

Or just ask in natural language — the agent loads the matching skill automatically.

---

## Deploy for your whole team

A single admin can roll these skills out to an entire team or org so everyone gets the same vetted specialists. See [`docs/org-deployment.md`](docs/org-deployment.md).

---

## Staying up to date

We actively improve these skills, fix correctness issues, and add new ones. To stay current:

- **Claude Code plugin:** run `/plugin update chili-piper-skills@chili-piper-skills` (or enable auto-update).
- **Claude Desktop / claude.ai:** re-download the skill `.zip` from the [latest release](https://github.com/Chili-Piper/mcp-assets/releases/latest) and re-upload it in Customize → Skills.
- **Manual install:** `git pull`, or re-download the skill folder.
- **Watch releases:** click **Watch → Custom → Releases** on this repo to be notified of every versioned update.
- **Changelog:** every release is logged in [`CHANGELOG.md`](CHANGELOG.md).
- **Discussions:** announcements and Q&A live in GitHub Discussions.

Each skill carries a `version` in its frontmatter and a maturity level (`draft` / `tested` / `verified`) so you always know how battle-tested it is.

---

## Data & security

This repository contains **zero customer data** — skills are instructions only. Your data stays in your Chili Piper account and is accessed live via the MCP using your own credentials. See [SECURITY.md](SECURITY.md).

---

## Contributing & support

Found a bug or want a new skill? Open an [issue](https://github.com/Chili-Piper/mcp-assets/issues). For product/security questions see [SECURITY.md](SECURITY.md).

**License:** MIT for code · CC-BY 4.0 for content — see [LICENSE](LICENSE).

---

*Official Chili Piper Skills. The MCP is the door into your Chili Piper account — these skills are the playbook for using it well.*

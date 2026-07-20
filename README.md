# Chili Piper Skills

**Official, first-party Skills and ChatGPT GPTs for the [Chili Piper](https://chilipiper.com) MCP server.**

Maintained by Chili Piper. These are ready-to-use AI specialists — meeting diagnostics, routing audits, user onboarding/offboarding, no-show analysis, and more — that run against your own Chili Piper account through the official Chili Piper MCP.

**Two pieces, one workflow.** The [Chili Piper MCP](mcp-servers/chili-piper/) is the *connection* into your account — set it up once. **Skills** are the vetted *recipes* that use it well. Connect the MCP, install the skills, then just ask.

> 📚 **On the Help Center:** [How do I connect Chili Piper via MCP?](https://help.chilipiper.com/hc/en-us/articles/50430350863635-How-do-I-connect-Chili-Piper-via-MCP) — plus the companion **Chili Piper Skills (AI recipes)** article *(publishing soon)*.

> **Sponsored and maintained by Chili Piper.** This repository lives under the verified [`Chili-Piper`](https://github.com/Chili-Piper) GitHub organization.

---

## What's in here

| Folder | What it is |
|--------|-----------|
| [`skills/`](skills/) | **Claude Code / Claude Skills** — drop-in specialists that call the Chili Piper MCP. One job each, done well. |
| [`gpts/`](gpts/) | **ChatGPT Custom GPTs** — the ChatGPT equivalent of each skill, with a GPT Actions schema. |
| [`mcp-servers/chili-piper/`](mcp-servers/chili-piper/) | **MCP setup guide** — connect the Chili Piper MCP via API key or OAuth. |
| [`gemini/`](gemini/) | **Google Gemini guide** — connect via Gemini CLI, Gen AI SDK / ADK, or Gemini Enterprise. |
| [`docs/`](docs/) | Authoring methodology, QA status tracker, and org-level deployment guide. |

A **Skill** is a small, self-contained instruction set that teaches an AI agent how to do one Chili Piper task correctly — which MCP tools to call, in what order, and how to format the result. A **GPT** is the same capability packaged for ChatGPT.

Every skill is built on **[progressive disclosure](docs/methodology.md)** (Anthropic's Agent Skills convention), so an agent loads only the slice of a skill the current step needs.

### Available skills

| Skill | What it does | Read-only? |
|-------|-------------|:---:|
| [meeting-inspector](skills/meeting-inspector/) | Deep-dive a single meeting — booking trigger, routing path, rep assignment, outcome | ✅ |
| [no-show-analyzer](skills/no-show-analyzer/) | Analyze no-show patterns by trigger, route, rep, or workspace | ✅ |
| [routing-audit](skills/routing-audit/) | Audit all concierge routers for coverage gaps and stale rules | ✅ |
| [distribution-analysis](skills/distribution-analysis/) | Analyze a round-robin distribution — meeting counts by rep, imbalance vs. weights, skew, cancellations | ✅ |
| [availability-inspector](skills/availability-inspector/) | Diagnose why a rep or team shows no available slots | ✅ |
| [concierge-debugger](skills/concierge-debugger/) | Trace why a specific lead didn't book | ✅ |
| [distro-debugger](skills/distro-debugger/) | Debug why a CRM record was (or wasn't) routed through a distribution — rule stage by rule stage | ✅ |
| [chat-conversation-inspector](skills/chat-conversation-inspector/) | Inspect Chat AI conversation logs — routing outcomes, transcripts, abandonment analysis | ✅ |
| [org-meeting](skills/org-meeting/) | Org-wide meeting volume and health snapshot | ✅ |
| [user-details](skills/user-details/) | Full profile for any Chili Piper user | ✅ |
| [user-meetings](skills/user-meetings/) | Rep-level meeting volume and health metrics | ✅ |
| [user-copy](skills/user-copy/) | Copy a user's workspace/team memberships to another user | ⚠️ writes |
| [user-offboarding](skills/user-offboarding/) | Safely remove a departing rep, with an audit trail | ⚠️ writes |
| [meeting-type-management](skills/meeting-type-management/) | Manage team meeting types and their reminders — durations, invite text, booking limits | ⚠️ writes |

See [`skills/README.md`](skills/README.md) for the full index with QA/maturity status, and [`gpts/README.md`](gpts/README.md) for the ChatGPT versions.

---

## Get started

### 1. Connect the Chili Piper MCP

Every skill talks to your Chili Piper account through the official MCP server. Set it up once — **API key** or **OAuth** — following [`mcp-servers/chili-piper/README.md`](mcp-servers/chili-piper/README.md).

### 2. Install the skills — pick your surface

**Option A — Claude Desktop or claude.ai (plugin, easiest — no terminal):**

Install the whole plugin (every skill + the Chili Piper MCP config) right inside Claude:

1. Open **Customize → Plugins** (or **Connectors**), click **＋** next to **Personal plugins** → **Create plugin → Add marketplace**.
2. Paste `https://github.com/Chili-Piper/mcp-assets` and click **Sync**.
3. Go to the **Directory → Plugins** (the **Personal** tab), open the **mcp-assets** marketplace, and click **＋** on **Chili Piper Skills** to install.

> **Admins:** add it under **Organization plugins** instead to make it available to your whole org in one step — see [Deploy for your whole team](#deploy-for-your-whole-team).

**Option B — Claude Code CLI (plugin):**

In the standalone Claude Code terminal CLI:

```
/plugin marketplace add https://github.com/Chili-Piper/mcp-assets
/plugin install chili-piper-skills@chili-piper-skills
```

> Both the marketplace and plugin are named **`chili-piper-skills`** (the ref is `plugin-name@marketplace-name`); or run `/plugin` and pick it from the **Marketplaces** menu. `/plugin` is CLI-only — on Desktop/web use Option A.
>
> **See a `git@github.com: Permission denied` / SSH error?** No key is needed for this public repo — tell git to use HTTPS and retry:
> ```
> git config --global url."https://github.com/".insteadOf "git@github.com:"
> ```

Options A and B install the full plugin (skills + slash commands + MCP config) and keep it updated — see [Staying up to date](#staying-up-to-date).

**Option C — Just one skill (upload a single `.zip`):**

Want only one skill, or to push a single skill as an **Organization skill**? Download it from the [latest release](https://github.com/Chili-Piper/mcp-assets/releases/latest) (e.g. [`meeting-inspector.zip`](https://github.com/Chili-Piper/mcp-assets/releases/latest/download/meeting-inspector.zip)) and upload it via **Customize → Skills → ＋** (added as a Personal skill; admins can choose **Organization** + **Share**).

**Option D — ChatGPT:** deploy the matching Custom GPT — see [`gpts/README.md`](gpts/README.md).

### 3. Run a skill

In Claude Code:

```
/inspect-meeting guest@example.com
/audit-routing "APAC Sales"
```

Or just ask in natural language — the agent loads the matching skill automatically.

Every skill also has a slash-command wrapper, so they all surface when you type `/chili…` (the plugin namespace). Type `/` to browse:

| Command | Skill |
|---|---|
| `/inspect-meeting` | meeting-inspector |
| `/audit-routing` | routing-audit |
| `/check-availability` | availability-inspector |
| `/debug-concierge` | concierge-debugger |
| `/debug-distro` | distro-debugger |
| `/inspect-chats` | chat-conversation-inspector |
| `/analyze-distribution` | distribution-analysis |
| `/analyze-no-shows` | no-show-analyzer |
| `/org-meeting-report` | org-meeting |
| `/user-details` | user-details |
| `/user-meetings` | user-meetings |
| `/copy-user` | user-copy |
| `/offboard-user` | user-offboarding |
| `/manage-meeting-types` | meeting-type-management |

`/copy-user`, `/offboard-user`, and `/manage-meeting-types` write to Chili Piper — they default to a dry run and confirm before applying.

---

## Deploy for your whole team

A single admin can roll these skills out to an entire team or org so everyone gets the same vetted specialists — and for a first-party set like this, org-wide is often the right call.

**Easiest (Claude Desktop / claude.ai):** add the marketplace under **Organization plugins** (Customize → **Organization plugins → ＋ → Create plugin → Add marketplace** → `https://github.com/Chili-Piper/mcp-assets` → **Sync**). It then shows up for everyone in your org's **Directory → Your organization** tab.

For Claude Code (settings.json), managed/enterprise rollout, and the private-fork option, see [`docs/org-deployment.md`](docs/org-deployment.md).

---

## Staying up to date

We actively improve these skills, fix correctness issues, and add new ones. To stay current:

- **Claude Desktop / claude.ai (plugin):** the plugin updates from the marketplace automatically; if needed, re-open **Add marketplace** and **Sync** to refresh.
- **Claude Code plugin:** run `/plugin update chili-piper-skills@chili-piper-skills` (or enable auto-update).
- **Single skill installed via `.zip`:** re-download from the [latest release](https://github.com/Chili-Piper/mcp-assets/releases/latest) and re-upload in Customize → Skills.
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

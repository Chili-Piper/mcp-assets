# Deploying Chili Piper Skills to your whole team

These skills ship as a **plugin** (`chili-piper-skills`) served from this repo's marketplace — installable in **Claude Desktop, claude.ai, and Claude Code**. A single admin can roll it out to an entire team so individual users don't each install by hand. The approaches below go from the simple in-app **Directory** to centrally-managed enterprise settings.

> **Names to know:** the marketplace lives in this repo, `Chili-Piper/mcp-assets`. The plugin is `chili-piper-skills`. So the fully-qualified plugin ref is `chili-piper-skills@chili-piper-skills`.

---

## Option 1 — Add it in the Directory (Claude Desktop / claude.ai — easiest)

No terminal, no settings files — just the in-app Directory:

**For one person (personal):**
1. **Customize → Plugins** (or **Connectors**) → **＋** next to **Personal plugins** → **Create plugin → Add marketplace**.
2. Paste `https://github.com/Chili-Piper/mcp-assets` → **Sync**.
3. **Directory → Plugins → Personal** → open the **mcp-assets** marketplace → click **＋** on **Chili Piper Skills**.

**For the whole org (admin):**
Do the same but from **＋ next to Organization plugins**. The plugin then appears for everyone under **Directory → Your organization**, so members don't install anything by hand. This is the simplest org-wide path for most teams.

> **Want a controlled/frozen copy?** Some orgs fork `Chili-Piper/mcp-assets` into a **private** repo and add *that* as the marketplace, so updates land on their own schedule and the catalog is locked to what they've vetted. Point the marketplace URL at the private repo instead (members need access to it). Otherwise, pointing at the public repo always serves the latest released version.

---

## Option 2 — Each user installs via Claude Code CLI

Two commands in Claude Code:

```
/plugin marketplace add https://github.com/Chili-Piper/mcp-assets
/plugin install chili-piper-skills@chili-piper-skills
```

Good for trying it out or small teams. Everyone runs it once; updates via `/plugin update` (see below).

> **SSH clone error?** If a user sees `git@github.com: Permission denied`, their git is cloning over SSH. This public repo needs no key — have them run this once and retry:
> ```
> git config --global url."https://github.com/".insteadOf "git@github.com:"
> ```

---

## Option 3 — Ship it with a team repo (Claude Code, settings.json)

Commit the marketplace + plugin into a shared repository's `.claude/settings.json`. When a teammate opens that repo in Claude Code and trusts the folder, they're **prompted to install** automatically — no manual commands.

`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "chili-piper-skills": {
      "source": { "source": "github", "repo": "Chili-Piper/mcp-assets" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "chili-piper-skills@chili-piper-skills": true
  }
}
```

This is the GitOps path: it's version-controlled, shared with everyone who clones the repo, and still consent-based (each user confirms on first trust).

---

## Option 4 — Enforce org-wide via managed settings (enterprise)

For centrally-managed fleets, IT can place the same config in Claude Code's **managed settings**, which users cannot override:

- macOS / Linux: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json` (or the corresponding `HKLM` policy)

```json
{
  "extraKnownMarketplaces": {
    "chili-piper-skills": {
      "source": { "source": "github", "repo": "Chili-Piper/mcp-assets" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "chili-piper-skills@chili-piper-skills": true
  }
}
```

Deploy this file via your MDM / configuration management. Managed settings take precedence over user and project settings. If your security team maintains an allowlist, add `Chili-Piper/mcp-assets` to `strictKnownMarketplaces`.

**Settings precedence (high → low):** managed settings → CLI flags → `.claude/settings.local.json` → `.claude/settings.json` → `~/.claude/settings.json`.

---

## Staying up to date

- With `"autoUpdate": true` (above), clients pull new plugin versions on startup.
- Otherwise, users run `/plugin update chili-piper-skills@chili-piper-skills` (or `/plugin marketplace update chili-piper-skills`).
- Each skill carries a `version`; releases are listed in [`../CHANGELOG.md`](../CHANGELOG.md). Watch this repo (**Watch → Custom → Releases**) for notifications.

---

## The bundled MCP connection

The plugin includes the Chili Piper MCP config (`.mcp.json`). On install, Claude Code shows a one-time trust prompt because the plugin bundles an MCP server — expected for a first-party plugin. Each user still authenticates with **their own** Chili Piper credentials (API key or OAuth) per [`../mcp-servers/chili-piper/README.md`](../mcp-servers/chili-piper/README.md); the plugin ships configuration, never credentials.

---

## How skills are discovered

Skills installed via the plugin are namespaced — invoke them as `/chili-piper-skills:<skill>` (e.g. `/chili-piper-skills:meeting-inspector`), or just describe the task and let the agent pick. Project- or user-level skills dropped into a `.claude/skills/` directory are invoked without the prefix; bundling them in the plugin is what makes org-wide distribution and updates clean.

---

*Mechanics reflect Claude Code as of mid-2026; if a command or settings key has changed, the current behavior in `/plugin` and the Claude Code docs is authoritative.*

# Deploying Chili Piper Skills to your whole team

These skills ship as a Claude Code **plugin** (`chili-piper-skills`) served from this repo's marketplace. A single admin can roll them out to an entire team so individual users don't each install by hand. There are three approaches, from lightest to most locked-down.

> **Names to know:** the marketplace lives in this repo, `Chili-Piper/mcp-assets`. The plugin is `chili-piper-skills`. So the fully-qualified plugin ref is `chili-piper-skills@Chili-Piper-mcp-assets`.

---

## Option 1 — Each user installs (simplest)

Two commands in Claude Code:

```
/plugin marketplace add https://github.com/Chili-Piper/mcp-assets
/plugin install chili-piper-skills@Chili-Piper-mcp-assets
```

Good for trying it out or small teams. Everyone runs it once; updates via `/plugin update` (see below).

> **SSH clone error?** If a user sees `git@github.com: Permission denied`, their git is cloning over SSH. This public repo needs no key — have them run this once and retry:
> ```
> git config --global url."https://github.com/".insteadOf "git@github.com:"
> ```

---

## Option 2 — Ship it with a team repo (recommended for teams)

Commit the marketplace + plugin into a shared repository's `.claude/settings.json`. When a teammate opens that repo in Claude Code and trusts the folder, they're **prompted to install** automatically — no manual commands.

`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "Chili-Piper-mcp-assets": {
      "source": { "source": "url", "url": "https://github.com/Chili-Piper/mcp-assets.git", "ref": "main" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "chili-piper-skills@Chili-Piper-mcp-assets": true
  }
}
```

This is the GitOps path: it's version-controlled, shared with everyone who clones the repo, and still consent-based (each user confirms on first trust).

---

## Option 3 — Enforce org-wide via managed settings (enterprise)

For centrally-managed fleets, IT can place the same config in Claude Code's **managed settings**, which users cannot override:

- macOS / Linux: `/etc/claude-code/managed-settings.json`
- Windows: `C:\Program Files\ClaudeCode\managed-settings.json` (or the corresponding `HKLM` policy)

```json
{
  "extraKnownMarketplaces": {
    "Chili-Piper-mcp-assets": {
      "source": { "source": "url", "url": "https://github.com/Chili-Piper/mcp-assets.git", "ref": "main" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "chili-piper-skills@Chili-Piper-mcp-assets": true
  }
}
```

Deploy this file via your MDM / configuration management. Managed settings take precedence over user and project settings. If your security team maintains an allowlist, add `Chili-Piper/mcp-assets` to `strictKnownMarketplaces`.

**Settings precedence (high → low):** managed settings → CLI flags → `.claude/settings.local.json` → `.claude/settings.json` → `~/.claude/settings.json`.

---

## Staying up to date

- With `"autoUpdate": true` (above), clients pull new plugin versions on startup.
- Otherwise, users run `/plugin update chili-piper-skills@Chili-Piper-mcp-assets` (or `/plugin marketplace update Chili-Piper-mcp-assets`).
- Each skill carries a `version`; releases are listed in [`../CHANGELOG.md`](../CHANGELOG.md). Watch this repo (**Watch → Custom → Releases**) for notifications.

---

## The bundled MCP connection

The plugin includes the Chili Piper MCP config (`.mcp.json`). On install, Claude Code shows a one-time trust prompt because the plugin bundles an MCP server — expected for a first-party plugin. Each user still authenticates with **their own** Chili Piper credentials (API key or OAuth) per [`../mcp-servers/chili-piper/README.md`](../mcp-servers/chili-piper/README.md); the plugin ships configuration, never credentials.

---

## How skills are discovered

Skills installed via the plugin are namespaced — invoke them as `/chili-piper-skills:<skill>` (e.g. `/chili-piper-skills:meeting-inspector`), or just describe the task and let the agent pick. Project- or user-level skills dropped into a `.claude/skills/` directory are invoked without the prefix; bundling them in the plugin is what makes org-wide distribution and updates clean.

---

*Mechanics reflect Claude Code as of mid-2026; if a command or settings key has changed, the current behavior in `/plugin` and the Claude Code docs is authoritative.*

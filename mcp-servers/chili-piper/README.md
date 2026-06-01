# Chili Piper MCP Server

The official Chili Piper MCP server. Gives AI agents a door into your Chili Piper account — routing, scheduling, handoff data, meeting analytics.

Maintained by the Chili Piper engineering team.

---

## What it does

The Chili Piper MCP exposes all public org API endpoints as tools. Key capabilities:

| Capability | MCP tools | Use case |
|-----------|-----------|---------|
| Routing & concierge | `concierge-list-routers`, `concierge-route-by-slug`, `concierge-logs` | Run a router, inspect routing decisions |
| Meeting analytics | `meeting-list-put`, `meeting-get` | No-show analysis, meeting lifecycle inspection |
| Availability | `availability-slots` | Show combined rep availability |
| Handoff | `handoff-init`, `handoff-schedule` | SDR → AE booking |
| Users & teams | `user-find`, `team-list-put`, `workspace-list` | Onboarding, offboarding, audits |
| Routing rules | `rule-list`, `rule-get`, `rule-create`, `rule-modify` | Audit and manage routing logic |
| Distributions | `distribution-list-put`, `distribution-adjust-v3` | Round-robin queue management |

> **Minimum data by default.** The MCP returns only what you ask for. API keys can be scoped to the exact permissions your recipe needs — see [API permissions](#api-permissions) below.

---

## Requirements

- A Chili Piper account with API access
- An API key from Admin Center (or OAuth via browser login — see below)
- Claude Code (or any MCP-compatible client that supports HTTP transport)

> No Chili Piper account = no access through this door. The MCP is the door, not the building.

---

## Installation

The Chili Piper MCP uses **HTTP transport** — it connects directly to Chili Piper's cloud API. No local server process to install or maintain.

### Option A — API key (recommended for most users)

Any Chili Piper user with API access can generate an API key in Admin Center and use it here. No Admin role required.

**Claude Code (one command):**

```bash
claude mcp add --transport http chili-piper \
  https://fire.chilipiper.com/api/fire-edge/v1/org/mcp \
  --header "Authorization: Bearer YOUR_API_KEY"
```

Replace `YOUR_API_KEY` with the key from Admin Center.

**Manual config** — add to `~/.claude.json` (or your agent's MCP config file):

```json
{
  "mcpServers": {
    "chili-piper": {
      "type": "http",
      "url": "https://fire.chilipiper.com/api/fire-edge/v1/org/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

> Store your API key in an environment variable or your OS keychain — never hardcode it in a committed file. Use `${CHILI_PIPER_API_KEY}` in the JSON to reference an env var.

**Cursor / Windsurf / other MCP clients:** use the same JSON format in your client's MCP config file.

### Option B — OAuth (Admin role required)

Claude Code and Codex support browser-based OAuth login — the agent handles token acquisition and refresh automatically.

> **Requires Admin role.** OAuth login authenticates you as a Chili Piper user directly. Only Admins have the org-wide permissions the MCP needs to function across all tools. Non-admin users should use Option A (API key) instead.

**Claude Code:**

```bash
claude mcp add --transport http chili-piper \
  https://fire.chilipiper.com/api/fire-edge/v1/org/mcp
```

On first use, Claude Code opens a browser window for Chili Piper login. Tokens are stored in Claude Code's credential store and refreshed automatically.

**Codex:**

```bash
codex mcp add chili-piper \
  --url https://fire.chilipiper.com/api/fire-edge/v1/org/mcp
```

> OAuth must be enabled for your tenant by Chili Piper. Contact support if the browser prompt does not appear on first use.

---

## API permissions

API keys are scoped. Assign only the permissions your recipe needs. Common scopes:

| Scope | Needed for |
|---|---|
| `api.ping` | Health check |
| `meeting.read` | `meeting-list-put`, `meeting-get` |
| `meeting.modify` | `meeting-cancel`, `meeting-noshow` |
| `concierge.read` | `concierge-list-routers`, `concierge-logs` |
| `concierge.schedule` | `concierge-route-by-slug`, `concierge-schedule` |
| `availability.read` | `availability-slots` |
| `handoff.schedule` | `handoff-init`, `handoff-schedule` |
| `user.read` | `user-find`, `user-read` |
| `workspace.read` | `workspace-list`, `workspace-list-users` |
| `team.read` | `team-list-put` |
| `rule.read` | `rule-list`, `rule-get` |
| `rule.create` / `rule.modify` / `rule.remove` | Rule management |
| `scheduling-links.read` | `scheduling-link-list-*` |

**Read-only key** (safe for analytics recipes): `api.ping` + `meeting.read` + `concierge.read` + `user.read` + `workspace.read` + `team.read` + `availability.read` + `rule.read` + `scheduling-links.read`

**Full scheduling key** (for booking/routing recipes): add `concierge.schedule` + `handoff.schedule` + `scheduling-links.schedule` + `meeting.modify`

Create and manage keys in **Admin Center > API Keys**.

---

## Getting your API key

1. Log in to your Chili Piper account
2. Navigate to **Admin Center** (top-right menu)
3. Go to **API Keys**
4. Click **Create new key**, name it, select scopes, copy the key
5. Store it in your environment: `export CHILI_PIPER_API_KEY=your_key_here`

Full guide: [help.chilipiper.com — Edge API References](https://help.chilipiper.com/hc/en-us/articles/35576029581971)

---

## Security

- API keys go in environment variables or your OS keychain — never in committed files
- Use the `local/` subfolder (gitignored) for recipe-specific credentials
- Scope API keys to exactly the permissions your recipe needs
- See [SECURITY.md](../../SECURITY.md) for the full six-layer security model

---

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

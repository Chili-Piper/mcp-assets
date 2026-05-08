# Chili Piper MCP Server

The official Chili Piper MCP server. Gives AI agents a door into your Chili Piper account — routing, scheduling, handoff data, meeting analytics.

Maintained by the Chili Piper engineering team.

---

## What it does

The Chili Piper MCP exposes these capabilities to Claude Code agents and recipes:

| Capability | What it returns | Use case |
|-----------|----------------|---------|
| `is_meeting_fit` | yes/no fit signal | Qualify before routing |
| `get_routing_rules` | Active routing logic | Audit or debug routing |
| `get_meeting_analytics` | Meeting show rates, no-shows by segment | Optimize booking flows |
| `create_handoff` | Structured handoff record | SDR → AE, Sales → CS |
| `get_handoff_status` | Status of in-flight handoffs | Monitor pipeline health |

> **Minimum data by default.** The MCP returns fitness signals rather than full records. This is intentional — see [SECURITY.md](../../SECURITY.md) Layer 5.

---

## Requirements

- A Chili Piper account with API access
- An API key from your Chili Piper admin settings
- Claude Code (or any MCP-compatible AI client)

> No Chili Piper account = no access through this door. The MCP is the door, not the building.

---

## Installation

### One-command install

```bash
# Add to your Claude Code MCP config
claude mcp add chili-piper \
  --command "npx @chilipiper/mcp-server" \
  --env CHILI_PIPER_API_KEY=your_api_key_here
```

### Manual install

1. Clone this directory or install via npm:
   ```bash
   npm install -g @chilipiper/mcp-server
   ```

2. Add to your `claude_desktop_config.json` (never commit this file):
   ```json
   {
     "mcpServers": {
       "chili-piper": {
         "command": "npx",
         "args": ["@chilipiper/mcp-server"],
         "env": {
           "CHILI_PIPER_API_KEY": "your_api_key_here"
         }
       }
     }
   }
   ```

3. Restart Claude Code. The Chili Piper tools will appear automatically.

---

## Local development

```bash
cd mcp-servers/chili-piper
npm install
npm run dev
```

Copy `.env.example` to `local/.env` (gitignored) and add your API key.

---

## Security

Your API key belongs in `local/.env` — never in a committed file. See [SECURITY.md](../../SECURITY.md).

---

## Contributing

Issues and PRs welcome. The server code lives in this directory. See [.community/CONTRIBUTING.md](../../.community/CONTRIBUTING.md).

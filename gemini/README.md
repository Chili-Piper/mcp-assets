# Using Chili Piper with Google Gemini

The Chili Piper MCP server is client-agnostic — the same endpoint that powers Claude and Cursor works with Google's Gemini tooling. This guide covers the three Gemini surfaces that support custom MCP servers today, and is honest about the one that doesn't.

**Server URL (same for every client):**

```
https://fire.chilipiper.com/api/fire-edge/v1/org/mcp
```

**Authentication:** use a Chili Piper **API key** (Bearer token). Generating a key requires an Admin — see [Getting your API key](../mcp-servers/chili-piper/README.md#getting-your-api-key).

---

## At a glance

| Gemini surface | Custom MCP support | Who it's for |
|---|:---:|---|
| **Gemini CLI** | ✅ | Most users — the direct analog to Claude Code |
| **Google Gen AI SDK / ADK** | ✅ | Developers building custom agents |
| **Gemini Enterprise** | ✅ | Enterprise admins (custom MCP server data store) |
| **Gemini web/mobile app & Gems** | ❌ | Not supported — no custom MCP or third-party API connectors |

---

## 1. Gemini CLI (recommended)

[Gemini CLI](https://github.com/google-gemini/gemini-cli) is Google's open-source terminal agent, and it supports remote MCP servers over streamable HTTP natively.

Add to `~/.gemini/settings.json` (global) or `.gemini/settings.json` (per project):

```json
{
  "mcpServers": {
    "chili-piper": {
      "httpUrl": "https://fire.chilipiper.com/api/fire-edge/v1/org/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

> Newer Gemini CLI versions accept `"url"` with an optional `"type": "http"` in place of `"httpUrl"` — both work. Keep the key in an environment variable rather than committing it: `"Authorization": "Bearer $CHILI_PIPER_API_KEY"`.

Verify: start `gemini`, run `/mcp`, and confirm `chili-piper` is listed as connected. Then ask: *"What Chili Piper tenant is connected?"* — you should get your organization name back.

**Using the Skills with Gemini CLI:** the [`skills/`](../skills/) in this repo are plain-markdown instruction sets — they are not Claude-specific. To run one through Gemini CLI, paste the skill's `SKILL.md` (and its `references/` files if needed) into your project's `GEMINI.md` context file, or reference the file directly in your prompt (e.g. *"Follow the procedure in skills/meeting-inspector/SKILL.md for meeting ID …"*).

## 2. Google Gen AI SDK / Agent Development Kit (developers)

Building your own agent? Both of Google's developer paths can consume the Chili Piper MCP directly:

- **Gen AI SDK** (Python/JS): MCP support is built in (experimental) — the SDK auto-calls MCP tools when the model requests them, for both local and remote servers.
- **ADK (Agent Development Kit)**: use `McpToolset` with `StreamableHTTPConnectionParams`, pointing at the server URL with the `Authorization: Bearer YOUR_API_KEY` header. ADK turns every Chili Piper tool into an agent tool automatically.

```python
# ADK example
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

chili_piper = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://fire.chilipiper.com/api/fire-edge/v1/org/mcp",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
    )
)
```

If you prefer raw function calling over MCP, the full OpenAPI spec is public: `https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/` — note that Gemini's native function-declaration schema uses uppercase type names (`OBJECT`, `STRING`) rather than OpenAPI's lowercase, which trips up direct ports.

## 3. Gemini Enterprise (admins)

Gemini Enterprise supports adding a **custom MCP server as a data store/connector** from the Google Cloud console, making Chili Piper tools available to your organization's Gemini Enterprise agents. Follow [Google's custom MCP server setup guide](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server) and point it at the server URL above with your API key. Google recommends keeping the number of enabled actions per custom MCP data store at or below 100.

## What about the Gemini app and Gems?

The **consumer Gemini web/mobile app and Gems do not support custom MCP servers or third-party API connectors** — Gems accept custom instructions but cannot call external APIs. If your team lives in the Gemini app, the closest paths are Gemini CLI (free, runs anywhere a terminal does) or an internal agent built on the Gen AI SDK. We'll update this guide if Google opens the consumer surface.

---

## Security notes

Everything in [SECURITY.md](../SECURITY.md) applies regardless of client:

- Scope the API key to only the permissions your workflow needs ([API permissions](../mcp-servers/chili-piper/README.md#api-permissions)).
- Keys go in environment variables or your OS keychain — never committed files.
- The MCP includes write tools (cancel meetings, delete rules, adjust distributions). Gemini CLI prompts for tool approval by default — leave that on.

# Using Chili Piper with Google Gemini

The Chili Piper MCP server is client-agnostic — the same endpoint that powers Claude and Cursor works with Google's Gemini tooling. This guide covers the three Gemini surfaces that support custom MCP servers today, and is honest about the one that doesn't.

**Server URL (same for every client):**

```
https://fire.chilipiper.com/api/fire-edge/v1/org/mcp
```

**Authentication:** use a Chili Piper **API key** (Bearer token). Generating a key requires an Admin — see [Getting your API key](../mcp-servers/chili-piper/README.md#getting-your-api-key).

**Required header for Gemini:** always send

```
X-MCP-Schema-Dialect: gemini
```

on every request. Gemini's function-calling accepts a **stricter JSON-Schema subset** than Claude does. This header tells the server to return each tool's input schema in Gemini's supported shape — unions as `anyOf` (not `oneOf`), single-value `enum` discriminators (not `const`), unsupported keywords dropped, and recursive schemas made loop-safe. **Without it, the tools with richer inputs — rules, distribution, routers, meeting types, handoff — fail to load with `400 INVALID_ARGUMENT`, and that one bad tool takes the whole tool list down with it.** Simple tools would still work, but there is no downside to always setting the header, so set it on every Gemini surface below. (Any non-Gemini client omits the header and gets the default dialect — Claude's behavior is unchanged.)

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
        "Authorization": "Bearer YOUR_API_KEY",
        "X-MCP-Schema-Dialect": "gemini"
      }
    }
  }
}
```

> Newer Gemini CLI versions accept `"url"` with an optional `"type": "http"` in place of `"httpUrl"` — both work. Keep the key in an environment variable rather than committing it: `"Authorization": "Bearer $CHILI_PIPER_API_KEY"`. The `X-MCP-Schema-Dialect: gemini` header is required (see above).

Verify: start `gemini`, run `/mcp`, and confirm `chili-piper` is listed as connected. Then ask: *"What Chili Piper tenant is connected?"* — you should get your organization name back.

**Using the Skills with Gemini CLI:** the [`skills/`](../skills/) in this repo are plain-markdown instruction sets — they are not Claude-specific. To run one through Gemini CLI, paste the skill's `SKILL.md` (and its `references/` files if needed) into your project's `GEMINI.md` context file, or reference the file directly in your prompt (e.g. *"Follow the procedure in skills/meeting-inspector/SKILL.md for meeting ID …"*).

## 2. Google Gen AI SDK / Agent Development Kit (developers)

Building your own agent? Both of Google's developer paths can consume the Chili Piper MCP directly. Send the `X-MCP-Schema-Dialect: gemini` header alongside your bearer token in both cases:

- **Gen AI SDK** (Python/JS): MCP support is built in (experimental) — the SDK auto-calls MCP tools when the model requests them, for both local and remote servers. Pass `X-MCP-Schema-Dialect: gemini` in the connection headers.
- **ADK (Agent Development Kit)**: use `McpToolset` with `StreamableHTTPConnectionParams`, pointing at the server URL with the `Authorization: Bearer YOUR_API_KEY` and `X-MCP-Schema-Dialect: gemini` headers. ADK turns every Chili Piper tool into an agent tool automatically.

```python
# ADK example
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

chili_piper = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://fire.chilipiper.com/api/fire-edge/v1/org/mcp",
        headers={
            "Authorization": "Bearer YOUR_API_KEY",
            "X-MCP-Schema-Dialect": "gemini",
        },
    )
)
```

If you prefer raw function calling over MCP, the full OpenAPI spec is public: `https://fire.chilipiper.com/api/fire-edge/public/org/docs/swagger/` — note that Gemini's native function-declaration schema uses uppercase type names (`OBJECT`, `STRING`) rather than OpenAPI's lowercase, which trips up direct ports.

## 3. Gemini Enterprise (admins)

Gemini Enterprise supports adding a **custom MCP server as a data store/connector** from the Google Cloud console, making Chili Piper tools available to your organization's Gemini Enterprise agents. Follow [Google's custom MCP server setup guide](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server) and point it at the server URL above with your API key. When configuring the connector's request headers, add `X-MCP-Schema-Dialect: gemini` alongside `Authorization`. Google recommends keeping the number of enabled actions per custom MCP data store at or below 100.

## What about the Gemini app and Gems?

The **consumer Gemini web/mobile app and Gems do not support custom MCP servers or third-party API connectors** — Gems accept custom instructions but cannot call external APIs. If your team lives in the Gemini app, the closest paths are Gemini CLI (free, runs anywhere a terminal does) or an internal agent built on the Gen AI SDK. We'll update this guide if Google opens the consumer surface.

---

## Troubleshooting

- **Tools don't appear / the agent errors with `400 INVALID_ARGUMENT` on startup** — the `X-MCP-Schema-Dialect: gemini` header is missing or misspelled. Gemini rejects the default (Claude-oriented) schemas for tools with union or recursive inputs, and one rejected tool fails the whole list. Add the header exactly as shown.
- **`/mcp` shows `chili-piper` but tenant queries fail with a permission error** — the API key is missing the scope your workflow needs; see [API permissions](../mcp-servers/chili-piper/README.md#api-permissions).

---

## Security notes

Everything in [SECURITY.md](../SECURITY.md) applies regardless of client:

- Scope the API key to only the permissions your workflow needs ([API permissions](../mcp-servers/chili-piper/README.md#api-permissions)).
- Keys go in environment variables or your OS keychain — never committed files.
- The MCP includes write tools (cancel meetings, delete rules, adjust distributions). Gemini CLI prompts for tool approval by default — leave that on.

# MCP Servers

Doors that let an AI agent talk to a tool. Each MCP server exposes one tool's functionality to Claude Code agents and recipes.

---

## Maintained by Chili Piper

- [chili-piper/](chili-piper/) — the official Chili Piper MCP server

## Curated third-party index

These MCPs are tested, recommended, and compatible with recipes in this repo.

| Tool | MCP | Notes |
|------|-----|-------|
| Salesforce | [salesforce-mcp](https://github.com/anthropics/mcp-salesforce) | CRM data read/write |
| HubSpot | [hubspot-mcp](https://github.com/anthropics/mcp-hubspot) | CRM alternative |
| Gong | [gong-mcp](https://github.com/anthropics/mcp-gong) | Call recording + transcripts |
| Clay | [clay-mcp](https://clay.com/mcp) | Account enrichment |
| Slack | [slack-mcp](https://github.com/anthropics/mcp-slack) | Team communication |
| Snowflake | Community | Warehouse queries |

> **Note:** The default MCP index does not include Cal.com, Default, Calendly, LeanData, or Qualified. Community recipes using those tools are welcome — they just won't appear in our recommended-stack defaults.

---

## Adding an MCP to the index

Open a PR that adds a row to the table above with:
- The tool name
- A link to the MCP implementation
- A brief note on what it enables

MCPs must be open-source or have a publicly documented protocol. No black-box integrations.

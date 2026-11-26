# Chili Piper Skills — Claude plugin

Official Chili Piper Skills for the [Chili Piper MCP](https://www.chilipiper.com/products/mcp): meeting diagnostics, routing audits, no-show analysis, availability checks, router configuration, and user onboarding/offboarding.

This folder is the Claude plugin. It holds only what the plugin ships:

| Path | What it is |
|------|-----------|
| `.claude-plugin/plugin.json` | Plugin manifest |
| `.mcp.json` | Chili Piper MCP connection |
| `skills/` | The skills (see [`skills/README.md`](skills/README.md)) |
| `commands/` | Slash commands that start a skill |

## Install

```
/plugin marketplace add https://github.com/Chili-Piper/mcp-assets
/plugin install chili-piper-skills@chili-piper-skills
```

When you enable the plugin, Claude Code asks for your **Chili Piper API key**. It keeps the key in your system keychain and sends it to the MCP as a Bearer token. An Admin generates the key in Command Center — see [Getting your API key](https://github.com/Chili-Piper/mcp-assets/blob/main/mcp-servers/chili-piper/README.md#getting-your-api-key).

## Where data goes

All data goes to Chili Piper only. The plugin sends nothing to third parties.

| Skill | Service | Data sent |
|-------|---------|-----------|
| All skills except `chili-piper-guest` | Chili Piper org MCP (`/api/fire-edge/v1/org/mcp`, declared in `.mcp.json`) | Tool arguments: workspace, router, meeting and user data, with your API key |
| `chili-piper-guest` | Chili Piper guest MCP (`/api/fire-edge/v1/guest/mcp`) or the company's public booking host (`<sub>.chilipiper.com`) over HTTPS | The guest's email and form answers, to book or change a meeting. No API key |

## Privacy

See the [Chili Piper Privacy Policy](https://www.chilipiper.com/privacy-policy). The plugin holds no customer data and no credentials.

## License

MIT — see the repository [LICENSE](https://github.com/Chili-Piper/mcp-assets/blob/main/LICENSE).

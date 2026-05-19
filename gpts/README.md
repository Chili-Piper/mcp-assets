# Chili Piper GPTs

ChatGPT Custom GPT configurations — the ChatGPT equivalent of the Claude skills in `../skills/`.

## Structure

Each subfolder is a self-contained GPT:

```
<gpt-name>/
├── GPT.md        # Name, description, conversation starters, and full system instructions
└── openapi.yaml  # GPT Actions schema — the Chili Piper API endpoints this GPT can call
```

## How to deploy a GPT

1. Go to [chat.openai.com/gpts/create](https://chat.openai.com/gpts/create)
2. Set **Name** and **Description** from the `GPT.md` frontmatter
3. Paste the body of `GPT.md` (everything below the `---` frontmatter) into the **Instructions** field
4. Add the **Conversation starters** from the frontmatter
5. Under **Actions**, click **Add actions** → paste the contents of `openapi.yaml`
6. Configure authentication on the action:
   - Auth type: **API Key**
   - API Key header: `Authorization`
   - API Key value: `Bearer <your Chili Piper API key>`

> **Note:** The OpenAPI schemas use `https://api.chilipiper.com` as the base URL with inferred endpoint paths. Verify paths against the official Chili Piper API docs before deploying.

## Key differences from Claude skills

| Dimension | Claude skill | ChatGPT GPT |
|-----------|-------------|-------------|
| Tool calls | MCP via `tool: X / args:` blocks | GPT Actions via OpenAPI schema |
| Reference files | Loaded on demand from `references/` | Inlined into instructions |
| Invocation | `/skill-name arg=value` | Conversation starters or natural language |
| Auth | API key in MCP server config | API key in GPT Action configuration |

## GPTs in this folder

| GPT | Description |
|-----|-------------|
| [availability-inspector](availability-inspector/) | Diagnoses why a rep shows no available slots |
| [concierge-debugger](concierge-debugger/) | Traces why a lead didn't book after form submission |
| [meeting-inspector](meeting-inspector/) | Deep-dives into a single meeting's full lifecycle |
| [no-show-analyzer](no-show-analyzer/) | Analyzes no-show patterns by trigger, route, or rep |
| [org-meeting](org-meeting/) | Org-wide meeting volume and health snapshot |
| [routing-audit](routing-audit/) | Audits routers for coverage gaps and stale rules |
| [user-copy](user-copy/) | Copies workspace/team memberships to a new rep |
| [user-details](user-details/) | Full profile for any Chili Piper user |
| [user-meetings](user-meetings/) | Rep-level meeting volume and health metrics |
| [user-offboarding](user-offboarding/) | Safely removes a departing rep with audit trail |

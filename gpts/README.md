# Chili Piper GPTs

ChatGPT Custom GPT configurations — the ChatGPT equivalent of the Claude [skills](../skills/). Each GPT calls the **real Chili Piper Edge API** directly via GPT Actions.

## Structure

Each subfolder is a self-contained GPT:

```
<gpt-name>/
├── GPT.md        # Name, description, conversation starters, and full system instructions
└── openapi.yaml  # GPT Actions schema — generated from the live Chili Piper Edge API spec
```

The `openapi.yaml` files are **generated**, not hand-written — see [Keeping GPTs in sync](#keeping-gpts-in-sync).

## How to deploy a GPT

1. Go to [chatgpt.com/gpts/editor](https://chatgpt.com/gpts/editor)
2. Set **Name** and **Description** from the `GPT.md` frontmatter
3. Paste the body of `GPT.md` (everything below the `---` frontmatter) into **Instructions**
4. Add the **Conversation starters** from the frontmatter
5. Under **Actions**, click **Create new action** → **Import** → paste the contents of `openapi.yaml`
6. Configure authentication on the action:
   - Authentication: **API Key**
   - Auth Type: **Bearer**
   - API Key value: your Chili Piper API key (Admin Center → API Keys)

The action's server URL is `https://fire.chilipiper.com/api/fire-edge` and auth is a Bearer API key in the `Authorization` header — both already declared in each `openapi.yaml`.

## Keeping GPTs in sync

The `openapi.yaml` for every GPT is generated from Chili Piper's canonical Edge API OpenAPI document, so the GPTs never drift from the real API:

```bash
pip install pyyaml
python .github/scripts/generate_gpt_openapi.py          # fetches the live spec
# or, against a local copy of the spec:
python .github/scripts/generate_gpt_openapi.py path/to/docs.yaml
```

Two separate mechanisms keep things aligned — don't confuse them:

- **GPTs ↔ the API** — `generate_gpt_openapi.py` builds each `openapi.yaml` from the live Edge spec, so the GPT Actions always reflect real endpoints/schemas. Re-run it whenever the Edge API changes. It holds, per GPT, the Edge operations that GPT uses (in the `GPT_OPERATIONS` map) and emits a self-contained spec with the transitive closure of referenced schemas. **The one manual step:** if a GPT should start or stop using an operation, edit `GPT_OPERATIONS` (mirror the matching skill's `tools_required`) *before* regenerating.
- **GPTs ↔ the skills** — `check_gpt_sync.py` (run in CI) enforces that every skill has a paired GPT at a matching `version`. When a skill changes, mirror the change in its paired `GPT.md`, bump the `GPT.md` `version` to match `SKILL.md`, and regenerate the `openapi.yaml`.

Neither script touches the Claude skills in `../skills/` — they only produce/validate the ChatGPT-side artifacts.

## Key differences from Claude skills

| Dimension | Claude skill | ChatGPT GPT |
|-----------|-------------|-------------|
| Tool calls | Chili Piper MCP via `tool: X / args:` blocks | GPT Actions against the Edge REST API (`openapi.yaml`) |
| Reference files | Loaded on demand from `references/` | Inlined into instructions |
| Invocation | `/skill-name arg=value` | Conversation starters or natural language |
| Auth | Bearer API key in MCP server config | Bearer API key in the GPT Action |

## GPTs in this folder

| GPT | Description |
|-----|-------------|
| [meeting-inspector](meeting-inspector/) | Deep-dives into a single meeting's full lifecycle |
| [no-show-analyzer](no-show-analyzer/) | Analyzes no-show patterns by trigger, route, or rep |
| [routing-audit](routing-audit/) | Audits routers for coverage gaps and stale rules |
| [concierge-debugger](concierge-debugger/) | Traces why a lead didn't book after form submission |
| [distro-debugger](distro-debugger/) | Debugs why a CRM record was (or wasn't) routed through a distribution |
| [availability-inspector](availability-inspector/) | Diagnoses why a rep shows no available slots |
| [org-meeting](org-meeting/) | Org-wide (and single-tenant) meeting volume and health snapshot |
| [distribution-analysis](distribution-analysis/) | Analyzes a round-robin distribution for rep imbalance |
| [user-details](user-details/) | Full profile for any Chili Piper user |
| [user-meetings](user-meetings/) | Rep-level meeting volume and health metrics |
| [user-copy](user-copy/) | Copies workspace/team memberships to a new rep |
| [user-offboarding](user-offboarding/) | Safely removes a departing rep with audit trail |

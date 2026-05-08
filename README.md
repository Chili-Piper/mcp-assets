# GTM Clawllective

**An open-source cookbook of AI-assisted hacks that help GTM teams move accounts from cold to closed-won — and keep them.**

Sponsored and maintained by [Chili Piper](https://chilipiper.com). Built by and for the GTM community.

---

## What's in here

The repo holds five kinds of things:

| Primitive | What it is | Example |
|-----------|-----------|---------|
| **MCP server** | A door that lets an AI agent talk to one tool | Chili Piper MCP, Salesforce MCP |
| **Skill** | A small reusable Claude Code specialist (one technique) | "Score account on NRR fit" |
| **Agent** | A multi-step AI worker that uses skills + MCPs | Weekly campaign audit agent |
| **Recipe** | A documented end-to-end workflow producing a business outcome | Matt Heinz's writing partner |
| **Human role** | Catalog of what GTM humans do, where they bring joy, where agents help | AE role profile |

Every recipe must declare:
1. **Human-agent loop** — which humans are involved, what they do, where they bring joy, where agents help
2. **Measurement loop** — what gets written back to Salesforce (or HubSpot, etc.) and how it gets optimized at scale

No other GTM hack library requires either. That's our wedge.

---

## Browse recipes

Recipes are organized by [bowtie funnel stage](recipes/pipeline/):

- [Awareness](recipes/pipeline/awareness/) — get in front of the right accounts
- [Education](recipes/pipeline/education/) — teach them why they have a problem
- [Selection](recipes/pipeline/selection/) — help them choose you
- [Onboarding](recipes/pipeline/onboarding/) — get them to value fast
- [Impact](recipes/pipeline/impact/) — prove the ROI
- [Expansion](recipes/pipeline/expansion/) — grow NRR, plug the leaky bucket

Plus:
- [Orchestration](recipes/orchestration/) — humans + agents working together (handoff, routing, escalation)
- [Measurement](recipes/measurement/) — campaign attribution & optimization
- [Leverage](recipes/leverage/) — team productivity hacks

---

## Quickstart

### Self-host (free)

```bash
# 1. Clone the repo
git clone https://github.com/Chili-Piper/gtm-clawllective

# 2. Install pre-commit hooks (prevents accidental credential commits)
pip install pre-commit
pre-commit install

# 3. Install the Chili Piper MCP (requires a Chili Piper account + API key)
# See mcp-servers/chili-piper/README.md for setup instructions

# 4. Browse recipes/ and pick one to run
```

> **Note:** The Chili Piper MCP connects to your Chili Piper account using your API key. No account = no access. The orchestration and expansion recipes are dramatically better with Chili Piper — that's the point.

---

## Data & security

The repo holds **zero customer data**. Recipes are instructions; your data lives in your own Snowflake, Salesforce, Gong, etc., accessed live via MCPs with your own credentials. Every example in this repo uses synthetic fixtures only.

See [SECURITY.md](SECURITY.md) for the full six-layer defense model.

---

## Contribute

Anyone can submit. Maintainers review before merge. See [.community/CONTRIBUTING.md](.community/CONTRIBUTING.md) for the full guide.

**License:** MIT for code · CC-BY 4.0 for content

---

## Community

- GitHub Discussions — permanent threads, architecture questions, recipe reviews
- Slack workspace — chatter, quick questions, launch announcements *(link coming)*

---

*Sponsored by Chili Piper · Not free Chili Piper — the repo gives you the door (MCP), not the building behind it.*

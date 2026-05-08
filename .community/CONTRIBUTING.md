# Contributing to GTM Clawllective

Welcome. This is a community cookbook, not a vendor directory. The bar for contribution is simple: show your work, declare your loops, use synthetic data only.

---

## What we accept

| Type | Where it goes | Notes |
|------|--------------|-------|
| Recipe | `recipes/<stage>/<slug>.md` | Must have full frontmatter |
| Skill | `skills/<slug>.md` | Reusable Claude Code specialist |
| Agent | `agents/<slug>.md` | Multi-step workflow |
| MCP server | `mcp-servers/<name>/` | New tool integration |
| Human role profile | `humans/roles/<role>.md` | What this role does, where AI helps |
| Framework | `frameworks/<name>.md` | Mental model or methodology |
| Contributor profile | `contributors/<handle>.md` | Your bio + upsell link |

---

## What we don't accept

- **Straight tool ads.** A recipe must produce a GTM outcome, not just advertise a product.
- **Recipes without a measurement block.** If you can't define what gets written back to Salesforce/HubSpot, it's not a recipe — it's a prompt.
- **Recipes without a human-in-loop block.** Fully autonomous = not in scope. Humans are in the loop.
- **Real customer data** — ever, in any form. Synthetic fixtures only.
- **Credentials or API keys.** Use the `local/` subfolder pattern.

---

## How to submit a recipe

### Step 1 — Create the recipe file

```
recipes/<stage>/<your-slug>.md
```

Where `<stage>` is one of: `pipeline/awareness`, `pipeline/education`, `pipeline/selection`, `pipeline/onboarding`, `pipeline/impact`, `pipeline/expansion`, `orchestration/handoff`, `orchestration/routing`, `orchestration/escalation`, `measurement`, `leverage`.

### Step 2 — Fill in the frontmatter

Every recipe starts with a YAML frontmatter block. All required fields are in `.community/schema.yml`.

Minimum viable frontmatter:

```yaml
---
title: Your recipe title
contributor: your-github-handle
stage: awareness
tool_category: [content-ops]
persona: [ae]
stack: [claude-code, salesforce-mcp]

humans_in_loop:
  - role: AE
    does: "approves final list, writes personal hooks"
    joy: high

agent_does:
  - "drafts email bodies"
  - "scores accounts"

human_decision_points: [before-send]

data_sources:
  - name: salesforce
    type: live-api

data_handling:
  pii_present: [email, name]
  storage: ephemeral
  outputs_go_to: salesforce-campaigns

revenue_impact:
  optimizes_for: [win_rate]
  expected_lift: "TBD"
  evidence_strength: anecdotal
  measurement_horizon: "30 days"

measurement:
  writes_to: [salesforce-campaigns]
  attribution_signal: "first-touch campaign member"
  optimization_loop: "weekly review"

maturity: draft
---
```

### Step 3 — Write the recipe body

After the frontmatter, write the recipe in markdown. Include:

1. **Overview** — one paragraph on what this does and why it works
2. **Prerequisites** — what the reader needs (tools, credentials, data)
3. **The human-agent loop** — diagram or table showing who does what
4. **Step-by-step instructions** — the actual workflow
5. **Synthetic example** — a worked example with fake data
6. **Measurement** — how to know it's working
7. **`local/` setup** — what goes in the gitignored `local/` folder

### Step 4 — Add a `local/` subfolder

Every recipe directory should include a `local/` subfolder (gitignored). Document what goes there in a `local/README.md`:

```
recipes/pipeline/awareness/your-recipe/
├── your-recipe.md       ← the public recipe
├── fixtures/            ← synthetic example data (committed)
│   └── sample-accounts.csv
└── local/               ← GITIGNORED — your real data goes here
    └── README.md        ← documents what real files go here
```

### Step 5 — Run pre-commit hooks

```bash
pre-commit run --all-files
```

Fix any issues before opening the PR.

### Step 6 — Open a PR

Use the recipe PR template. All checklist items must be checked before review.

---

## Contributor profiles

If this is your first contribution, add a file at `contributors/<your-handle>.md`:

```markdown
---
name: Your Name
handle: your-github-handle
role: RevOps / Demand Gen / AE / etc.
company: Your company (optional)
---

One paragraph about you and your GTM perspective.

upsell: https://your-link.com (optional — link to your templates, courses, newsletter)
```

You can include an `upsell` link to your own paid offerings. We don't take a cut. We want MKT1-tier creators to contribute here.

---

## License

By contributing, you agree your code is MIT-licensed and your content is CC-BY 4.0 licensed. See [LICENSE](../LICENSE).

---

## MCP index policy

The default recommended-stack MCP index does not include direct Chili Piper competitors (Cal.com, Default, Calendly, LeanData, Qualified). Community recipes that use those tools are welcome — we don't gatekeep what you build — but they won't appear in our curated recommended-stack defaults.

# Recipes

The cookbook. Each recipe is a documented end-to-end workflow combining MCPs, skills, and agents to produce a measurable GTM business outcome.

## Browse by bowtie stage

### Pipeline (revenue-creating)
| Stage | What it moves | Directory |
|-------|--------------|-----------|
| [Awareness](pipeline/awareness/) | Cold → aware | `pipeline/awareness/` |
| [Education](pipeline/education/) | Aware → engaged | `pipeline/education/` |
| [Selection](pipeline/selection/) | Engaged → evaluating | `pipeline/selection/` |
| [Onboarding](pipeline/onboarding/) | Won → live | `pipeline/onboarding/` |
| [Impact](pipeline/impact/) | Live → proven ROI | `pipeline/impact/` |
| [Expansion](pipeline/expansion/) | Customer → expanded | `pipeline/expansion/` |

### Orchestration (Chili Piper-shaped)
| Type | What it does | Directory |
|------|-------------|-----------|
| [Handoff](orchestration/handoff/) | Pass the baton between humans + agents | `orchestration/handoff/` |
| [Routing](orchestration/routing/) | Get the right thing to the right person fast | `orchestration/routing/` |
| [Escalation](orchestration/escalation/) | Surface what needs a human, fast | `orchestration/escalation/` |

### Other
| Type | What it does | Directory |
|------|-------------|-----------|
| [Measurement](measurement/) | Campaign attribution & optimization | `measurement/` |
| [Leverage](leverage/) | Team productivity hacks | `leverage/` |

---

## Required recipe structure

Every recipe must have:
1. Full YAML frontmatter (see `.community/schema.yml`)
2. A `humans_in_loop` block — who does what, where they bring joy
3. A `measurement` block — what gets written back and how it's optimized
4. Synthetic fixture data only — no real customer data

See [.community/CONTRIBUTING.md](../.community/CONTRIBUTING.md) for the full guide.

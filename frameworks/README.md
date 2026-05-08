# Frameworks

Mental models and methodologies that inform how recipes are designed and measured.

---

## The bowtie model

The organizing framework for all pipeline recipes. The bowtie maps the full customer lifecycle — from first awareness to expansion — and makes the difference between left-side (new pipeline) and right-side (NRR) explicit.

```
AWARENESS → EDUCATION → SELECTION ◆ ONBOARDING → IMPACT → EXPANSION
          [new pipeline]          ◆          [NRR protection & growth]
```

The ◆ is the closed-won moment. Most "AI for GTM" tools play left of the diamond. Our wedge is right of it.

---

## Revenue Architecture

A framework for thinking about which levers move NRR:

- **Churn rate** — customers who leave
- **Expansion rate** — customers who grow
- **Contraction rate** — customers who downgrade
- **NRR = (Starting ARR + Expansion - Churn - Contraction) / Starting ARR**

Every expansion recipe in this repo declares which of these rates it moves.

---

## The human-agent loop

Every recipe must declare:

1. **Which humans are involved** — by role
2. **What they do** — specifically
3. **Where they bring joy** — what energizes them about this task
4. **Where agents help** — the specific tasks agents handle

This isn't just documentation. It's the design constraint that makes recipes actually work in practice.

---

## The measurement loop

Every recipe must declare:

1. **What gets written back** — to Salesforce, HubSpot, or another system of record
2. **The attribution signal** — how you know this recipe influenced the outcome
3. **The optimization loop** — how you improve it over time

Without a measurement loop, a recipe is a prompt, not a hack.

---

*Submit a new framework via PR to `frameworks/<name>.md`.*

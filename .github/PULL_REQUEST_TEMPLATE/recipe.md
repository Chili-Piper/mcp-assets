## Recipe submission checklist

Before submitting, confirm each item:

### Content
- [ ] Recipe has complete YAML frontmatter (all required fields — see `.community/schema.yml`)
- [ ] `humans_in_loop` block present with at least one human role, `does`, and `joy` level
- [ ] `measurement` block present with `writes_to`, `attribution_signal`, and `optimization_loop`
- [ ] `data_handling` block present with `pii_present`, `storage`, and `outputs_go_to`

### Data safety
- [ ] **No real customer data** — all examples use synthetic fixtures only
- [ ] **No credentials, API keys, or tokens** in any file
- [ ] **No `.env` files** committed
- [ ] Real data (if needed for local testing) lives in the recipe's `local/` subfolder (gitignored)
- [ ] Pre-commit hooks ran locally without errors (`pre-commit run --all-files`)

### Quality
- [ ] Recipe has been tested end-to-end at least once
- [ ] Synthetic fixture data is realistic enough to understand the recipe
- [ ] `maturity` field accurately reflects the evidence level (`anecdotal` / `one-team` / `multi-team` / `benchmarked`)
- [ ] Filed in the correct directory (see folder structure in README)

### Attribution
- [ ] Contributor name/handle matches your profile in `contributors/`
- [ ] `upsell` link (if included) points to your own offerings, not competitor tools

---

**What does this recipe do?** *(one sentence)*

**Which bowtie stage does it move?**

**What's the human decision point?**

**What measurement signal does it write back?**

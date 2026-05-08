# First-PR Checklist

Complete this before your first PR is reviewed. It only takes 5 minutes and ensures the community stays safe and high-quality.

---

## Data safety (non-negotiable)

- [ ] I have read [SECURITY.md](../SECURITY.md) and understand the six-layer defense model
- [ ] My recipe contains **zero real customer data** — all examples are synthetic fixtures
- [ ] No `.env` files, API keys, tokens, or credentials are in any committed file
- [ ] I understand that real data goes in the recipe's `local/` subfolder (gitignored) and never gets committed
- [ ] I ran `pre-commit run --all-files` and it passed

## Recipe quality

- [ ] My recipe has full frontmatter with all required fields (validated by CI)
- [ ] The `humans_in_loop` block accurately describes who does what and how much they enjoy it
- [ ] The `measurement` block describes what gets written back to Salesforce/HubSpot and how it's optimized
- [ ] I set `maturity: draft` if I haven't tested this end-to-end more than once
- [ ] The synthetic fixture data is realistic enough that a reader can understand the recipe without running it

## Community norms

- [ ] My recipe produces a GTM business outcome — it is not an ad for a tool
- [ ] I have added a contributor profile at `contributors/<my-handle>.md` (or it already exists)
- [ ] If I included an `upsell` link, it points to my own offerings, not a competitor product
- [ ] I understand the license: MIT for code, CC-BY 4.0 for content

---

*Questions? Open a GitHub Discussion or ask in the community Slack.*

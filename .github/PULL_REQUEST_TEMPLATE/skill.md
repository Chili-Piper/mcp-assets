## Skill submission checklist

Before submitting, confirm each item:

### Content
- [ ] Skill lives in `skills/<slug>/SKILL.md` with complete frontmatter (`name`, `description`, `version`, `tools_required`, `writes_to`)
- [ ] `name` in frontmatter matches the directory name (kebab-case)
- [ ] Any deep-dive content is in `references/*.md` and listed under `references:`
- [ ] Skill is registered in `skills/README.md` with its maturity/QA status
- [ ] If a ChatGPT version applies, the paired `gpts/<slug>/` (GPT.md + openapi.yaml) is updated to the same `version`

### Correctness
- [ ] MCP tool names and response field names match the live Chili Piper MCP schema
- [ ] Documented limits (window sizes, pagination) are accurate
- [ ] Read-only vs. write behavior is correctly stated in `writes_to`

### Data safety
- [ ] **No real customer data** — examples use synthetic values only
- [ ] **No credentials, API keys, or tokens** in any file
- [ ] Pre-commit hooks ran locally without errors (`pre-commit run --all-files`)

### QA
- [ ] Skill has been tested against a real tenant (read-only skills) and logged in `docs/QA.md`
- [ ] `version` was bumped if behavior changed

---

**What does this skill do?** *(one sentence)*

**Which Chili Piper MCP tools does it call?**

**Is it read-only or does it write?**

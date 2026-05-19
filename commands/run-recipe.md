---
description: Run a GTM recipe end-to-end. Finds the recipe file, checks prerequisites, and walks through each step with you.
argument-hint: "<recipe-name or path>"
allowed-tools: [Read, Glob, Grep, WebFetch]
---

# /run-recipe

Load and execute a GTM recipe from this repository.

## Steps

1. **Find the recipe.** If the user provided a full path, use it. Otherwise search `recipes/**/*.md` for a file whose frontmatter `title` or filename matches the argument.

2. **Read the recipe file.** Parse the YAML frontmatter completely before doing anything else.

3. **Check prerequisites.**
   - Read `rules/gtm-agent-rules.md` for the full guardrails.
   - Verify `maturity:` and warn if `idea` or `draft`.
   - Check `tools_required:` — confirm the Chili Piper MCP (and any other listed MCPs) are connected. If not, output the setup command from `mcp-servers/chili-piper/README.md` and stop.
   - Check `stack:` — list any tools the user needs to have configured.

4. **Load required skills.** For each skill listed in `stack:` or referenced in the recipe body, find the matching file under `skills/` and read its `SKILL.md`. Load any `references/` files the skill points to.

5. **Summarize before starting.** Output a brief plan:
   - What the recipe does
   - What data it will read
   - What it will write (or "nothing — read-only")
   - Where human decision points are
   
   Ask: *"Ready to start? (yes / no / show me the full recipe first)"*

6. **Execute step by step.** Follow the recipe's instructions. Stop at every declared `human_decision_point` and wait for explicit approval before continuing.

7. **Close the measurement loop.** After the final step, ask the user whether to write results to the declared `writes_to` destination.

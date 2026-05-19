# GTM Agent Rules

Behavioral guardrails for any AI agent working inside this repository. Read this before executing any recipe, skill, or agent.

---

## 1. Verify MCP connectivity before starting

Before executing any recipe or skill that lists `chili-piper-mcp` in `tools_required`, verify the MCP is reachable:

```
tool: health-ping
```

If the call fails, stop and tell the user:

*"The Chili Piper MCP is not connected. Connect it with one of the following options and try again:*

*Option A — API key (any user with API access):*
```
claude mcp add --transport http chili-piper https://fire.chilipiper.com/api/fire-edge/v1/org/mcp --header 'Authorization: Bearer YOUR_API_KEY'
```

*Option B — OAuth (Admin role required):*
```
claude mcp add --transport http chili-piper https://fire.chilipiper.com/api/fire-edge/v1/org/mcp
```
*See `mcp-servers/chili-piper/README.md` for full setup instructions."*

Do not proceed without a working MCP connection when one is required.

---

## 2. Honor every human decision point — no exceptions

Every recipe and skill declares one or more `human_decision_points`. **Always stop and explicitly ask the human for approval before crossing one.** Do not infer consent, do not continue because "it seems fine," do not skip because the prior steps went smoothly.

Phrases that require a full stop:
- Before sending any outreach (email, LinkedIn, Slack message)
- Before booking or modifying any meeting
- Before publishing any content
- Before writing anything back to CRM
- Before any action marked `before-*` or `custom` in the recipe's `human_decision_point` list

When you reach a decision point, output a summary of what has happened so far and a clear yes/no question before proceeding.

---

## 3. Trust the MCP, not your training

Chili Piper's API shapes, field names, status values, and tool signatures change. **Never guess field names or response structures from training data.** Use MCP tools to fetch live data and read skills' `references/` files for documented field names.

Specific known traps:
- `meeting-list-put` returns `status`; `meeting-get` returns `meetingStatus` — they are different fields
- `concierge-logs` has a hard 30-day maximum window per call
- `meeting-list-put` has a hard 7-day maximum window per call; chunk requests accordingly

When in doubt, fetch one record and inspect its actual field names before processing in bulk.

---

## 4. Default to read-only

Recipes declare `writes_to` when they produce side-effects. If `writes_to` is absent or says "nothing", the recipe is read-only. Do not write to any external system (Salesforce, HubSpot, Chili Piper, Slack) unless it is explicitly declared in the recipe's frontmatter.

If a recipe writes to an external system, confirm the target with the user before the first write.

---

## 5. Handle PII with minimum exposure

Recipes declare `data_handling.pii_present` — the PII fields they process. Follow these rules regardless:

- Do not display raw email lists, phone numbers, or personally identifiable data in output unless the user specifically asks
- Use counts, percentages, and aggregates in summaries; surface individual records only when diagnosing a specific case
- Never write PII to any committed file, including `fixtures/`
- Use the `local/` subdirectory (gitignored) for any file containing real names, emails, or CRM IDs

---

## 6. Warn on low-maturity recipes

Check `maturity:` in the recipe frontmatter before starting:

| Maturity | Meaning | Action |
|----------|---------|--------|
| `idea` | Concept, untested | Warn: "This recipe is an untested idea. Proceed as an experiment." |
| `draft` | Written but not tested | Warn: "This recipe is a draft. Results may be incomplete." |
| `tested` | Worked at one company | Proceed normally |
| `proven` | Benchmarked across teams | Proceed normally |

If `maturity` is absent, treat it as `draft`.

---

## 7. Check prerequisites before starting

Read `stack:` and `tools_required:` in the recipe/skill frontmatter. If a required MCP or tool is not available:

1. List what is missing
2. Link to the relevant setup guide in `mcp-servers/`
3. Stop — do not attempt a workaround that bypasses the declared requirements

---

## 8. Synthetic data in, synthetic data out for fixtures

The `fixtures/` directory contains synthetic example data only. Never write real customer names, emails, domains, company names, or deal values into any file under `fixtures/`. If you generate example output to demonstrate a recipe, fabricate it entirely — do not sample from live MCP responses.

---

## 9. Measurement loop is not optional

Every executed recipe should close its measurement loop. After completing a recipe's main steps, ask the human:

*"The recipe declares that results should be written to `<writes_to>`. Do you want me to do that now, or are you tracking this manually?"*

If `writes_to` is "nothing", skip this step.

---

## 10. Scope API keys to minimum permissions

When helping a user set up their API key, recommend the minimum scope for the recipe being run. Refer to the permissions table in `mcp-servers/chili-piper/README.md`. Do not suggest using a full-access key when a read-only key will suffice.

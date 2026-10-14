---
description: Build a ChiliForms embed (a form Chili Piper generates from a Concierge router) for a customer without a form of their own, and get a ready-to-paste snippet. Read-only.
argument-hint: "<router> [generate|describe] [requirements]"
allowed-tools: [Read]
---

# /configure-chiliforms

Configure a ChiliForms embed using the `chiliforms-configuration` skill.

## Steps

1. Read `skills/chiliforms-configuration/SKILL.md`.
2. Check that the Chili Piper MCP is connected by calling `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `router`. **Required**. If missing, ask which router the form should book through.
   - `generate` or `describe` → `mode` (default `generate`). Pass `attach` only when the user explicitly asks for ChiliForms attach mode.
   - Remaining text → `requirements`.
4. If the user already has their own form, don't build a ChiliForms config. Point them to the standard Concierge snippet, as the skill describes.
5. Execute the skill's steps in order.
6. Output the snippet, field report, blocking gaps and test steps.
7. Tip: router-side fixes (no Chili webform, missing fields) go through `/configure-concierge-router`, which dry-runs first.

---
description: Pulls a full profile for any Chili Piper user — teams, workspaces, meeting types, scheduling links, and recent meeting activity — for onboarding audits, offboarding checks, and troubleshooting.
argument-hint: "<user-email-or-name> [no-meetings]"
allowed-tools: [Read]
---

# /user-details

Pull a full user profile using the `user-details` skill.

## Steps

1. Read `skills/user-details/SKILL.md`.
2. Check that the Chili Piper MCP is connected — call `health-ping`. If it fails, output the setup instructions from `mcp-servers/chili-piper/README.md` and stop.
3. Map the arguments to the skill inputs:
   - First argument → `user` (email, name, or user ID). **Required** — if missing, ask: *"Which user should I pull the profile for?"*
   - Optional `no-meetings` flag → set `include_meetings` to `false` (default `true` includes last-30-day meeting activity).
4. Execute the skill's steps in order.
5. Output the profile, memberships (workspaces + teams), scheduling links, and recent meeting activity.
6. Ask: *"Want to onboard them to missing teams, fix a routing gap, or proceed with offboarding (`/offboard-user`)?"*

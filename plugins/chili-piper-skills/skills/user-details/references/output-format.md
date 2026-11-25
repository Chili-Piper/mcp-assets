# user-details — output format

The exact profile layout. Render in this order; omit the Recent activity table if
`include_meetings=false`.

## User profile layout

### User Profile: `<name>` (`<email>`)

**Identity**

| Field | Value |
|-------|-------|
| User ID | |
| Super Admin | true / false |
| Licenses | distro, chiliCalOrg, concierge, … (list enabled boolean flags); Tier: RoutingAndScheduling / Experiences / ChiliDataPlatform (if set) |

**Warnings** (if any)
- ⚠ Calendar connection status is not available from the API — check routing/availability failures if scheduling issues are reported
- ⚠ CRM connection status is not available from the API — ownership-based routing failures will surface at routing time

**Workspace memberships**

| Workspace | ID |
|-----------|-|
| ... | |

**Team memberships**

| Team | Workspace |
|------|----------|
| ... | |

**Scheduling links**

| Link name | Type | Meeting type |
|-----------|------|--------------|
| ... | Personal / Round-robin / Admin one-on-one / Group / Ownership | |

**Recent activity (last 30 days)**

| Metric | Value |
|--------|-------|
| Meetings (completed + no-show) | |
| No-shows | |
| No-show rate | |
| Cancelled | |

**Human decision point**

*"What would you like to do with this user? I can check missing workspace memberships, look at their routing assignments, or start an offboarding flow."*

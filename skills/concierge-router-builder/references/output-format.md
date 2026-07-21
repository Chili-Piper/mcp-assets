# Output format — concierge-router-builder

## Build plan (Phase 2 checkpoint)

Present the whole plan before creating anything. Nothing is written until the admin confirms.

```
## Build plan — "Inbound Demo" router · Marketing workspace · DRY RUN, nothing created yet

Trigger(s): Web Form (+ Router Link)
Form fields: Email*, First Name, Last Name, Company Size, Country

ROUTING ORDER (first match wins)
1. Ownership            → Owned Accounts team  → Demo (30m) → Owned Accounts dist
2. Customer routing     → CSM team             → QBR (30m)  → CSM dist
3. SMB NA               → SMB NA AEs           → Demo (30m) → SMB NA dist
4. Enterprise EMEA      → Ent EMEA AEs         → Demo (45m) → Ent EMEA dist
Catch-all: Schedule → AE Queue · Demo (30m)   |  Not scheduled: 10 min → Landing

OBJECTS TO CREATE
- Teams:         Owned Accounts (you), CSM (you), SMB NA AEs (you), Ent EMEA AEs (you), AE Queue (you)
- Meeting types: Demo (30m), Demo (45m), QBR (30m)
- Rules:         Ownership; Customer; SMB NA; Enterprise EMEA
- Distributions: one per team (Meeting / Flexible / no limit)

CRM ACTIONS (per rule): Convert Lead on SMB NA  (API-supported)
UI-ONLY — configure by hand after build: Update Ownership, Create Event, Add to Campaign

⚠️ Not transactional: if a step fails, earlier objects remain. The router PUBLISHES LIVE on success.
Build it now?
```

Rules:
- Placeholder members render as "(you)"; name the real reps when supplied.
- Split CRM actions into **API-supported** (Convert Lead) and **UI-only** (update ownership,
  create event, add to campaign) — always list the UI-only ones for manual follow-up.
- Reuse a single meeting type across rules when the admin chose "same for all".

## Result (after build, dry_run=false)

```
## Built — "Inbound Demo" (rtr_2c8a…) · LIVE
Booking URL slug: inbound-demo

Created:
- Teams:         Owned Accounts (tm_…), CSM (tm_…), SMB NA AEs (tm_…), Ent EMEA AEs (tm_…), AE Queue (tm_…)
- Meeting types: Demo 30m (mt_…), Demo 45m (mt_…), QBR 30m (mt_…)
- Rules:         Ownership (rl_…), Customer (rl_…), SMB NA (rl_…), Enterprise EMEA (rl_…)
- Distributions: Owned Accounts (dist_…), CSM (dist_…), SMB NA (dist_…), Ent EMEA (dist_…), AE Queue (dist_…)

Verified via concierge-router-get: 4 rows + catch-all match the plan ✅
```

Report resolved names with raw IDs in parentheses on first mention. If the build stopped
partway, report what exists and the failure per `build-procedure.md` § Partial-build recovery
instead of a success block.

## Go-live checklist (Phase 4 hand-off)

Present after a successful build. Lead with the UI-only items the API could not do.

```
Your router is built and live. Before you rely on it, finish these in the Chili Piper app:

Data & CRM actions (UI-only — the API can't set these)
- [ ] Configure UI-only CRM actions on each routing row (Update Ownership, Create Event, Add to Campaign)
- [ ] Confirm data fields & web-form mapping are complete (Settings → Data Fields; form mapping)

Reps & calendars
- [ ] Replace placeholder members with the real reps (Settings → Teams)
- [ ] Every rep has a connected Google/Outlook calendar and working hours set

Matching & ownership
- [ ] Lead-to-account matching enabled (Settings → Matching) if the ownership rule uses L2A
- [ ] Ownership fields (Account/Lead OwnerId) are populated in the CRM, or ownership won't match

Form & meeting experience
- [ ] Test the form end-to-end — correct rule fires, right rep booked
- [ ] JS snippet installed on the page (third-party forms)
- [ ] Review meeting type invite title/description, conferencing, reminders; add buffers
```

## Best practices to suggest
- Ownership first, then customer routing, then segments, then catch-all.
- Multiple condition groups (form + CRM objects) per rule for better matching.
- Set a timeout on every scheduling outcome; add an "unknown region/size" fallback before catch-all.
- Add reminders to meeting types to cut no-shows; add buffers between meetings.

# Discovery — Concierge Router Builder

The conversational script for Phases 0–1. Be helpful and offer best-practice defaults.
Ask in small groups; wait for answers before moving on. Presets (size thresholds, region
country lists, field/data-source maps) live in `segment-presets.md`.

## Phase 0 — Concept check & prerequisites

### 0A. Familiarity check

> "Before we start — how familiar are you with the building blocks of a Concierge router:
> **rules, teams, distributions, and meeting types**?"

If they're comfortable, skip the primer. Otherwise offer it:

- **Router** — the brain: when a lead submits your form, it evaluates their data and decides who they meet with and how.
- **Rules** — conditions evaluated top-to-bottom; the **first match wins**. Common kinds: *ownership* (lead already has a CRM owner → route to them) and *segment* (route by size, region, product, etc.).
- **Teams** — groups of reps a rule can route to.
- **Distributions** — how a team's leads are shared out (round-robin, weighting).
- **Meeting Types** — what gets booked: duration, invite details, conferencing.
- Flow: **Lead submits form → router evaluates rules top-to-bottom → first match → team → distribution picks the rep → meeting type defines the booking.**

### 0B. Prerequisites — data fields & form mapping (UI-only)

**Both are prerequisites the API cannot do.** Do not skip this gate.

> "Two things must be set up in the Chili Piper app before we build — I can't do either
> through the API:
> 1. **Data fields** (Settings → Data Fields) — how form submissions map to your CRM
>    (Email, First Name, Company Size, Country, …). Common defaults: PersonEmail,
>    PersonFirstName, PersonLastName, CompanyName, CompanyEmployees, PersonCountry,
>    PersonPhone, PersonTitle, PersonState. Custom fields (product interest, UTMs,
>    industry) must be created in the UI first — each gets a UUID we can reference.
> 2. **Web-form mapping** — connecting your form's inputs to those data fields (or using a
>    Chili Form). Set this in the app or via the JS snippet on your site.
>
> Help articles: Data Fields — https://help.chilipiper.com/hc/en-us/articles/27607845025555 ·
> Form Mapping — https://help.chilipiper.com/hc/en-us/articles/28929554231187
>
> Are your **data fields set up** and your **form mapped**, or do you need to do those first?"

- If either is missing, **pause** and offer to continue when ready.
- If unsure, have them check Settings → Data Fields and list what exists.
- The router can only *reference* fields that already exist — we validate against the ones
  discovered in Phase 1. → `api-reference.md` § Data fields (the API gap).

## Phase 1 — Discovery interview

Orient first: `tenant-get`, `workspace-list`, then `concierge-list-routers` for the target
workspace. Read existing routers' form/trigger fields to learn which `dataField` references
this tenant already uses; standard defaults are always valid. Only use references confirmed
to exist — an invalid one fails router creation.

### 1.1 Basics
- Which **workspace**? (show the list) · What **router name**?

### 1.2 Form fields
- Which **fields** should the form collect? (defaults: Email, First Name, Last Name,
  Company Size, Country). Map each to its data field → `segment-presets.md` § Field map.
- A field not in the defaults and not on an existing router = a custom data field: pause and
  have them create it in the UI first. `PersonEmail` is always required on the form.

### 1.3 Ownership rule (recommend: yes, first)
- Check **existing record ownership** first? On which objects (recommend Account, Contact, Lead)?
- Include **lead-to-account matching**? (recommend yes) · Which **team** handles owned records — new or existing? · Who's on it (or start with just the admin)?

### 1.4 Customer routing (recommend if they have a customer base)
- Route existing **customers** separately (to CSM/AM/account owner) before segment routing?
- If yes: what field marks a customer (e.g. `Account.Type = "Customer"`, a custom status)?
  Which **owner field** routes them (`Account.OwnerId` or a custom `CSM__c`/`TAM__c`)? Which
  **team**? Which **meeting type + duration**?
- Build as a non-ownership rule after ownership, before segments — or, when routing by a
  custom owner field, as an ownership rule whose `ownership` reference is that field →
  `api-reference.md` § Rules.

### 1.5 Segments
Explain first: *"Rules run top-to-bottom, first match wins — that's why ownership is first.
Segments catch everyone else."* Then ask how to segment — by **company size**, **region**,
**both**, or **another field**. Per segment: conditions, rule name, team (new/existing),
whether to add people now (else the admin is a placeholder — teams can't be empty). Ask
once: **same meeting type for all rules, or different per segment?** Thresholds and region
country lists → `segment-presets.md`.

### 1.6 Rule data sources
Per segment, offer multiple condition groups OR'd together (better matching): Form/Person,
SF Lead, SF Contact, SF Account. Field/object/source per group → `segment-presets.md`
§ Data-source map. Offer to set up all applicable groups automatically.

### 1.7 CRM actions (per rule)
Which post-booking actions? **Convert Lead is the only API-supported CRM-mutating action**
— but Notify (post to a Slack channel) is also writable via the API; it's a notification,
not a CRM write. Update ownership, create event, and add to campaign are **UI-only** —
capture them so the summary flags them for manual setup after the build.

### 1.8 Catch-all & not-scheduled
- No rule matches (**catch-all**): redirect to a URL, schedule with a fallback team, or
  schedule-with-timeout-redirect? The catch-all is **required**.
- Lead doesn't book (**not scheduled / timeout**): redirect URL or default landing page?
  What **timeout**? (default 10 min). Assign unscheduled/catch-all leads to a team?

### 1.9 Extra triggers
Besides the web form: a **Router Link** (shareable URL) and/or an **In-App Button**? Each
must include `PersonEmail`.

### 1.10 Naming convention
Any suffix/convention for created teams, rules, meeting types, distributions (e.g. a project
abbreviation)? Apply it consistently.

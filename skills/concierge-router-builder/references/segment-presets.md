# Segment presets — Concierge Router Builder

Standard thresholds, region country lists, and the field/data-source mappings used when
building rule conditions in Phase 1. Offer these as defaults; the admin can override.

## Company-size thresholds

| Segment | Employees |
|---------|-----------|
| SMB | 1–250 |
| Mid-Market | 251–1,500 |
| Enterprise | 1,501+ |

Encode as `StaticValueCondition` on a size field with `<=` / `>=` (or a `>` / `<=` pair for
a band). Add an "unknown company size" fallback rule before the catch-all if the admin wants
one. Condition shape → `api-reference.md` § Rules.

## Region country lists

Offer to populate these `isAnyOf` value lists (country display strings) on a country field:

- **NA** — United States, Canada, Mexico
- **EMEA** — United Kingdom, Germany, France, Spain, Italy, Netherlands, Sweden, Norway,
  Denmark, Finland, Ireland, Belgium, Switzerland, Austria, Portugal, Poland, Czech Republic,
  Romania, Hungary, Greece, Turkey, Israel, United Arab Emirates, Saudi Arabia, South Africa,
  Nigeria, Kenya, Egypt
- **APAC** — Australia, New Zealand, Japan, South Korea, Singapore, India, China, Hong Kong,
  Taiwan, Thailand, Philippines, Indonesia, Malaysia, Vietnam
- **LATAM** — Brazil, Argentina, Colombia, Chile, Peru, Costa Rica, Panama, Dominican
  Republic, Puerto Rico, Ecuador

Add an "unknown region" fallback before the catch-all if desired.

## Field map — form field → data field

Map the admin's plain-language fields to `dataField` references (used on the form and,
where applicable, in rule conditions). These standard defaults are always valid; anything
else must already exist as a custom data field (UUID from the UI).

| Field | dataField |
|-------|-----------|
| Email (required) | `PersonEmail` |
| First Name | `PersonFirstName` |
| Last Name | `PersonLastName` |
| Phone | `PersonPhone` |
| Company | `CompanyName` |
| Company Size / Employees | `CompanyEmployees` |
| Country | `PersonCountry` |
| Title | `PersonTitle` |
| State | `PersonState` |

## Data-source map — condition groups per object

For each segment rule, offer these condition groups (OR them together for better matching).
`source` is the `DataSource` enum (`SF`, `DF`, `CP`, `HS`, `MK`); `object`/`field` are the
`dataReference` for each `StaticValueCondition`.

| Group | source | object | Country field | Size field |
|-------|--------|--------|---------------|-----------|
| Form / Person | `DF` | `Person` | `Country` | `NumberOfEmployees` |
| SF Lead | `SF` | `Lead` | `Country` | `NumberOfEmployees` |
| SF Contact | `SF` | `Contact` | `MailingCountry` | *(size from Account)* |
| SF Account | `SF` | `Account` | `BillingCountry` | `NumberOfEmployees` |

- HubSpot tenants use `source: "HS"` with the equivalent HubSpot objects/fields — confirm
  the field names against an existing rule (`rule-list`) rather than guessing.
- Build one inner `ConditionGroup` per applicable source, wrapped in an outer group with
  `operator: "or"`; within a group combine size + region with `operator: "and"`.
- Full condition JSON shapes → `api-reference.md` § Rules.

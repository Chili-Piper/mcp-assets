# Embed reference: ChiliForms runtime

The public contract of `chiliforms.js` (ChiliForms 2.1.1). Source: `Chili-Piper/frontend`
`apps/chiliforms`.

## Contents

- Script tags
- Options
- Overrides
- Field types
- Generate mode behaviour
- Customer already has a form
- Attach mode (explicit request only)
- describe() and the instance API

## Script tags

```html
<script id="chilipiper-concierge"
        src="https://fire.chilipiper.com/concierge-js/cjs/concierge.js"
        crossorigin="anonymous" type="text/javascript"></script>
<script src="https://fire.chilipiper.com/chiliforms/cjs/chiliforms.js"></script>
```

- **Order matters.** `concierge.js` provides `window.ChiliPiper.submit`, which opens the booking popup. ChiliForms waits up to 10 s for it at submit time, so rendering still works if it's late, but a submission without it fails.
- `/chiliforms/cjs/chiliforms.js` is the **only** path. The legacy `js.chilipiper.com/chiliforms.js`, `chiliforms-fire.js` and `/concierge-js/cjs/chiliforms.js` are different, older scripts. Don't mix them on one page.
- Globals: `ChiliPiper.create(config)` (legacy call site, still supported) and `ChiliForms.create` / `ChiliForms.describe`. `ChiliPiper.ChiliFormVersion` reports the live version.
- The API host follows the script's own domain, so always serve the `fire.chilipiper.com` URL on customer sites.

## Options

`create()` resolves to an instance, or to `false` if it couldn't start. The reason is logged
with a `ChiliForms:` prefix and passed to `onError`.

| Option | Type | Default | Notes |
|--------|------|---------|-------|
| `domain` | string | **required** | Tenant subdomain (`tenant-get` → `tenantData.subdomain`) |
| `tenantId` | string | looked up | `tenantData.tenantId`. Pass it to skip the lookup |
| `router` | string | **required** | Router **slug** |
| `mode` | `'generate'`\|`'attach'` | `attach` if `formId`, else `generate` | |
| `formId` | string | — | `id` of an existing `<form>`. Implies attach |
| `selector` | string | `document.body` | Generate: CSS selector of the host element. Falls back to `<body>` with a warning if nothing matches |
| `trigger` | `'ChiliForm'`\|`'RouterLink'`\|`'ThirdPartyForm'`\|`'InAppButton'` | auto | Which trigger's field set to read |
| `locale` | string | router default | `en-US` or legacy `en_US`. Uses the router's `localizations`, with same-language fallback |
| `submitLabel` | string | `'Submit'` | Generate only |
| `injectStyles` | boolean | `true` (generate) | Minimal layout CSS. Set `false` to style from scratch |
| `overrides` | object | — | § Overrides |
| `prefillFromQuery` | boolean | `true` | Prefill from `window.location.search` via smart parameters |
| `multiValueSeparator` | string | `';'` | Joins multi-select values (the separator Salesforce multi-picklists expect) |
| `enhance` | boolean | `false` | Attach: apply router required flags, placeholders and email/tel/number input types to existing controls |
| `recaptcha` | string | — | reCAPTCHA **v2** site key. The page must load `https://www.google.com/recaptcha/api.js` itself |
| `post` | string (URL) | — | Also POST the lead there as `multipart/form-data`, fire-and-forget |
| `options` | object | — | Merged into the `ChiliPiper.submit` call: `lead` (extra/pinned values, which win over form values), `trigger` (pins the submit trigger, see Generate mode behaviour), and any other Concierge options (e.g. `onSuccess`) |
| `debug` | boolean | `false` | Log every API call and the resolved schema |
| `onReady(schema, form)` / `onSubmit()` / `onSubmitted(lead)` / `onError(err)` | functions | — | Lifecycle callbacks |

## Overrides

Keyed **case-insensitively** by data field reference or control name. Take the keys from
the field report, never invent them.

```javascript
overrides: {
  Industry: ['Retail', 'Technology'],               // shorthand: dropdown with these choices
  Segment: { smb: 'Small business', ent: 'Enterprise' }, // shorthand: value → label dropdown
  PersonCity: { hidden: 'Winnipeg' },               // pin a value, render as hidden
  PersonPhone: { required: true, errorMessage: 'We need a number to call you on' },
  CompanyName: { label: 'Company', placeholder: 'Acme Inc.' },
  InternalRef: { exclude: true },                   // drop from the form (and from routing)
}
```

Long-form keys: `type`, `label`, `placeholder`, `required`, `hidden`, `multiple`,
`errorMessage`, `options` (array or value→label map), `exclude`. An object without any of
these keys is read as the value→label shorthand.

## Field types

| `dataType.type` | Control |
|-----------------|---------|
| `ShortText` | `<input type="text">` |
| `LongText` | `<textarea>` |
| `Email` | `<input type="email">`, format-validated |
| `Phone` | `<input type="tel">`, format-validated |
| `Number` | `<input type="number">` |
| `Date` / `DateTime` | `<input type="date">` / `<input type="datetime-local">` |
| `Picklist` | `<select>` with a blank first option |
| `RadioButton` | radio group in a `<fieldset>` |
| `Checkbox` | multi-select checkbox group (values joined with `multiValueSeparator`) |
| `TrueFalse` | single checkbox |
| pinned `hidden` | `<input type="hidden">` |
| unknown reference | `<input type="text">` (collected, not dropped) |

Styling hooks: `.chiliForm` (form), `.chiliField` (wrapper), `.chiliRequired`,
`.chiliError` (inline message), `.chiliSubmit`, `.chiliRecaptcha`. These are the classes the
legacy scripts used, so existing CSS keeps working.

## Generate mode behaviour

- Controls are named by data field reference (e.g. `PersonEmail`), which is what the lead is keyed by.
- It submits under the first trigger whose mapping covers every field: a ThirdPartyForm mapping opens the booking calendar as a **modal**, and failing that a RouterLink opens **full-page** booking. If neither covers every field it refuses to render. `options.trigger` pins the choice, and a trigger that doesn't cover the fields fails at submit. Rules are in `api-reference.md` § Submit trigger.
- Values in `options.lead` are applied to matching controls and always win at submit.
- An inactive router (not accepting routing) still renders, but submissions won't route. A console warning says so.

## Customer already has a form

ChiliForms is for customers **without** a form. A customer with their own form (custom
HTML, CMS, form builder, HubSpot, Marketo, Pardot, …) uses the **standard Concierge
snippet**. Tell them so, and don't produce a ChiliForms config. Generic shape:

```html
<script src="https://<subdomain>.chilipiper.com/concierge-js/cjs/concierge.js" type="text/javascript"></script>
<script>
  ChiliPiper.deploy("<subdomain>", "<router-slug>", {"formType": "<type>"})
</script>
```

- The first argument is always the **subdomain** (`tenant-get` → `tenantData.subdomain`), never the company domain.
- `formType` depends on the platform (`Marketo`, `PardotFormHandler`, `GravityForms`, `Typeform`, `Instapage`, …). Plain HTML forms are detected without a platform type.
- **The script and function differ by platform.** HubSpot, for example, uses `marketing.js` plus `ChiliPiper.submit` in a form-callback listener. Don't adapt one snippet to another. Follow the Help Center article for the platform, starting from *Concierge Snippet and JS API* (32588330506643).
- The router needs a `thirdPartyForm` mapping of the form's field names. That is a router change for `concierge-router-configuration`.

## Attach mode (explicit request only)

Use only when the customer explicitly asks for ChiliForms to wire up their form, e.g. to
migrate a legacy `chiliforms-fire.js` integration. Otherwise use § Customer already has a form.


- A `<form id="...">` in the page, and a submit button (`button[type=submit]` or `input[type=submit]`). ChiliForms intercepts `submit` and calls `preventDefault()`, so the form's own `action` doesn't run.
- Each control's `name` must equal a ThirdPartyForm trigger `mapping[].name` (`concierge-list-routers` → `formMapping`) to be routed on. Controls with no mapping entry are still submitted, but Concierge can't route on them.
- The email mapping must be present **and** matched by a control.
- **Reserved names:** a control whose `name` is also an HTML form property (e.g. `id`, `name`, `action`, `method`, `target`, `elements`, `submit`, `reset`, `length`, `title`, `hidden`, `lang`, `dir`) shadows that property and can break submission. Rename the control. `overrides.exclude` doesn't fix this.
- If the router config can't load, the form still submits with native browser validation. It degrades to the legacy behaviour and doesn't break the page.
- `enhance: true` changes the customer's form visibly (required flags, input types), so only use it when asked.

## describe() and the instance API

```javascript
const schema = await ChiliForms.describe({ tenantId: 'acme.com', router: 'inbound-demo' })
// schema.fields[]: {name, dataFieldRef, label, type, required, hiddenValue?, options?, aliases?}
```

`describe()` renders nothing and never submits, so `domain` is optional. It reports every
trigger kind, including `ThirdPartyForm` and `InAppButton`. Use it when the customer wants
to render the form in their own framework, then submit through `ChiliPiper.submit`.

Instance: `getLead()` returns the current values as submitted, `validate()` renders inline
errors and returns a boolean, `submit()` goes through the same path as the button, and
`destroy()` detaches listeners (in generate mode it also removes the form).

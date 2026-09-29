# Troubleshooting: ChiliForms embeds

Every ChiliForms console message starts with `ChiliForms:`. Ask the customer to reload with
`debug: true` added to the config and paste the console lines. Then match them below. Check
`ChiliPiper.ChiliFormVersion` in the console to confirm which script is live (2.x means the
new one).

## Nothing renders

| Console says | Cause | Fix |
|--------------|-------|-----|
| `you must provide a router` / `…a domain…` | Missing required option | Add `router` (slug) and `domain` from `tenant-get` |
| `no Chili Piper tenant is registered for the subdomain "…"` | Wrong `domain` (often the website domain) | Use `tenantData.subdomain`, and pass `tenantId` too |
| `tenantId "…" was given without a domain` | Only `tenantId` supplied | Add `domain`, which `create()` requires |
| `"…" is not a valid router slug` | Display name used instead of slug | Use `slug` from `concierge-router-get` |
| `…/router/<slug> failed with HTTP 404` | Slug wrong, or router renamed (a rename re-derives the slug) | Re-read the slug |
| `router has no usable trigger (looked for ChiliForm, RouterLink)` | Router has no Chili webform or router link with fields | Hand off: add a Chili webform or router link. If the customer has their own form, they want the Concierge snippet instead |
| `resolved to the ThirdPartyForm trigger … Nothing is rendered` | `trigger: 'ThirdPartyForm'` forced in generate mode | Remove `trigger` |
| `router has no "X" trigger configured` | `trigger` option names a kind the router lacks | Remove `trigger` or pick one the router has |
| `exposes no fields for the … trigger` | Trigger exists but is empty | Hand off: add fields to that trigger |
| `no <form> found with id "…"` | `formId` doesn't match, or the script ran before the form existed | Fix the id. For forms injected later (CMS/form builders), call `create()` after the form is in the DOM, e.g. in the builder's ready callback |
| `selector "…" matched nothing` | Host element missing | The form falls back to `<body>`. Fix the selector |
| Nothing at all, no `ChiliForms:` lines | Script blocked or never loaded | § Blocked scripts |

## Renders, but submit fails

| Console says | Cause | Fix |
|--------------|-------|-----|
| `window.ChiliPiper.submit is unavailable` | `concierge.js` missing, blocked, or loaded after a 10 s wait | Add the Concierge snippet before `chiliforms.js`. See § Blocked scripts |
| `router "…" is inactive` | Router isn't accepting routing | Re-enable it in Concierge. The form renders, but nothing routes |
| `reCAPTCHA must be completed…` | Guest skipped the captcha | Expected behaviour |
| `grecaptcha never became ready` | `recaptcha` set but Google's `api.js` not on the page | Add `<script src="https://www.google.com/recaptcha/api.js" async defer>`. Until then the form submits **without** a captcha |
| `these control names shadow a form property: …` | A control is named `id`, `action`, `name`, … | Rename the control (see embed-reference § Attach mode (explicit request only)) |
| `ignoring "post" option` | `post` isn't a valid absolute URL | Use a full `https://` URL |

## Renders, but fields are wrong

- **A field shows as plain text instead of a dropdown.** Its data field has no catalogue entry, or the catalogue failed to load (`could not load data field metadata`). Check the reference in `data-field-list`. A missing one means the router mapping is stale, so hand off.
- **Labels are in the wrong language.** `locale` isn't in the router's `localizations`, so the router's default labels are used. Add the translation in Concierge, or drop `locale`.
- **A recent router edit isn't showing.** ChiliForms serves the *published* configuration. Publish the router's draft in Concierge.
- **Attach: a field never reaches routing.** Its `name` doesn't exactly match a `formFieldName` (the match is case-sensitive). Fix the control name, or hand off a mapping entry.
- **URL prefill doesn't work.** The query parameter isn't the reference, the control name, or one of the field's `smartParameters`. Add an alias (`data-field-set-smart-parameters` is a write, so it needs an admin).
- **Multi-select values arrive merged wrong in the CRM.** Set `multiValueSeparator` to what the CRM field expects (default `;`).

## Calendar opens full-page instead of as a modal

Generate mode submits as `ThirdPartyForm`, which opens the modal. If `options.trigger` is set
(e.g. `'RouterLink'`), Concierge opens the full-page booking instead. Remove it.

## Blocked scripts

- **Consent managers** (OneTrust, Osano, Cookiebot, …) often block `fire.chilipiper.com` scripts until consent, or categorise them as marketing. A blocked script may still show in the Network tab but never execute. The customer must categorise both scripts as strictly necessary/functional, or load them after consent.
- **Content Security Policy:** the page must allow `script-src https://fire.chilipiper.com` and `frame-src https://calendar.chilipiper.com` (the hidden bridge iframe that makes the API calls). The booking popup also needs `frame-src https://*.chilipiper.com`.
- **Ad blockers / privacy extensions** can block the bridge iframe. Test in a clean browser profile before escalating.

## Escalate to Chili Piper support when

The config is correct, both scripts load, the router slug resolves, and the form still fails.
Include the `debug: true` console output, the page URL, `ChiliPiper.ChiliFormVersion`, and
the router slug. Leave out guest data.

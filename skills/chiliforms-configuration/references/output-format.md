# Output format: chiliforms-configuration

Lead with the snippet (what the customer came for), then what it will do, then anything
that blocks it, then how to test it. Keep examples synthetic.

---

## Layout

### ChiliForms setup | `<router name>` (`<slug>`) | `<generate|describe>` mode

**Why this router works:** one sentence tied to the trigger inventory, e.g. *"This router has a Chili
webform with 5 fields, so ChiliForms can build the form for you."*

**Snippet**: paste where the form should appear. Generate mode: put the host element where
the form should render.

```html
<div id="chiliform-host"></div>

<script id="chilipiper-concierge"
        src="https://fire.chilipiper.com/concierge-js/cjs/concierge.js"
        crossorigin="anonymous" type="text/javascript"></script>
<script src="https://fire.chilipiper.com/chiliforms/cjs/chiliforms.js"></script>
<script>
  ChiliPiper.create({
    domain: 'acme',          // tenant-get → tenantData.subdomain
    tenantId: 'acme.com',    // tenant-get → tenantData.tenantId
    router: 'inbound-demo',  // router slug
    selector: '#chiliform-host',
    // only the options the customer's requirements need, each with a one-line comment
  })
</script>
```

Explicit attach requests only: replace `selector` with `formId: '<form id>'`, put the
snippet **after** the form markup, and omit the host `<div>`.

If the page already loads `concierge.js`, say so and tell the customer not to add it twice.

**What the form collects**

| Field | Reference | Control | Required | Notes |
|-------|-----------|---------|:--------:|-------|
| Work email | `PersonEmail` | email | ✅ | prefill: `?email=` |
| Company size | `<uuid>` | dropdown (4 choices) | — | |
| Source | `<uuid>` | hidden | — | pinned to `website` |

**Field mapping check** (explicit attach requests only)

| Form control `name` | Maps to | Status |
|---------------------|---------|--------|
| `email` | `PersonEmail` | ✅ mapped (email field) |
| `company` | `CompanyName` | ✅ mapped |
| `utm_source` | — | ⚠ not mapped. Submitted, not routed on |
| *(none)* | `PersonPhone` (`phone`) | ⚠ mapping entry with no control |

**Blocking gaps**: omit the section when there are none. Each one names the fix and who
applies it:

> ⛔ **This router can't generate a form.** It has no Chili webform or router link. Add a
> Chili webform → `/configure-concierge-router <workspace> update <router>`. If the router
> already serves a form through a third-party mapping, use a dedicated router instead,
> because converting it would break that form.

> ⛔ **Email not mapped.** Proposed `thirdPartyForm` entry to add:
> `{formFieldName: "email", dataField: "PersonEmail"}` → `/configure-concierge-router`
> (a live write, which shows its own dry run first).

**Warnings**: non-blocking items: unknown data field references, a `locale` with no
translation, reserved control names, reCAPTCHA needing Google's `api.js`, and the
published-vs-draft note if the router was edited recently.

**Test it**

1. Put the snippet on a staging page. Temporarily add `debug: true` to the config.
2. Open the browser console. Expect `ChiliForms:` log lines and no errors, and `ChiliPiper.ChiliFormVersion` should read `2.x`.
3. Submit with a test email and confirm the booking calendar opens.
4. Remove `debug: true` before publishing. If anything fails, paste the console lines back here.

**Human decision point**

*"Want me to adjust anything before you put this on a live page? Any router-side fixes
listed above need `/configure-concierge-router`, which shows its own dry run before
changing anything."*

---

## Customer already has a form

No ChiliForms snippet. Lead with one line: *"Since you already have a form, you want the
standard Concierge snippet rather than ChiliForms."* Then give the generic
`ChiliPiper.deploy` shape with their subdomain and router slug filled in, the platform
caveat, and the Help Center pointer (`embed-reference.md` § Customer already has a form).
Close by offering the router's `thirdPartyForm` mapping via `/configure-concierge-router`.

## Describe mode

Replace the snippet with a `ChiliForms.describe({tenantId, router})` example and the field
table, and note that the customer's own form must submit through
`ChiliPiper.submit(domain, router, {trigger: 'ThirdPartyForm', lead})`, with `lead` keyed
by data field reference.

## Troubleshooting runs

When the input is a broken embed rather than a new one, lead with **Diagnosis** (the
matched row from `troubleshooting.md` and the evidence behind it), then the corrected
snippet, then **Test it**.

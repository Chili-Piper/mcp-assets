# Concierge

Inbound form routing. Read `shared-assets.md` first: teams, rules, distributions, meeting types and the data-source rule are there.

## The shape of a router

**Gate before `concierge-router-create`:** is the mapping table filled (field names, submitted values, CRM targets)? Do you have a URL for **every** Redirect, including the catch-all, from the customer rather than a placeholder? Is the catch-all outcome one they chose? Does every Schedule path carry the `crmActions` the plan agreed, including record creation for net-new and the ownership update if they asked for it? The create publishes live, so there is no draft to fix afterwards.

`concierge-router-create` publishes live in one step. **Concierge and Handoff routers cannot be created inactive**, so a successful create is live immediately. (A publish that fails is the exception: it leaves an unpublished draft behind; see Verify.) Distro is the exception: `distro-router-activate` / `-deactivate` let a Distro router be built inactive and reviewed before it fires on live records.

In the app a router is a flow of nodes; the MCP exposes it flattened, as an ordered `routing` matrix plus trigger config. For exact field shapes on `routing`, `assignment`, `timeout`, `crmActions` and the four trigger kinds (`form`, `thirdPartyForm`, `inAppButton`, `routerLink`), read the live schema with `describe-tools` on `concierge-router-create` rather than working from memory. Describe it on its own, never batched with the router list or log tools, which are very large to describe (`build-patterns.md` § Reading the account). The gotchas the schema will not warn you about:

- **Use only the CRM action family matching the connected CRM.** The schema exposes both Salesforce and HubSpot families and will not stop you choosing wrong (`build-patterns.md` § One CRM).
- **`thirdPartyForm` and `form` are mutually exclusive**, and writing one onto a router configured for the other converts it. Never send both.
- **`formFieldName` is the name the external form submits, not the label the visitor sees.** HubSpot has two shapes and which one you get depends on the embed: the older form payload looks like `0-1/email`, while the current `marketing.js` embed passes `submissionValues` keyed by plain property name (`email`, `firstname`, `country`). Check which snippet is on the page before writing the mapping. Read the submitted names from the customer's form platform; Pardot and HubSpot name them differently and that is where mapping mistakes come from. The same trap applies one level down, to a picklist's **option values**: a `<select>` option labelled `51-100` may carry `value="50-100"`, and Chili Piper receives the value, so a rule written from the label never matches and nothing errors. Ask the customer to paste the field's HTML and both problems disappear at once.
- **`routerLink` is how you make progress before the external field names arrive.** It coexists with `thirdPartyForm` (only `form` and `thirdPartyForm` are mutually exclusive), so a router built with a `routerLink` trigger gives a shareable URL you can verify against today, and the third-party mapping is added to the same router later. Better than stalling the build, and better than guessing at field names.
- **`hidden` on a form field is a prefilled value**, not a show/hide flag.
- Every trigger kind must include `PersonEmail`, and a `dataField` that does not exist is rejected with a 400.
- `ruleId` is required on every row. An always-match route is the `catchAll`; a router with neither rows nor a catchAll is rejected.
- Supplying no trigger at all auto-generates a minimal email-only Chili webform.

The customer's form platform being HubSpot or Marketo says nothing about their CRM. A HubSpot form routes into a Salesforce-connected org with no HubSpot integration at all.

## Routing steps: what runs before the routes

`routingSteps` is an ordered array on the router that runs **before** any route is evaluated. Two kinds, both buildable:

- **`{type: "SpamCheck", writeSpamScoreToDataField, onSpam?}`.** `onSpam` is a full outcome, so the spam path can redirect or schedule. Scoring settings are still shared with Chat and still live in the workspace at `/workspaces/<wsId>/chili-agents/spam-checker`. Read Disqualification below before telling anyone the defaults will do.
- **`{type: "Enrichment", waterfalls: [{dataField, waterfallId}], timeoutSeconds?}`.** `waterfalls` must be non-empty. This is what makes a segment work on data the form does not carry, because it runs before the decision rather than after it. Get ids from `enrichment-waterfall-list` (it needs a `workspaceId`, and each result carries `tiedToDataField`, which tells you which data field that waterfall populates and therefore what to pair it with). **Configuring the providers behind a waterfall is Admin Center**, so on an org with none this is a prerequisite to name, not a step you can finish.

Two things not to lose. A waterfall set in the Concierge app against a third-party form or a router-link field is **preserved when you update the router**, so an in-app one is safe from your later `concierge-router-update` calls. And **Distro's `routingSteps` use different shapes for the same two ideas** (`Enrichment` takes `fieldMappings` with a `variableId`, `SpamCheck` takes `salesforceWrite`), so a step copied from one product into the other is a 400.

## Disqualification

Ask who should **not** get a meeting. Customers describe who they want to reach and rarely volunteer who they want turned away, so the question has to be asked. Common answers: personal email addresses, competitors, students and job seekers, existing customers, unsupported regions, companies under a size floor.

Two ways to do it in the routing itself. The catch-all covers everyone in one outcome; an explicit rule is what you reach for when a named group needs its own destination.

**Implicitly, at the catch-all.** This is the common shape and the one to set up by default: the booking rows say who qualifies, and the catch-all at the end of the flow handles everyone who matched nothing. Most customers point that catch-all at a disqualification outcome, so the router reads as an allow-list. Set it deliberately, because the alternative is equally valid: send unmatched visitors to an SDR or a fallback pool instead of turning them away. That choice is the question to put to the customer, and a router with no catch-all leaves it unanswered.

**Explicitly, with a rule above the booking rows.** Use this when a named group needs its own destination rather than the one everybody else gets: SMB to a self-serve signup URL, competitors to the homepage, students to careers. Routing is top-down and the first match wins, so a row placed above the booking rows short-circuits them. Give it `{type: "Redirect", url}` instead of `Schedule`. The condition is an ordinary rule, so excluding personal addresses can simply read on the email field (does not contain `@gmail.com`, and so on).

**Only build the explicit row where the destination differs.** The two mechanisms overlap, and the overlap is easy to miss: once the booking rows are an allow-list and the catch-all disqualifies, **everyone below the floor is already turned away**. A row that tests "size is the smallest band" and redirects to the same place as the catch-all adds a rule, a row and a thing to maintain for an outcome that already happened. The test is whether that group needs its *own* destination. Same destination as everybody else who did not qualify means no row: let the catch-all do it, and say so, because "the catch-all covers this" is a sentence customers accept readily once the allow-list shape is explained.

Either way, ask where each group lands: a pricing page, self-serve signup, a "we'll be in touch" page, or back to the form.

**"Turn them away" and "redirect to a page" are the same outcome**, so never offer them as two options. Both are `{type: "Redirect", url}`; one just has not named the URL yet. The only real choices for a group are: redirect somewhere (ask where), or route to a pool (ask which). Presenting a third makes the customer pick between two spellings of the same thing and leaves the destination unasked.

**Spam Checker is the other mechanism, for the shape of an address rather than a named list** (help 44735133771795). It is a `SpamCheck` entry in `routingSteps`, so it runs before the routes, and its `onSpam` outcome is where the spam path goes. Binary checks disqualify instantly: MX check, domain blocklist, email blocklist. Weighted checks add points against a threshold: role-based (`info@`, `sales@`), disposable, free-provider, and an AI gibberish check. The spam path is a redirect URL or a fallback distribution; suggest the fallback, since it catches false positives and does not tell a real spammer they were caught.

**Its defaults do not disqualify a personal email.** Free Email Check is on at 2 points against a threshold of 3, so a Gmail address alone scores 2 and books. So "DQ personal emails" is never answered by the defaults: either write the rule, or deliberately raise that weighting, knowing a lower threshold catches more of everything.

So: the **catch-all** for the general "did not qualify" outcome, an **explicit rule** where a named group needs its own destination, and **Spam Checker** for junk nobody can enumerate in advance.

Whichever mix you build, set the catch-all deliberately. The API allows omitting it, so nothing will stop you, but a router with no catch-all drops unmatched visitors silently, which is the one outcome nobody chose. Recommend one in every plan and leave it out only when the customer says so explicitly.

## Distribution handling

**Default the Meeting distribution to Flexible** and say why in a line rather than asking. The prospect is the one picking a time, so combined availability across the pool gives them far more to choose from and more of them book. Strict is the deliberate exception: take it if the customer asks for even distribution above conversion.

## CRM actions

`crmActions` on a Schedule outcome is an ordered chain that runs after the booking. It is the only place these behaviours can be set, so an omitted chain is a decision, not a default.

**A publish can fail on the contents of a `crmActions` chain without saying which action.** `Failed to publish draft` can come back while the draft reads back looking correct. Not every action is valid on every outcome type: the assignment is the required part of a Schedule outcome, and an action that is merely useful can still be the thing being rejected. So when a publish fails and the draft looks right, **narrow it by removing the chain and adding it back a piece at a time** rather than reasoning about what should be allowed. That usually finds it in a couple of calls.

**Logging the meeting on the record is a `crmAction`, so build it.** This is the Create Event node in the app (help 28522554434323), and it writes an activity for every scheduled meeting.

- **`SalesforceCreateEvent`** requires `meetingCancellationBehavior` (`DeleteEvent` or `DoNothing`) and `guestsBehavior` (`CreateEvents` or `DoNothing`). Optional `relatedTo`: `Account`, `Opportunity`, `Case`, `Campaign` (with a `campaignId`), `ExplicitObject` (with an id), `NoRelationNeeded`, or `RelationDisabled`.
- **`HubspotCreateEngagement`** requires `owner` (`Assignee` or `Booker`) and `meetingCancellationBehavior`. Optional `relatedTo`: `Company`, `Deal`, `Ticket`.

Neither has a sensible default worth guessing at. Ask what the event should hang off and whether cancelling the meeting should delete it, the same way you would ask about any other customer-facing behaviour.

**Order matters in the chain.** Create or Update Record must come **before** Create Event, Update Field, Add to Campaign and Update Ownership: the record has to exist before anything can be written to it. That is the same reason record creation is a standing default here.

**Ask whether the booking should change the record's owner.** `SalesforceUpdateOwnership` / `HubspotUpdateOwnership` set the owner to the booked host. Customers routing inbound through a round-robin very often want this: the pool picked a rep, so the rep should own what they were handed. It is a policy question with a real wrong answer, so ask rather than defaulting either way, and ask it per row: an ownership row routed to the existing owner already, so there is nothing to update there.

**Create the record for net-new bookers, by default.** `SalesforceUpsertRecord` / `HubspotUpsertRecord` creates the record when nothing matched. Put it in without waiting to be asked, because an inbound form exists to catch people who are not in the CRM yet, and without it every other write-back on that path has nothing to act on: the ownership update the customer just approved is a no-op for exactly the population the router was built for. It is still record-creation policy, so name it as a default you have included rather than slipping it in.

Worth raising in the same breath, since it is one conversation:

- `AddToCampaign` with a `memberStatus`, for a campaign-driven motion (`campaign-list` / `campaign-search` for the id).
- `SalesforceUpdateFields` / `HubspotUpdateFields`, to write submitted values onto the record. A value can be a date as well as a static string: `StaticDate`, or `RelativeDay` / `RelativeWeek` / `RelativeMonth` / `RelativeQuarter` / `RelativeYear`, each with `offset`, `length` and an IANA `timeZone`. The schema does not say what `offset` and `length` count from, so check the written value on one record before relying on it.

**Use only the family matching the connected CRM.** The schema exposes both and will not stop you picking wrong (`build-patterns.md` § One CRM).

**Do not build `ConvertLead`.** Lead conversion is a Distro capability, and a Convert Lead action on a Concierge router does not appear in the flow builder, so an admin would have no way to see or maintain it. So a customer who asks about converting leads on booking wants the Distro Lead Conversion node instead (`distro.md`), and the honest answer names that rather than shipping a step nobody can find. If a router you inherit already has one, it can be read and removed through `concierge-router-get` / `-update`.

## Data timing

The one thing to establish before building a segment: ask which population it must cover, then make sure net-new has somewhere to land rather than silently hitting catch-all. This is a Concierge question specifically; Distro starts from a record that already exists, and Handoff's version of it (a rep booking someone the CRM has never seen) is settled at the Handoff router's catch-all. What each population can actually be routed on → `routing-data.md`.

## Deployment snippet

Assemble it rather than sending them to the router's Embed tab. `tenant-get` gives `tenantData.subdomain`; `concierge-list-routers` (or the create response) gives the slug. **The first value is always the subdomain, not the company domain.**

**The script and the function both differ by platform, so do not adapt one snippet to fit another.** Search the help center for the customer's platform and follow that article: HubSpot, Marketo, Pardot (form handler and iframe are separate articles), Typeform, Gravity Forms, Webflow, Contact Form 7, Instapage, plain HTML. Start from 32588330506643 (Concierge Snippet and JS API) and 16883161528339 (callback methods).

Generic, where the router runs on page load:

```html
<script src="https://<subdomain>.chilipiper.com/concierge-js/cjs/concierge.js" type="text/javascript"></script>
<script>
  ChiliPiper.deploy("<subdomain>", "<router>", {"formType": "<type>"})
</script>
```

HubSpot, which is a **different script and a different function** (help 36470707166611):

```html
<script src="https://js.chilipiper.com/marketing.js" type="text/javascript"></script>
<script>
  var cpTenantDomain = "<subdomain>";
  var cpRouterName = "<router>";
  var cpHSDataFormIDs = [];   // empty accepts all forms; otherwise list data-form-ids
  window.addEventListener("message", function (event) {
    if (["hsFormCallback", "hsCallsToActionCallback"].includes(event.data.type) &&
        ["onFormSubmitted", "onCallToActionFormSubmitted"].includes(event.data.eventName)) {
      if (cpHSDataFormIDs.length > 0 && !cpHSDataFormIDs.includes(event.data.id.toString())) return;
      var lead = event.data.data.submissionValues;
      for (var key in lead) { if (Array.isArray(lead[key])) { lead[key] = lead[key].join(";"); } }
      ChiliPiper.submit(cpTenantDomain, cpRouterName, { map: true, lead: lead });
    }
  });
</script>
```

Two HubSpot gotchas that stop the calendar appearing even with a correct snippet:

- **The post-submit redirect has to be off in two places**, the form's own Options and the landing-page module that embeds it. Miss either and the prospect is redirected away before the calendar loads. This is the usual cause of "the snippet is live and nothing happens".
- **The Trigger screen's Find Form button auto-maps the live field names**, which is faster and more reliable than typing them, and it settles the `0-1/email`-versus-plain-name question by reading what the form actually sends.

`ChiliPiper.deploy` runs the router on page load; `ChiliPiper.submit` fires it on a form submission you hook yourself. Verify by inspecting page source, not by looking at the page.

## Verify

**Run the router rather than re-reading it.** `concierge-route-by-slug` takes a slug and a lead, evaluates the rules and returns the resolved assignment, which proves the matrix end to end without waiting for real traffic. Send one lead per segment plus one that should be disqualified, and read `distributionIds` / `assignments` against what you intended. A disqualified lead comes back `schedulingAllowed: false` with no distribution.

Two things decide whether that test is worth anything:

- **Pass an `interval`.** Without one the call returns `schedulingAllowed: true` and looks healthy on a tenant where nothing can be booked. With one, the availability engine actually runs. The same router and the same broken prerequisite look opposite depending on this one field, so a verify without an interval is a false green.
- **An interval is necessary and not sufficient, because a Flexible pool fails loudly only when it fails completely.** If **every** host lacks a calendar you get a hard error naming the userIds. If **some** do, they are silently dropped from availability and the call returns `schedulingAllowed: true`, a full slot list, and an empty `failures` object. The router reports healthy while routing to a subset, and a weighted pool can be routing to nobody. So read the returned attendees against the pool roster and check the count, rather than trusting a green result: a pool of six answering with three bookable hosts is a finding, not a pass.
- **Only supply values the form genuinely sends.** You are filling in the `form` map yourself, so a rule that reads a field the customer's form does not populate will match perfectly in your test and never fire in production. If the mapping gate left a field unconfirmed, that segment is untested no matter what the call returns, and saying so is the honest report.

Then check Concierge logs and the CRM (including Booking Status for no-book leads). `concierge-logs` and `concierge-list-routers` carry very large schemas, so read `schemaTokens` before describing them.

**If `describe-tools` on `concierge-router-create` is too large for your client.** Where the client saves the payload to a file, read only the tool's `description` and `inputSchema.properties` from it. Where it does not, build from the `routing`, outcome and trigger shapes documented above, and expect to correct a field name on the first 400. Remember that a failed publish leaves an unpublished draft and a retry mints a second one, so fix or delete the leftover in the Concierge app rather than retrying.

**Did not fire on submit:** check the snippet is actually live (view source); check field mapping; check the trigger and routing conditions; check Spam Checker did not disqualify.

# Chat

Website chat journeys, playbooks and web experiences. Chat AI is the AI capability configured inside journeys, not a separate product line. Read `shared-assets.md` first.

**Include Chat** in the "what would you like next?" options whenever the org's tier covers it.

## Where the journey actually lives

**The journey is the `conversation` node graph inside a web experience.** It is not a separate object and it does not have its own tool category. The `chat` category holds one read-only tool (`chat-logs`), so do not conclude from that category alone that journeys have to be built in the app.

Build and edit them with `web-experience-create` / `-update` / `-get` / `-list` / `-delete`. `widgetType` is `Chat`, `Scheduling`, `Offer` or `Message`.

## Publishing, drafts, and what "live" means

**`web-experience-create` publishes.** The experience is Enabled and customer-facing in one call. This is the most consequential write in the whole skill, so get explicit approval before making it, on the level you would for a Concierge router.

Two things make that less alarming than it sounds, and both are worth saying to the customer rather than leaving them to worry:

- **Nothing shows on their site until the Chili Piper snippet is on the page.** "Live" means live in Chili Piper. On a site with no snippet deployed, building a Chat experience changes nothing a visitor can see, which makes it safe to build ahead of the deployment.
- **The product does have a draft state**, even though the MCP write path does not stage anything. `web-experience-update` patches the draft **and republishes in the same call**, so you cannot use it to prepare a change and publish later. Related consequences from the schema: a rename hits the draft and the live version keeps its old name until the next publish; `enabled` toggles Live and Paused but needs a prior publish; and a rename returns **423 while someone has the draft open in the app's builder**, which is a lock, not an error to retry around.

## A failed create can leave a draft behind

Whether a failed create leaves anything behind depends on the error:

- **`DecodingFailure at .x.y`** is input validation, rejected before anything is created. Nothing left behind, safe to retry.
- **`Proxied call error: <a business rule>`** means the draft was already minted and survived the rejection. **Retrying creates a second one.**

A draft left this way does not appear in `web-experience-list`, and `web-experience-get` returns the same validation error on it, so only the app shows it.

So on a `Proxied call error`: do not retry. Tell the customer an orphan exists, give them the workspace journeys link, and ask what they can see, because the API will not tell either of you. `web-experience-delete` is the cleanup, and you cannot confirm the target with `web-experience-get` first.

## What the interview has to settle

**Start with the open box** (`interview.md` § Ask for it in their words first): ask them to describe how they want the chat set up, then work the list below as a gap check rather than a questionnaire. Name what you took from their description and ask only for what is missing or ambiguous.

1. **Where and when it shows.** Chat is the one motion whose trigger is about the visitor's behaviour on the page rather than a form submission or a CRM change, so ask for it properly: which pages (URL rules, and whether by exact match, path prefix or pattern), query parameters, time on page, scroll depth, device type, browser language. "On the pricing page after twenty seconds" and "everywhere" are very different experiences and customers rarely volunteer the difference. Get this before designing the journey, because it decides how qualifying the conversation itself needs to be.
2. **The welcome message.** The first thing the visitor reads, so it is customer-facing copy: get their words rather than writing it and shipping it unseen.
3. **Then branch on whether the org has Chat AI.** It needs **`Experiences` or above**; an org on `RoutingAndScheduling` does not have it. Do not close the question on one user's tier, though, because the seat you read is not the org's entitlement: check **which licences are still free to assign** before telling anyone they cannot have Chat AI (Command Center Users, `/fire/admin/users`; search the live tool list for a licence or seat read first). An org holding unassigned Experiences seats can have Chat AI today, and the answer is to assign one rather than to build the scripted version.
   - **No Chat AI.** A scripted journey: welcome message, reply buttons, Send Data Field nodes, routing rules. Ask what the reply-button paths are.
   - **Chat AI.** A Chat AI node at the top instead (help 44471539899411). Three asks: Smart or Fixed greeting, which **Strategies** to detect (meeting requests, pricing questions, product questions, competitor mentions), and any **Shortcut** buttons for visitors who want to skip the conversation. Then build a path per strategy.
4. **The actions on each path**, whichever branch. **One or many, not a choice between them**: a single path routinely does several, for example create the Salesforce record, notify the assignee in Slack, then hand to a live rep. Ask which they want, take several, and never offer these as a menu of one.
   - **Live rep handoff** - Route for Live Chat, plus Wait for Rep with both branches. Available whether or not they have Chat AI.
   - **Show the calendar** - Display Calendar, to book for later rather than talk now.
   - **Write to Salesforce** - Update or Create Record, Create Event, Update Field, Create Task. Chat is a first-touch surface, so most visitors are net-new and the create side matters more here than anywhere else.
   - **Notify the rep** - Send a Slack Notification. Native, and it needs the Slack integration configured plus @chilinbot in the channel. Microsoft Teams is not a native node: it goes through Zapier (help 42781515384851), so name it as a prerequisite rather than putting it in the plan as a build.
5. **Who the live chats go to, and what happens when nobody is available.** Ask both explicitly. A chat journey looks like content rather than routing, so assignment is the easiest thing to skip, and a journey with no assignment reaches nobody. The no-rep branch is a real decision with no safe default (see the Wait-for-rep node below).
6. **What qualifies a visitor.** The routing question is the same shape as any other motion; the data is not (see Anonymous visitors below).

## Building the journey

Read the node types from the live schema before designing anything, and set `type` explicitly on every node: it equals the variant's schema title (`build-patterns.md` § Typed errors).

Nodes worth building in deliberately, because a journey without them looks complete and does less than the customer expects:

- **An email-collecting node before anything that routes.** `StartLiveChat` rejects with `Node with id: 'N' does not have an email input before` if nothing upstream has collected one. That constraint shapes the whole journey: a form comes before any branch that assigns.
- **An assignment node on the live-chat path.** Easy to omit, and the journey still builds. Without it the chat reaches no rep at all.
- **Wait-for-rep, with both branches.** If a rep is available, hand over. If not, say what happens instead: offer a booking link, take a message, or fall back to a different pool. Ask which, do not pick.
- **Spam Checker and enrichment**, if the schema carries them for this widget. Both exist as routing steps on Distro and on Concierge, in different shapes from each other, so check what Chat's own schema takes rather than copying either.
- **Create or update the CRM record.** Without it, anything else written to the record has nothing to write to for a net-new visitor.

## Two things Chat cannot do that other motions can

- **`NavigateTo` moves between nodes in the journey, it is not a URL redirect.** So a disqualified visitor cannot be sent to a pricing page the way a Concierge catch-all sends them. Anyone asking to mirror a Concierge disqualification in Chat needs telling this before the design, not after.
- **Chat uses both Conversation distributions** (live chat routing) **and Meeting distributions** (when the journey books), so a Chat build can reuse a Concierge or Handoff meeting pool, but the live-chat side needs a Conversation pool of its own.

## Anonymous visitors

Chat decides while the visitor is on the page, so a CRM condition only covers visitors who match an existing record. Unlike Concierge, a journey can collect and enrich during the conversation before it routes, so an anonymous visitor is not stuck with whatever a single form submission carried. Worth knowing when a segment has to cover both (`routing-data.md`).

A rule reading the `DF` form layer does not carry to a Chat journey unless that journey collects the same field. Check what the journey actually asks for before reusing a rule built elsewhere.

## Configuration that is not a tool call

- **Knowledge Base**: a website URL with scan depth (shallow / medium / deep) plus uploaded files. Keep it current.
- **Personality**: bot name, avatar, tone, response length, matched to brand.
- **Strategies** for real intents (a demo request triggers scheduling, pricing routes to a rep, a competitor mention triggers a differentiator). **Guidances** for handling (pricing: do not quote figures, offer to connect with sales; support: redirect to the support address).
- **Spam Checker** settings are shared with Concierge; configure once at `/workspaces/<wsId>/chili-agents/spam-checker`.

## Verify

Test end to end and check `chat-logs`. There is no Chat equivalent of `concierge-route-by-slug`, so verification is a config read-back plus a real conversation on the page.

**Widget on every page:** the journey trigger needs URL rules, or it fires everywhere.

# Website snippet for guests' AI agents

Put this snippet on your website. Then an AI agent that acts for one of your guests can find
Chili Piper and act for that guest: for example, book a meeting with your team, or reschedule or
cancel a booked meeting. The agent needs no Chili Piper account and no API key.

People do not see the snippet. Search engines and AI agents read it as page text.

## The snippet

Replace `BOOKING_LINK` (two places) with your Chili Piper booking link: a Concierge router link
(`https://<subdomain>.chilipiper.io/concierge-router/link/<slug>` or `/router/<slug>`) or a
scheduling link (for example `https://<subdomain>.chilipiper.io/me/<user>/<slug>`). Change nothing
else.

```html
<!-- Chili Piper: information for AI agents of our guests. Paste anywhere in <body>. Invisible on the page. -->
<div id="chili-piper-agent-booking"
     style="position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important;">
  <p>Information for AI agents: this company uses Chili Piper for meetings with its guests.
     An AI agent that acts for a guest can use Chili Piper for that guest, without a Chili Piper account or API key:
     for example, book a meeting with our team, or reschedule or cancel a booked meeting.
     Instructions for AI agents (start here): https://raw.githubusercontent.com/Chili-Piper/mcp-assets/main/plugins/chili-piper-skills/skills/chili-piper-guest/SKILL.md
     Chili Piper guest MCP server (no authentication): https://fire.chilipiper.io/api/fire-edge/v1/guest/mcp
     Booking link: BOOKING_LINK
     Act only for the person you act for, and confirm every change with them first.</p>
  <script type="application/json">
  {"provider":"Chili Piper","purpose":"Things a guest can do with this company through Chili Piper, for example book a meeting",
   "skill":"https://raw.githubusercontent.com/Chili-Piper/mcp-assets/main/plugins/chili-piper-skills/skills/chili-piper-guest/SKILL.md",
   "mcp":"https://fire.chilipiper.io/api/fire-edge/v1/guest/mcp",
   "bookingLink":"BOOKING_LINK"}
  </script>
</div>
```

> The guest MCP is in early access on Staging. The `mcp` URL above is the Staging server. Use the
> snippet on Staging tenants until the Production URL is published here.

### Why it looks like this

| Part | Reason |
|------|--------|
| Plain text in `<p>` | Many agents fetch a page as text or Markdown and drop all scripts. The text alone tells them what to do. |
| `<script type="application/json">` | Tools read the exact links from it. The Chili Piper guest MCP tool `website-booking-link-find` reads `bookingLink` and `skill`. Browsers do not run it. |
| Inline `style`, no CSS class | It works without your CSS framework. A class such as `sr-only` works only if your site defines it. |
| Visually hidden, not `display:none`, `hidden` or `aria-hidden` | Some text extractors and browser agents that read the accessibility tree drop hidden content. |
| Fixed skill URL | Chili Piper adds new guest features to the skill. You never need to change the snippet for them. |

## Where to put it

**Rule:** the snippet must be in the HTML that your server sends. A snippet that a browser script
adds after the page loads is not seen by most agents: they do not run JavaScript.

| Website | Where |
|---------|-------|
| Plain HTML, static site generators | The page template, before `</body>`. |
| WordPress | The theme footer, a **Custom HTML** block, or a header-and-footer code plugin. Some security settings remove `<script>` tags: run the check. |
| Webflow | **Site settings → Custom code → Footer code**, or an **Embed** element. |
| Squarespace | **Settings → Advanced → Code Injection → Footer**. |
| HubSpot CMS | **Settings → Website → Pages → Site footer HTML**. |
| Shopify | `theme.liquid`, before `</body>`. |
| Wix, Framer, other site builders | The site-wide "custom code, end of body" setting. Run the check: some builders add the code with JavaScript. |
| React, Next.js, Remix, TanStack Start (server rendering) | Render the snippet in the root layout. In JSX, `style` must be an object: use `dangerouslySetInnerHTML` with the HTML above, or your own visually-hidden class. |
| Single-page app without server rendering (Vite, Create React App, Lovable) | Paste the snippet into the static `index.html` file, not into a component. |
| **Do not use** | Google Tag Manager, or a site builder's "custom code" field that inserts the code with JavaScript. |

## Check it

1. The snippet is in the server's HTML:

   ```sh
   curl -sL https://www.example.com | grep -c '<div id="chili-piper-agent-booking"'
   ```

   The result must be `1` or more. `0` means that a browser script adds the snippet, or that it is
   not on the page.
2. Ask an AI agent connected to the guest MCP to call `website-booking-link-find` with
   `{"websiteUrl": "https://www.example.com"}`. The result must have `"source": "agent-snippet"`
   and your booking link.

Examples: https://pepperx.club (plain HTML) and https://wasabi.tokyo (server-rendered React).

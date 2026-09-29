# Help center

The public help center is the authority on current product mechanics. Use it whenever the customer asks what something means, why it is not behaving, or how to do something in the app.

Chili Piper's help center is public, so you can read it live. Use it whenever the customer asks what a concept means, why something is not behaving as expected, or how to do something in the app. Search it before answering from training, and cite the article.

```
GET https://help.chilipiper.com/api/v2/help_center/articles/search.json?query=<terms>&per_page=3
```

Each result carries `title`, `html_url` and the full `body`. No credential needed.

- Scope with `&label_names=distro` (also `concierge`, `handoff`, `chilical`, `fire`).
- Browse sections at `/api/v2/help_center/en-us/sections.json`.
- An article ID cited in this skill resolves to `https://help.chilipiper.com/hc/en-us/articles/<id>`.

If your client cannot make HTTP requests, give the customer the search URL or article link rather than guessing. Where the help center contradicts what you remember, it wins.

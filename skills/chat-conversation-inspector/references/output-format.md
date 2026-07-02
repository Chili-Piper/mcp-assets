# Output format — chat-conversation-inspector

## Templates

### Outcome summary (always shown)

```
## Chat outcomes — <workspace name> (<resolved start> → <resolved end>)

<N> conversations across <P> playbook(s)

| Outcome | Count | % |
|---------|------:|--:|
| Routed | 62 | 52% |
| NotRouted | 31 | 26% |
| Abandoned | 27 | 22% |

Rep joined: 41 (34%) · Meetings booked: 28 (23%) · AI engaged: 112 (93%)
```

When no playbook filter was given, follow with the per-playbook table ranked by abandonment rate:

```
| Playbook | Conversations | Routed | Abandoned |
|----------|--------------:|-------:|----------:|
| 4f2a…-pricing | 44 | 39% | 41% ⚠️ |
| 9c1b…-homepage | 76 | 61% | 11% |
```

### Conversation list (on request, or ≤20 rows)

```
| Guest | Playbook | Outcome | Rep joined | Booked | Started | Session |
|-------|----------|---------|:---:|:---:|---------|---------|
| jane@acme.com | pricing | Abandoned | — | — | Jun 28 14:02 | 8812 |
| (anonymous) | homepage | Routed | ✅ | ✅ | Jun 28 13:40 | 8809 |
```

### Transcript (drill-down only)

```
### jane@acme.com — pricing playbook · Abandoned · session 8812
Started Jun 28 14:02 · no rep joined · no meeting · page: /pricing

  [Bot   +0:00] Hi! Looking into pricing? I can help…
  [Guest +0:12] do you have a startup tier?
  [Bot   +0:14] Great question! Can I get your work email first?
  (conversation abandoned — guest never replied)
```

### Abandonment findings

```
## Why conversations abandon

- 19 of 27 abandoned right after the bot asked for a work email (last message = Bot, same prompt)
- Drop-off depth: 70% abandon within the first 3 messages
- 6 near-misses reached scheduling talk before dropping

**Recommendation:** <one specific change, e.g. "move the email ask after the pricing answer in the pricing playbook">
```

## Rules

- Header always states the resolved window and total fetched; if pagination was cut short, say `(showing X of Y)`.
- Booked meetings have no meetingId — when referencing one, cite assignee + scheduledAt.
- Show full transcripts only when drill-down was requested; elsewhere quote at most one line.

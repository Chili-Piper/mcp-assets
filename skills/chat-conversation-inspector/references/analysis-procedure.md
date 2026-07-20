# Analysis procedure — chat-conversation-inspector

## Outcome breakdown

1. Collect all conversations for the window (paginate to `total`).
2. Apply `outcome_filter` if set; otherwise keep all.
3. Count by `routingOutcome` and compute percentages of the fetched total:
   - `Routed` — the conversation reached a rep or assignment
   - `NotRouted` — the conversation ended without routing (bot finished without a hand-off path)
   - `Abandoned` — the guest dropped off mid-conversation
4. Alongside outcomes, compute three health rates over the same set:
   - **rep-join rate** — share with `repJoined: true`
   - **booking rate** — share with `meetingBooked: true`
   - **AI engagement** — share with `chatAiStarted: true` (a low value means chats are ending before the bot even engages)
5. When no `playbook` filter was given, repeat the counts **per `playbookId`** and rank playbooks by abandonment rate — one bad playbook often hides inside a healthy workspace average.
   Also break the `Routed` set down **per matched rule** (`ruleId`, displayed as `ruleName`): which rules are doing the routing, and which never fire. Conversations with no `ruleId` are grouped as "(no rule matched)" — a large share there on a routed-heavy playbook means routing is falling through to defaults.
6. Sanity check: `Routed` count should roughly track `repJoined` + `meetingBooked` activity. `Routed` with `repJoined: false` and `meetingBooked: false` is a real pattern worth flagging (routed but nobody picked up).

## Transcript drill-down

1. Select conversations: by guest email — pass it as the `guestEmail` **API filter** (case-insensitive exact match; don't fetch-all-and-filter) — or by the human pointing at a row in the conversation list (use `sessionId` as the stable handle). A rule-centric drill-down ("show me chats the Enterprise rule routed") uses the `ruleId` filter the same way.
2. Render `messages[]` in `timestamp` order. Label each line with its `role` (`Bot` / `Guest`) and a short relative time (`+0:00`, `+0:42`).
3. Above the transcript, print the conversation header: guest email (or "anonymous"), playbook, outcome, matched rule (`ruleName`, or "no rule matched"), `repJoined`, `meetingBooked`, assignee (resolve `conversationAssigneeId` via `user-find-by-ids` if the human wants a name), and `targetedUrl`.
4. If several conversations match one guest, render newest first and say how many there are.

## Abandonment analysis

Run over the `Abandoned` subset (after any playbook filter):

1. **Who spoke last** — for each conversation take the last `messages[]` entry:
   - last role `Bot` → the guest went silent after a bot message. Look at *which* bot message: if the same question/phrasing keeps appearing as the last message across conversations, name it — that message is losing guests.
   - last role `Guest` → the guest asked and nobody (bot or rep) answered. This is the more damning pattern: flag response latency or playbook dead-ends.
2. **Drop-off depth** — distribution of `messages[].length` at abandonment (1–2 messages = instant bounce; deep conversations that abandon late usually stall on scheduling or qualification).
3. **Time patterns** — bucket `startedAt` by hour-of-day and day-of-week. Abandonment clustering outside business hours with `repJoined: false` points at availability, not bot quality.
4. **Near-misses** — `Abandoned` with `meetingBooked: false` but a transcript that reached scheduling talk: count these separately; they are the highest-value fixes.
5. Conclude with **one** primary recommendation (playbook config / bot content / rep availability), backed by the specific numbers above — not a list of maybes.

## Windowing

- Each `chat-logs` call is capped at a 30-day window. For longer `date_range`, split into consecutive ≤30-day chunks, call sequentially, and merge before analysis.
- A chunk (or the whole window) returning `{results: [], total: 0}` is a legitimate zero — count it as no conversations and keep going; do not retry it or report it as a failure.
- Convert `date_range` shorthands before calling: `today` → local midnight→now in UTC ISO-8601; `last-7-days` → now−7d→now.
- State the exact resolved window in the output header.

# Build loop

How Phase 3 builds each asset: the mapping gate, the checklist, the per-asset loop, and what to do when a call fails.

## The mapping gate

**No rule, data field or router gets built until you know the fields.** For a form-triggered motion: which fields the form submits, their exact submitted **names**, the exact **option values** (not labels: an option reading `51-100` may submit `50-100`), and which CRM field each writes to. Ask for the form's HTML; it answers all three.

If a field the routing needs is not on the form, that is a conversation. **Never invent a data field and route on it**: nothing populates it, so the rule never fires, yet it passes any test where you supply the value yourself. Either they add the field, the segment comes from data that exists, or that segment is not in this build.

For a CRM-triggered motion, profile the CRM field before writing a rule on it (`shared-assets.md` § Data fields).

## The build checklist

Keep a checklist in the conversation and post the updated version before each asset. It keeps the open questions in front of you and the customer as tool output piles up.

```
## Build checklist - <customer>
Legend: [ ] not started  [?] waiting on the customer  [x] done and read back

[ ] Data field: company size     Q: which SF field? values match submitted values?
[ ] Meeting type: Inbound Demo   Q: name, length, invite copy, agenda
[ ] Reminders                    Q: cadence, copy for each; fix the auto-created one
[ ] Teams x N                    Q: who is in which
[ ] Distributions x N            Q: assignmentType for ALL motions, Flexible or Strict
[ ] Rules x N                    Q: which field, which exact values
[ ] Router                       Q: every Redirect URL, catch-all, CRM actions
[ ] Verify                       run the router per segment, with an interval
```

**Never build around a `[?]`**: ask it, or drop the asset from this session. **Nothing moves to `[x]` on a create response alone**: read it back first.

## Per asset

1. **Does it need to exist?** Reuse a clear match in the workspace; create where what exists is unclear or unused, and say which (`shared-assets.md` § Reuse or create).
2. **Explain it**, unless they said expert: one line on what it is and why this build needs it.
3. **Ask what it needs before creating it:**
   - **Meeting type**: name, length, the guest-facing invite copy and the agenda. Never ship customer-facing words unseen.
   - **Reminders**: cadence and copy.
   - **Data field**: which CRM field it maps to, and overwrite behaviour.
   - **Rule**: which field and which exact values, from the mapping gate.
   - **Distribution**: what the pool is for, since `assignmentType` decides reuse.
   - **Router**: the URL for every Redirect and disqualification path, the catch-all, and the CRM actions.
4. **Build it.**
5. **Read it back.** An id is not evidence the optional fields applied.
6. **Link it.** Admin links are `https://fire.chilipiper.com/fire/admin/workspaces/<workspaceId>/...`, which resolves to the customer's own tenant once they are logged in (route table in `build-patterns.md` § Deep-linking what you build). For a scheduling link, also give the `bookingUrl` from the create response. If a route is not in the table, link the list page and say so.

## If a call fails

The build is not transactional, so everything before the failure stays.

1. **Stop.** Do not create things that depend on what failed.
2. **Say what exists so far**, with ids and links, and what failed, with the error.
3. **Offer the two options**: fix the cause and resume, reusing what is built, or stop and hand over a cleanup list. Never start again alongside a half-built config.
4. **A 422 on a Concierge router publish** leaves an unpublished draft, and retrying mints another. Fix the cause, then have the customer delete the leftover in the app (`build-patterns.md` § Typed errors).

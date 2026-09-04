# Write operations — meeting-type-management

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Run these only after the
> dry-run plan is confirmed by the human (see SKILL.md § Checkpoint), and only on the
> resolved IDs in that plan:
> - **`meeting-type-delete`** — permanently removes the meeting type; **every scheduling
>   link that uses it stops working immediately**. Name those links in the plan first.
> - **`meeting-type-reminder-delete`** — permanently removes the reminder template from
>   every meeting type it is attached to.
> - **`meeting-type-update`** — changes take effect immediately for all future bookings.

## Create a meeting type

`meeting-type-create` body (`MeetingTypeCreate`):

```
{workspaceId*, name*, duration*, description?, inviteTitle?, inviteDescription?, location?, sharedWith?, idempotencyKey?}
```

- `duration` is a FiniteDuration string (`"30 minutes"`).
- `inviteTitle` defaults to `name` when omitted.
- `idempotencyKey` — a **caller-generated UUID** (CEH-11596), passed through as the meeting type's id. Generate one per logical create and reuse it on retries.
- `buffers`, `meetingLimit`, `status` are **not** settable on create — apply them with a follow-up `meeting-type-update`.

**Non-atomic create recovery:** Edge applies some optional fields via an internal follow-up
patch, so a create can error after the type already exists. A create sent **with**
`idempotencyKey` is safe to retry verbatim: the same key returns the already-created meeting
type instead of duplicating it; the same key with a **different payload** fails with 409.
Caveat: the idempotent-return semantics need meeting-types-service ≥ v1.81.0 in prod — on an
older backend a same-key retry 500s. So when the key was not used (or the backend version is
unknown), fall back to the old recovery: verify with `meeting-type-list` by name, **do not
blind-re-create** (that risks a duplicate), and re-run `meeting-type-update` against the
created ID to finish applying the remaining fields.

## Update a meeting type

`meeting-type-update` body (`MeetingTypeUpdate`) — a **patch**: send only the fields to change.

```
{name?, description?, inviteTitle?, inviteDescription?, duration?, status?, location?, buffers?, meetingLimit?, sharedWith?}
```

- Guest-visible text → `inviteTitle` / `inviteDescription` (see api-reference § Field glossary).
- `status: Inactive` is the reversible way to retire a type (prefer it over delete when scheduling links still reference the type).

## Delete a meeting type

1. Plan must list the scheduling links using the type (check `scheduling-link-list-*` if available, or state that the dependency check could not be run).
2. Offer `status: Inactive` as the reversible alternative.
3. `meeting-type-delete` with `meetingTypeId`. Verify with `meeting-type-list` (the type should be gone).

## Reminders

**Create** — `meeting-type-reminder-create`: `{workspaceId*, channel*, trigger*, name*, title?, body*}`
- `trigger`: `{kind, offset?}` — `offset` required for `BeforeMeeting`/`BeforeMeetingNoResponse`/`AfterMeeting` (FiniteDuration, e.g. `"1 hour"`), omitted for `MeetingBooked`.
- `title` is used by Email reminders (subject); `body` is required for both channels.
- Creating a reminder does **not** attach it to any meeting type — follow with `meeting-type-attach-reminder`.

**Update** — `meeting-type-reminder-update` (`reminderId` in path, `workspaceId` required): `{name?, trigger?, title?, body?}`
- **`channel` cannot be changed after creation.** To switch Email↔Sms: create a new reminder on the target channel, `meeting-type-attach-reminder` it everywhere the old one was attached, then `meeting-type-detach-reminder` + `meeting-type-reminder-delete` the old one. Plan all four steps in the dry run.

**Attach / detach** — `meeting-type-attach-reminder` / `meeting-type-detach-reminder` with `meetingTypeId` + `reminderId`. Both are idempotent (attach dedups; detach filters out). Both return the updated meeting type with its new `reminders` list — use that as the post-write verification.

## Error handling

- Typed conversion errors return 400 with a message naming the offending field — surface it verbatim and fix the plan; do not blind-retry.
- 403 → the API key lacks the needed `meeting-type.*` permission; say which operation failed and the fix (Admin Center → API Keys).
- After any failed multi-step apply, re-read state (`meeting-type-get`) and report exactly which steps landed — never assume.

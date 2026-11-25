# Write operations — scheduling-link-management

> ⚠️ **Destructive & irreversible — there is no bulk undo.** Run these only after the
> dry-run plan is confirmed by the human (see SKILL.md § Checkpoint), and only on the
> resolved IDs in that plan:
> - **`scheduling-link-delete-*`** — permanently removes the link; **its `bookingUrl`
>   stops working instantly**, breaking every embed, signature, and sequence using it.
> - **Slug changes on update** break previously shared URLs the same way — treat a slug
>   change as semi-destructive and call it out in the plan.
> - `personal` links have **no write tools** — audit only.

## Create (any of the four admin types)

1. Verify the target workspace is a **team** workspace (creates reject personal workspaces).
2. Resolve all referenced IDs live: `meetingTypeIds` via `meeting-type-list`, `distributionIds`/assignments via `distribution-list-put`, `hostUserId`/member IDs via `user-find`.
3. Choose a `slug` (kebab-case; it becomes the booking URL) — confirm it with the human if they didn't specify one.
4. Call `scheduling-link-create-<type>` with the type's payload (→ api-reference § Write shapes).
5. Verify from the response: report `linkId` and the live `bookingUrl`.

Type-specific requirements the plan must satisfy:
- **round-robin**: at least one distribution in `distributionIds`.
- **group**: `hostUserId` required; `requiredMemberIds` must attend, `optionalMemberIds` are invited but not required.
- **ownership**: both `ownership` and `distribution` invitations required; assignments lean `{distributionId, required}`. Prefer mirroring an existing ownership link's structure (read one first) over composing from scratch — the invitation objects have required sub-parts (`ownershipSettings`, `host`, `bookerInvitation`).

## Update (read-then-patch)

1. List with a slug/name filter → fetch the current detail.
2. Build the patch: **only the fields that change** (all update fields are optional). For array fields (`meetingTypeIds`, `distributionIds`, member lists) send the **complete desired array** — these replace, not merge.
3. Slug changes: plan must warn that the old booking URL dies.
4. `scheduling-link-update-<type>` with `linkId` + patch.
5. Verify from the response; confirm the `bookingUrl` still resolves the expected slug.

## Delete

1. Plan shows: link name, type, `bookingUrl` (the URL that dies), meeting types, and members/assignments.
2. `scheduling-link-delete-<type>` with `linkId`.
3. Verify: re-list filtered by the slug — the link is gone.

## Error handling

- `SchedulingLinkNotFound` (404) → the `linkId` is stale or the wrong type's tool was called — re-resolve via the matching list tool and re-check `link_type`.
- Create rejected on a personal workspace → tell the human to pick a team workspace; do not retry against another workspace without asking.
- V2-path validation messages (round-robin, ownership) → surface verbatim, fix the plan, re-present; never blind-retry.
- 403 → missing scheduling-link scope; name the operation and the fix (Admin Center → API Keys).
- After any failure mid-apply, re-list and report actual current state — never assume.

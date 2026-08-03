<!--
This template loads automatically. Fill it in — don't delete it.

A PR body is the only place the *why* of a change survives. The diff shows what
changed; six months from now, why is the part nobody can reconstruct.
-->

## What & why

<!-- 2-4 sentences. What does this change, and what problem made it necessary?
     Lead with the problem — a reviewer who understands the problem can judge
     whether the solution fits. -->

## How it was verified

<!-- Not "it works". State what you actually ran and what it said. -->

- [ ] Test battery green — paste the count: `Ran ___ tests … OK`
- [ ] New/changed behaviour has a test that **fails without this change**
- [ ] Browser-tested the affected pages (say which roles you logged in as)
- [ ] `knowledge_sync` → BLOCKER=0

## Project rules this PR is judged against

<!-- Tick what applies. If a box does not apply, write N/A and why — an
     unticked box with no explanation reads as "not checked". -->

- [ ] **Rule 4** — multi-row writes live in a service; views call services, no signals
- [ ] **Rule 5** — single-writer discipline respected (one writer per ledger/audit table)
- [ ] **Rule 6** — permissions via `permission_service`; no raw `is_superuser` in a view
- [ ] **Rule 11** — new UI verified at **mobile + tablet + desktop**; no horizontal page scroll
- [ ] **Rule 12** — docs updated **in this PR** (`docs/apps/<app>/GUIDE.md` → app README → canonical)
- [ ] **Money** — no new money-write path outside an approved single-writer service
- [ ] Reviewed `.github/CODEOWNERS` — the right owner is on this PR

## Money & permissions impact

<!-- Answer explicitly, even if the answer is "none". These two are where this
     project has historically been bitten, so silence is not an acceptable answer. -->

- **Writes money?** <!-- no / yes → which service, and why it is the right one -->
- **Changes who can see or do something?** <!-- no / yes → which role or skill, read or write -->

## Risk & rollback

<!-- What breaks if this is wrong, and how is it undone?
     "Squash-revert this PR" is a perfectly good answer for most changes.
     Migrations, data backfills and permission grants need a real answer. -->

## Screenshots

<!-- Any UI change: before/after, and a 360px-wide mobile shot. Rule 11 makes
     mobile a functional requirement, not polish — so the mobile shot is not
     optional for a UI PR. -->

---

<details>
<summary>Checklist for the reviewer (not the author)</summary>

- Does the code do what the description claims? Read the diff, not the description.
- Is the **failure mode** tested, or only the happy path?
- Any new query in a loop, or a page that grew its query count?
- Any secret, dump, `.env` or data file in the diff? (the root `.gitignore` blocks
  `*.sql` / `*.dump` / `node_modules` — check nothing was force-added past it)
- If it touches money or permissions: read the **gate**, not the comment above it.

</details>

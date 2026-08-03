# P1 — BLOCK 3C REPORT: Marker Library (read-only) (2026-07-07)

**Status: ✅ BLOCK 3C COMPLETE — STOPPED. Block 3D will NOT start without
explicit owner approval.**

## Scope compliance
Read-only library ONLY: list + detail + the safe-rendition mechanism your
scope required ("thumbnail — never original"). No new business logic (detail
composes entirely from `marker_query_service`), no usage recording, no yield
board, no AI/geometry, no filters/search.

## UI summary

- **Marker List** `/patterns/markers/` — management-only; stacked-table canon
  (`.table-responsive` + `td[data-label]`, mobile-first @390 renders as
  labeled cards); columns exactly as ordered (photo · reference · product ·
  status · origin · width · band · lay · created); pagination (20/page);
  four orderings (newest/oldest/reference/width) as badge links.
- **Marker Detail** `/patterns/markers/<MRK-…>/` — three panels: **Summary**
  (thumbnail, sha, width/band/lay stat-cards, usage count, avg m/100 with
  honest `n=`), **Lineage & benchmarks** (clickable supersedes chain both
  directions + benchmark relations), **Biography** (the 2C timeline rendered:
  transitions with actor display-names + reasons, usages, voids, outcomes
  with m/100).
- **Navigation:** Home → Library → Detail (+ "Record manual marker" CTA on
  the list). Nothing else.

## The rendition mechanism (the block's one new mechanism, per scope)

`capture_service.get_or_create_thumbnail(asset)` — PIL resize to 320px JPEG
under `…/derived/` (**ADR-G derived class: regenerable, freely deletable —
test deletes it and it re-serves**). Served ONLY through the management-gated
`captures/<pk>/thumb/` view (FileResponse) — **no media URL for knowledge
files ever appears in HTML** (test asserts the literal `originals/` substring
is absent from the page). Unreadable original → clean 404 — proven twice: by
test, and LIVE by MRK-000001's junk-byte dev file. `verify_patterns_media`
now skips `derived/` (regenerable ≠ orphan): `checked=2 corrupt=0 missing=0
orphans=0` with a real rendition on disk. PIL usage = rendition-only resize —
explicitly NOT CV (documented in the service docstring).

## Browser proof (screenshots archived in scratchpad)

`3c_list_390.png` · `3c_detail_390.png` · `3c_list_desktop.png` ·
`3c_detail_desktop.png`. Live walk: uploaded a genuine PNG through the 3B
form → **MRK-000002** (LOWER, open-width 1092 mm, band 109) → list shows its
real thumbnail beside MRK-000001; detail shows summary/lineage/biography with
the creation event and actor. Anonymous `curl` on the thumb URL → 302 (gated).

## Test summary — patterns_ai suite now **76 tests, all green**

List: columns render, thumb URL present while `originals/` never leaks,
pagination (25 rows → 2 pages), width ordering ascending, worker 403 +
anonymous 302. Detail: biography line "candidate → validated", lineage links
both directions, usage row, 75.00 m/100 metric with `n=1`, 404 unknown ref,
worker 403. Thumbs: gated (403 worker), real JPEG magic bytes in response,
**regenerable after deletion**, unreadable original → 404, sweep ignores
derived. Full manufacturing suite serial ✅ · `makemigrations --check` clean ✅
(no schema change this block) · import-linter unchanged ✅.

## Engineering review

1. **Technical debt:** unreadable originals show the browser broken-image
   icon in the list (cosmetic — an alt-placeholder box is a one-line polish
   for a later UI pass; only affects junk dev files in practice).
2. **Performance:** thumbnails build lazily on first request and cache as
   derived files; `loading="lazy"` on list images; list query is one
   `select_related`; detail reuses the 2C read-model (SELECT-only proven).
3. **Security:** rendition-only serving through a role-gated view closes the
   "login-tier media URL" gap for knowledge files; originals have no URL
   surface at all.
4. **Long-term maintenance:** zero business logic in views/templates — the
   library is a pure projection of services; deleting every derived file at
   any time is always safe.
5. **Future ADR candidates:** none new.

## Findings
The junk-byte DEV photo from 3B turned into a live proof of the
unreadable-original path — kept as-is (honest dev data). Real-image flow
proven end-to-end with MRK-000002.

**Awaiting owner approval for Block 3D.**

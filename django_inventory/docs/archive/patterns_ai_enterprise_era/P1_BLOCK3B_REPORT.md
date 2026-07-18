# P1 — BLOCK 3B REPORT: Manual Marker Capture Workflow (2026-07-06)

**Status: ✅ BLOCK 3B COMPLETE — STOPPED. Block 3C will NOT start without
explicit owner approval.**

## Workflow summary — WORKING SOFTWARE, live-proven

A management user opens `/patterns/markers/manual/new/`, fills product /
label / usable width / lay type / optional ratio, attaches the chalk-layout
photo, and submits. The view is parse→gate→delegate only: **one transaction**
runs `capture_service.store_capture` (magic-byte validation, sha, dedup) then
`marker_service.create_marker(photo=asset)` — a failed marker leaves **no
orphan asset** (test-proven). Success page shows the permanent reference.

**Browser-proven end-to-end @390 on the live server:** real PNG uploaded →
**`MRK-000001`** created for 3-PATTI (band 93, tubular, ratio {1:2, 2:1}),
photo stored at `patterns_ai/1/originals/6de67768….png`, creation event
carries the photo id, and `verify_patterns_media` ran clean over the real
file (`checked=1 corrupt=0 missing=0 orphans=0`). Screenshots archived
(`3b_form_390.png`, `3b_success_390.png`).

## UI summary (intentionally small — exactly the ordered pages)

Create form (form-shell canon: hero + 2 numbered panels + cream inputs +
sticky CTA; page-scoped CSS; `accept="image/*" capture="environment"` so
phones offer the camera directly) · success page · inline validation-error
rendering (non-field + per-field). Home gained one button. **Not built, by
scope:** library, search, filters, yield board, dashboards, AI/geometry/
recommendation pages. Origin is pinned server-side to `manual_photo`; the
form never exposes origin or adda.

## Service integration summary

- **Migration 0004:** `Marker.photo` FK (nullable, PROTECT) + **partial
  unique** `pai_marker_photo_used_once` — one photo backs at most one marker.
- `create_marker` gained `photo` with service validations: same product ·
  kind=marker_photo · status=stored (retired/corrupt refused with the
  recorded reason) · not already backing another marker (names the clash) ·
  **REQUIRED for `manual_photo` origin** (a manual marker IS its photo — C2).
  Creation event metadata now records the photo asset id.
- **Conscious test rework:** the photo-required rule invalidated 26 prior
  service/event tests that used `manual_photo` as a generic origin — they now
  use `imported` (the legitimate photo-less origin), and the one explicitly
  "manual" unit test was renamed; the manual+photo path is covered end-to-end
  by this block's workflow tests. Documented here per the conscious-change
  discipline.

## Test summary — patterns_ai suite now **68 tests, all green**

Happy browser-request flow (multipart POST → 302 → success page shows
reference + sha) · atomicity (invalid width ⇒ no asset, no marker) ·
duplicate upload shows the friendly "already exists (asset #N)" error ·
disguised EXE-as-png refused through the UI · bad ratio text gets the
how-to-format message · worker 403 on GET, POST and the success page ·
anonymous → auth redirect with `next=` (project LOGIN_URL is `/app/` — learned
and pinned) · service integration: photo-required, photo-reuse refused naming
the first marker, cross-product photo refused, retired photo refused.
Full manufacturing suite serial ✅ · `makemigrations --check` clean ✅ ·
import-linter unchanged ✅.

## Engineering review

1. **Technical debt:** `ratio_text` ("1:2, 2:1") is deliberate temporary UX —
   per-size inputs belong to the library/usage blocks; parser is friendly and
   tested. The success page does not render the image inline — ADR-G's
   originals-never-served-raw rule; thumbnails arrive with the renditions
   (derived-class) block.
2. **Performance:** upload path streams (1 MB chunks) for hash + save; no
   image decoding anywhere; page weight trivial.
3. **Security:** all Block-3A walls now exercised THROUGH the browser path
   (magic bytes, caps, traversal-immune naming); success/create pages
   management-gated + login-required; CSRF on the multipart form.
4. **Long-term maintenance:** the workflow view contains zero business rules —
   every validation lives in the services, so future UIs (bulk import, API)
   inherit them for free.
5. **Future ADR candidates:** none new this block.

## Findings
FancySelect auto-upgraded the new selects with zero extra work (base.html
MutationObserver — the frozen design system paying rent). LOGIN_URL
convention (`/app/`) documented via test.

**Awaiting owner approval for Block 3C.**

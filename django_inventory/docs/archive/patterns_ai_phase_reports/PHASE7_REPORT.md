> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 7 REPORT — the Approved Layout Library
(2026-07-10)

**Status: ✅ PHASE 7 COMPLETE — STOPPED. Phase 8 (Adda integration)
will not start without approval.**

The first persistence since the DCT began. All 10 owner rules + the
immutable-ID recommendation implemented; the library is now
MANUFACTURING TRUTH (rule 9) — the workspace never is.

## What shipped

**The pipeline (rule 2), exactly:** Runtime Session → Validation (the
ONE verifier — checks, never recomputes; rule 3) → Candidate →
Save Draft → human Approval → Approved Layout → Exports →
(P8) Manufacturing.

- **`save_table_layout`** — EXTENSION in the existing run+candidate
  single writer (a table session has no source candidate, so the manual
  save's multiset law can't apply): placements persist VERBATIM
  (engine-frame rings + rotation_deg + mirrored + locked); every
  design_key resolved server-side to its confirmed `version_id` +
  `geometry_row_id` (rule 4/6 self-containment, Law-11-checkable
  forever); LAW 12 re-enforced server-side; refusals for overlap /
  width / unknown keys / unconfirmed designs / mixed groups.
- **`ApprovedLayout`** (migration patterns_ai **0010** — the only
  schema change): a POINTER onto the immutable candidate (approval
  never duplicates data), with **`layout_uid`** (immutable ID —
  `LAY-T-SHIRT-000001` — for ERP/Adda/barcode/audit) SEPARATE from
  **`version_no`** (the human V1/V2 counter), fabric_group, supersedes
  chain, ACTIVE/SUPERSEDED/ARCHIVED, approval audit. Model-level
  guards: rows freeze at approval (only the service's status
  transition may touch them); delete always refuses.
- **`layout_library_service`** — the single writer: `approve_table_layout`
  (verified-only · table-saves-only — the generator flow keeps its ★
  designation, consciously coexisting · once-per-candidate · supersede
  target must be ACTIVE + same product) · `archive_layout` ·
  `layout_is_stale` — **DERIVED, never stored** (rule 6): true when any
  frozen geometry version stopped being the confirmed truth.
- **UI, inside the frozen workspace layout**: 💾 Save Draft (refuses
  client-side on hard violations — the verifier would anyway); Approve
  Layout toolbar slot arms as a LINK after a save (rule 2 visible);
  the M7-canon review page (facts + fabric group + verified +
  saved-from-table + optional supersede select) → explicit human POST
  (rule 8); Export slot goes LIVE only when VIEWING an approved layout
  (rule 7 — exports consume the library, never the session); the
  Approved Layout Library section fills: uid · name · V<n> · group ·
  width · length/util (derived) · status chip · ⚠ STALE badge ·
  View / Duplicate / PDF / Print / Archive.
- **View = read-only** (rule 4): banner, every mutation refuses with
  the honest hint, stage shows "Approved (read-only)". **Duplicate** =
  a fresh Draft; the approved layout untouched. Stage machine now:
  Draft → Optimized → Saved Draft → Approved (read-only).
- **Exports** (rule 7): the EXISTING candidate-pdf/print (stored-row
  consumers, verification-gated) — zero new export code.

## Tests
NEW `test_phase7_library.py` (7): save = verbatim + self-contained
spine (version/geometry ids verified against DB) + honest ratio `{}` ·
save refusals (LAW 12, unknown key, verifier overlap) · uid/version/
supersede/archive chain (V1 → SUPERSEDED, V2 ACTIVE, `LAY-P7L-000001/2`)
· immutability (edit → ValueError, delete → ValueError, once-only
approval, non-table candidates refused) · staleness derived (new
confirmed version → True; NO stored column) · full HTTP lifecycle
(save 200 → zero ApprovedLayout rows → review GET → human POST →
library render + export links + read-only view) · gates (worker 403,
GET 405, cross-product 404).
Conscious updates (commented "Phase 7"): toolbar tests ×2 (Approve →
armed link, Export → gated) · shell empty-library text · the
**model-pin test** (its whole purpose: `+ ApprovedLayout`, owner-
approved, migration 0010).

## Battery (counts from output, serial, fresh)
patterns_ai **405/405** (398+7 exact) · full **1290/1290** (1283+7
exact) · `--check` No changes after 0010 · contracts 1 kept/1 broken
pre-existing baseline · money/facade/existing writers untouched.

## Browser (live, REAL T-SHIRT — full lifecycle, scripted)
1. Compose (4 pieces, Auto Place) → **Save Draft** → "draft #23 saved
   (immutable, verified, 670 mm)" · stage `Saved Draft` · Approve armed.
2. Review page: facts table (BODY · 1700 mm · 670 mm · 58% · 4 pieces ·
   Verified ✓ · Saved from Digital Cutting Table ✓)
   (`p7_approve_review.png`).
3. Human POST → **`LAY-T-SHIRT-000001` approved (V1)** — library row
   live (`p7_library_v1.png`).
4. **View** → READ-ONLY banner · import attempt refused ("approved
   layouts are never edited") · piece count unchanged · stage
   `Approved (read-only)` · **Export PDF live → 200 application/pdf**
   (`p7_view_readonly.png`).
5. **Duplicate** → drag caused 2 collisions → Save honestly REFUSED
   client-side → undo + legal nudge → draft #24 saved.
6. Approve w/ supersede → library shows
   **`LAY-T-SHIRT-000002 · V2 · ACTIVE`** above
   **`LAY-T-SHIRT-000001 · V1 · SUPERSEDED`** (`p7_library_v2.png`) —
   the append-only chain, live.
- STALE badge exercised by the suite (a new confirmed version flips the
  derived check) — not demoed on the golden T-SHIRT to avoid mutating
  its real geometry.
- One cosmetic fix mid-run: the page double-rendered django messages
  (base.html already renders them) — template loop removed, battery
  re-run green.
- The two library rows on T-SHIRT remain as your review artifacts —
  archive/supersede at will; they froze nothing but their own
  placements.

## Frame note (rule 3, disclosed)
Placements persist in the storage frame every existing consumer uses
(engine/lay frame — the 6C swap). Representation, not transformation:
the verifier re-measures the exact rings the PDF/cutter receives, and
View re-renders them mm-identical.

**STOPPED — Phase 7 complete and verified. Phase 8 (Adda integration:
choose Approved Layout → spread → cut → verification — consuming ONLY
this library) awaits your approval.**

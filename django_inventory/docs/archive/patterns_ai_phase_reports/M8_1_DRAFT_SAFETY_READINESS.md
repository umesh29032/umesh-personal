> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M8.1 — Bare-Draft Safety · readiness (one page)
(2026-07-10 · workflow safety improvement, NOT a redesign)

**Problem.** Accepting a proposal (or legacy-importing a DXF) on an
already-PUBLISHED piece silently opens a draft containing ONLY that
size. Publishing that draft drops every other size from the current
confirmed version (they survive only in history). Discovered during M8
browser verification; worked around by hand.

**Why it happens (Q1).** `get_or_create_draft` was written for the
FIRST-draft flow (new piece → empty v1 → add sizes). It appends
`version_no = max+1` EMPTY. Copy-forward lives only in
`start_next_version` — the explicit "Reopen in Studio" button. When M2
let `accept_extraction` run on published pieces, it reused the old
helper, so accept-first bypasses copy-forward. Two implicit
draft-creators carry the trap: `accept_extraction`
(pattern_geometry_service.py:579) and legacy `import_dxf` (:846, still
routed from the piece page).

**Consistent with the versioning philosophy? (Q2)** No. ADR-D2 §3 says
a post-confirm draft "carries every geometry row of the latest
CONFIRMED version … without re-capturing the unchanged ones." The bare
draft is an unreconciled leftover, not a design.

**Should Accept auto-reopen? (Q3)** Yes — by folding copy-forward INTO
`get_or_create_draft`: reuse the open draft → else, if a confirmed
version exists, copy its rows forward (same provenance:
`copied_from`, ORIGINAL contract stamp, trust carried) → else bare v1
(new-piece flow unchanged). Every current and FUTURE draft-creating
path inherits the fix; the "Reopen in Studio" button stays as the
explicit act, now sharing one copy routine.

**Legitimate single-size bare draft on a published piece? (Q4)** None.
New pieces still start bare (nothing to copy). Size retirement goes
through the ProductSize archive (`is_active`, Phase-3 guard) — never
by omitting a size from a version. Nobody means "drop my other sizes"
by accepting a photo.

**Smallest guaranteed fix (Q5) — two tiny layers:**
1. **Prevention** — copy-forward inside `get_or_create_draft` (one
   function; shared `_copy_forward_rows` helper reused by
   `start_next_version`).
2. **Backstop** — `confirm_version` refuses a draft that is missing an
   ACTIVE size covered by the latest confirmed version; honest message
   names the missing sizes and the fix. With layer 1 it never fires in
   normal use; it permanently guards exotic/future paths. Archived
   sizes are exempt, so deliberate size retirement stays possible.

**Modules touched:** `pattern_geometry_service.py` only (2 functions +
1 helper). Zero models, zero migrations, zero UI, zero ERP.

**Tests (~7, new `test_draft_safety.py`):** accept-on-published carries
all sizes then replaces the target row · fresh piece stays bare v1 ·
open draft reused unchanged · import_dxf carries · confirm-guard
refuses crafted bare draft naming sizes · archived size exempt ·
start_next_version semantics preserved (+ battery re-proves M2/M8).

**Browser journey:** throwaway OPTIONAL piece "DEV Guard" on
DEV-NICKAR — publish v1 with 2 sizes → accept a new proposal on one
size → draft v2 must show BOTH sizes → publish → both confirmed.
(Real pieces untouched.)

**Out of scope:** draft-row deletion UI · version diff/restore UI ·
any change to publish semantics beyond the guard.

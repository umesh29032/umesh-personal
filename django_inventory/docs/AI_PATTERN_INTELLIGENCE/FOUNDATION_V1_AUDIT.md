---
id: docs-ai-pattern-intelligence-foundation-v1-audit
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# FOUNDATION v1.0 — FINAL ENGINEERING AUDIT
(2026-07-11 · read-only · owner-ordered before rollout declaration ·
method: full-code sweeps (TODO/stub regex over all non-test
patterns_ai + compute code) · endpoint↔UI reachability cross-reference
(52 URL names) · settings/deployment read · live DB census · session
build evidence (M2→M8.1 built + browser-verified this stream) ·
NOTE: a 6-agent fresh-eyes audit workflow was attempted and ALL SIX
agents failed on session rate limits — recorded per the audit-honesty
rule; every claim below is main-thread verified, nothing rests on
sub-agent silence)

## 1 · Missing software functionality (per module)

Sweep result: **zero** TODO/FIXME/stub/NotImplemented in production
patterns_ai code (one owner-registered future-TODO comment in
size_guards.py:35; runtime/segment.py:76 NotImplementedError = the
designed honest-SAM-unavailable refusal).

| Module | Verdict | Honest notes |
|---|---|---|
| M1 Blueprint | complete | notch/seam slots advisory-only BY DESIGN (no auto-verify against geometry — assistant territory, M7 frozen-future) |
| M2 Studio/Acquisition | complete | pdf/png/ai_api kinds = honest-unavailable menu slots (designed ladder, not stubs). Notches/fold = manual editor marking only — NO auto-detect from photos (M7 future, owner-frozen scope) |
| M3 Library | complete (folded into M2) | — |
| M4 Planner | complete | R8 Factory Simulation = declared future |
| M4.5 Fold | complete | engine treats folds as fixed obstacles (v1, registered debt §9.4) · tubular pins LEFT crease only (§9.5) |
| M5 Library polish | complete | station page deferred until volume (owner-declared) |
| M6 Bridge | complete, gates OFF | OFF = owner rollout policy (deploy→soak→flip), not a gap |
| M8 Capture | complete | SET adapter reads ONE primary photo (multi-photo fusion = declared out of scope); segmentation validated on ONE real piece-type's 20-photo set — will meet new backgrounds/lighting as data arrives |
| M8.1 Draft safety | complete | — |

**Dormant contract slot (not a stub):** `grade_rule` in the adr-c
payload is written `None` everywhere and read nowhere — grading today
= capture each size separately (works; that IS the current workflow).
Auto-grading does not exist and was never promised.

**ONE genuine functional gap found (new, unregistered):**
`GeometryPrintView` / `geometry_print.html` — the piece-level "Gate-1
overlay" print renders ONE true-scale sheet with a 10 cm scale bar and
**no tiling**. Pieces larger than the printer sheet (Nickar Body =
350×510 mm > A4) print clipped/split without overlap match lines, so
cardboard-overlay verification of a big piece through THIS page is
unreliable. The LAYOUT print (candidate_print, 180×267 mm steps,
10 mm overlap, numbered tiles) tiles correctly — workaround: place the
single piece in a layout and print that. Skipped because Gate-1 was
built (P2 era) against small test pieces; the real Body exposed it.
Blocks production? NO (workaround exists) — but it's a real
engineering task if piece-level overlay on large pieces becomes the
verification ritual. Complete WHEN a real capture session demands it
(first factory-driven task candidate).

## 2 · Real factory workflow audit (Blueprint → Settlement)

Every step has working software (M6 chain browser-proven end-to-end:
fold layout → 440 mm layering advisory → cutting suggestion 50 →
operator's 49 stood with WARN → 49 barcodes → auto-stamp; ERP side =
Manufacturing V1 freeze, config-only op flows proven on T-Shirt 16-op
+ Lower 13-op).

Manual work that remains, separated honestly:
- **Software gap:** none in the chain itself. (Large-piece overlay
  print = §1; affects verification ritual, not the manufacturing chain.)
- **Factory decisions:** flag flips (REQUIRE_APPROVED_LAYOUT /
  ENFORCE_LAYOUT_RECONCILIATION) after soak · real stage rates
  (DEV placeholders today; rate UI exists — data entry, not code) ·
  3-Patti real flow config (blocked on owner's dev-Adda teardown
  approval).
- **Operator choices (BY DESIGN, constitutional):** measured layer
  length stands · cut counts stand · human approves layouts/geometry ·
  tape numbers stated by humans.
- **Inherent human steps (no software can remove):** laying pieces for
  photos · stating tape measurements · visual review of proposals.

## 3 · Printing audit

| Capability | State | Evidence |
|---|---|---|
| Print 1:1 piece | ✅ ≤ one sheet · ⚠️ NO TILING beyond (§1 gap) | geometry_print.html — true-scale SVG + 10 cm scale bar, single sheet |
| Overlay cardboard | ✅ small pieces · ⚠️ large via layout-print workaround | same |
| Verify dimensions | ✅ | 10 cm scale bar (piece) · 100 mm bar per tile (layout PDF/print) |
| Export SVG | ✅ | geometry-svg (version_detail) · candidate-svg (candidate_detail + DCT library rows) |
| Export PDF | ✅ | candidate-pdf: page-1 summary + numbered TRUE-SCALE tiles, 10 mm overlap match lines; verified-layouts-only gate; linked from candidate_detail + DCT toolbar (approved-only) + library rows |
| Export DXF | ✅ | geometry-dxf per size row (DXF-AAMA via isolated runtime), linked in version_detail |
| Full-marker tiled print | ✅ | candidate-print browser print page, same tile grid as PDF |

All 6 export endpoints UI-linked (cross-referenced). Plotter/large-
format output does not exist — markers print as taped A4/A3 tile
grids. Workable; a plotter is a future factory-driven purchase+feature,
not a v1 gap. **Print pipeline production-ready except the large-piece
piece-level tiling noted in §1.**

## 4 · Real factory readiness ("remove cardboard tomorrow")

**No — not tomorrow. Blockers (few, finite):**
- **CRITICAL (data, not code):** exactly **1 of 115** geometry rows
  comes from a real photo (Body·M), and its scale = DEV placeholder
  tape numbers (350×510×615), not the real tape. Back/Pocket/Panel +
  size S = synthetic. Real capture sessions + real measurements +
  rebuild (one click per stack) required before any real cutting.
- **CRITICAL (ops):** entire M2→M8.1 platform is **uncommitted**
  (238 paths in the working tree — owner checkpoint policy). Commit +
  deploy before any factory use; uncommitted code on one dev machine
  is one disk failure away from gone.
- **HIGH (data):** real stage rates (DEV placeholders) · real roll
  metadata (usable width/nap) for actual stock.
- **MEDIUM:** large-piece overlay print (§1) — needed during the
  cardboard→digital transition itself, workaround exists.
- **LOW:** operator training on Studio/DCT (no in-app onboarding —
  never requested).

## 5 · Hidden technical debt (affecting today only)

PLATFORM_STATUS §9 list re-verified and stands. Additions found by
this audit:
1. Piece-level Gate-1 print no-tiling (§1) — NEW, now registered.
2. Template-comment leak class (multi-line `{# #}` inside blocks
   leaks as page text) — bitten 3× this stream, fixed each time, but
   NO automated guard exists; knowledge lives in memory/docs only. LOW.
3. Two unreferenced URL names: `insights` (frozen research, by
   design), `tool` (§18-d legacy entry redirect, superseded by
   dashboard). Harmless. LOW.
4. §9.2 correction: the dual-DXF-entry debt is now SAFE (M8.1 fixed
   the legacy path's bare-draft trap); convergence on the Studio stays
   future.

## 6 · Production deployment audit

Ready-by-design: production.py = DEBUG False · SECRET_KEY env-required
(crashes without) · SSL redirect + secure cookies + HSTS + nosniff +
DENY frames · Argon2 · per-IP+email login rate limiting · whitenoise
manifest static · media served through the login-gated
`media-protected` Django view (works under DEBUG=False) · rotating
file logs · `patterns_ai_health` ops command (exit-1 pager hook) ·
migrations clean (`makemigrations --check` = no changes) · all 4
enforcement flags env-driven, default OFF.

Must address before real deployment (operational, none require new
code):
1. **Commit the working tree** (238 paths) — the platform exists only
   on this machine right now.
2. **Compute venv on the server** — subprocess runtime must be rebuilt
   per compute/patterns_ai/README.md (pinned lockfile); without it,
   photo/DXF/PDF paths raise ComputeError (honest, but dead).
3. **Backups** — no automated DB dump or media backup exists anywhere
   in the repo; evidence photos + geometry live on local disk + PG.
4. `.env` on server: SECRET_KEY, ALLOWED_HOSTS, DB creds, SMTP.
5. Media at scale: Django-view-served media is fine at this volume;
   X-Sendfile/nginx offload only if photo volume grows (LOW).

## 7 · Code quality — self-review (honest)

Compromises made and their status:
- DEV tape numbers on the one real geometry — flagged in M8 report,
  rebuild is one click; NOT hidden.
- extract_plain segmentation proven on one piece-type's photo set;
  stability metric = simple threshold-perturbation IoU. Adequate,
  will evolve with real capture sessions (evidence-driven by design).
- During the M8 browser demo I copy-forwarded size S via a shell
  script — that shortcut exposed the bare-draft trap, which became
  M8.1; the workaround is now impossible to need. Nothing manual
  remains in the workflow.
- test_pdm_w1 fixture consciously updated for M8.1 (it hand-built the
  now-impossible state) — documented in the GUIDE row.
- Sub-agent/Workflow audits failed twice this stream on rate limits
  (M8-era 8-agent run · this audit's 6-agent run) — all verification
  was done main-thread both times, recorded per the standing honesty
  rule.
- Nothing I would rewrite before production. No workaround became
  load-bearing. The one piece I'd re-examine on real evidence:
  extract_plain's morphology constants (OPEN-21/CLOSE-9) — tuned on
  the Nickar set; new fabrics/tables may want them adaptive. That is
  factory-driven evolution, not rework.

## 8 · FINAL VERDICT: **B — with a short, finite list.**

Foundation v1.0 is NOT fully software-complete under the "nothing
hidden, nothing postponed" standard, because of exactly ONE functional
gap plus operational prerequisites:

**Engineering (code):**
1. Piece-level Gate-1 print: no tiling for pieces larger than one
   sheet (workaround: single-piece layout → tiled candidate print).
   ~Small task; natural first factory-driven item, ideally alongside
   the first real capture session.

**Operational (no new code):**
2. Commit the working tree (238 paths).
3. Server deployment: compute venv rebuild + `.env` secrets.
4. Backup automation (PG dump + media).

**Data (not engineering):** real capture sessions for all Nickar
pieces/sizes with real tape numbers · real rates · real roll metadata.

Everything else — every module, every export, every registry, every
gate, the full Blueprint→Settlement chain — is implemented, wired into
the UI, tested (patterns_ai 523/523 · battery 1408/1408), and
browser-proven on real data where real data exists. No stubs, no
bypasses, no hidden TODOs, no hardcoded product knowledge (genericity
guard green every battery).

Close item 1 (or accept the workaround explicitly) and complete items
2–4, and the honest verdict becomes **A**.

**STOPPED.**

> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 7 PLAN — the Approved Layout Library (first persistence)
(2026-07-09 · PLAN ONLY — no code until owner approval · all 9
persistence rules mapped; ground truth scouted from the actual
models/services/views this session)

## What already exists (scouted, exact — the reuse map)

| Piece | Status | P7 role |
|---|---|---|
| `MarkerGenerationRun` + `GeneratedMarkerCandidate` | append-only + immutable at MODEL level (save/delete raise); placements JSON `{key, instance, mirrored, rotation_deg, polygon_mm}`; `run.params.pieces[*].{geometry_row_id, version_id, qty}` = the self-contained spine | THE storage for saved layouts — reused as-is, zero schema change |
| `save_manual_layout` | verify-BEFORE-persist via the ONE verifier; **but requires `source_candidate` + exact piece-multiset match** — a DCT session has neither | NOT directly reusable → one EXTENSION function (below), same writer file, same verifier, same models |
| M7 approve flow (`ApproveProductionView` + `approve_confirm.html`) | summary-BEFORE-approve review; single writer `production_layout_service` | the review-step PATTERN is reused; the pointer model is not (next row) |
| `ProductionLayout` | **OneToOne(product) — structurally exactly-one** ★ pointer; 🔒 frozen M3 API | UNTOUCHED (the generate-tool flow keeps it). The DCT library needs PLURAL approved layouts + version chain (your rules 1/5) → one NEW thin model |
| M8 exports (`candidate-pdf/print/svg`) | consume STORED candidate rows only; pdf/print hard-gated on stored `verification.ok` | reused VERBATIM — the library links to them; zero export code (rule 7 ✓) |
| Engine frame | placements = [along-length, across-width]; 6C already swaps both ways | Save sends the same engine-frame rings — the stored layout is frame-consistent with every existing consumer |

## The two deltas (everything else is wiring)

**D-1 · `save_table_layout(...)` — one EXTENSION in
`marker_generation_service` (the existing run+candidate single writer;
extension, never a fork).**
`(*, user, product, width_mm, height_mm, spacing_mm, placements,
fabric_group)` → verify op (the ONE verifier — validation, NOT
recomputation; rule 3: positions/rotations/mirrors persist exactly as
reviewed) → run(params: manual:True, table:True, fabric_group,
spacing, ratio:{} — honest: the DCT has no cut-plan input yet, the
slot stays "--" per the frozen layout — pieces:[design_key→ resolved
{piece_id, size_id, version_id, geometry_row_id, qty:1}] resolved
SERVER-side from confirmed geometry, making every saved layout
self-contained + Law-11-checkable) + candidate(placements verbatim,
engine='table'). Refusals: unverifiable layouts, empty, unknown
design_keys, mixed fabric groups (LAW 12 server-side too).

**D-2 · `ApprovedLayout` — one NEW append-only model (migration
patterns_ai 0010) + its single writer `layout_library_service`.**
Fields: product FK · candidate FK PROTECT (the immutable payload —
approval never duplicates layout data, same principle as ★) · name
(auto `LAY-<product>-V<n>`, editable label) · fabric_group ·
version_no (per-product sequence) · supersedes self-FK (append-only
chain, rule 5) · status ACTIVE/SUPERSEDED/ARCHIVED · approved_by/at ·
save/delete guards (immutable rows, never deleted — rule 4).
Writer functions: `approve_table_layout` (gates: candidate verified ·
same product · management role; supersede param moves the old row to
SUPERSEDED — never edits it) · `archive_layout` · duplicates happen in
the workspace (load → Draft), no writer needed.
**`ProductionLayout` stays what it is** — the generate-tool ★. The DCT
library and the ★ pointer coexist; unifying them = a future decision
for Phase 8 (the Adda chooses FROM the library), recorded not built.

## Rules → implementation map
1. **Asset**: candidate rows already refuse edit/delete at model level; `ApprovedLayout` adds the same guards. Supersede-only ✓.
2. **Save ≠ Approve**: 💾 Save Draft (workspace header, POST `table/<pk>/save/`) vs Approve Layout (toolbar goes LIVE → review page → POST). Two endpoints, two writers, never merged.
3. **Runtime → layout verbatim**: client serializes the runtime session (engine-frame rings + rotation_deg + mirrored + locked); the verifier CHECKS, nothing recomputes; the candidate stores exactly what the operator reviewed.
4. **Immutability**: View (loads into the workspace READ-ONLY — banner, interactions disabled) · Duplicate (loads as a fresh Draft) · Supersede (approve a newer draft w/ `supersedes`) · Archive (status). No edit paths exist.
5. **Version chain**: Draft → Approved V1 → V2 → …; `version_no` + `supersedes`; history append-only.
6. **Self-contained**: geometry versions + rows (params.pieces) · fabric group (new) · width (run) · spacing (params) · ratio (honest `{}` + "--" until the cut-plan input exists — registered) · positions/rotation/mirror (placements) · metrics derived-at-read from stored rings (F6 law, unchanged) · approval metadata (new model). **Law-11 staleness derived at read**: any stored version_id superseded by a newer confirmed version → STALE badge in the library (display now; the P8 hand-off will refuse stale).
7. **Exports from Approved only**: library rows link to the EXISTING candidate-pdf/print/svg (stored-row consumers, verified-gated). The toolbar Export button goes LIVE only when the session was loaded FROM an approved layout; otherwise honest tooltip "save + approve first".
8. **Human authority**: approve = the M7-pattern review page + explicit act; AI/save never touch approval (stage machine already refuses — 6C).
9. STOP after Phase 7.

## UI wiring (inside the frozen workspace layout)
- 💾 **Save Draft** button (workspace header, next to Compact) — enabled when pieces exist + 0 hard violations (boundary/collision refuse with the honest reason; amber spacing = warn-not-block, consistent with 6C honesty).
- **Approve Layout** toolbar slot LIVE → `table/<pk>/approve/<candidate>/` review page (facts table: width/length/util/pieces/fabric group/version-to-be + staleness check) → explicit POST.
- **Approved Layout Library section** (the P4 amendment-7 permanent slot) fills: one row per ApprovedLayout — name · V<n> · fabric group · width · length/util (derived) · status chip · STALE badge if any · [View] [Duplicate] [PDF] [Print] [Supersede…] [Archive]. Drafts line: "n saved drafts" linking the newest.
- Stage label completes: Draft → Saved Draft → Approved (loaded read-only).

## Files (~10 + 1 migration)
`models/layouts.py` (NEW: ApprovedLayout) + migration 0010 ·
`marker_generation_service` (+`save_table_layout`) ·
`services/layout_library_service.py` (NEW single writer) · `views.py`
(+TableSave POST · +TableApprove review/POST · +library actions ·
shell view loads library rows + view/duplicate params) · `urls.py`
(+3) · `cutting_table.html` (save btn · live Approve/Export · library
rows · read-only mode) · `dct_approve_confirm.html` (NEW, composed
from `approve_confirm.html` canon) · tests (NEW
`test_phase7_library.py`: save verify-refusals + self-contained params
+ LAW-12 server check · approve/supersede/archive chain + immutability
guards + version_no · staleness derive · exports linkage + gates ·
save≠approve separation · worker 403s) · conscious updates (toolbar
tests: Approve Layout + Export go live) · report.

## Risks
- R-1 first migration since 0009 — additive-only, one new table,
  nothing existing touched (candidate/run/★ schemas unchanged).
- R-2 two approval systems visible (★ tool designation vs DCT library)
  — consciously coexisting; unification = P8 agenda item, recorded.
- R-3 save volume (append-only drafts) — same policy as the proven
  workspace flow; grouping/cleanup = future, noted.
- R-4 ratio empty until the cut-plan input exists — honest "--"
  everywhere it shows; registered future.

---
**STOP — Phase-7 plan delivered. No code. Awaiting your approval
(D-1 save extension · D-2 ApprovedLayout + coexisting ★ · rules map).**

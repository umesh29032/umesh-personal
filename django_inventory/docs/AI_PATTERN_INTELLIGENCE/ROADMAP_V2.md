---
id: docs-ai-pattern-intelligence-roadmap-v2
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# ROADMAP V2 — the ONLY active roadmap (owner reset, 2026-07-07)

**🔒 FINALITY (owner, 2026-07-07): Phase 6 is the FINAL implementation
phase. Phases 1–5 = ✅ COMPLETE + FROZEN. After Phase 6 the project is
COMPLETE — no Phase 7, no new roadmap, no feature proposals, no AI
expansion — unless the owner explicitly requests new functionality.
Phase-6 scope = ROADMAP Phase 6 (PDF · full-marker true-scale print ·
final validation) PLUS the four integration items in
[PRODUCT_INTEGRATION_DESIGN §5](PRODUCT_INTEGRATION_DESIGN.md) (smart
redirect · entry button · Layout switcher · Approve-for-production ·
Pattern Design Hub w/ validation checklist · required/optional flag ·
reference images · ProductFabricProfile defaults · BLF internal
timebox — the nine items of [PRODUCT_INTEGRATION_DESIGN §5](PRODUCT_INTEGRATION_DESIGN.md)).**

Governed by [PRODUCT_VISION_V2](PRODUCT_VISION_V2.md). Supersedes the
enterprise roadmap (master plan P0–P6 phase framing) and every "next"
list in prior era reports.

## 1. The six product phases — status against what already exists

| Phase | Scope (owner's words) | Status | Gap to close |
|---|---|---|---|
| **1 · Pattern Capture** (photo → geometry) | capture photos, extract accurate geometry | ✅ **DONE** (built as "P2"): phone wizard → immutable photo → metrology-gated extraction (isolated CV runtime, ChArUco mat scale recovery, honest refusals) | none blocking; D7 real-mat validation = the standing accuracy gate before production trust |
| **2 · Geometry Verification** (editing, validation, storage) | verify, edit, store digital patterns | ✅ **LARGELY DONE**: annotator (accept/reject) · draft vertex editor · confirm w/ grain + tape check · canonical µm storage · per-size rows · trust grades · library pages | minor polish only (richer vertex editing — add/delete points — if ever needed; ask first) |
| **3 · Marker Generation** (basic layout engine) | generate layouts in fabric width | ✅ **DONE** (built as "P3"): SVGnest (vendored, primary) + BLF floor · independent overlap/width verification · multiple candidates · visualization · SVG download | **height/max-length input missing** (today width-only, length unbounded) — moves to Phase 4 |
| **4 · Interactive Marker Workspace** | zoom · pan · grid · guides · drag · rotate · lock · width control · height control · live utilization/wastage/length | ✅ **COMPLETE + FROZEN** (2026-07-07; [receipt](PHASE4_COMPLETION_REPORT.md)) | — |
| **5 · AI-Assisted Optimization** | multiple layouts · AI rearrangement · manual correction loop · regenerate UNLOCKED pieces · continuous improvement | ✅ **COMPLETE + FROZEN** (2026-07-07, rules 1–10; [receipt](PHASE5_COMPLETION_REPORT.md)) | — |
| **6 · Export & Production Ready** | DXF · SVG · PDF · print · final validation | 🟡 **THE FINAL PHASE (owner-gated)**: SVG ✓ · DXF-AAMA ✓ · per-piece true-scale print ✓ | PDF export · full-marker tiled true-scale print · final validation · + the 4 integration items (smart redirect, entry button, Layout switcher, Approve-for-production) |

**Remaining core work = Phase 6 only.** Phases 1–5 complete + frozen. After Phase 6 the project is COMPLETE (finality ruling above).

## 2. Audit of P0–P5 against the vision (the owner's 5 questions)

### 2a. Directly supports the product (ACTIVE core)
Compute runtime (ADR-F isolation, lockfile, vendored SVGnest, node) ·
metrology chain (CalibrationMat + checks, gates, hold-out residuals) ·
capture pipeline (CaptureAsset, magic-bytes, sha, renditions) ·
geometry era (PatternPiece/Version, PieceSizeGeometry, canonical µm
format ADR-C, annotator, editor, confirm, trust grades) · generation era
(runs, candidates, verification, visualization, engines) · exports
(SVG/DXF, Gate-1 print) · health command, runbook, **D7 protocol** (=
"extract ACCURATE geometry" made honest) · all walls/tests over the above.

### 2b. Unnecessary for the goal (optional research, OFF the roadmap, frozen as-is)
P1 production-memory loop: MarkerUsage/MarkerOutcome recording UIs,
**Yield Board**, marker biography/lineage surfaces · **P4 Cut Advisor +
SuggestionEvent spine** (recommendation system beyond marker generation) ·
**P5 Insights dashboard** (executive reporting — explicitly on the
do-not list) · benchmark/beats-baseline promotion law (depends on
production outcomes) · P5 Adda-page links (ERP embedding).
**None of it gets extended. It stays only as frozen, tested, harmless
code** unless the owner orders removal.

### 2c. Harmless infrastructure that remains
Everything in 2b (append-only tables, read-only services, gated pages —
zero maintenance pressure, zero coupling into the core flow) · marker
model + MRK references (the promoted-layout container; promotion gate
simplifies under this vision when Phase 5 touches it) · sidebar/RBAC
wiring · media sweep · rollout/onboarding docs (trim at Phase 6).

### 2d. Removed from the FUTURE roadmap (were "next"; now research-only)
ADR-B background worker (enterprise scaling) · D10 local-LLM/learned
ranking · SAM vendoring (revisit ONLY if classical segmentation fails on
real photos — a Phase-1-quality question, not a feature) · cloth-roll
width-stock integration · suggestion-outcome analytics · multi-order
optimization · derived-metrics caches · "assistant surfaces" of every
kind.

### 2e. Exact remaining phases
**Phase 4 → Phase 5 → Phase 6** as defined in §1 (plus the height
control folded into Phase 4). Nothing else.

## 3. Standing constraints carried forward (they serve THIS product)
Single-writer services · append-only knowledge · immutable confirmed
geometry · derived-at-read metrics · human verification boundaries ·
ADR-F engine isolation · honest refusals/labels · phase discipline
(design → review → build → test → browser → review → regression → docs →
freeze → next).

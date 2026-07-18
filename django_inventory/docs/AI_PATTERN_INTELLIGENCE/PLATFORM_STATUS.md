---
id: docs-ai-pattern-intelligence-platform-status
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PLATFORM STATUS — the master reference
(2026-07-10 · the snapshot that CLOSES the architecture phase · owner
ruling: "Reality becomes the architect from this point onward" —
architecture changes only when a real factory exposes a genuine
problem · constitution: PRODUCT_DESIGN_FREEZE + UI_WORKFLOW_FREEZE +
MGE_MASTER_DESIGN + MANUFACTURING_INTEGRATION_REVIEW + this document)

```
Architecture Phase:               COMPLETE          (owner, 2026-07-10)
Manufacturing Geometry Platform:  STABLE
Development Mode:                 FACTORY DRIVEN
Foundation Version:               v1.0
```
**Owner ruling closing the era (M8.1 approval, 2026-07-10):** every
implementation starts from a REAL factory problem; no invented
milestones; no architecture documents unless reality forces one; no
freeze documents; no redesign passes. Ownership question FIRST
(PI / ERP / Shared boundary — unclear ⇒ stop and review). All existing
laws stay constitutional (single writers · derive-at-read · immutable
approved layouts · deterministic calculations · AI proposes, humans
approve · operator authority · genericity guard · provider-registry
boundary · engine never knows products · settlement-only money).
Every change: evolutionary, evidence-driven, as small as possible.
First real geometry milestone: M8 (owner's cardboard Body photo →
published measured design) + M8.1 bare-draft safety (see §8a).

## 1 · MODULE STATUS

| Module | State | Proof |
|---|---|---|
| M1 Blueprint (structure + capabilities) | ✅ DONE | atomic register API · rules/count/notch/seam slots · fold+pair advisory |
| M2 Pattern Intelligence Studio (+ Acquisition Layer) | ✅ DONE | Evidence Stack · adapters photo/DXF/SVG/dims on ONE contract · compare/confidence display-only · QR phone hand-off · conveyor |
| M3 Pattern Library | ✅ DONE (folded into M2) | the Studio's Browse mode = the shelf; checklist chips = the readiness law |
| M4 Manufacturing Planner | ✅ DONE | Marker Plan → params · Marker Recipes · Import Queue pieces-math · size-index colors · live estimates · Suggest-Better-Layout explained verdict |
| M4.5 Fold | ✅ DONE | adr-c.3 fold_edge · capabilities contract · placement modes · crease pin · content ÷2 · readiness unblocked with named fix |
| M6 Manufacturing Bridge | ✅ DONE (gates OFF) | layering advisory edge · usage↔stage-record stamp · REQUIRE/ENFORCE gates (owner flips post-soak) |
| M5 Layout Library polish | ✅ DONE | rows = thumbnail/recipe/notes/lay/roll/lineage · live search · recipe deactivate (soft-state) |
| M8 Real Pattern Capture | ✅ DONE (owner-approved) | Evidence-SET adapter (photo_plain + tape-stated scale) · Otsu no-mat CV · cross-checks advisory · FIRST REAL GEOMETRY published (Body M measured) |
| M8.1 Bare-Draft Safety | ✅ DONE (owner-approved) | copy-forward in EVERY draft-creating path + confirm backstop — published sizes can never be dropped by accident |
| M7 Pattern Assistant | 🔮 FUTURE | proposals-only scope frozen (suggest notches/seam/grain/retake/missing/duplicate/layout) |
| Analytics (yield/advisor/insights) | 🧊 FROZEN research | revive later against library data — never extend without owner order |
| SaaS / multi-tenancy | 🔮 FUTURE | identity already license-grade (uids + stamps, ADR-0010); nothing assumes single-factory |

## 2 · ARCHITECTURE (as built)

```
┌────────────────────── THE TRUTH LAYER ───────────────────────┐
│ PieceSizeGeometry (int-µm · versions · contract stamp)       │
│ ApprovedLayout (uid · immutable · supersede chains)           │
│ ApprovedLayoutUsage (the manufacturing timeline, stamped)     │
│ ManufacturingStrategy (Marker Recipes = knowledge as data)    │
│ ONE single-writer service per store · append-only · human-gated│
└───────────────────────────────────────────────────────────────┘
   ▲ proposals only                      │ derive-at-read only
┌──┴───────────────────┐      ┌──────────▼───────────────────┐
│ ACQUISITION LAYER    │      │ READ-ONLY INTELLIGENCE        │
│ Evidence→Adapter→    │      │ facade (capabilities contract)│
│ Proposal→HUMAN→Truth │      │ providers · staleness · content│
└──────────────────────┘      └───────────────────────────────┘
   ▲                                        │ registries (dicts)
┌──┴────────────────────────────────────────▼──────────────────┐
│ SURFACES: 5-station rail — Blueprint · Studio(Browse=Library) │
│ · Digital Cutting Table · Layout Library · Manufacturing      │
└───────────────────────────────────────────────────────────────┘
                                            │ THE WALL (ADR-H)
┌───────────────────────────────────────────▼──────────────────┐
│ ERP: Layering → Cutting → Bundles → Barcodes → Tracking →     │
│ Inventory → Costing → Settlement (money NEVER touched by PI)  │
└───────────────────────────────────────────────────────────────┘
```

## 3 · DATA OWNERSHIP (permanently frozen, owner ruling)

**Pattern Intelligence owns:** Blueprint · Piece Definitions · Pattern
Capabilities · Verified Geometry · Pattern Library · Layout Planning ·
Marker Recipes/Strategies · Approved Layouts · Marker Content (derived)
· Layout Usage · Manufacturing Traceability (the stamp).
**ERP owns:** Layering (plies truth) · Roll Consumption · Cutting ·
Bundles · Barcodes · Production Tracking · Inventory · Costing ·
Settlement.
**The asymmetry preserved forever:** plies never enter PI; content
never persists in ERP; NO PI field ever feeds money.
**Every future feature answers first: "PI or ERP?" — unclear ownership
⇒ stop and review before coding** (constitution).

## 4 · PROVIDER REGISTRY MAP (the ONLY communication mechanism)

| Registry (ERP side) | Registered by patterns_ai | Contract |
|---|---|---|
| `production.services.product_size_service.ARCHIVE_VALIDATORS` | `refuse_archiving_sole_design_size` | validator(size) may raise — guards sizes holding sole confirmed designs |
| `production.stages.cutting_pattern.handler.LAYOUT_PROVIDER` | `build_layout_panel(adda)` | dict: usage groups · content_by_pattern_size (plies-free) · choose_url |
| `production.stages.layering.handler.LAYOUT_PROVIDER` | `build_layering_recommendation(adda)` | dict: {groups:[{group,uid,length_mm,layering_type}]} — ADVISORY |
| `production.stages.cutting.service.CUTTING_COMPLETE_LISTENERS` | `stamp_adda_usages(adda, sr)` | post-completion hook; failures isolated, cutting never breaks |
Plus: URL-name reverses (navigation) · patterns_ai FKs INTO production
(read-down) · settings flags. Nothing else crosses — enforced by
test_purity + import-linter every battery run.

## 5 · THE MANUFACTURING WORKFLOW (browser-proven on the real Nickar)

Blueprint (Body ×2 pair+fold · Panel ×2 other-fabric · Pocket ×2) →
Studio digitize+verify (fold edge marked, proposals one-shot) → shelf
READY → DCT Marker Plan (recipe · roll → human-confirmed width · lay
type · sizes×garments) → Import Queue (placement modes; fold opens to
1/layer; over-import refused with the fold way out) → arrange →
Suggest Better Layout (explained verdict, Accept/Keep) → Save (plan
rides into params) → human Approve → LAY-uid asset → the Adda CHOOSES
per fabric group → layering sees "Recommended layer length: 440 mm —
advisory only" (operator's number stood) → cutting suggestion = content
× plies (Body 20 · Pocket 20 · fold-Back 10) → operator cuts (49 vs 50
→ WARN "your numbers stand") → barcodes → usage auto-stamped to the
cutting record → tracking → inventory. Money: settlement-only, forever.

## 6 · GENERICITY GUARANTEES

The engine never knows a garment name. Enforced by: ① the GENERICITY
GUARD test (regex wall over all non-test patterns_ai + compute code,
every battery) ② the capabilities CONTRACT (one derived dict; consumers
never read garment-specific anything) ③ config-only ERP operations
(proven: T-Shirt 16-op + Lower 13-op flows, zero handler code) ④ new
garment = Product + sizes + Blueprint + geometry + ERP config, nothing
else (proven live with Nickar end-to-end). If a new garment ever needs
engine code ⇒ ARCHITECTURAL FAILURE (owner ruling).

**Permanent DEV reference products (real-manufacturing validation for
every future milestone):** DEV-NICKAR (fold + separate-panel + double
lay — the fold reference; real cardboard photos in owner's Downloads/
"nikkar body pattern multiple images") · golden T-SHIRT (regression
gold, untouched) · Lower (ERP config reference). Hoodie/Shirt/School
Uniform join later. Real examples over synthetic fixtures from now on.

## 7 · CONTRACT VERSION HISTORY (the stamp did its job 3×)

| Version | Landed | What + why |
|---|---|---|
| adr-c.1 | Platform Phase 1 | the canonical payload law (integer µm · y-up · CCW outer · origin bbox-min · polyline-at-chord-tolerance = the CUT line at manufacturing accuracy) + the STAMP itself — so future semantics changes would be conscious, single-writer-controlled acts |
| adr-c.2 | M2 | + typed optional `features.notches` + piece-level declared seam — manufacturing marks the physical pattern carries; consciously added when the Studio (the room that captures them) was built |
| adr-c.3 | M4.5 | + typed optional `features.fold_edge` (straight vertical outline segment) — the half-pattern's fold line; consciously added when fold placement physics landed. Every prior payload stays valid; old rows keep their stamps |
Bezier = consciously REJECTED (polyline at 0.5 mm chord = the
manufacturing answer); adr-c.4 exists only if a real piece proves
insufficient fidelity.

## 8 · REMAINING ROADMAP (implementation-driven from here)

- **Flag flips** (owner, post-soak): REQUIRE_APPROVED_LAYOUT ·
  ENFORCE_LAYOUT_RECONCILIATION (+ tolerance tuning).
- **M7** Pattern Assistant (proposals-only, frozen scope).
- **Analytics revival** on library data (frozen research, owner-gated).
- **Commercial/SaaS**: multi-tenancy, deployment, licensing — identity
  layer already ready.
- **FUTURE NOTE (owner, documented NOT designed): MANUFACTURING
  PACKAGE** — a higher-level object grouping a product's layouts
  (Body + Panel + Pocket markers) so an Adda consumes ONE approved
  package instead of choosing per group. Roadmap note only; no design
  work until reality demands it.
- Open acquisition ideas (noted, not promised): tape-measure-
  calibrated photo adapter (scale from the visible ruler — the owner's
  natural capture style) · large-piece capture direction (mats /
  multi-shot / external — owner decision open) · Studio viewfinder
  overlay.

## 8a · FACTORY DRIVEN DEVELOPMENT (owner ruling 2026-07-10 — the
permanent working mode; supersedes the milestone protocol)

Every future task uses THIS format only:
```
1. Real factory problem
2. Why it matters
3. Ownership (PI / ERP / Boundary)   ← unclear ⇒ STOP and review
4. Smallest implementation
5. Browser verification
6. Tests
7. STOP
```
No freeze documents. No redesign passes. No speculative milestones.
Every implementation validates against ALL reference products —
**DEV-NICKAR** (primary real manufacturing reference) · **golden
T-SHIRT** · **Lower** — without introducing product-specific logic
(the genericity guard enforces this mechanically). Features touching
geometry or manufacturing additionally validate on at least one REAL
factory example before they count as complete.

**The genericity question (constitutional, owner ruling 2026-07-10):**
before implementing ANY new feature, ask — *is this a generic
manufacturing capability, or only one product's workflow?* Generic ⇒
implement ONCE so every future product benefits. Product-specific ⇒ it
lives as Product Definition / Blueprint / Rules / Geometry /
Configuration / ERP Data — never as engine code. Product knowledge
never enters the engine.

**Communication rule (owner ruling 2026-07-10):** no auto-generated
implementation plans. When the owner reports a real factory problem:
analyze → determine ownership → propose the smallest solution →
implement → verify → STOP. If architecture is genuinely required,
STOP first and explain exactly WHICH real factory problem forces it —
before creating any architecture document. (Constitution ratified by
the owner with this ruling: "The architecture is now the constitution.
Reality is the architect.")

**Final audit + acceptance (2026-07-11):** FOUNDATION_V1_AUDIT.md
(verdict B → owner ruled ENGINEERING COMPLETE except one item).
**Both audit items CLOSED same day (owner execution order):**
① Gate-1 large-piece TILED print — geometry_print now tiles on the
exact candidate-print grid (190×277 window · 180×267 step · 10 mm
dashed match lines · per-sheet scale bar); browser-proven on the REAL
Body M (2×2 = 4 sheets, outline in every window); small pieces stay
one sheet. ② template-comment leak class — permanent guard test
(test_template_hygiene: multi-line `{# #}` inside a block = failure).
**🔒 PATTERN INTELLIGENCE IS FROZEN (owner, 2026-07-11).** Development
moved to the Production/ERP verification campaign (module-by-module,
role-based, real factory data, browser-verified; module 1 role-login
matrix = PASS). Deployment tasks (commit · server compute venv · .env ·
backups) and factory data (real captures/tape/rates/rolls) =
acknowledged non-engineering prerequisites for rollout.

## 8b · THE BARCODE IDENTITY LAW (owner-frozen 2026-07-11)

> **Identity is meaning-blind; meaning lives on the lane.** A barcode
> names exactly ONE physical piece (`{ADDA}-{SEQ}`) — never a garment,
> bundle, worker, stage, or intent. Meaning = derive-at-read over DB
> facts (lane reason · statuses · batches · Blueprint). Identity is
> permanent: never reused, inherited, or renumbered; sequences append
> `Max+1` forever; destroyed pieces retire by terminal STATUS (the row
> is the death certificate). Piece-level "replaces" pointers are
> permanently rejected (fungibility = false precision). Full law:
> tracking/README.md + docs/BARCODE_IDENTITY_REVIEW.md.

## 9 · TECHNICAL DEBT (genuine only)

1. Legacy generate/workspace/manual-marker pages: retired from
   navigation, still live at URLs — fold away when confidence allows.
2. Dual DXF entry: legacy `import_dxf` page (direct-to-draft) + the
   Studio's contract path — converge on the Studio someday.
3. Readiness twin body (`_hub_readiness_legacy_reference`) kept only
   for the W1 parity test — retire test + body together.
4. Engine fold optimization: fold placements = fixed obstacles v1;
   slide-on-edge search = a future engine op.
5. Tubular right-edge fold pin (v1 pins LEFT crease only).
6. Phone capture v1: guidance text + QR + poll; no live viewfinder.
7. ~~Layout notes/recipe not yet displayed on library rows~~ CLOSED (M5).
8. import-linter known-broken contract: one TEST-only import
   (raw_materials.tests → inventory.models) — baseline, documented.
9. sentry_sdk optional-import IDE warnings (prod-only dependency).

## 10 · NEVER REDESIGN AGAIN (the spine, owner-frozen)

The truth model (geometry versions + stamps) · single writers ·
append-only history · the ADR-H wall + registry inversions · the
canonical validator twins · the metrology loop · mm-world ≠ camera ·
the engine + frame swap · ApprovedLayout immutability + usage timeline
+ freezes F1–F3 · the count hierarchy (content · plies · advisory) ·
operator authority ("your numbers stand") · AI-proposes-humans-approve
· deterministic-and-seeded · settlement-only money · the capabilities
contract · the three-concepts law (pattern CAN · lay POSSIBLE ·
placement CHOSE) · the genericity guard.

**The architecture phase is officially finished. The foundation is
complete. Implementation and real-world evolution begin.**

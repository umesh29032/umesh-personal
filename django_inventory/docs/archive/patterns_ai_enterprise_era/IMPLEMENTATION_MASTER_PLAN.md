# AI PATTERN INTELLIGENCE — IMPLEMENTATION MASTER PLAN (Phase 2 · 2026-07-06)

> **Status: 📋 PLAN — no implementation authorized by this document.**
> Governing chain (in precedence order):
> [MANUFACTURING_V1_FREEZE.md](../MANUFACTURING_V1_FREEZE.md) →
> [06_BLUEPRINT_V3_FINAL.md](06_BLUEPRINT_V3_FINAL.md) (architecture, CLOSED) →
> [ADR pack A–H](ADR/ADR_PACK_CERTIFICATION.md) (implementation contract,
> owner-approved) → [Kickoff Contract](../AI_PATTERN_INTELLIGENCE_KICKOFF.md).
> This plan ADDS scheduling, checkpoints, and acceptance mechanics ONLY —
> any conflict with the chain above is a plan bug (rule 11: STOP + report).
> Owner global rules apply: one phase per session-block, completion report +
> STOP + approval between phases; implementation code begins only at owner-
> approved Phase 4 (= P0 below).

---

## 1. Overview

| Project phase | Owner session-phase | Goal (one line) | Est. effort* | Key deliverable |
|---|---|---|---|---|
| **P0 Feasibility** | Phase 4 | prove the three risky claims: nesting quality, metrology honesty, yield-board math | 3–5 sessions | bake-off numbers (ADR-A addendum) · error tiers (ADR-E addendum) · 3-PATTI-016 yield walk |
| **P1 DIGITAL MEMORY** | Phase 5 | the factory's marker memory: manual markers + usage/outcomes + YIELD BOARD | 6–10 sessions | `patterns_ai` app (memory subset) + yield board live |
| **P2 CAPTURE** | Phase 6 | cardboard → confirmed geometry, honestly measured | 10–15 sessions | capture pipeline + pattern library (geometry era) + DXF import |
| **P3 GENERATION** | Phase 7 | markers generated, benchmarked vs manual baselines, chosen in the marker room | 10–14 sessions | async worker + engine adapters + marker room + D11 flow |
| **P4 ASSISTANT DEPTH** | Phase 8 | confidence scores, two-tier recommendations, Product-360, DXF export | 6–8 sessions | assistant era complete |
| **P5 HARDWARE** | Phase 9 | plotter/projector output behind one interface | 4–6 sessions (hardware-gated) | HPGL/projector outputs |
| **P6 REAL ML** | Phase 10 | probably never — written gate only | 0 until gate met | gate review memo |

\* 1 session ≈ one focused half-day of solo-dev + AI pair work. Ranges are
honest uncertainty, not commitments; each phase re-estimates at its start.

**Dependency graph (DAG — no cycles):**

```
ADR pack (done) ─┬─► P0 ──► P3 (engine choice feeds adapters)
                 │
D2/D3 mini-ADRs ─┼─► P1 ──► P2 ──► P3 ──► P4 ──► P5
(owner, at P1)   │    ▲               (P6 gated forever)
ADR-C spec doc ──┘    └── D7 purchases (mat+mount) before P2 capture work
```

Hard sequence rules: ADR-C spec is written **in P1** but gates the first
geometry ROW (written in P2). ADR-B worker is built **in P3** (memory + capture
eras have no async need). DXF-AAMA **import** lands in P2 (jumps the queue only
if a brand file arrives). D2 (`fabric_construction`) + D3 (GSM) are separate
owner mini-ADRs — additive nullable fields on the manufacturing side — approved
at P1 start; the yield board renders ₹ only after D3 data exists (honest-NULL
until then).

## 2. Global strategies (apply to every phase)

### 2.1 Testing strategy
- **Baseline wall:** the manufacturing suite (885 at freeze) must stay green
  untouched — patterns_ai never edits a manufacturing test.
- **Per-phase suite:** each phase adds `patterns_ai` tests in the same style
  as the engine's walls: golden tests (yield-board math against 3-PATTI-016's
  settled numbers; geometry round-trip SVG/DXF; instruction-diagram render),
  guard tests (purity: production imports no patterns_ai; no-network on
  compute paths; single-writer: no raw-ORM creation of knowledge rows),
  state-machine tests (marker/geometry transitions incl. reasoned negatives),
  and RBAC/sidebar tests per new URL.
- **Serial gate discipline:** one test command at a time (documented lesson);
  full gate = manufacturing baseline + patterns_ai suite, run at every phase
  end and before every completion report.
- Query-count pins for the two hot reads (yield board; marker resolution) are
  set CONSCIOUSLY when the pages first ship, with written re-pin rules.

### 2.2 Rollback strategy
- **App-level kill switch:** all patterns_ai URLs are SidebarItemRule-gated;
  removing the rules (config) hides menu + blocks URLs instantly — UX-level
  rollback with zero code.
- **Migrations:** patterns_ai migrations are additive-only (F3) and reversible;
  each phase documents its `migrate patterns_ai <prev>` point. Manufacturing
  mini-ADR fields (D2/D3) are nullable additive → reversible independently.
- **Media:** knowledge-class files are never deleted on rollback (they are
  facts); a rolled-back phase leaves orphan-safe files (re-adopted on
  roll-forward).
- **Worker (P3+):** systemd unit stop = full async rollback; queued jobs stay
  as rows (append-only), resumable.
- **The freeze guarantee:** because production is never written or imported,
  NO patterns_ai rollback can affect manufacturing — verified by the purity +
  baseline-suite gates at every phase end.

### 2.3 Browser verification checkpoints
Every phase that ships UI ends with a browser pass on **@390 phone AND
desktop**, using the DEV cast, with screenshots archived: P1 yield board +
manual-marker entry; P2 capture wizard (phone) + annotator (desktop) + Gate-1
print preview; P3 marker room + evidence cards + diagram/print ritual + D11
promotion flow; P4 confidence chips + recommendations + Product-360; P5 output
previews. The 4-role audit habit (owner/manager/cutting-master/worker-
exclusion) applies at each checkpoint.

### 2.4 Data-migration checkpoints
Gate at every phase end: `makemigrations --check` clean · new migrations
reviewed against F3 (additive, versioned payloads, no repurposing) · **no
backfill of unknown facts ever** (Data/History rule — the yield board starts
empty and fills from real use; no fabricated history) · D2/D3 fields enter
only via their owner mini-ADRs.

### 2.5 Performance checkpoints
- P1: yield board ≤ its conscious query pin on 3 years of simulated rows
  (script-generated DEV volume test, then torn down).
- P2: interactive segmentation < 5 s CPU; capture session ≤ 90 s/piece
  measured on the real factory table; media integrity sweep runtime bounded.
- P3: nesting job respects wall-clock budget; worker cap keeps floor-ERP page
  latency unchanged (measured before/after under a running job).
- P4: marker-resolution query uses the `width_band` index (EXPLAIN checked);
  confidence computation O(facts) at read with no N+1.

### 2.6 Review checkpoints & Definition of Done (every phase)
DoD: phase suite + full baseline green (serial) · browser checkpoints passed
with screenshots · docs-sync same session (app GUIDE + chokepoint docs +
index) · memory updated · completion report written · **zero frozen-contract
violations** (purity/no-network/single-writer tests green) · owner approval
received → STOP. Mid-phase hostile mini-reviews are mandatory inside P2
(metrology claims) and P3 (utilization-honesty claims) before their UIs ship.

## 3. Phase details

### P0 — FEASIBILITY (implementation Phase 4)
1. **Goal:** replace the three biggest unknowns with numbers: (a) can an
   open-source engine nest our real shapes well, (b) what capture error is
   honestly achievable, (c) does the yield-board math work on real data.
2. **Inputs:** ADR-A harness spec; ADR-E gate spec; 3-PATTI-016 settled data;
   hand-digitised polygons (T-shirt front/back/sleeve, patti set, one >1 m
   Lower panel, one curved-heavy piece, one on-fold tubular piece); a
   printed test mat (A0-tiled acceptable for POC only).
3. **Outputs:** `poc/patterns_ai/` reproducible harness (own pinned venv per
   ADR-F style, NON-production code, kept for reproducibility) · ADR-A
   addendum (bake-off table: utilization/constraint-fidelity/wall-clock per
   engine incl. BLF floor) · ADR-E addendum (measured error tiers) ·
   yield-board data walk memo (3-PATTI-016 manual-marker facts → meters/
   garment by hand) · GO/NO-GO recommendation per V3 roadmap gates.
4. **Files/modules affected:** `poc/patterns_ai/**` (new, isolated),
   `docs/AI_PATTERN_INTELLIGENCE/ADR/*addendum*`, this plan (re-estimate).
   NO Django app, NO models, NO migrations, NO production files.
5. **Risks:** engines fail the concave test (mitigation: BLF floor + SVGnest
   runner budgeted); POC mat print inaccurate (mitigation: commissioning
   tape-check FIRST, per ADR-E, even for the POC mat); enthusiasm-creep into
   app code (mitigation: rule 7 — poc/ only).
6. **Validation steps:** harness re-runs from vendored artifacts on a clean
   venv; every bake-off number reproducible from a committed script; error
   tiers measured against tape-measured golden pieces (≥3 pieces × ≥3
   captures).
7. **Exit criteria:** ≥75–80 % utilization on the harness by at least one
   engine (else NO-GO report + owner decision); published tiered error spec;
   yield-walk memo matches the settled ₹633 journey's fabric math;
   completion report; STOP.

### P1 — DIGITAL MEMORY (implementation Phase 5)
1. **Goal:** the factory's marker memory goes live: manual markers recorded,
   usage + outcomes captured, yield board answering "which marker wastes
   less" — zero CV.
2. **Inputs:** approved P0 report; D2/D3 owner mini-ADRs (approved at phase
   start); ADR-C/D/G/H texts.
3. **Outputs:** `patterns_ai` app (INSTALLED_APPS, urls, sidebar rules,
   media tree) · memory-subset models: `Marker` (origins; manual complete),
   `MarkerUsage` (+repeats), `MarkerOutcome` (facts-only), `SuggestionEvent`,
   `CalibrationMat` (registry skeleton), `CaptureAsset` (manual-photo subset),
   `GarmentTemplate`(+revisions, seed data) · services: `marker_service`,
   `marker_feedback_service` (+ the ONE quantization helper) · UIs: manual
   marker entry (photo + width/ratio/repeats), usage recording at cut
   planning (link-out seam), **yield board** · ADR-C geometry spec doc
   checked in (gate for P2) · importlinter entry + purity test + no-network
   test scaffold · DEV dummy data per V3 §13 · docs (app GUIDE, chokepoints).
4. **Files/modules affected:** `config/patterns_ai/**` (new) ·
   `config/config/settings/base.py` (INSTALLED_APPS) · `config/config/urls.py`
   · `config/.importlinter` · SidebarItemRule fixtures/config ·
   manufacturing mini-ADR migrations (D2/D3, additive nullable — the ONLY
   production-side touches, owner-approved) · docs tree. NO other production
   file.
5. **Risks:** scope creep toward capture (defense: geometry rows FORBIDDEN in
   P1 — spec exists, table may exist empty, no write path shipped); manual
   entry friction kills adoption (defense: ≤2-minute entry gate measured);
   D2/D3 approval slips (defense: yield board ships meters-only,
   honest-NULL ₹).
6. **Validation steps:** golden yield math vs 3-PATTI-016 · full gates (§2.1)
   · browser checkpoint (§2.3) · performance pin (§2.5) · migration gate
   (§2.4).
7. **Exit criteria:** the owner reads a real yield board row for one product
   from data entered that week; a manual marker + its usage + outcome exist
   end-to-end with biography visible; all DoD items; STOP.

### P2 — CAPTURE (implementation Phase 6)
1. **Goal:** cardboard patterns become confirmed, trusted, per-size geometry —
   the pattern library's geometry era.
2. **Inputs:** P1 live; ADR-C spec (gate); ADR-E/F; D7 purchases done (real
   mat + phone mount, commissioned per ADR-E).
3. **Outputs:** geometry models live (`PatternPiece`, `PatternPieceVersion`,
   `PieceSizeGeometry`, `PatternSetLabel`) · `capture_service` +
   `pattern_geometry_service` · ADR-F compute runtime (vendored artifacts,
   isolated venv, no-network enforced) · capture wizard (phone) + 3-step
   annotator (desktop) + batch sessions + trust grades + numeric tape
   acceptance · CalibrationMat commissioning UI + device profiles · Gate-1
   overlay prints · **DXF-AAMA import** · SVG export live · media lifecycle
   jobs (integrity sweep) · docs.
4. **Files/modules affected:** `config/patterns_ai/**` · `compute/patterns_ai/`
   (isolated runtime + artifact manifest) · deploy runbook (worker NOT yet;
   integrity cron + media budget) · docs. NO production files.
5. **Risks:** metrology tiers miss on the real table (mitigation: mid-phase
   hostile review + tier re-publication before UI ships; manual-entry door
   remains the trust path); per-size burden (mitigation: batch capture +
   ≤90 s gate; D9 scaled-draft policy); design-system canvas gap (mitigation:
   mandated design-system extension audit BEFORE annotator build).
6. **Validation steps:** golden geometry round-trips (JSON↔SVG, DXF import
   fidelity set) · error-tier re-validation on factory table · full gates ·
   browser checkpoints (phone capture, desktop annotator) · media sweep run.
7. **Exit criteria:** the cutting master digitises one real graded set
   unaided within gates; geometry confirmed with provenance + trust grades;
   Gate-1 receipt recorded; DXF sample imports faithfully; DoD; STOP.

### P3 — GENERATION (implementation Phase 7)
1. **Goal:** generated markers exist, are benchmarked against manual
   baselines with evidence, and get chosen/used through the marker room.
2. **Inputs:** P2 geometry; P0 engine winner; ADR-B/D.
3. **Outputs:** ADR-B job table + systemd worker + overnight window ·
   `MarkerRequest`/`MarkerRun` live · engine adapters (winner + BLF floor;
   losers stay in-tree) · strategy alternatives + honest three-numbers cards ·
   evidence cards vs baselines (`benchmarked_against`) · marker room UI
   (concrete options incl. manual baseline) · instruction diagram + short-
   marker ritual print (100 mm forced confirm) · D11 adda-temporary flow +
   promotion · Gate-2 receipts (side-by-side lay: FIRST product only) ·
   deploy runbook (worker unit) · docs.
4. **Files/modules affected:** `config/patterns_ai/**` · `compute/patterns_ai/`
   (nesting adapters) · deploy runbook · docs. NO production files.
5. **Risks:** winner engine underperforms on new shapes (mitigation: adapters
   swappable; regenerate-with-other-engine = new marker); worker starves the
   floor box (mitigation: cap 1 + measured latency checkpoint); print
   mis-scale (mitigation: the ritual is unskippable by design).
6. **Validation steps:** determinism audit (stored placements render
   identically; seed/engine recorded) · queue kill/restart/orphan-recovery
   tests · evidence-card math golden · full gates · browser checkpoints incl.
   promotion flow · floor-latency measurement under load.
7. **Exit criteria:** one generated marker BEATS the recorded manual baseline
   on ≥1 real product with receipts; D11 temporary→promotion exercised
   end-to-end; DoD; STOP.

### P4 — ASSISTANT DEPTH (implementation Phase 8)
1. **Goal:** the assistant era completes: confidence, recommendations,
   Product-360 knowledge view, DXF export.
2. **Inputs:** P3 live; accumulated real usage/outcome rows; optional
   measured-lay extras mini-ADRs (end-loss/splice — owner-gated).
3. **Outputs:** confidence tiers + why-chips (formula versioned) · two-tier
   recommendations + deterministic TRIAL rule · Product-360 view (read-side)
   · DXF-AAMA export + round-trip tests · width-band EXPLAIN proof · docs.
4. **Files/modules affected:** `config/patterns_ai/**` · docs. NO production
   files.
5. **Risks:** thin data makes tiers feel arbitrary (mitigation: tier
   thresholds published; badges always show n); recommendation over-trust
   (mitigation: honest-AI copy review = mid-phase checkpoint).
6. **Validation steps:** confidence pure-function goldens (fixed facts →
   fixed score) · recommendation honesty tests (no render below n rules) ·
   full gates · browser checkpoints.
7. **Exit criteria:** owner acts on one recommendation with visible evidence;
   Product-360 composes the product's full knowledge; export round-trips;
   DoD; STOP.

### P5 — HARDWARE (implementation Phase 9; hardware-gated)
1. **Goal:** physical output: plotter (HPGL) and/or projector, behind ONE
   output interface with per-output validation rituals.
2. **Inputs:** owner hardware purchase; tightened error spec re-proven
   (ADR-E addendum 2).
3. **Outputs:** output-interface module + HPGL generator + projector view ·
   calibration rituals per output · docs.
4. **Files/modules affected:** `config/patterns_ai/**` + `compute/` renderers.
5. **Risks:** device quirks (mitigation: per-device profiles like capture);
   error spec insufficient for direct cutting (mitigation: hard gate — no
   plotter-cut before re-proven tiers).
6. **Validation steps:** plotted golden square/piece measured by tape;
   projector overlay vs cardboard.
7. **Exit criteria:** one real marker plotted/projected within spec; DoD; STOP.

### P6 — REAL ML (implementation Phase 10; probably never)
Gate memo only, per V3: consider ONLY if hundreds of (marker, outcome) pairs
exist AND deterministic ranking demonstrably fails a task. Any entry = new
owner ADR. No effort planned.

## 4. Milestone summary

M0 P0 numbers published → M1 first real yield-board row → M2 first confirmed
digitised graded set → M3 first generated-beats-manual receipt → M4 first
acted-on recommendation → M5 first in-spec plot (hardware-gated). Each
milestone = its phase's headline exit criterion; no milestone spans phases.

## 5. Project-level risk register (beyond per-phase)

| Risk | Mitigation anchor |
|---|---|
| Session/scope discipline erosion (multi-phase temptation) | owner global rules; this plan's per-phase STOP lines |
| Solo-dev bus factor on new domain (CV/nesting) | ADR-F reproducibility + docs-sync + poc/ harness as executable documentation |
| Frozen-contract drift over a long project | purity/no-network/single-writer tests run EVERY phase gate; rule 11 STOP |
| Estimate optimism | re-estimate at each phase start; ranges not dates; owner sees effort table per completion report |
| Dummy-vs-real data confusion | DEV-marking discipline (V1 precedent) + teardown-only-by-owner |

## 6. Certification

Cross-checked against the four governing documents —
see [IMPLEMENTATION_MASTER_PLAN_CERTIFICATION.md](IMPLEMENTATION_MASTER_PLAN_CERTIFICATION.md).

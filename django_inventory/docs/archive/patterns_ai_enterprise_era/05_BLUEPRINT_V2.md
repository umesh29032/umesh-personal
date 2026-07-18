# AI Pattern Intelligence — Platform Blueprint V2 (2026-07-06)

> **Status: ⚠️ SUPERSEDED → [06_BLUEPRINT_V3_FINAL.md](06_BLUEPRINT_V3_FINAL.md) (V3 FINAL = V2 + F1-F8 permanence completions; V2's §4-§14 remain design-of-record text where 06 §6 says so). NOTHING implemented.**
> Produced from the owner-approved [04_KICKOFF_HOSTILE_REVIEW.md](04_KICKOFF_HOSTILE_REVIEW.md)
> plus the owner's seven V2 principles (2026-07-06). Until the owner approves
> this document, [03_PLATFORM_BLUEPRINT.md](03_PLATFORM_BLUEPRINT.md) remains
> the design of record; on approval, 03 is marked superseded and V2 becomes the
> contract for the ADR pack + P0. All V1 owner locks carry forward unchanged:
> honest-AI vocabulary · permanence/versioned-forever · open-source, offline,
> no paid APIs, repo-reproducible · human confirmation = the source of truth ·
> Manufacturing V1 frozen contracts inviolable.

---

## 0. The mission, restated as three eras (the V2 spine)

**Era 1 — DIGITAL MEMORY (the new foundation).** Before optimizing anything,
the platform becomes the factory's permanent memory: every product's pattern
knowledge, every marker that is actually cut — *including the master's manual
chalk markers* — every width, ratio, repeat, and yield. Value from week one;
zero computer vision required; the master's knowledge becomes the founding
asset, not bootstrap data.

**Era 2 — INTELLIGENT ASSISTANT.** On top of recorded memory: capture/digitise
patterns, compare markers with evidence, recommend with confidence scores,
suggest pieces for new products. Deterministic analytics; honest vocabulary.

**Era 3 — MARKER GENERATOR.** Nesting-engine generation that must **beat the
recorded manual baseline with measurable evidence** before it earns trust.
Generation is the last era, not the first — it competes against memory.

Every design decision below is judged by the owner's V2 priority order:
**simplicity · long-term maintainability · knowledge preservation** over
technical elegance.

## 1. CHANGELOG — exactly what changed from V1, and why

| # | Change | Was (V1) | Now (V2) | Why |
|---|---|---|---|---|
| C1 | **Three-era mission spine (§0)** | roadmap framed around capture→generate | memory → assistant → generator | Owner principle 6; V1 optimized before it measured (review CB-1) |
| C2 | **Manual markers = first-class, FOREVER** | library admitted only generated/imported markers | `Marker.origin ∈ {manual_photo, generated, imported, adda_temporary}`; a manual marker = photo of the chalked lay + human-entered width/ratio/repeats; permanent citizens, never retired as "bootstrap" | CB-1 + owner principle 2; the factory's real markers had no home; Gate 2 compared AI to a memory |
| C3 | **Roadmap resequenced: measure before optimize (§11)** | P1 library+DXF → P2 capture → P3 generate → P4 feedback | **P1 = library-lite + manual marker registry + usage/outcomes + YIELD BOARD** → P2 capture → P3 generate → P4 deep analytics | CB-1; value in week one; every later phase inherits real baselines |
| C4 | **Baseline-competition rule** | Gate 2 = side-by-side cut only | every generated marker is benchmarked against the product's recorded manual baseline (`benchmarked_against` lineage FK + evidence card); side-by-side lay kept for the FIRST product as trust theatre | Owner principle 3; evidence over memory |
| C5 | **Marker confidence score (§5 — NEW section)** | no trust signal beyond status | deterministic, transparent, versioned score + tier (PROVEN/TRUSTED/TRIAL/UNVERIFIED) derived from usage count, realized utilization consistency, validation receipts, geometry trust, recency, origin | Owner principle 4; "how trustworthy is this marker" answered at a glance, honestly |
| C6 | **D11 promotion mechanics designed (§4/§8)** | temporary Adda markers impossible under V1's own trust rule | `origin=adda_temporary` markers MAY pin **draft** geometry (UNVERIFIED badge, excluded from recommendations); **promotion = confirming those geometry rows + one status flip + audit event** — no copying, immutability intact | CB-2; owner vision (Adda = consumer; promotion after human approval) |
| C7 | **`MarkerUsage.repeats`** | plies + width only | + integer `repeats` (markers repeat along the lay) | CB-3; outcome math was silently wrong without it |
| C8 | **`SuggestionEvent` entity** | suggestions were a mechanism, never stored | product-homed, append-only suggestion artifacts (template+version, payload, accepted/rejected/modified, by/at) | CB-4; owner's product-asset list includes AI Suggestions |
| C9 | **PatternSetRevision demoted to OPTIONAL label** | hard snapshot entity markers must pin | markers pin `PieceSizeGeometry` rows directly (PROTECT, as before); revision = optional named grouping for owner communication | Review §8; hard revisions = ceremony on every re-confirm; simplicity principle |
| C10 | **`width_band` stored integer bucket on Marker** | width matching computed at query time | `usable_width_band = floor(mm/10)` written at creation, indexed | Hottest future query (candidate markers for THIS Adda) stays cheap at thousands of markers |
| C11 | **`grade_rule` optional JSON slot on PieceSizeGeometry** | independent per-size polygons only | slot for per-point grade deltas (spec in ADR-C; empty in year 1; engine = future) | Year-3 "add size XXL = full recapture" wall; brand-DXF grade fidelity; absent-vs-empty rule |
| C12 | **Geometry numbers = INTEGER micrometers** | "mm floats" | all stored coordinates/dimensions = integer µm (display converts); ONE quantization helper from line one (I-4) | Float drift + cross-language JSON round-trip risk inside a permanent asset |
| C13 | **`CalibrationMat` + capture-device registry** | per-photo mat self-check only | physical-asset rows: mat_id, commissioning tape-measured control distances, status, recheck log; every CaptureAsset FKs its mat + device profile | Metrology chain of custody ("recall every capture made on the stretched mat"); free per-site anchor for multi-factory later |
| C14 | **Globally-unique human references** | unspecified | `MRK-000001`-style references via the shared `next_reference` discipline | Zero cost now; multi-factory renumbering never happens |
| C15 | **Two-tier recommendation honesty + deterministic TRIAL rule (§9)** | n≥3 per (product·fabric·width·ratio) cell or silence | cell-level ranking when n≥3; else product-level "vs manual baseline average" with small-sample badge; exploration = one rule: predicted beats incumbent's realized average by > tolerance ⇒ TRIAL badge on next matching Adda | n≥3-per-cell stays unmet for YEARS at this volume — the assistant would look dead; honesty preserved via badges |
| C16 | **Reproducibility honesty** | "every approved marker reproducible (seed+engine pinned)" | stored placements ARE the artifact: re-RENDER always reproducible; re-RUN best-effort (seed+engine pinned for audit) | GA nesting won't replay bit-for-bit years later; don't promise what year-2 disproves |
| C17 | **D3 (GSM) pulled to P1** | P4 measurement foundation | one additive intake field (owner mini-ADR) at P1 → yield board speaks **₹/garment** from the start | The owner thinks in ₹; the memory era should too |
| C18 | **DXF-AAMA import slides P1 → P2/P3** | P1 deliverable | import lands with capture era (unless a brand file arrives sooner — then it jumps the queue) | Heavy parser before any factory value contradicted measure-first |
| C19 | **Digitisation triage guidance** | absent | written rule: digitise on recurring volume; the yield board itself identifies where marker waste pays for capture effort | 30-40 captures/product is real cost; owner decides where it's worth it |
| C20 | **Marker biography (traceability spine)** | events existed separately | every marker has a timeline view: created→benchmarked→validated→used→outcomes→superseded/promoted; lineage FKs (`supersedes`, `benchmarked_against`) | Owner principle 5: every improvement traceable; no knowledge ever lost |

Unchanged from V1 (survived the hostile review): product-centric ownership ·
per-size geometry with provenance + trust grades · fabric groups · tubular/
on-fold semantics · PROTECT-pinned placements (never loose JSON) ·
MarkerUsage as the feedback join · honest-AI glossary · capture pipeline core
(mat, ladder, 3-step annotator, numeric acceptance) · frozen-architecture
compliance contract · trust gates · media/vendoring/async ADR scopes ·
single-writer services · mm→µm canonical units at the edges · dummy-data plan.

## 2. Honest mechanism glossary (V1 glossary + V2 rows)

V1 rows stand (template library · classical-CV-first capture · ChArUco
measurement · strategy-based nesting · "remembers and compares" analytics).
V2 adds:

| Phrase | Actual mechanism |
|---|---|
| "Marker confidence score" | Deterministic formula over stored facts (usage count, realized-vs-predicted utilization mean & spread, validation receipts, geometry trust grade, recency, origin), formula version stamped; components always visible ("why this score"). No ML. |
| "The factory's digital memory" | Append-only registry of ALL markers incl. manual chalk layouts (photo + width/ratio/repeats) + their usage and yields. Data entry, not intelligence — and the most valuable table in the module. |
| "The AI beat the master's marker" | Evidence card: recorded manual baseline (n lays, avg meters/garment) vs generated marker's realized outcomes on the same product/width-band — never a claim without the numbers behind it. |

## 3. Concept model (owner language, V2)

```
Product ("T-SHIRT")                                ← permanent home of EVERYTHING
 ├─ Pattern Library (per fabric group: BODY, RIB…)
 │   ├─ Piece → Version(s) → Geometry per size (provenance + trust grade)
 │   └─ optional named Pattern Set labels (grouping, not machinery)
 ├─ Marker Library (ALL markers, forever)
 │   ├─ MANUAL  M-chalk-01: photo · 17″ tube · S2:M2:L1 · repeats 3 ── the baseline
 │   ├─ GENERATED M2: strategy=sectioned · benchmarked_against M-chalk-01
 │   ├─ IMPORTED / ADDA-TEMPORARY (draft-pinned, UNVERIFIED until promoted)
 │   └─ each with: confidence tier · validation receipts · biography timeline
 ├─ Usage history: "Adda X cut with M · 30 plies · 3 repeats · width 432 mm"
 ├─ Outcomes: predicted vs realized · leftover · quality flags → YIELD BOARD
 └─ Suggestions: stored SuggestionEvents (template used, accepted/rejected)
```

The **Adda is a consumer**: it picks from the product's library (or records the
manual layout actually used, or — when product data is insufficient — generates
an `adda_temporary` marker that can be **promoted** into the library after
human approval).

## 4. Data model (app `patterns_ai` — FKs INTO production only)

Changes from V1 marked **[V2]**. Single-writer services unchanged:
`capture_service` · `pattern_geometry_service` · `marker_service` ·
`marker_feedback_service` (+ **[V2]** every creation path — UI, import,
backfill — goes through them; raw-ORM writes are a review-reject, per I-1).

| Entity | Grain + load-bearing fields | Notes |
|---|---|---|
| `GarmentTemplate` (+pieces) | garment_type → expected pieces | unchanged |
| **[V2] `SuggestionEvent`** | FK Product · template+version · payload JSON · outcome accepted/rejected/modified · by/at | C8; append-only |
| `PatternPiece` | UNIQUE(product, pattern); FK Product + ProductPattern (name-link) + optional 1:1 ProductPatternAssignment; fabric_group; pair; on_fold | unchanged |
| `CaptureAsset` | immutable original + checksum + EXIF + calibration provenance + pipeline_version; **[V2]** FK `CalibrationMat` + device profile | C13 |
| **[V2] `CalibrationMat`** | mat_id · commissioning control-distance measurements · status active/retired · recheck log (append-only) | C13; physical-asset registry, machines-app pattern |
| `PatternPieceVersion` | draft→confirmed (freeze via service); superseded_by; voided_at; confirmed_by/at | unchanged |
| `PieceSizeGeometry` | FK version + ProductSize (PROTECT); outline + features (notches/drills/internal lines) + grain + fold-edge + seam-allowance flag; provenance enum; trust grade; stored area; **[V2]** coordinates in INTEGER µm (C12); **[V2]** optional `grade_rule` JSON slot (C11) | marker generation still restricted to MEASURED/PHOTO-CALIBRATED — EXCEPT the D11 carve-out below |
| `PatternSetLabel` **[V2 renamed/demoted]** | optional named grouping {piece-versions} per (product, fabric_group) | C9; communication aid, no FK from Marker required |
| `MarkerRequest` | human-confirmed input snapshot (usable_width_mm→µm, construction, allowances, ratio INTEGER counts, constraints); **[V2]** nullable FK Adda (temporary-generation context) | C6 |
| `MarkerRun` | async job: engine+commit+seed+params, progress, cancel | unchanged (ADR-B) |
| `Marker` | immutable; **[V2]** `reference` MRK-global (C14) · **[V2]** `origin` {manual_photo, generated, imported, adda_temporary} (C2/C6) · **[V2]** nullable FK Adda (temporary context) · **[V2]** `usable_width_band` int (C10) · **[V2]** lineage: `supersedes` + `benchmarked_against` (C4/C20) · strategy enum (generated only) · three honest numbers · status: candidate → validated → **[V2]** promoted (from temporary) → superseded; staleness derived | manual markers: placements optional — photo + declared width/ratio/repeats is a complete, permanent record (C2) |
| `MarkerPlacement` | FK marker CASCADE + FK PieceSizeGeometry PROTECT + x/y(µm)/rotation/flip + piece label | unchanged; **[V2]** temporary markers may pin DRAFT geometry (D11 carve-out — badge UNVERIFIED, excluded from recommendations until promotion confirms the pins) |
| `MarkerValidationEvent` | append-only Gate 1/2/3 receipts | unchanged |
| `MarkerUsage` | FK Marker + FK Adda + optional stage-record; plies; **[V2] repeats** (C7); measured usable width; confirmed_by/at; voided_at | works for manual AND generated markers from P1 |
| `MarkerOutcome` | derived per usage: predicted vs realized utilization; leftover; **[V2]** ₹/garment when GSM exists (C17); data-quality flags (honest-NULL) | feeds §5 confidence + §9 yield board |

**Audit spine (C20):** every mutation above is either append-only or a
service-audited status transition; the "marker biography" is a read-side
timeline over MarkerRun/ValidationEvent/Usage/Outcome/promotion/supersession —
no new write machinery.

## 5. Marker confidence score (NEW — owner principle 4)

Deterministic, transparent, versioned. **Never a black box.**

- **Inputs (all stored facts):** usages `n` and total garments cut · realized
  utilization mean and spread vs predicted · validation receipts (Gates 1-3) ·
  geometry trust grades of pinned pieces · days since last outcome · origin.
- **Tiers (what the owner sees first):**
  **PROVEN** (n ≥ 5, consistent realized yield) · **TRUSTED** (n ≥ 3) ·
  **TRIAL** (new or n < 3; incl. every fresh generated marker) ·
  **UNVERIFIED** (adda_temporary / draft-pinned).
- A 0–100 score refines ordering *within* tiers; `confidence_formula_version`
  is stamped so historical scores remain explainable after any formula change.
- **"Why" chips are mandatory UI**: `used 7× · avg 84.1% (±1.2) · Gate-2 ✓ ·
  last used 12d ago`. The score is never shown without its ingredients.
- Manual markers earn confidence exactly the same way — a chalk marker with
  30 recorded lays outranks a fresh generated marker, **as it should**.
- Computed at read time from facts (nothing stale stored except an optional
  cache); pure function in `marker_feedback_service` behind the ONE
  quantization helper (I-4).

## 6. Capture pipeline

Unchanged from V1 (mat + station + quality gates + segmentation ladder +
3-step annotator + numeric tape acceptance + phone-capture/desktop-edit split +
batch sessions + ≤90 s/piece gate) with two V2 additions: **CalibrationMat
commissioning** (tape-measure control distances recorded before first use;
periodic recheck appends to its log; every capture FKs the mat) and **device
capture profiles** (phone model + app mode recorded per capture). Physical
master still wins; recapture triggers unchanged.

## 7. Frozen-architecture compliance contract

All eight V1 clauses carry forward verbatim (proposals-only, link-out UI seam +
runtime purity test, FK direction, no money + honest-NULL ₹ only after GSM,
RBAC + SidebarItemRule, media tree + ADR-G, compute isolation + ADR-F,
PDD amendment gate). V2 adds nothing that touches production tables — C17
(GSM) and any `fabric_construction` field remain **owner-approved additive
mini-ADRs on the manufacturing side**, exactly as the freeze demands.

## 8. Trust & adoption ladder (V2)

- **The library opens with the master's markers** — photographing tomorrow's
  chalk layout IS the first library entry. Nothing to distrust: it's his own
  work, now remembered.
- Gate 1 (overlay print) unchanged, applies from P2 (capture era).
- **Gate 2 rewritten (C4):** a generated marker must show its evidence card —
  recorded manual baseline vs its own predicted (then realized) numbers.
  The side-by-side sacrificial lay is kept ONCE, for the first product, as
  trust theatre; after that, evidence replaces ceremony.
- Gate 3 (first-ply check) unchanged.
- **Marker room lists concrete options (I-3), now including the manual
  baseline**: "Master's layout M-chalk-01 — PROVEN · used 12× · 3.42 m/100pc"
  beside "Generated M7 — TRIAL · predicted 3.29 m/100pc". Honest and
  disarming: the AI asks to be tried, never pretends to be trusted.
- Promotion moment (D11/C6): confirm geometry → promote marker → full history
  travels with it into the product library.
- v1 output = instruction diagram + short-marker ritual print — unchanged.

## 9. Feedback: the yield board first, ranking second

- **YIELD BOARD (P1, the era-1 deliverable):** per product/width-band/marker —
  lays, plies×repeats, meters consumed, garments out, meters/garment (and
  ₹/garment once GSM lands), leftover; manual and generated markers side by
  side. Pure arithmetic over MarkerUsage + LayeringRecord + APSCPB +
  RemainingCloth — all of which already exist in Manufacturing V1.
- **Two-tier honesty (C15):** cell-level ranking when n≥3 in the exact
  (product, fabric_group, width_band, ratio) cell; otherwise product-level
  comparison vs the manual baseline average, always badged with its n.
- **Deterministic exploration (C15):** predicted beats incumbent's realized
  average by more than the stated tolerance ⇒ TRIAL badge on the next matching
  Adda; no badge otherwise. One sentence, no ML.
- Confounder flags, honest-NULL, consistency guard (pieces×plies×repeats vs
  garment counts) — carried from V1, now with repeats correct (C7).

## 10. Risk register (V2 deltas only — V1 table still applies)

| Risk | V2 answer |
|---|---|
| Yield board shows embarrassing waste numbers on day one | That IS the product working; frame as baseline, not blame (owner-facing copy rule) |
| Manual-marker entry becomes sloppy (wrong widths/repeats) | entry form mirrors packing's blank-row honesty; usage confirms at cut time; outcomes expose nonsense quickly |
| Confidence score gamed by re-generating markers to reset history | lineage (`supersedes`) carries history forward in the biography; tier requires OUTCOMES, not freshness |
| Temporary markers linger unpromoted, cluttering the library | UNVERIFIED tier + Adda-scoped visibility + periodic "promote or retire" review list |
| PatternSetLabel optionality lets mixed-version markers confuse | marker biography names exact pinned versions; staleness badge derived as before |

## 11. Roadmap V2 (resequenced — every phase ships factory value)

| Phase | Deliverable | Gate |
|---|---|---|
| **ADR pack** | A–H drafted against V2 + D1–D11 rulings + PDD amendment | owner signs |
| **P0 Feasibility** | engine bake-off (unchanged harness incl. >1 m, curved, on-fold tubular) + metrology POC + **yield-board data walk on 3-PATTI-016's real numbers (manual marker + usage + outcome, on paper)** | bake-off numbers published; walk reproduces ₹633-journey fabric math by hand |
| **P1 DIGITAL MEMORY** | `patterns_ai` app: Marker (all origins) + MarkerUsage(+repeats) + MarkerOutcome + yield board + manual-marker entry (photo + width/ratio/repeats) + SuggestionEvent + CalibrationMat registry skeleton + GSM mini-ADR (C17) + geometry spec doc (ADR-C, incl. µm + grade_rule slot) | **the owner reads a real yield board for one product within days of P1 start**; every marker cut that week is remembered |
| **P2 CAPTURE** | mat + station + wizard + ladder + annotator + trust grades + Gate-1 prints + DXF-AAMA import (C18) | master digitises a graded set unaided; ≤90 s/piece on the factory table |
| **P3 GENERATION** | async worker (ADR-B) + strategy alternatives + evidence cards vs baseline (C4) + marker room + instruction diagram + ritual print + D11 temporary/promotion flow | a generated marker BEATS the recorded manual baseline on ≥1 real product, receipts attached |
| **P4 ASSISTANT DEPTH** | confidence scores live (§5) + two-tier recommendations + measured lay extras (end-loss/splice — additive mini-ADRs) + DXF export | recommendations render with honest badges; owner acts on one |
| **P5 HARDWARE** | plotter/projector behind one output interface; tightened error spec re-proven | when hardware exists |
| **P6 (probably never)** | real ML | written gate unchanged |

## 12. Owner decisions (updated; PROPOSED finals for the ADR step)

| # | Decision | V2 proposed final |
|---|---|---|
| D1 | Pattern Sets semantics | revisions-over-time as optional LABELS (C9); fit variants = separate labelled dimension if ever real |
| D2 | `fabric_construction` on ClothType | YES — additive mini-ADR at P1 (with GSM, same migration) |
| D3 | GSM capture | **pulled to P1** (C17), additive mini-ADR, owner enters per cloth type |
| D4 | Who digitises/approves | capture = cutting_master skill; approve = cutting_master; activate/promote = manager/owner; ≥2 trained; confirm names at P2 |
| D5 | v1 output | instruction diagram YES; plotter re-cost after P4 |
| D6 | Short-marker print path | office printer + forced 100 mm ritual |
| D7 | Mat + phone-mount purchase | YES at P2 start (commissioning per C13) |
| D8 | ops-master §11 wording | amend to proposals-only on V2 approval |
| D9 | Scaled sizes | draft-only until tape-confirmed (unchanged) |
| D10 | Local LLM | skip v1; documented slot |
| D11 | Adda-temporary markers | mechanics per C6: draft-pin carve-out + UNVERIFIED tier + promotion = confirm pins + status flip + audit; excluded from recommendations until promoted |

## 13. Dummy-data plan (V2)

As V1, plus: **one manual marker recorded against 3-PATTI-016's real journey**
(photo placeholder, 37″ tube, 30 plies, declared repeats) with its true
usage/outcome derived from the settled data — the yield board's first real row
and the worked example for §9's math (I-2).

## 14. Idea-register disposition (I-1..I-4 folded in)

I-1 single-writer-only creation → §4 services clause. I-2 3-PATTI-016 reference
world → §13 + P0 gate. I-3 concrete-options UI law → §8 marker room. I-4 one
quantization home → §5 + C12 (µm integers make its domain exact).

---

*Stop point per owner instruction: Blueprint V2 only. ADR drafting and all
implementation wait for owner review of this document.*

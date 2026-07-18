---
id: docs-ai-pattern-intelligence-manufacturing-integration-review
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# MANUFACTURING INTEGRATION REVIEW — the boundary, field by field
(2026-07-10 · REVIEW, not redesign — the architecture is FROZEN ·
reference = the owner's REAL workflow, Nickar throughout · evidence =
the shipped code M1–M4.5 + the ADR-H wall proofs)

## §0 · THE CONTRACT IN ONE LINE

**Pattern Intelligence CREATES manufacturing assets. ERP CONSUMES
manufacturing assets.** The wall: production never imports patterns_ai
(source-scanned by test_purity + import-linter, every battery run).
Legal crossings, all four already built: ① provider REGISTRIES
(patterns_ai registers callables in apps.ready(); production calls
them wrapped in try/except and receives PLAIN DICTS) ② URL-name
reverses (navigation hand-offs) ③ patterns_ai FKs INTO production
(read-down, the allowed direction) ④ settings flags. Nothing else
crosses. M6 adds one registry of the same species (§4).

## §1 · THE NICKAR JOURNEY — every transition audited

```
Nickar (Product Definition — data, never engine vocabulary)
  │  Blueprint: Body ×2 pair+fold · Panel ×2 pair (other fabric) ·
  │  Pocket ×2 — PATTERN CAPABILITIES, owner: Pattern Intelligence
  ▼
Body/Back marker (body group) · Panel marker (other group)
  │  LAW 12 forces the separate Panel marker — the factory's rule,
  │  zero garment code
  ▼
Approved Layout(s)  LAY-DEV-NICKAR-000001/2 — IMMUTABLE ASSETS
  │  carry the frozen Marker Plan: width(human-confirmed) · lay type ·
  │  multiplier · fold_edges · ratio · roll ref · recipe label · notes
  ▼
Marker Recipe  "Body+Pocket · double · 42″" — reusable knowledge (PI)
  ▼
── THE BOUNDARY ──  the Adda CHOOSES (ApprovedLayoutUsage, human act)
  ▼
Layering   lay_count = OPERATOR FACT (ERP truth; PI never touches
  │        plies).  M6 adds: "Recommended layer length: 440 mm — from
  │        LAY-…-000002" (ADVISORY, derived, operator free to differ)
  ▼
Cutting    suggestion = content/layer × multiplier-baked × lay_count
  │        (ADVISORY prefill) · reconciliation WARN ("your numbers
  │        stand") · Breakdown = OPERATOR FACT
  ▼
Bundles → Barcodes → Adda → Tracking → Inventory   pure ERP —
  │        Pattern Intelligence appears ONLY as traceability strings
  ▼
Costing → Settlement   MONEY — Pattern Intelligence NEVER reaches
           here (ADR-0009 cost-truth · settlement-only money · the
           Money-Write STOP rule). No layout value feeds any ledger.
```

## §2 · FIELD-BY-FIELD BOUNDARY TABLE

Legend: **F**=manufacturing fact · **A**=advisory · **D**=derived at
read (persisted nowhere) · **I**=immutable after creation.

| Field crossing → ERP | Originates | Owner / sole writer | Modifiable by | I | F/A/D | Consumed as | Persisted where | Belongs to |
|---|---|---|---|---|---|---|---|---|
| `layout_uid` (LAY-…-NNNNNN) | approval act | PI / layout_library_service | nobody | I | F (identity) | display · traceability | PI (ApprovedLayout) | PI |
| `version_no` (V1, V2…) | approval act | PI / same | nobody | I | F | human reference | PI | PI |
| layout `name` | approval form (human) | PI / same | nobody (frozen-at-approval guard) | I | F | display | PI | PI |
| layout `status` (active/superseded/archived) | approval/supersede/archive acts | PI / same | humans via the service only | state-machine | F | choose-page gating | PI | PI |
| `fabric_group` | Blueprint rule → LAW-12 save | PI / geometry+save writers | nobody post-save | I | F | one-marker-one-group; usage uniqueness | PI (+ the ONE sanctioned denorm on usage, editable=False) | PI |
| `width_mm` (usable) | Marker Plan — human-confirmed, roll-prefilled | PI / save_table_layout | nobody post-save | I | F (of the asset) | display · M6 layering context | PI (run) | PI |
| `length_mm` | THE verifier at save | PI / verifier | nobody | I | F (of the asset) | **M6: recommended layer length (A when displayed)** | PI (candidate) | PI |
| `layering_type` / `layer_multiplier` / `fold_edges` | Marker Plan | PI / save | nobody | I | F (of the asset) | content math input | PI (params) | PI |
| `ratio` (sizes × garments) | Marker Plan | PI / save | nobody | I | F (of the asset) | display; future planning | PI (params) | PI |
| `roll` ref + `recipe` label + `notes` | Marker Plan | PI / save | nobody | I | F (provenance) | display | PI (params) | PI |
| placements (+ `on_fold`, mirrored, rotation) | the operator's table session | PI / save (verbatim, verifier-checked) | nobody | I | F (the marker) | SVG/PDF/print · content derivation | PI (candidate) | PI |
| `stale` | LIVE check vs confirmed versions | PI / derived | n/a | n/a | **D + A** | choose refusal · loud badge | NOWHERE (Law 11) | PI |
| `content_by_pattern_size` | COUNT placements × multiplier (÷2 fold) | PI / provider | n/a | n/a | **D** | × lay_count → expected | NOWHERE | PI |
| usage row (Adda ↔ layout, per group) | the Adda's CHOICE (choose page, human) | PI table / layout_usage_service | void-with-reason only (F1: never reassign, never delete) | append-only | **F (the manufacturing decision)** | stage panel · suggestion source | PI (ApprovedLayoutUsage) | boundary row: PI stores it, MANUFACTURING decides it |
| `usage.stage_record` stamp (M6) | cutting completion | PI / stamp_stage_record (once-only) | nobody | I | F (traceability) | audit: which cut used which asset | PI | PI |
| **`lay_count`** | LAYERING operator | **ERP / layering service** | operator flow | per record | **F (plies truth)** | expected math ×; fabric math | ERP (LayeringRecord) | **ERP — PI never reads-modifies, only multiplies at read** |
| expected pieces | content × lay_count | derived in ERP cutting service at read | n/a | n/a | **D + A** | suggestion prefill + WARN | NOWHERE (count-hierarchy law) | derived AT the boundary, owned by neither |
| suggested breakup | expected ÷ colors | ERP derived | n/a | n/a | **D + A** | prefill only | NOWHERE | ERP |
| Breakdown / bundle counts | CUTTING operator | ERP / cutting service | operator flow | append/audited | **F** | bundles → barcodes → tracking → inventory | ERP | ERP |
| barcodes, tracking, inventory rows | ERP flows | ERP single writers | per their laws | — | F | ERP | ERP | ERP |
| costing / settlement values | ERP money writers | expense/production per ADR-0009/0011 | settlement laws | — | F | money | ERP | **ERP — NO PI field ever feeds money** |
| flags REQUIRE_APPROVED_LAYOUT · ENFORCE_LAYOUT_RECONCILIATION (M6) | settings (owner) | deployment config | owner | — | policy | ERP-side gate checks | settings | shared policy, default OFF |

**Reverse direction (ERP → PI): exactly ONE value ever crosses —
nothing.** PI never reads lay_count, breakdowns, money or worker data.
The multiplication content × lay_count happens ON THE ERP SIDE from
the provider's plies-free dict (asserted by test). That asymmetry IS
the clean contract.

## §3 · THE EIGHT PROTECTED PRINCIPLES — status against code

1. Manufacturing Knowledge Platform, not CAD — the identity is in both
   freezes + the M4 review; the Studio/DCT split enforces it. ✅
2. Engine never knows garments — the GENERICITY GUARD is a permanent
   TEST (M4), swept again after M4.5. ✅ automated forever.
3. Studio = only geometry creator — single writers + the wall; DCT
   payload is read-only facade data; manufacturing consumes approved
   layouts only. ✅ structural.
4. Approved layouts immutable — model guards (delete raises,
   status machine, frozen-at-approval), View/Duplicate/Archive only. ✅
5. Operator authority — count hierarchy + "your numbers stand" WARN +
   expected-persisted-nowhere. ✅ law in code + tests.
6. AI proposes, humans approve — extraction one-shot review · Suggest
   Better Layout = pending verdict + Accept/Keep · approval human-only.
   ✅
7. Deterministic calculations — seeded engines, rule ⑩, no ML;
   fold/multiplier math = integer arithmetic on rows. ✅
8. Genericity Gate on every future feature — the guard test + the M4
   plan's gate section make it procedural. ✅

## §4 · M6 BOUNDARY ADDITIONS (reviewed BEFORE build — no new species)

- **Layering recommendation**: a second registry of the EXISTING
  species (`LAYOUT_PROVIDER` on the layering stage handler);
  patterns_ai registers a read-only builder returning
  {group → {uid, length_mm, layering_type}}; production renders it
  wrapped (provider failure → section absent). ADVISORY text; the
  operator's layer length stays the fact.
- **Stage-record stamp**: a listener REGISTRY on the ERP cutting
  service (`CUTTING_COMPLETE_LISTENERS`, same inversion as
  ARCHIVE_VALIDATORS); patterns_ai registers the stamper; the stamp is
  a PI-owned traceability fact, once-only, wrapped so a failure never
  breaks cutting.
- **Gates**: settings flags, default OFF (ship → soak → owner flips).
  REQUIRE = cutting completion refuses without an ACTIVE usage (names
  the choose page). ENFORCE = completion refuses when |operator −
  expected| > LAYOUT_RECONCILIATION_TOLERANCE (names both numbers).
  Both checks live ERP-SIDE reading the provider dict — no new
  crossing.

## §5 · SCALE STATEMENT (platform, not single-factory software)

The decisions that already carry hundreds of factories / thousands of
products: derive-at-read everywhere (nothing cached to migrate) ·
single writers (auditable at any volume) · registries over imports
(new consumers bolt on) · uid + contract-version stamps (license-grade
identity, ADR-0010) · capabilities/recipes/lay data as ROWS (new
manufacturing styles = configuration) · deterministic engines (results
reproducible on any deployment) · flags-off shipping (per-factory
rollout). Multi-tenancy = the known future step — nothing above needs
rework for it, and nothing below M6 may assume a single factory.

**Verdict: the boundary is clean. Zero responsibility leaks found in
either direction. One asymmetry to preserve forever: plies (lay_count)
never enter Pattern Intelligence; content never persists in ERP.
M6 may proceed.**

> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M4 PRE-PLANNING REVIEW — the Generic Manufacturing Planner
(2026-07-10 · ARCHITECTURE REVIEW ONLY, no code · the owner's final
alignment before M4: "the engine should never know what a Nickar is" ·
companion to MANUFACTURING_GEOMETRY_ENGINE_MASTER_DESIGN.md · evidence
= main-thread code sweeps this session, commands + hits recorded)

## §0 · FRAMING ACCEPTED + THE VERDICT

**"Manufacturing Knowledge Platform" — accepted as the platform's
identity.** Garments are DATA (Product Definitions); the engine is
physics + rules. And the audit result: **the codebase already honors
this — completely.** The engine does not know what a Nickar is. It
does not know what a T-Shirt is. It never has.

## §1 · GENERICITY AUDIT (method + results)

Swept every non-test engine/planner path (patterns_ai python+templates,
compute runtime, production stage handlers) for:
(a) garment names (nickar/t-shirt/hoodie/polo/cargo/track-pant/
uniform/patti/tee) · (b) product-identity branching
(`product.code ==` / `product.name ==`) · (c) fabric-group VALUE
branching (`fabric_group == '...'`) · (d) rule-value handling.

| Check | Result |
|---|---|
| Garment names in patterns_ai non-test code | **2 hits, both false positives**: `suggestions.py:23` help-text EXAMPLE string (`'garment_template:tshirt@r1'`) in the frozen research-era SuggestionEvent model — documentation, not logic; its migration echo. |
| Garment names in compute runtime | **1 hit, false positive**: `nest.py` — `str.lower()` + a "lower = more compact" comment. No garment knowledge in the engine, ever. |
| Product-identity branching anywhere | **ZERO.** No service, view, engine or template branches on product code/name. |
| Fabric-group value branching | **ZERO.** LAW 12 (markers never mix groups) compares VALUES mechanically; no code assigns meaning to 'collar' vs 'body'. |
| Rule consumption | Engine consumes `allow_180`/`allow_mirror`/`spacing`/polygons per piece (nest.py contract line 16); DCT consumes `grain_rule`→rotation-set lookup table, `is_pair`→mirror gate. Pure data. |
| Production stage handlers | `base` + `generic_stage` + registry fallback — **config-only operations already PROVEN**: the T-Shirt 16-op and Lower 13-op flows were built as pure configuration (Phase-3 config pass, gate 885; Operation Independence Audit 8/9 PASS: rename/reorder/rate/activate all safe). |
| Docstring examples ("e.g. T-Shirt") | comments only (`cutting_pattern/service.py:8`). |

## §2 · THE OWNER'S FIVE QUESTIONS — ANSWERED

**1. Does any planned M4 component contain product-specific logic?**
No. Every M4 input is data: Marker Plan (sizes × garments-per-size =
the order), Import Queue (Blueprint `pieces_count` × plan), size
colors (palette cycled by SIZE-CHART ORDER INDEX — binding design
note, §5-F4: never a name lookup), roll/layering inputs (G2/G3 =
rows), physics/engine (rules only).

**2. Can every garment be represented by Product + Piece Definitions
without engine changes?** Yes — and it is already PROVEN twice: the
platform side (this sweep: pieces + rules + geometry are the only
vocabulary) and the ERP side (T-Shirt + Lower real flows = config
only, zero handler code). A Nickar = Product `NICKAR` + Blueprint
{Body ×2 pair, Panel ×2 pair, Pocket ×2} + rules + geometry per size.
Nothing else.

**3. Has "Nickar" (or any garment) leaked into architecture?** No.
Garment names exist ONLY in test/DEV data (golden T-SHIRT, 3-PATTI,
DEV-*) and two cosmetic doc-strings — the correct places.

**4. Can the planner operate only on Products·Pieces·Rules·Rolls·
Layering·Geometry?** Yes — that is exactly its designed I/O (§3). It
has no other vocabulary available to it.

**5. New garment tomorrow (Shirt/Polo/Hoodie/Cargo/Uniform…): new code
or new data?** **New DATA only**: ① Product + sizes ② Blueprint pieces
+ rules ③ geometry per size (Studio) ④ stage flow + rates (ERP config,
proven config-only) ⑤ compose + approve layouts. **Zero planner/engine
code.** No area requiring code changes was found.

## §3 · GENERIC MANUFACTURING PLANNER — the design (M4's identity)

The planner = a PURE FUNCTION over factory data. It never learns
garment names; it consumes definitions and emits a manufacturing
asset.

```
INPUT (all rows/config, zero code per garment)
  Product Definition   product + sizes (data)
  Piece Library        confirmed geometry per piece×size (the truth)
  Manufacturing Rules  count · pair/mirror · grain/rotation · fold ·
                       seam · notches · fabric group · future rules
  Roll                 usable width (human-confirmed) + metadata (G4:
                       stretch · nap · selvedge)
  Layering Type        single / double / tubular (G3)
  Order Quantity       Marker Plan: sizes × garments-per-size
        │
  MARKER PLAN (session opener, M4) → IMPORT QUEUE (required/imported/
  remaining, size-colored by INDEX) → ARRANGE (physics: rules-gated)
  → AI OPTIMIZE (proposal only) → SAVE → APPROVE
        ▼
OUTPUT (the manufacturing asset + derived advisories)
  Marker Layout        ApprovedLayout (uid · immutable · versioned)
  Piece Placement      stored placements (mirror/rotation recorded)
  Fold Placement       G1 (M4.5)
  Piece Counts         marker content — derive-at-read
  Bundle Information   ADVISORY derivation: content × layer-multiplier
                       × lay_count → suggested bundle breakdown (count
                       hierarchy law: operator numbers always stand;
                       persisted nowhere; NOT a new writer)
  Utilization / Waste  layoutMetrics + engine buckets (exists)
  Production stats     length · layer math → layering suggestion (M6)
```
Laws binding it: single writers · derive-at-read · advisory-never-
blocks · settlement-only money · ADR-H wall (roll/layering data cross
the wall as read-only provider data, never imports) · deterministic
core, AI = proposals.

## §4 · UPDATED M4 PLAN (scope, confirmed generic)

**M4 = Manufacturing Planner v1:**
1. **Marker Plan v2** — fabric group (LAW 12) · roll picker →
   usable width (human-confirmable, the legacy Marker's discipline) ·
   layering type (G3) · sizes × garments-per-size.
2. **Import Queue** — Blueprint-driven required/imported/remaining ·
   optional opt-in · over-import refused · per-size colors (index-
   cycled).
3. **Double-lay math (G3)** — layer-multiplier recorded ON the layout
   at save; 8C expected-math consumes it; pairs place once on double
   lay.
4. **Roll metadata (G4)** — additive raw_materials fields
   (usable_width_mm · stretch · nap one-way · selvedge note) + its
   docs-sync.
5. **Nap constraint (G5)** — one-way lay ⇒ rotation sets narrowed
   (lay-level override on the existing grain machinery).
6. **DCT JS → static file** (§18-f) + **§18-d retirements** (generate
   tool, ★, Marker research out of navigation).
**M4.5 = Fold placement (G1)** — payload `fold_edge` (reserved slot,
conscious adr-c.3 if payload changes) + DCT physics + engine + the
readiness law stops blocking on_fold. Own plan, own battery.

Every item consumes rules/rows; none knows a garment. M4 planning doc
will carry a **genericity gate**: each component states its inputs as
data or it doesn't ship.

## §5 · REMAINING PRODUCT-SPECIFIC ASSUMPTIONS (the honest list)

| # | Finding | Verdict + action |
|---|---|---|
| F1 | `FabricGroup` = closed enum (BODY/RIB/COLLAR/TRIM/OTHER) — knit-leaning VOCABULARY | Mechanically generic (zero value-branching, verified). Coarse fabric classes cover Nickar (panel/pocket → body/other). KEEP; promote to a data-driven master only on real evidence — flagged, not blocking. |
| F2 | `suggestions.py` help-text example 'tshirt' | Frozen research-era model, cosmetic. No action. |
| F3 | Docstring examples ("e.g. T-Shirt") | Comments. No action. |
| F4 | UI freeze names the size palette "S blue · M green…" | BINDING M4 NOTE: implement as palette CYCLED BY SIZE-CHART ORDER, never name-keyed — any size chart (28/30/32… or FREE) colors correctly. |
| F5 | Golden T-SHIRT · 3-PATTI · DEV-* data | Test/DEV data — the correct home for garment names. |
| F6 | `universal` size code (reserved word) | System mechanism, not garment knowledge. Fine. |

## §6 · CONFIRMATION

**The engine is completely data-driven.** New garment = new Product
Definition + Piece Definitions + geometry + ERP config. Zero engine
code. Evidence: this sweep (zero identity/meaning branching) + the
Phase-3 config-only proof (two full real garments built without
touching a handler) + the Operation Independence Audit.

**STOPPED — no code. On your approval of this review + §4 scope, M4
planning (the milestone plan document) begins under the standard
discipline.**

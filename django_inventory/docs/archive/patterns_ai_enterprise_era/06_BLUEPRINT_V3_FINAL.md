# AI Pattern Intelligence — BLUEPRINT V3 (FINAL) — 2026-07-06

> **Status: 🔒 FINAL ARCHITECTURE — certified at the last pre-implementation
> checkpoint. NOTHING implemented. On owner sign-off this document supersedes
> [03](03_PLATFORM_BLUEPRINT.md) and [05](05_BLUEPRINT_V2.md) and becomes the
> single design of record for the ADR pack (A–H) and P0.**
>
> **Certification statement: after three review passes (7-lens adversarial →
> owner-lens hostile kickoff review → this 10-year permanence review), NO
> FURTHER ARCHITECTURAL REDESIGN IS RECOMMENDED BEFORE IMPLEMENTATION.**
> Remaining unknowns are empirical (P0 bake-off numbers, metrology error tiers),
> not architectural. Change control after sign-off: project ADRs.
>
> Carried locks: honest-AI vocabulary · permanence/versioned-forever ·
> open-source, offline, no paid APIs, repo-reproducible · human confirmation =
> source of truth · Manufacturing V1 frozen contracts · owner's V2 principles
> (product = home of everything · manual markers first-class forever ·
> generated must beat manual baselines with evidence · confidence from real
> history · complete traceability · memory→assistant→generator ·
> simplicity/maintainability/knowledge-preservation over elegance).

---

## 0. The ten-year review — verdicts on the owner's six challenges

**Q1 — Should the Product evolve into the complete manufacturing knowledge
graph, not just a pattern/marker library? YES — as a stance, not machinery.**
The knowledge graph ALREADY EXISTS as the relational schema: every asset in
this module is reachable from Product by FK chain, and every event is
append-only. V3 therefore locks the principle — *"the Product is the root of
the manufacturing knowledge graph; the graph IS the relational schema plus its
append-only events"* — and explicitly REJECTS any graph database, generic
knowledge-node abstraction, or parallel store as over-engineering that would
betray the simplicity principle. What gets built is read-side only: a
**Product-360 knowledge view** (P4) composing patterns, markers, yields,
suggestions, and decisions for one product — the A360 pattern applied to
knowledge. Manufacturing V1's own quality/ops telemetry (G/A/M/D × op ×
machine, already captured) joins the same view later as read-only surfaces
(documented slot, ops-master §11 — never a write path from this module).

**Q2 — Should every important business decision be an immutable knowledge
asset? YES — and V2 was incomplete.** V2 stored approvals, validations,
promotions, suggestions, and usage — but REJECTIONS and OVERRIDES vanished
(a rejected marker candidate or rejected capture carried no reason; a
constraint override wasn't an event). V3 completes the decision spine (F2):
`rejected(reason)` becomes a terminal state on both state machines; every
negative or override transition REQUIRES actor + timestamp + reason,
service-enforced; typed event tables are kept (no generic content-type event
table — weak FKs age badly); the **biography** is a read-side union. Ten years
from now, "why did we reject this marker in 2027?" has an answer.

**Q3 — Can versioning ever require destructive migrations? NO — with F3
closed.** Mechanisms audited: geometry `schema_version` ✓ · `pipeline_version`
✓ · `confidence_formula_version` ✓ · immutable markers + PROTECT pins ✓ ·
supersede chains ✓ · `grade_rule` absent-vs-empty ✓ · integer µm ✓. Two gaps
found and closed: `GarmentTemplate` was unversioned (now append-only revisions,
F7) and `MarkerRequest.params` JSON lacked a schema version. F3 adds the
**schema-evolution constitution**: every JSON payload carries `schema_version`;
enums are additive-only and values are never repurposed; new columns are
nullable-first; nothing is ever reinterpreted in place.

**Q4 — Is the architecture completely AI-engine independent? YES — now stated
as an invariant, not an accident.** Stored placements ARE the marker
(engine-agnostic); confirmed geometry IS the pattern (capture-pipeline-
agnostic); engine identity/commit/seed are AUDIT fields, not dependencies;
derived CV artifacts are regenerable caches. F4 locks the invariant: *canonical
geometry and placements NEVER contain engine-native data; adapters translate at
the service boundary; OpenCV, SAM-family, nest2d, SVGnest, or any future engine
is replaceable without touching the database or the business model.*

**Q5 — Is knowledge ever deleted? NO — with the three-class policy made
explicit (F5).** KNOWLEDGE (confirmed geometry, markers, usage, outcomes,
decisions, originals) is never deleted — superseded, retired(reason), or
cold-archived only. REGENERABLE artifacts (renditions, masks, render caches)
are freely deletable — they are not knowledge. DEV-marked data is deletable
only by owner-sanctioned teardown (the Manufacturing V1 precedent). Full
status sets are now written down (§5) so "retired" is a visible, reasoned,
永-queryable state — never a DELETE.

**Q6 — What breaks at 5–10 years / many factories? Nothing structural; two
refinements landed.** (a) **MarkerOutcome now stores RAW FACTS ONLY** (meters
consumed, garments out, leftover, flags); every ratio (utilization,
meters/garment, ₹/garment) is computed at read through versioned pure functions
— the entire "recompute historical outcomes after a formula fix" migration
class is deleted (F6). (b) The **asset-scope table** (§4.0) fixes org-level vs
product-level vs site-level ownership now, so factory #2 is a filter: org =
templates + geometry spec; product = patterns/markers/suggestions (org-global
assets); site = usage, outcomes, calibration mats, capture devices. Read-scale
slots (materialized yield summaries, library pagination) are documented, not
built (F8).

## 1. Changelog

**V2 → V3 (this review):**

| # | Change | Why (challenge) |
|---|---|---|
| F1 | Knowledge-graph stance: relational schema + append-only events IS the graph; Product-360 read view at P4; graph stores/abstractions explicitly rejected | Q1 |
| F2 | Decision spine completed: `rejected(reason)` states; mandatory actor+at+reason on every negative/override transition; typed events kept; biography = union view | Q2 |
| F3 | Schema-evolution constitution: `schema_version` on EVERY JSON payload (incl. MarkerRequest params, grade_rule); additive-only enums; nullable-first columns; no value repurposing | Q3 |
| F4 | Engine-independence invariant stated (canonical data never engine-native; adapters at boundaries; engines replaceable without schema/business change) | Q4 |
| F5 | Deletion policy: KNOWLEDGE never / REGENERABLE freely / DEV by sanctioned teardown; complete status sets written for markers + geometry | Q5 |
| F6 | MarkerOutcome = raw facts only; all derived metrics computed at read via versioned pure functions (kills recompute migrations) | Q6 |
| F7 | GarmentTemplate versioned (append-only revisions); SuggestionEvent pins the revision | Q3 |
| F8 | Asset-scope table (org/product/site) §4.0 + documented read-scale slots | Q1/Q6 |

**V1 → V2 (kickoff hostile review + owner principles — full detail in
[05 §1](05_BLUEPRINT_V2.md)):** C1 three-era spine · C2 manual markers
first-class forever (`origin` enum) · C3 measure-before-optimize roadmap
(P1 = digital memory + yield board) · C4 baseline competition + lineage ·
C5 confidence score · C6 D11 temporary-marker promotion mechanics ·
C7 `MarkerUsage.repeats` · C8 `SuggestionEvent` · C9 PatternSet demoted to
optional label · C10 stored `width_band` · C11 `grade_rule` slot ·
C12 integer µm · C13 `CalibrationMat` + device registry · C14 global MRK-
references · C15 two-tier recommendation honesty + deterministic TRIAL rule ·
C16 render-reproducibility honesty · C17 GSM→P1 · C18 DXF import→P2/P3 ·
C19 digitisation triage · C20 marker biography.

## 2. The three eras (mission spine — unchanged from V2)

**Era 1 DIGITAL MEMORY** (P1): every marker actually cut — including manual
chalk markers — remembered with width/ratio/repeats/yields; the yield board;
zero CV; value in week one. **Era 2 INTELLIGENT ASSISTANT** (P2/P4): capture,
digitise, compare with evidence, confidence-scored recommendations,
suggestions. **Era 3 MARKER GENERATOR** (P3+): nesting that must beat the
recorded manual baseline. Judged always by: simplicity · maintainability ·
knowledge preservation > elegance.

## 3. Honest mechanism glossary

V1+V2 rows stand unchanged (template library · classical-CV-first ·
ChArUco measurement · strategy nesting · remembers-and-compares · confidence =
deterministic versioned formula with visible ingredients · digital memory =
append-only registry). Nothing in V3 adds an "AI" claim.

## 4. Data model (final)

### 4.0 Asset scope (F8 — the multi-factory decision, made now, built never)

| Scope | Assets | 10-year rule |
|---|---|---|
| ORG (global) | GarmentTemplate(+revisions), geometry format spec, confidence formulas | shared knowledge; no site key ever needed |
| PRODUCT (org-global) | PatternPiece/Versions/Geometry, PatternSetLabels, Markers (all origins), SuggestionEvents, biographies | the owner's "permanent home of everything"; site-independent by construction |
| SITE (physical/local) | MarkerUsage, MarkerOutcome facts, CalibrationMat, capture-device profiles | already hang off Adda/physical assets — a future `site` dimension is a FILTER, not a migration |

### 4.1 Entities (V3 deltas marked)

All V2 entities and grains stand ([05 §4](05_BLUEPRINT_V2.md)) with these
completions:

- `GarmentTemplate` → **[F7]** append-only revisions; `SuggestionEvent` FKs the
  revision row.
- `MarkerRequest` → **[F3]** `params_schema_version`.
- `Marker` status set **[F5]**: `candidate → validated → promoted(from
  temporary) → superseded | retired(reason) | rejected(reason)`; every
  transition audited (actor, at; reason mandatory on negative paths **[F2]**).
- `PatternPieceVersion` status set **[F5/F2]**: `draft → confirmed →
  superseded | rejected(reason)`; voided_at retained for capture mistakes.
- `MarkerOutcome` → **[F6]** raw facts only: meters_consumed, garments_out,
  leftover_m, plies, repeats echo, quality flags, `facts_schema_version`;
  ratios/₹ computed at read (versioned pure functions, single quantization
  helper per I-4).
- Biography **[F2]** = read-side union over MarkerRun · ValidationEvent ·
  SuggestionEvent · Usage · Outcome · status transitions — no new write tables.
- Everything else exactly as V2: origin enum incl. `manual_photo` +
  `adda_temporary` (draft-pin carve-out + promotion = confirm pins + status
  flip + audit) · repeats on usage · width_band · grade_rule slot · integer µm ·
  CalibrationMat + device registry · MRK- references · PROTECT-pinned
  placements · single-writer services with the no-raw-ORM rule (I-1).

## 5. Constitution (the clauses implementation may never break)

1. **Product-root knowledge graph** — every module asset reachable from
   Product by FK chain (org/site assets per §4.0); graph = schema + events;
   no parallel stores. (F1)
2. **Decisions are knowledge** — every approve/reject/promote/retire/validate/
   override is an immutable, reasoned, attributed event. (F2)
3. **Schema evolution is additive** — versioned JSON payloads everywhere;
   additive-only enums; nullable-first; no reinterpretation. Destructive
   migrations are a design failure, not a chore. (F3)
4. **Engine independence** — canonical data never engine-native; adapters at
   service boundaries; any engine replaceable without schema or business
   change. (F4)
5. **Deletion policy** — knowledge never; regenerables freely; DEV by
   sanctioned teardown only. (F5)
6. **Facts stored, metrics derived** — computed numbers live in versioned
   functions, not rows. (F6)
7. Plus the inherited eight compliance clauses (proposals-only toward
   production · link-out UI seam + runtime purity test · FK direction ·
   no money / honest-NULL ₹ after GSM · RBAC + sidebar rules · media
   lifecycle ADR-G · compute isolation ADR-F · PDD amendment gate) and the
   honest-AI vocabulary, verbatim from V1/V2.

## 6. Unchanged-by-V3 sections (design of record = V2 text)

Capture pipeline (§6 of 05, + mat commissioning) · confidence score spec
(§5 of 05; formula inputs now read F6 facts) · trust & adoption ladder incl.
evidence cards and the one-time side-by-side lay (§8 of 05) · feedback/yield
board + two-tier honesty + TRIAL rule (§9 of 05) · risk registers (V1 §8 +
V2 §10) · dummy-data plan (§13 of 05) · idea-register disposition (§14 of 05).

## 7. Roadmap (final — V2's resequenced roadmap with two F-notes)

ADR pack → P0 (bake-off + metrology POC + **yield-board data walk on
3-PATTI-016**) → **P1 DIGITAL MEMORY** (manual markers + usage/outcomes(F6
facts) + yield board + SuggestionEvent + GSM mini-ADR + geometry spec) →
**P2 CAPTURE** (+DXF import) → **P3 GENERATION** (async ADR-B, evidence cards,
D11 flow) → **P4 ASSISTANT DEPTH** (confidence live, two-tier recommendations,
**Product-360 knowledge view (F1)**, DXF export) → P5 HARDWARE → P6 (probably
never) real ML. Every phase ships something the factory uses; gates as in 05.

## 8. Owner decisions D1–D11 — proposed finals unchanged from V2 §12

(D3 GSM at P1 · D8 ops-master §11 amendment on sign-off · D11 per C6 —
ready for formal rulings at the ADR step.)

## 9. FINAL CERTIFICATION

Three independent review passes are complete: the 7-lens adversarial review
that produced V1, the owner-approved hostile kickoff review (04) that forced
V2's measure-first inversion, and this 10-year permanence review closing the
knowledge-graph, decision-spine, versioning, engine-independence, deletion,
and scale questions.

**The architecture is certified: product-rooted, append-only, engine-
independent, additively-evolvable, deletion-free, factory-first, and honest.
No further architectural redesign is recommended before implementation.**

Next steps on owner sign-off of this document: mark 03 + 05 superseded ·
amend ops-master §11 (D8) · draft ADRs A–H against V3 · formal D1–D11 rulings ·
begin **P0**.

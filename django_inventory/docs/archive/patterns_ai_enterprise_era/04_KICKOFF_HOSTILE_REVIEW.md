# AI Pattern Intelligence — Kickoff Hostile Review of Blueprint V1 (2026-07-06)

> **Status: 🔍 REVIEW ONLY — no code, no migrations, no project changes.**
> Fresh-eyes, first-principles review of
> [AI_PATTERN_INTELLIGENCE_KICKOFF.md](../AI_PATTERN_INTELLIGENCE_KICKOFF.md) +
> [03_PLATFORM_BLUEPRINT.md](03_PLATFORM_BLUEPRINT.md), factory-owner lens first,
> blueprint presumed wrong until proven. Frozen Manufacturing V1 contracts
> respected throughout. *Provenance: the multi-agent panel was killed by a
> session limit before returning anything; per the audit-honesty rule this
> review was performed single-reviewer, main-thread, against the documents and
> the production code. Both source documents were re-read in full from disk.*

---

## 1. Critical blockers (must change before P0)

**CB-1 — The blueprint optimizes before it measures, and its library excludes
the markers the factory already has.** V1's library admits only *generated*
markers (plus future imports). But the factory cuts every day TODAY with the
master's chalk markers — and V1 has no way to record them, their widths, their
ratios, or their yields. Consequences: (a) the first fabric-saving insight
arrives only at P3/P4, after weeks of digitisation with zero payback; (b) Gate 2
("cut one lay both ways") compares the AI against a *memory*, not a recorded
baseline; (c) the owner's own knowledge-preservation goal is unserved until the
hardest part (CV capture) works. **Fix: make MANUAL markers first-class library
members from day one** — `Marker.origin ∈ {manual_photo, generated, imported,
adda_temporary}`; a manual marker = a photo of the chalked lay + human-entered
width/ratio/repeats. Then `MarkerUsage` + `MarkerOutcome` work from week one
with ZERO computer vision: the platform's first deliverable becomes a
**yield board** (meters-in vs garments-out per product/width/marker), which is
deterministic, cheap, immediately valuable, and gives every future generated
marker a real baseline to beat. This inverts the roadmap's value curve and is
the single most important change this review found.

**CB-2 — D11 (Adda-temporary marker → promotion) is owner-locked vision with NO
schema mechanics in V1.** V1's trust rule says only MEASURED/PHOTO-CALIBRATED
confirmed geometry may be nested — which makes the owner's temporary-marker
flow impossible as specified. Fix (design, elegant, no copying): a temporary
marker is a `Marker(origin=adda_temporary, adda=FK)` whose placements MAY pin
**draft** geometry, rendered everywhere with an UNVERIFIED badge and excluded
from recommendations; **promotion = human-confirming those geometry rows +
flipping the marker's status** (the PROTECT pins already point at the right
rows — nothing is duplicated, immutability holds, one audit event records
promoted_by/at). Must be in V2 §3 + ADR-D.

**CB-3 — `MarkerUsage` lacks `repeats`.** A lay is N marker-repeats along its
length plus end losses; V1 records plies and measured width but not repeats, so
the outcome formula (÷ lay_length × width × plies) silently assumes one repeat
and mis-scores every real lay. One integer field, but without it the entire
feedback pillar computes wrong numbers. Must be in the v1 schema (and in the
manual-marker entry form of CB-1).

**CB-4 — "AI Suggestions" is on the owner's product-asset list but V1 stores no
suggestion artifacts.** The template MECHANISM exists (`GarmentTemplate`), but a
suggestion made for a product is never persisted as the product-homed,
auditable asset the vision demands. Fix: `SuggestionEvent` (product FK, template
+ version used, payload, accepted/rejected/modified, by/at) — cheap append-only
row, closes the vision gap and doubles as the audit trail for W2.

## 2. Architecture risks

- **PatternSetRevision as a hard dependency creates ceremony** (see §8/§9 —
  recommend demoting to optional label).
- **Promotion vs immutability** interplay (CB-2) is the one place V1's
  supersede-never-edit chain could have deadlocked; the status-flip design
  resolves it, but ADR-D must spell out the state machine
  (draft-geo→confirmed-geo × marker candidate→temporary→promoted→approved→stale).
- **Bit-for-bit reproducibility is over-promised.** GA nesting with float math
  and threads will not replay identically years later even seed-pinned. The
  honest contract (already half-stated in V1) is: **stored placements ARE the
  artifact — re-RENDERING is always reproducible; re-RUNNING is best-effort.**
  Kickoff success-metric wording ("every approved marker reproducible") must be
  softened to render-reproducible, or it will be "proven false" in year 2.
- The runtime purity test + link-out UI seam + single-writer map are sound; no
  change. The `q_paisa` lesson (one quantization home, I-4) stands.

## 3. Scalability risks (2–5 year, and the hundreds-of-factories question)

- **Width-band must be a STORED integer bucket** (e.g. `usable_width_band =
  floor(mm/10)`) written at marker creation — the candidate-marker resolution
  query ("markers fitting THIS Adda's rolls") is the hottest read in the
  system; computing bands at query time across thousands of markers = the
  year-3 slow page. Costs one column now.
- **Media, not rows, is the scale problem.** Row counts at thousands of
  products are trivial for Postgres; originals-forever photos are not — ADR-G
  (tiers, integrity job, S3 switch point, restore SLA) is correctly scoped and
  must stay a P1 gate, not a promise.
- **Multi-factory:** geometry + templates are org-global; usage/outcomes are
  factory-local *by construction* (they hang off Adda). Two zero-cost decisions
  now: (1) globally-unique human references for markers (MRK-000001 style, same
  discipline as ADST-), no factory-implicit uniqueness anywhere; (2) the
  physical-asset registries this review adds (calibration mats, capture
  devices — §4) become the natural per-site anchors later. Nothing else should
  be built for multi-factory today.
- Nesting compute stays safe only if ADR-B keeps the cap-1-CPU-job +
  overnight-window rule — the same box runs the floor ERP.

## 4. Data-model issues

1. **`Marker.origin` + nullable `adda` FK + promotion state** (CB-1/CB-2).
2. **`MarkerUsage.repeats`** (CB-3) — plus confirm the v1 fact list so no
   historical migration is ever needed: adda, marker, plies, repeats,
   measured_usable_width_mm, confirmed_by/at, voided_at. Leftover meters comes
   from `RemainingClothOfClothRoll` (exists), operator from the cutting task,
   rolls from `LayeringRollEntry` — all derivable, nothing new to capture.
3. **`SuggestionEvent`** (CB-4).
4. **Grade-rule SLOT missing.** V1 stores independent per-size polygons with a
   'graded' provenance value but no representation of grade relationships.
   Adding size XXL to a 3-year-old product = full physical recapture, and
   brand DXFs carry grade structure V1 would flatten. Fix now = one optional
   `grade_rule` JSON field (per-point deltas, spec'd in ADR-C, empty in year 1);
   grading ENGINE stays future. Absent-vs-empty is exactly the mistake class
   the blueprint itself warns about.
5. **Geometry number representation:** "mm floats" in JSON is drift + cross-
   language round-trip risk inside a permanent asset. Spec integers (micrometers
   or 0.01 mm units) in ADR-C; the I-4 single quantization helper then has an
   exact domain.
6. **Calibration mat has no identity.** Metrology chain of custody requires a
   `CalibrationMat` physical-asset row (mat_id, commissioning tape-measured
   control distances, date, status) referenced by every CaptureAsset — V1 has
   per-photo self-checks but no commissioning record and no way to recall "all
   captures made on the stretched mat". Same pattern as the machines registry.
7. `MarkerRequest`/`MarkerRun`/`Marker`/`MarkerPlacement` grains are right;
   PROTECT-pinning placements is right; CaptureAsset immutability is right.

## 5. Workflow issues

- **Roadmap order is wrong** (CB-1). Corrected shape: **P1 = library-lite +
  MANUAL marker registry + MarkerUsage/Outcome + yield board** (value in week
  one, no CV); P2 = capture pipeline; P3 = generation + marker room; P4 =
  deeper analytics + GSM ₹; DXF-AAMA import slides P1→P2/P3 (unless a brand
  file arrives first) — it currently front-loads a heavy parser before any
  factory value.
- **Gate 2 improves under CB-1**: the AI's first marker competes against the
  RECORDED manual baseline for that product/width — evidence, not a sacrificial
  side-by-side lay every time (keep the side-by-side for the first product
  only, as theatre that builds trust).
- **Digitisation triage is missing**: nothing tells the owner WHICH products
  deserve the 30-40-capture investment. One rule in the doc: digitise on
  recurring volume; the yield board (CB-1) itself identifies the products
  where marker waste is worth attacking.
- Promotion workflow (CB-2) needs its UI moment specified at P2/P3: confirm
  geometry → promote marker → appears in product library with full history.

## 6. Factory usability issues

- **The first month of V1-as-written gives the owner nothing to look at.**
  CB-1's yield board fixes this — it is also the screen that finally speaks
  ₹ once GSM lands (see §8: pull D3 earlier).
- Capture @390 is honestly scoped (phone captures, desktop edits) — keep; but
  the ≤90 s/piece gate must be measured on the REAL factory table in P2, not a
  desk.
- Trust gates are practical; the 100 mm print ritual is right and must never be
  relaxable in config.
- Recommendation surface correctly lists concrete markers (I-3); with CB-1 the
  list includes "Master's manual layout — your current baseline" as an option,
  which is both honest and disarming for adoption.

## 7. AI assumptions that are unrealistic

- **n ≥ 3 per (product, fabric_group, width-band, ratio) cell will stay unmet
  for YEARS at this factory's volume** — the recommendation engine as spec'd
  would sit silent, and the owner would read that as "the AI does nothing".
  Fix: two-tier honesty — cell-level ranking when n≥3; otherwise product-level
  "generated vs manual baseline average" comparison with an explicit
  small-sample badge. Never invent precision; also never show nothing when an
  honest coarser comparison exists.
- **Exploration policy is a phrase, not a rule.** Make it deterministic: a new
  marker whose predicted consumption beats the incumbent's realized average by
  more than the stated tolerance gets a TRIAL badge on the next matching Adda;
  otherwise incumbent stays. One sentence, no ML.
- Bit-for-bit re-run reproducibility (see §2) — soften.
- The "likely never" stance on real ML remains correct; nothing in this review
  changes it. Local-LLM stays an optional, flag-gated drafting aid (D10: skip
  for v1).

## 8. Missing opportunities

1. **Manual-first marker library + yield board (CB-1)** — the platform earns
   its keep in week one and captures the master's existing knowledge as the
   foundation asset, not as an afterthought.
2. **GSM earlier (D3 → P1 additive owner-ADR):** one intake field converts the
   yield board to ₹/garment — the owner's language — years before P4.
3. **Grade-rule slot (D-4 §4)** — protects against the year-3 recapture wall.
4. **CalibrationMat + capture-device registry (§4.6)** — metrology custody now,
   free multi-site anchor later.
5. **Width-band bucket column (§3)** — kills the hottest future query's cost
   for one integer.
6. **Two-tier recommendation honesty (§7)** — visible intelligence years
   earlier without dishonesty.

## 9. Final recommendation

**Blueprint V1 must become BLUEPRINT V2. Do not certify V1.**

V1's foundations survive this attack: product-centric ownership, per-size
geometry with provenance/trust grades, fabric groups, tubular/on-fold handling,
PROTECT-pinned placements, MarkerUsage as the feedback join, honest-AI
vocabulary, frozen-contract compliance, open-source/offline stack. None of that
changes.

But four blocker-class findings (manual-first library + measure-before-optimize
resequencing · D11 promotion mechanics · usage `repeats` · stored suggestions),
one demotion (PatternSetRevision → optional label), and six cheap-now schema
decisions (origin enum, width-band bucket, grade-rule slot, integer units,
CalibrationMat registry, global marker references) are material design changes,
not polish. Ship them as V2 with a changelog, then rule D1–D11 (this review
recommends: pull **D3 to P1**; fold CB-1/CB-2 into **D11**'s ruling), then draft
ADRs A–H against V2.

**P0 readiness: GO after V2 is owner-approved** — with P0's scope amended to
include the yield-board data walk (manual marker + usage + outcome on
3-PATTI-016's real numbers) alongside the engine bake-off and metrology POC,
so feasibility is proven for the measure-first roadmap, not just the
generate-later one.

*Stop point per owner instruction: review only. No V2 written, no ADRs drafted,
no code, no migrations. Next step awaits owner approval of this review's
direction.*

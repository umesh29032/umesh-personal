---
id: docs-implementation-readiness-pre-production
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# IMPLEMENTATION READINESS — Pre-Production Cutting Streams (one page)
(2026-07-11 · gate document; NOTHING built until the owner approves)

**Real factory problem.** Multi-fabric products (real Nickar: Body+
Pocket on one fabric, Panel on another) need independent
layering→pattern→cutting lanes per fabric group; the garment exists —
and may be bundled/barcoded — only when all lanes are cut. Today's ERP
allows exactly one lane per Adda (AddaStageRecord unique per stage;
single current_stage pointer; bundle anchored to one CuttingRecord).

**Why it matters.** Blocks honest validation of campaign modules 7–13
for any real multi-fabric product; bundles today cannot represent a
complete garment, which corrupts everything downstream that consumes
them (tracking, counting, future barcode Option B).

**Ownership.** ERP (production app). Pattern Intelligence: ZERO changes
(it is already per-fabric-group; the stream mirrors its existing
`(adda, fabric_group)` layout-contract key). Boundary: the two
LAYOUT_PROVIDER payloads already return per-group data — consumed
per-stream instead of flattened; no registry contract change.

**Smallest implementation** (detail: PRE_PRODUCTION_REDESIGN_PROPOSAL):
1. `CuttingStream` table + `AddaStageRecord.stream` (nullable FK;
   unique widened to (adda, workflow_stage, stream)) +
   `CuttingBundle.adda` anchor. ~2 migrations, additive.
2. Stream derivation at Adda creation (distinct mandatory-piece fabric
   groups) + join rule in advance ("leave pre-production only when all
   streams cut_complete").
3. Stream-scoped accessors for the three pre-production stage services;
   ops stages untouched (stream NULL).
4. Bundling step moves to post-join; bundle items span streams.
5. Console pass: lane headers + Pattern Design simplification
   (select→preview→confirm; PI statistics removed from production UI) +
   cutting console slimmed to expected/actual/pending/breakup.
6. Data migration: one default stream per existing Adda; existing SRs +
   bundles assigned; single-group products byte-identical.

**Modules affected.** production: models (adda, cutting), adda_service,
layering/cutting_pattern/cutting stage services, pool first-ops-sum,
reopen guard stream-scoping, 3 consoles + A360 lane display, tracking
history events gain stream context. NOT affected: patterns_ai, expense/
settlement (re-verified later in modules 10–11), accounts, ops stage
handlers, all flags.

**Browser journey that proves it.** Create a REAL two-stream Adda
(DEV-NICKAR): see two lanes on A360 → walk the body lane to
cut_complete (rolls→lay→pattern confirm→cut) → verify bundling REFUSED
("Panel stream not cut") → walk the other lane → join unlocks → create
Size bundles holding Body+Pocket+Panel items → 1 continuous barcode
range per Adda → first ops stage pool = Σ both cuts → Lower single-
stream Adda re-run proves byte-identical old behavior.

**Tests that protect it.** Stream derivation (1-group ⇒ 1 stream;
Nickar-shaped fixture ⇒ 2) · per-stream SR uniqueness · join gate
refusal + unlock · bundle completeness across streams · pool sum ·
reopen inside a lane vs across the join · migration on existing
fixtures (single-group byte-identity) · full production suite + battery
· genericity guard stays green (no product names).

**Migration impact.** Additive schema; reversible until cutover; no
data loss; dev DB migrated in place; existing completed Addas
untouched in meaning.

**Explicitly OUT of scope.** Barcode redesign (Options A/B both kept
open — decided later) · per-size early bundling (future refinement,
schema already permits) · multiple lays per stream (future factory
ask) · any ops-stage change · any money/settlement change · flag flips.

**STOP. Awaiting owner approval before any implementation.**

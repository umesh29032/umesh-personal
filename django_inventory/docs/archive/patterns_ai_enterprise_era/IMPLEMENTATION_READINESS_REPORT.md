# IMPLEMENTATION READINESS REPORT — Phase 3 (2026-07-06)

> **The final pre-implementation gate.** First-principles hostile review of the
> entire project chain, attempting to break the implementation plan before a
> line of code exists. Scope reviewed: Blueprint V3 · Manufacturing V1 Freeze ·
> ADR pack A–H · Implementation Master Plan · Kickoff Contract · D1–D11
> rulings · import boundaries · single-writer guarantees · rollback safety ·
> testing & documentation completeness · risks, unknowns, hidden assumptions,
> missing dependencies · future-migration / operational / data-integrity /
> performance risks.

## 1. Verification matrix

| Area | Verdict | Evidence / notes |
|---|---|---|
| Blueprint V3 internal consistency | ✅ | Three review passes on record; V3§6 delegation to V2 text is explicit in both banners — no orphan normative text |
| Manufacturing V1 freeze compliance | ✅ | Plan's ONLY production touches: P1 app wiring (machines-app precedent class) + D2/D3 owner mini-ADRs — both owner-authorized paths; purity + untouched-baseline gates at every phase end |
| ADR pack ↔ plan alignment | ✅ | Certification §3 mapping re-checked; no ADR contradicts another (job-history classes B↔G consistent; D11 carve-out D↔E consistent) |
| Master plan structure | ✅ | DAG re-verified acyclic; every phase input produced upstream or named as owner action (D2/D3/D7, hardware) |
| Kickoff contract + D1–D11 | ✅ | All eleven ratified via pack approval (cert §4); D8 EXECUTED (ops-master §11 amended — grep-verified) |
| Import boundaries | ✅ | patterns_ai correctly ABSENT from `.importlinter` today (0 hits — it's a P1 deliverable with no-ignores + runtime purity test); zero-exception rule stricter than machines precedent |
| Single-writer guarantees | ✅ | Four services named; I-1 no-raw-ORM rule carried into guard tests (P1 suite); import/backfill tooling bound to the same chokepoints |
| Rollback safety | ✅ | Kill-switch (SidebarItemRule) + reversible additive migrations + worker-stop + knowledge-never-deleted; freeze guarantee provable via baseline suite |
| Testing completeness | ✅ w/ additions | Golden/guard/state-machine/RBAC layers defined; **N-5 adds upload-security tests; N-8 adds tblib + test-DB rules** (below) |
| Documentation completeness | ✅ | Full chain on disk and indexed (verified by listing); ADR-C spec doc pending BY DESIGN (P1 gate) |
| Future migration risks | ✅ | F3 constitution + µm integers + additive enums + versioned payloads; no field found whose absence forces a future backfill (repeats/width_band/grade-slot/origin all land in v1 schema) |
| Data integrity risks | ✅ | Checksums at upload, integrity sweep, PROTECT web (placements→geometry→ProductSize), append-only events |
| Performance risks | ✅ | Checkpoints defined with numbers (≤90 s/piece, <5 s segmentation, worker cap-1 + floor-latency proof, width_band EXPLAIN, conscious pins) |
| Operational risks | ⚠️ N-1 | see hostile findings — one real, evidence-backed item |

## 2. Hostile findings (N-1…N-8) — none is a blocker; all bind via certification

**N-1 · OPERATIONAL (the real one): 228 uncommitted files.** The entire frozen
Manufacturing V1, both excellence audits, the freeze package, and every AI-PI
document exist ONLY in the working tree (`git status` = 228 entries; last
commit predates all of it). One disk failure erases the certified foundation.
The checkpoint commit is the owner's call (standing policy honored) — but this
gate must say it plainly: **recommendation: execute the checkpoint commit
BEFORE any P0 work.** Readiness condition: P0 may not start with the tree
uncommitted unless the owner explicitly waives this.

**N-2 · Hidden assumption: SVG's y-axis points DOWN; ADR-C canonical is y-UP.**
Every SVG export/preview requires a documented flip transform, and the P1/P2
round-trip goldens MUST include an asymmetric piece so a silent flip cannot
pass. (DXF is y-up; HPGL device-dependent — same golden discipline at P5.)

**N-3 · Hidden dependency: a JavaScript runtime.** If SVGnest wins the
bake-off, the headless runner needs Node on the factory server — Node itself
must be VENDORED (ADR-F manifest entry, ~40 MB, license MIT) exactly like
model weights. The bake-off harness (P0) must already run from a vendored
runtime so the dependency is proven, not assumed.

**N-4 · Hidden dependency: system libraries for the print pipeline.**
CairoSVG/WeasyPrint pull cairo/pango at the OS level — these enter the ADR-F
rebuild-from-vendored drill scope (apt package list pinned in the runbook),
or the diagram renderer must be chosen to avoid them. Resolve at P1 when the
diagram stack is picked.

**N-5 · Testing gap: upload security.** Capture/manual-marker photos are a
user-upload attack surface. P1/P2 DoD gains: content-type + size validation
tests, path-traversal safety, no raw serving of originals (ADR-G already),
and a decision note that EXIF is retained BY DESIGN (provenance) on
internally-served knowledge files.

**N-6 · Underspecified moment: when are outcome FACTS written in P1?** No
worker exists until P3. Resolution consistent with the constitution: outcome
facts are written by an explicit human "record outcome" action on the usage
row (human-confirmed truth; synchronous read of layering/APSCPB at that
moment). P1 design note — not a schema change.

**N-7 · Rollback nuance: the integrity sweep must tolerate roll-back
orphans.** Knowledge files from a rolled-back phase remain on disk by design;
the sweep must classify "file present, row absent (rolled back)" as WARN-
with-context, not corruption. ADR-G sweep design note.

**N-8 · Test-operations hygiene.** (a) The P1 yield-board volume test runs in
the TEST database only (script-generated), never in the dev DB — the
no-fabricated-history rule stays clean. (b) Install `tblib` with the P1 dev
dependencies so parallel test failures are reported, and keep the
one-test-command-at-a-time rule (documented collision lesson).

## 3. Unknowns consciously carried (not gaps)

Engine choice + real utilization numbers (P0 exists to answer); achievable
error tiers on the factory table (P2 re-validation); DXF-AAMA wild-file
fidelity (import test set at P2); factory adoption friction (measured gates,
trust ladder). Each has a phase, a gate, and a fallback already in the plan.

## 4. Verdict

**No architectural contradiction found. No implementation blocker found.**
One operational risk (N-1) requires an owner action or explicit waiver before
P0; seven findings bind as DoD additions to their phases via the
certification. The project is genuinely ready for implementation.

→ [IMPLEMENTATION_READINESS_CERTIFICATION.md](IMPLEMENTATION_READINESS_CERTIFICATION.md)

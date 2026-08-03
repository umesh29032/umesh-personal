# P1 FREEZE RECOMMENDATION (2026-07-07)

## Recommendation: **FREEZE P1 — Digital Memory era — as delivered.** ✅

Same discipline as the Manufacturing V1 freeze: frozen means *no refactor,
no redesign, no "improvement" of these modules without explicit owner
approval*; additive evolution only, through the constitution (F1–F8) and
new owner-approved blocks.

## 1. What is frozen

**The Digital Memory contract — behavior, not just code:**

- **Schema (migrations 0001–0004):** 9 models; facts in integer mm; every
  JSON carries `schema_version`; append-only tables guarded in save/delete
  AND by constraints. Future schema change = ADDITIVE ONLY (F3).
- **Single-writer services and their rules:** `marker_service`
  (create/transition/supersede + one immutable event per change),
  `marker_feedback_service` (usage/void/outcome; `derive_metrics` = the
  only math home, METRICS_VERSION), `capture_service` (magic-byte
  pipeline, immutable originals, retire/corrupt with reasons).
- **Read-model guarantee:** metrics are DERIVED AT READ; no calculated
  value is ever persisted; `marker_query_service` stays SELECT-only
  (test-enforced).
- **Media classes (ADR-G):** knowledge originals forever + hash-named;
  derived renditions regenerable/deletable; renditions-only serving —
  `originals/` never gets a URL surface.
- **Boundary (ADR-H):** production never imports patterns_ai; patterns_ai
  never writes a manufacturing table. Money stays settlement-only —
  patterns_ai holds ZERO money paths (verified: no ledger/settlement
  imports anywhere in the app).
- **UI surfaces:** the 8 canon-compliant pages incl. the Yield Board's
  honest-language contract (`n=`, `— (no facts yet)`, NULLs-last,
  "derived at read" footer).
- **Walls that keep it frozen:** purity scans, exactly-9-models pin,
  FileField confinement, I-1 repo-wide write guard, SELECT-only captures,
  query ceilings, import-linter layer. These tests ARE the freeze —
  breaking one = tripping the freeze, not noise to re-pin silently.

## 2. Intentionally deferred (NOT defects)

- 500-on-tampered-id fix (3 one-liners) + dead `big = None` — queued for
  the NEXT owner-approved code block (verification-only order today).
- Derived-metrics cache — only if volume ever demands it (ADR candidate).
- DB-level append-only hardening (grants/triggers) — ADR candidate.
- Adda-dropdown cap, ratio_text UX, broken-image placeholder,
  `update_outcome_facts` UI — polish items, listed in the debt register.
- Checkpoint commit — owner's own hand. Real rate card — production
  rollout. S6 + enforcement flags — manufacturing stream (R11).

## 3. What belongs to P2 (Geometry/CV era — NOT started)

- `pattern_geometry_service` logic (today an empty placeholder = P2's
  front door), CalibrationMat workflows (ADR-E metrology), PatternPiece /
  PatternPieceVersion capture UI, piece extraction (SAM/OpenCV), geometry
  format enforcement (ADR-C integer-µm gate), D2/D3 mini-ADRs.
- SuggestionEvent surfaces (Era-2 assistant) — schema waits, frozen.
- Any nesting/marker generation (Era 3) — furthest out, gated twice.

## 4. Risks (with mitigations, all standing)

| Risk | Mitigation |
|---|---|
| Freeze erosion by "small improvements" | The wall tests + this document + owner gate on every block |
| Facts recorded wrong (human error) | void/retire with mandatory reasons — corrections are new facts, never edits |
| Derive-at-read cost creeps with volume | pinned query ceiling makes it visible; cache slot pre-designed |
| Media dir drifts from DB | `verify_patterns_media` sweep (cron at deploy); orphans WARN, corruption flagged with evidence |
| P2 pressure to "just store the metric" | F6 is constitutional; any persistence of derived numbers requires an ADR |

## 5. Readiness statement

- Full manufacturing suite: green (serial, re-verified twice today).
- patterns_ai: 94/94 green, three runs today.
- Migrations clean · import contracts unchanged · media sweep clean
  (`checked=2 corrupt=0 missing=0 orphans=0`).
- Live walkthrough re-proven @390 + desktop (8 screenshots, final package).
- Hostile review (main-thread + independent sub-agent, triaged): zero
  critical, zero money-risk; findings registered.

**P1 is DONE, verified, and safe to freeze. Recommended freeze marker:
this document + the P1 Final Package, owner-accepted. The checkpoint
commit that follows is the owner's.**

# P2 READINESS REPORT — Geometry/CV entry check (2026-07-07)

**Nothing here is implementation. This report only verifies that P2 can
begin safely when the owner says so. P2 is NOT started.**

## Verdict: **READY — no architectural blockers. 4 entry criteria to
execute at P2 kickoff (none require design changes).**

## 1. Is Digital Memory sufficient to build on? YES

P2 (geometry capture + piece extraction) consumes exactly what P1 built:

- **Product-homed knowledge** — CaptureAsset is already product-scoped
  with immutable originals + sha anchors; geometry captures reuse the SAME
  pipeline (`kind=pattern_capture` is already reserved in the model).
- **Custody anchor exists** — `CaptureAsset.mat` FK to CalibrationMat is
  live in schema since 3A; ADR-E's chain (mat → capture → extraction) has
  its DB spine waiting.
- **Grain holders exist** — PatternPiece / PatternPieceVersion (2A,
  constraint-guarded) are the landing tables for extracted geometry;
  no schema invention needed to start.
- **Decision spine exists** — SuggestionEvent (2A) is where Era-2
  reasoned proposals land; P2 extraction confidence/acceptance events
  have a home.
- **The metric truth P3+ needs** — usage/outcome facts + derive-at-read
  are live and already producing real numbers (96.00 m/100). A generated
  marker's "must beat manual baseline with evidence" test (owner
  principle) is now measurable software, not intent.

## 2. Can geometry begin safely? YES

- `pattern_geometry_service` placeholder = the single front door; I-1
  guard already covers knowledge writes, so P2 code physically cannot
  bypass the discipline.
- ADR-C (integer µm, polyline tolerance, **P1 gate**: quantization home
  ready) — `units.py` is that home; µm helpers are an additive extension.
- ADR-E metrology is PROVEN feasible (P0: ChArUco algo-chain ≤0.08 mm,
  hold-out corner validation 0.003–0.076 mm) — poc/patterns_ai/ is the
  executable reference.
- ADR-F two-runtime isolation defined (vendoring, engine independence);
  ADR-A nesting bake-off already eliminated the dead ends
  (SVGnest-core-headless primary + BLF floor; pynest2d out).
- Media lifecycle handles P2's derived artifacts by class (regenerable),
  already sweep-aware.

## 3. Architectural blockers: NONE FOUND

Checked against the constitution + freeze:

- No P1 schema decision forecloses geometry (all additive slots open).
- No reverse-import pressure: extraction runs inside patterns_ai; the
  manufacturing boundary is untouched by P2 by design.
- No money surface anywhere near P2 scope (settlement-only rule safe).
- Enforcement flags / S6 / rate card are orthogonal manufacturing items —
  no coupling to P2.

## 4. Known risks going into P2 (register, not blockers)

| Risk | Standing answer |
|---|---|
| CV extraction quality on real chalk/cloth photos | Era-2 stance: propose + human confirm, never auto-accept; SAM/OpenCV are assistive |
| Metrology drift (mat wear, phone optics) | CalibrationMat custody chain + per-capture validation (ADR-E); re-validate on site data |
| Geometry format churn | ADR-C integer-µm + schema_version; additive-only |
| Two-runtime (node/python) ops complexity | ADR-F isolation; P0 harness already runs both headless |
| Scope gravity toward Era-3 nesting | Blueprint gates: Era 2 must earn trust before Era 3; owner gate on every block |
| P1 debt items leaking into P2 | Debt register in P1_ENGINEERING_REVIEW §7; the 3 id-500 one-liners should ride the FIRST P2 code block |

## 5. Entry criteria for P2 kickoff (all owner-side or first-block work)

1. **Owner approval** of the P1 Final Package + freeze (this package).
2. **Checkpoint commit** — owner's own hand, before new implementation
   (readiness N-1 discipline, still standing from Phase 3).
3. **D2/D3 mini-ADRs** — the two decisions the master plan slated "during
   P1": D2 piece-grain detail (per-size piece rows vs versioned piece
   sets) and D3 capture provenance depth (EXIF/device profiling).
   P1 forced neither; both must be decided in P2's FIRST design step
   because extraction writes into exactly those tables.
4. **P2 block map** — same discipline as P1: small owner-gated blocks,
   each with scope, do-not list, tests, browser proof, report, STOP.
   (Drafting that map = the first P2 deliverable, on approval.)

**STOPPED here. No P2 work begins without the owner's explicit go.**

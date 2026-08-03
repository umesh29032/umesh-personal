# P3 ENGINEERING REVIEW — hostile eyes on the generation era (2026-07-07)

**Method:** self-hostile re-read of nest.py / nest_runner.js /
marker_generation_service / views / templates + live UI probes.
**No sub-agent this phase** (small surface, single-threaded hostility);
recorded per the audit-honesty rule.

## Verdict
**SOUND.** Constitution intact; the owner's beat-the-baseline principle is
ENFORCED, not advisory. Debt registered below; nothing critical.

## 1. Correctness / honesty
- **The verifier is the product's spine:** every candidate is re-measured
  in shapely inside the isolated runtime (pairwise overlap ≤ 4 mm²
  rounding allowance, width ±0.5 mm, true length from real rings) — and a
  test feeds it a CRAFTED overlapping layout to prove it refuses. Engine
  fitness claims are never persisted as truth.
- **Benchmark honesty:** theory-vs-reality is labeled in the UI, the
  refusal message, and the frozen evidence payload. Width-band matching
  first; any-width fallback is flagged (`same_width_band: false`).
- **Determinism:** BLF fully deterministic (test-pinned byte-equal
  placements); SVGnest seeded (mulberry32) + trial-capped — same seed +
  same inputs reproduce on same hardware ordering (P0 finding, carried).
- **Reproducibility spine:** run params freeze the exact
  `geometry_row_id`s + seed + spacing + engine — any future pipeline can
  re-derive and compare.
- **Degenerate dev data caught a viz papercut live** (101×900 mm marker →
  very tall SVG; pieces below the fold): fixed with max-height scaling
  during the browser walk. Rendering convention (length horizontal)
  verified correct.

## 2. Architecture
- Nesting lives ENTIRELY in the isolated runtime; node is invoked from
  `nest.py`, never from Django. The ADR-F walls (source-scan both
  directions) re-ran green with the new files in place.
- `marker_generation_service` writes runs/candidates; the Marker is still
  born ONLY in `marker_service` (extended additively with `candidate` +
  `benchmark_evidence`; generated⇒candidate is now a service law with a
  DB-facing FK). I-1 repo scan covers both new models.
- Views stayed parse→gate→delegate — the generate POST parses ratio
  inputs and delegates; every rule lives in the service.
- Sync generation: a conscious, recorded scope decision (owner's P3 list
  has no async item; ADR-B worker remains the designed lever). Timebox +
  node-startup keeps requests ≤ ~25 s worst case at dev scale.

## 3. Performance
- BLF on the test set: <1 s. SVGnest: timeboxed (8 s in tests, 20 s
  default UI). NFP cache per run. Fine at factory cadence.
- Candidate pages derive metrics per render — trivial (one polygon-area
  pass over stored rings).
- P3 suite adds ~40 s to the app suite (real engines, real node) —
  accepted: the engines ARE the feature.

## 4. Security
- All 4 new URLs management-gated (worker 403 / anon 302 — swept).
- Ratio/width parsed defensively (`_int_or_404`, per-field numeric
  errors); engine name whitelisted in the service.
- Node subprocess: fixed script path, JSON-file input, no shell, timeout;
  hostile geometry crashes a subprocess, surfaces as a recorded error.
- SVG output built from numeric data only (no user strings except the
  piece key, which comes from pattern names already rendered site-wide).
  Tooltip titles use template-escaped-equivalent static composition.

## 5. Concurrency
- Promotion under select_for_update + promote-once check + MRK- advisory
  lock (P1) — double-click safe.
- Two simultaneous identical runs would both persist (append-only runs
  are FACTS of two requests) — correct by design, not a race.

## 6. Debt register (P3 additions)

| # | Item | Severity |
|---|---|---|
| 1 | Sync generation (no ADR-B worker yet) | conscious scope; lever ready |
| 2 | Holes ignored by engines (outer rings only; holes stored) | future lever, documented |
| 3 | SVGnest GA-lite search depth (≤201 trials) | quality lever, artifact-stable |
| 4 | Multi-width sweep = one run per width manually | UX lever |
| 5 | Piece keys in SVG titles unescaped-by-construction (names only) | watch |
| 6 | views.py keeps growing (mechanical split candidate, carried from P2) | cosmetic |

## 7. Future ADR candidates
- ADR-B worker activation (when generation moves off-request).
- Search-depth/quality profile ADR if the owner wants long overnight
  optimization runs (same engines, bigger timebox, candidate flood).

No redesign recommended.

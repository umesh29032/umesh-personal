# P1 — BLOCK 3E REPORT: The Yield Board (2026-07-07)

**Status: ✅ BLOCK 3E COMPLETE — STOPPED. P1 functional blocks are DONE.
Next deliverable (on owner approval only): the P1 Final Report package
(final report + engineering review + regression report + freeze
recommendation + P2 readiness). P2 Geometry/CV will NOT start without it.**

## Scope compliance
Yield Board ONLY: a pure read model over MarkerUsage + MarkerOutcome facts.
Nothing stored, nothing cached, no summary tables, no background jobs, no
AI, no editing, no searching. Sorting only; Product selection is the ONLY
filter. `derive_metrics()` reused everywhere (via `get_marker_summary` —
one code path for detail card and board). No schema change
(`makemigrations --check` clean).

## The board — Era 1's payoff page, live

`/patterns/yield/` — management-only. One row per marker of the selected
product, EVERY number derived at read:

- **Columns:** photo (gated rendition) · reference · status · origin ·
  used (with voided count when ≠0) · outcomes (honest `n=`) ·
  **Avg m/100** · **Avg m/garment** (new in summary: `avg/100`, same
  derivation, no second code path) · last used.
- **Sorts (badge links):** `avg` (best yield first — **honest-NULLs sort
  LAST**, never masquerade as good), `usage`, `recent`, `reference`.
  Unknown sort falls back to `avg` (test-pinned).
- **Best-row highlight** on the avg sort — the board answers its one
  question at a glance: *which marker feeds the factory cheapest.*
- **Honest language everywhere:** `n=` on every average, `— (no facts
  yet)` for missing metrics, footer states "All numbers derived at read…
  '—' means the facts don't exist yet, never a guess."
- **Empty states:** product with no markers, and no products at all.
- Product select = FancySelect (auto-upgraded), submits on change.
  Stacked-table canon (`.table-responsive` + `td[data-label]`) — @390
  renders as labeled cards.

## Query service (the only new logic, and it's read-only)

`marker_query_service.get_product_yield_board(product, sort)` — composes
`get_marker_summary` per marker; sorts in Python; SELECT-only
**proven by test** (`CaptureQueriesContext` asserts zero
INSERT/UPDATE/DELETE across a full board build). `get_marker_summary`
gained `avg_meters_per_garment` (= avg_m/100 ÷ 100, quantized 2dp) so the
detail card and the board can never disagree.

## Live browser proof (screenshots archived)

`3e_board_390.png` · `3e_board_desktop.png`. Walk: login → Yield board →
LOWER: **MRK-000002 · Used 1× · n=1 · 96.00 m/100 · 0.96 m/garment** —
the exact number Block 3D flashed at outcome time, now standing on the
board, still derived from the same two fact rows. 3-PATTI shows
MRK-000001 with `— (no facts yet)` (honest-NULL live). Product switch +
sort badges exercised.

## Test summary — patterns_ai suite now **94 tests, all green**

Aggregation: two-usage average math (60/90 → 75.00, n=2) · best-first on
avg with **NULLs last** · usage/recent/reference orderings · voided usage
excluded from counts/averages · zero-persistence (SELECT-only capture) ·
perf sanity ceiling (≤ 4 + 4·N queries for N=8 markers — documented, not
optimized, per scope). View: columns + honest `n=`/`—` language render ·
board scoped to selected product (other product's reference absent) ·
bad sort falls back to avg · empty states · worker 403 + anonymous
redirect. Full manufacturing suite serial ✅ · `makemigrations --check`
clean ✅ · import-linter: patterns_ai contract kept; the 1 broken contract
is the PRE-EXISTING aspirational "Acyclic app layering (target)"
(tracking.tests → production, known Arch-Remediation backlog) — zero
patterns_ai violations, state identical to Blocks 3A–3D ✅.

## Engineering review

1. **Technical debt:** board derivation is O(N markers × queries) — by
   scope and by F6 (facts stored, metrics derived). The documented future
   slot if a product ever holds hundreds of markers is a *derived-class
   cache* (regenerable, deletable — ADR-G semantics), explicitly NOT
   built. Perf test pins today's honest ceiling so growth is visible.
2. **Performance:** fine at factory volumes (a product carries a handful
   of markers); thumbnails lazy-load; page is one GET, zero JS beyond the
   select submit.
3. **Security:** management-gated (403/302 proven); renditions-only
   images (no `originals/` URL surface); no user input beyond
   product id + sort keyword, both validated against known sets.
4. **Long-term maintenance:** one derivation path (`derive_metrics` →
   `get_marker_summary` → board) — a future metrics change lands in ONE
   place and every surface follows; METRICS_VERSION already stamps it.
5. **Future ADR candidates:** none new.

## Findings

P1's Digital Memory era is functionally COMPLETE as working software:
capture → manual marker → library → usage → outcome → yield board, every
number derived at read, every fact immutable, every write behind a
single-writer service. Remaining master-plan P1 line items
(SuggestionEvent/CalibrationMat surfacing) have their schema + services
live since 2A/2B but no UI — an honest gap to state in the P1 Final
Report, not silently absorbed here.

**STOPPED. Awaiting owner review of Block 3E and the go-word for the P1
Final Report package.**

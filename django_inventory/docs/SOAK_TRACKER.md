# P2→P3 Soak Tracker — Worker Reporting Under Real Usage

**Opened:** 2026-06-11 (P2 shipped, commit dfcff6ca) · **Closes:** when ≥1 full Adda cycle has run through the worker report flow AND the soak review (§4) is written and owner-approved. **P3 (V2-1d M2M drop) is gated on this document.**
Scope guard (owner): no settlement, no MissingPiece, no Alter/Rework work during soak.

## 1) Soak success criteria (locked C2)
- [ ] ≥1 full Adda cycle: assignment → worker report (draft → submit) on each payable stage → stage completions → Adda done.
- [ ] Multiple workers report on at least one shared stage (isolation under real concurrency).
- [ ] At least one manager correction case exercised (`verified_quantity` path) — confirms D6 model suffices.
- [ ] Dual-write parity verified at soak end (§3).
- [ ] Soak review (§4) written, owner signs.

## 2) Live log (append entries here during soak — date · who · what)
Categories: `UX` worker feedback · `SCHEMA` contribution schema limitation · `EDGE` contribution edge case · `SEC` isolation/security observation · `PARITY` M2M↔task divergence · `BUG`.

| Date | Cat | Entry | Status |
|---|---|---|---|
| 2026-06-11 | — | Soak opened. P2 browser-verified pre-soak (draft/submit/locked/badges/mobile). | — |

## 3) Pre-V2-1d worklist (kept visible per owner)
| Item | Shape | Status |
|---|---|---|
| **Parity assertion** | `check_worker_task_parity` command + check.sh gate [5/5] (runs against the dev DB on every check). Re-run at soak end + immediately before V2-1d. | ✅ BUILT 2026-06-11 (c851f902, 3 tests) |
| Kill-switch semantics | Documented in V2_1_REVIEW §10 header (flag OFF ⇒ tasks stale ⇒ re-backfill before re-enable). | ✅ done (R0) |
| Clone rehearsal | up→down→up of the drop migration on a dev-DB clone. | TODO (at V2-1d time) |
| Stale docstrings (A8) | `worker_task.py:14` "deferred to V2-1c" + `adda.py:89-92` M2M note — fix inside the V2-1d PR (already on V2_1_REVIEW:218's list). | TODO (V2-1d PR) |

## 4) Soak review template (fill at soak end — the P3 gate document)
1. **Worker feedback** — usability, mobile, language, chip ergonomics, draft habits.
2. **Schema limitations discovered** — fields workers needed but schema lacked; any pressure toward the `attributes` JSONB (note: JSONB lands only with a real consumer — F1).
3. **Contribution edge cases** — multi-line patterns, replace-draft surprises, concurrent reports on one stage, reopen interactions, blank/partial lines.
4. **Isolation / security findings** — any cross-worker visibility, URL probing results, manager-bypass correctness.
5. **Parity observations** — `check_worker_task_parity` output; any divergence + root cause.
6. **Recommended changes** — classified: fix-before-V2-1d / fix-after / won't-fix.

## 5) Tracked risks from P2 (owner triage 2026-06-11 — none block roadmap)
- **Registry restore footgun** (TRACK): `registry.clear()+autodiscover()` cannot restore handlers in-process (modules already in `sys.modules` → re-import no-op → registry left empty). Tests must snapshot/re-register (pattern in `test_worker_report_view.py`). Candidate hardening later: guard `clear()` behind test-only flag or make `autodiscover()` force-reload.
- **Seed collisions** (TEST HYGIENE): seeded Stage codes / ClothColor names break naïve `objects.create` in tests — use `get_or_create` (helper pattern now exists).
- **Perf-baseline semantics** (DOCUMENT ONLY): worker-dashboard baseline measures the context builder; lazy querysets count zero until materialized — documented in `test_perf_baseline.py`.
- **Pre-existing foundation-purity gate failure**: ✅ FIXED 2026-06-11 (2399b044, P4.2 PR-0) — gate [1/5] KEPT.

## 6) P4.2 during soak — evaluation (owner asked)
**Recommendation: YES, run P4.2 during the soak window**, with sequencing rules.

For: (1) fully independent of the worker-report flow — touches barcode assembly/export/scan code paths only; (2) zero data migration (string FKs; verified by design review) → `git revert`-able; (3) characterization tests come FIRST and outputs must be byte-identical, so regressions surface before merge, not in the factory; (4) clears the import-cycle suppressions (P4.4 contract flip) and directly advances extraction readiness; (5) uses an otherwise idle engineering window.

Against (mitigated): two things in flight muddies attribution if a barcode page breaks mid-soak → mitigation = small reversible PRs in the planned order (characterization → assembly move → export/view move → contract flip), each gate-green before the next; pause P4.2 immediately if soak surfaces report-flow bugs needing fixes.

Suggested P4.2 PR order (from P4_2_BARCODE_DESIGN_REVIEW): characterization lock → relocate 3 assembly fns into `production/stages/barcode_generation/assembly.py` → relocate export production-reads + 4 views (D1: cross-cutting views → inventory/apps; stage panel stays production) → flip `.importlinter` layers (tracking BELOW production) + drop `ignore_imports` → `makemigrations --check` must say "No changes" at every step. Fold in the foundation-purity test-import chore.

— **Owner approved 2026-06-11 → ✅ P4.2 EXECUTED same day**, 4 commits, all gates green, `makemigrations --check` clean throughout (no data ever moved):
  - PR-0 `2399b044` purity chore + characterization baseline
  - PR-1 `23ba2b69` assembly (generate_for_cutting/_legacy/from_breakdown + _allocation_key) → `production/stages/barcode_generation/assembly.py`
  - PR-2 `ce930ac1` export service → production stage pkg; 4 /tracking/ views → `inventory/views/tracking_*.py`; urls → `inventory/tracking_urls.py` (namespace + every path/name preserved)
  - PR-3 `4b19fe01` layers flipped (tracking BELOW production), tracking ignore block deleted — **production↔tracking cycle GONE**; remaining worklist = production→expense (V2-3 facade) + raw_materials edges + test noise.
  Rollback for any step = `git revert` (pure code moves).

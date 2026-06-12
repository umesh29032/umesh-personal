> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: docs/REMEDIATION_PLAN.md (status banners) — M7 baseline snapshot.

# Remediation Scorecard — M7 (Phase 10) sign-off

> Final re-score of the M0–M7 remediation (branch `new_flask_app`, 2026-06).
> **Governing principle (locked): architect for multi-factory / async / scale; do NOT
> implement them. Target 8.5–9 at low complexity — NOT a forced 10/10.** See
> [docs/adr/0006](adr/0006-architect-for-scale-do-not-implement.md).

## Hard metrics (measured 2026-06-10)
| Signal | Value | Note |
|---|---|---|
| Tests | **417 green** (305 at P0.1 baseline) | full suite, `--parallel`, ~47s |
| Local gate | `scripts/check.sh` | ruff (blocking on changed) · import-linter (ratchet) · coverage floor 65% · mypy (report) |
| import-linter | **0 kept / 2 broken** | foundation-purity + acyclic — both = the **parked** production↔tracking/expense cycles (Phase 7) |
| ruff (full repo) | 2 (F403 `from .base import *` in settings) | conventional Django pattern — benign |
| mypy typed island | **211** untyped-def errors in `services.*`/`stages.*` | the ratchet target; `user_service` = first fully-green module |
| Security (CSO-lite) | clean | prod `SECRET_KEY=config('SECRET_KEY')` (no default), `DEBUG=False`, no raw `is_superuser` gates, no hardcoded prod secrets, argon2 + per-IP/email rate-limit |

## Dimension scorecard (review baseline → now; target band 8.5–9)
| # | Dimension | Was | Now | Evidence |
|---|---|---|---|---|
| 1 | Architecture | 7.5 | **8.7** | service-layer discipline (no-signals, single-writer) now codified as ADRs; stage-engine registry keystone; RBAC relocated to `accounts` foundation; models package |
| 2 | Scalability | 6.5 | **8.5** | dashboard N+1 killed (bulk `attach_layering_snapshots`, flat ~5 q); `assertNumQueries` oracles lock dashboard/list/costing; derived balances + reconciliation; async-ready signatures. Redis/pagination-remainder = deferred seams |
| 3 | Maintainability | 6.5 | **8.4** | docs reconciled + `DocAccuracyTests` auto-guard; archive discipline + ADRs; dead code removed; request-id logging. **Caps <9: `stage_views.py` 1446-line god-file (Phase 8 parked)** |
| 4 | Extensibility | 5.5 | **9.0** | stage engine: registry + autodiscover + `StageHandler` ABC + `contribution_schema`; new stage = a folder, proven by `test_open_closed_proof`. Biggest gain |
| 5 | Tech Debt | 6.5 | **8.3** | dead-code sweep, characterization net, F841/dead-flag cleanup. Remaining (stage_type shim, legacy cutting form, dual-write) is **tagged transitional** (`FUTURE-STAGE-REDESIGN`), not rot; +211 mypy ratchet tracked |
| 6 | RBAC / Security | 8.0 | **8.8** | three-concept RBAC, data-driven skill-gating (view+mutation consistent), menu+URL co-gating, request-cached principal, **self-lockout/last-admin rails now service-tested**, V2 worker-isolation leak closed |
| 7 | Data Model / Integrity | 8.5 | **9.0** | 26 CheckConstraints, PROTECT discipline, denorm + `reconcile_denorm` drift detection, immutable ledger, frozen cost snapshots, P0.5 migration-safety protocol |
| 8 | **Coupling** | 7.5 | **7.8** | **the sole laggard — by deliberate deferral.** import-linter 2/2 broken = production↔tracking + production↔expense lazy cycles. Fix = Phase 7 (P4.2 cycle break) **PARKED** pending the manufacturing-domain review (barcode ownership). → ~8.7 when executed |
| 9 | Observability | 7.5 | **8.3** | `RequestIDMiddleware` (ContextVar) + filter + `[{request_id}]` format + RotatingFileHandler + optional Sentry hook + structured service logging |
| 10 | Testing / Quality gates | 7.5 | **8.5** | 417 tests, characterization + perf + doc-accuracy + foundation-purity guards, single-writer/safety-rail tests, local gate + pre-commit, ~68% coverage |

**9 of 10 dimensions in/above the 8.5–9 target band.** Coupling (7.8) is the lone exception — held there *on purpose* by parking the cycle-break until the manufacturing-domain review settles barcode ownership ([P4_2_BARCODE_DESIGN_REVIEW](P4_2_BARCODE_DESIGN_REVIEW.md)).

## What's left (deliberately deferred — not gaps of neglect)
- **Phase 7** — production↔tracking cycle break (P4.2) + import-linter tighten (P4.4). Unlocks Coupling → ~8.7. Parked pending the domain review (owner decision).
- **Phase 8** — `stage_views.py` split (P2.8) + `draft_*` polymorphic move (P2.9). Stage-coupled → deferred with Phase 7. Unlocks Maintainability → ~9.
- **Ratchets (no deadline):** annotate the 211 island service/stage defs; pagination remainder.
- **Seams, not built (by design):** Redis/Celery async, multi-factory scoping, ledger closing-balance snapshot table, Sentry DSN, GH Actions CI.

## Verdict
The remediation hit its target: a clean, well-layered, well-tested single-site ERP with the
*seams* for multi-factory/async/scale but none of the speculative machinery. The one
below-target dimension (Coupling) is a known, documented, owner-parked decision — not a
defect. No over-engineering introduced.

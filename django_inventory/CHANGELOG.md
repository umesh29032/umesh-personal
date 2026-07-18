---
id: root-changelog
type: status-anchor
status: active
owner: handwritten
scope: all — system-level
anchors: —
verified: 2026-07-13
---

# Changelog — Kapil Enterprises Inventory

All notable changes. Dates are absolute. Branch `new_flask_app` work is
**uncommitted** pending owner approval; entries below the "Unreleased" heading
describe the working tree, not a tagged release.

## [Unreleased] — 2026-06-02

### Added
- **Access Control hub** (`/inventory/access/`, super-admin only): one read-only
  page with cross-functional RBAC matrices — Roles × Sidebar Pages, Production
  Stages × skills/roles, Users roster, Roles summary — each deep-linking to its
  existing editor. Fills the master-spec "single admin access surface" gap
  without rewriting the battle-tested CRUD pages. Doc: `docs/PAGES/ACCESS_CONTROL.md`.
- Worker payroll / settlement stack (expense app): allocation-driven earnings,
  immutable ledger, advances (separate loan pool), on-demand settlements,
  per-worker scoping. Production stage costing (frozen `processing_cost` on
  advance, cleared on reopen). Docs: `PAYROLL_ARCHITECTURE.md`,
  `SETTLEMENT_ARCHITECTURE.md`, `STAGE_COSTING_PLAN.md`.

### Fixed (Stage A re-audit, 2026-06-02)
- Settlement reference cross-worker race (`SETL-NNNN` IntegrityError → 500) —
  transaction-scoped Postgres advisory lock serializes reference allocation.
- `total_settled` / `total_earnings` now net ledger reversals by the reversed
  entry's category (a reversed settlement payment no longer inflates either).
- `PayrollSettlementItemInline` made read-only in Django admin (was mutable,
  could break `advance_deducted == Σ amount_recovered`).
- Cutting `add_bundle_item` / `add_item_to_bundle` re-sync a sourced breakup's
  `consumed_count` after overwriting an item count (was leaving it stale).

### Docs
- Fixed `SYSTEM_DESIGN.md` drift: `StageWorkAssignment` is a standalone FK model,
  not an M2M `through`; `AddaStageRecord.workers` is roster-only.
- `PAYROLL_ARCHITECTURE.md` status header → IMPLEMENTED.
- New `docs/PAGES/` + `docs/FLOWS/` structure; QA logs updated
  (`docs/QA/bugs_found.md`, `fixes_applied.md`, `STAGE_A_REAUDIT_2026_06_02.md`).

### Verification
- 276 tests green (was 270). No migration drift. `manage.py check` clean.
- Browser QA on :8000: Access Control hub renders for super-admin (0 console
  errors, no mobile overflow); manager direct-URL → 403; payroll/costing/my
  pages render clean.

---

## Earlier (committed history — see `git log`)
- `4fd746d2` barcode_generation stage + breakdown materialization + export system
- `13bde910` critical audit bugs — migration 0017 + scan race + ActiveManager wiring
- `b422570a` cutting overhaul + 4-phase scaling work + audit doc
- `17d029f5` cutting_pattern stage + ProductPattern + reopen + curated roles
- `1bba7571` stage library + sidebar/stage RBAC + per-product flow editor

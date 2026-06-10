# Stage A Re-Audit — Master-Spec Sweep (2026-06-02)

Static + structural audit of the uncommitted costing/payroll/settlement/RBAC stack on
branch `new_flask_app`, mapped against the master ERP spec. Method: 7 parallel domain
deep-readers → adversarial skeptic per critical/high finding (default-refute). 19 agents.

> **Headline:** every finding the readers tagged *critical* or *high* was **refuted or
> downgraded** under adversarial verification. The system is in good shape. The real list
> is a handful of medium/low bugs + one genuine **feature gap vs the master prompt** (unified
> RBAC admin page) + doc drift. No data-loss, no money-corruption, no production-reachable
> security hole found.

---

## A. Confirmed real defects (worth fixing)

| ID | Sev | File | Defect | Fix |
|----|-----|------|--------|-----|
| **payroll-2** | medium ✅confirmed | `expense/services/settlement_service.py:39-51,116` | `_next_reference()` reads global max `reference` with an **unlocked SELECT**; per-worker `WorkerProfile` lock does NOT serialize two concurrent settlements for *different* workers → both compute `SETL-0002` → 2nd hits unique constraint → unhandled `IntegrityError` → **500**. Loud-fail, non-corrupting (txn rolls back). | PG sequence, or `select_for_update` on max row, or catch `IntegrityError` + retry. |
| **payroll-3** | medium | `expense/services/payroll_service.py:124-142` | `total_settled` sums `SETTLEMENT_PAYMENT` debits but **does not net reversals** (reversal rows are category `REVERSAL`). After a reversal, dashboard still shows full settled amount. (Corroborates prior QA deferred item.) | Subtract reversals of settlement_payment debits. |
| **db-integrity-1** | medium | `expense/admin.py:55-58` | Parent `PayrollSettlementAdmin` is read-only (`_MoneyReadOnlyAdmin`) but `PayrollSettlementItemInline` has **no `has_add/change/delete` overrides** → admin can mutate `amount_recovered`, breaking `advance_deducted == Σ items.amount_recovered`. | Add the 3 `has_*_permission → False` overrides. |
| **cutting count-clobber** | low (skeptic-surfaced) | `cutting_service.py:622-625, 675-678` | `add_item_to_bundle` / `add_bundle_item` `update_or_create` keyed on `(bundle,pattern,color)` — if it matches a row originally created **with** a `source_breakup` (via `add_pieces_to_bundle`), it overwrites `count` WITHOUT calling `_recompute_breakup_consumed` → that breakup's `consumed_count` desyncs. Cannot go negative (`available_count` clamped) or double-allocate. Needs mixing two UI flows on same key. | Recompute on the matched row's source after update, or include `source_breakup` in the key. |

> Note: the readers' *high* "consumed_count drift" claims (dbag-1/2/5) were **refuted** —
> `consumed_count` is path-disjoint (only `add_pieces_to_bundle` writes it, always with
> source), `_recompute` is an absolute re-sum, `available_count = max(count-consumed,0)`.
> The clobber edge above is the only real residue.

## B. Hardening / defense-in-depth (medium-low, optional)

| ID | Sev | File | Item |
|----|-----|------|------|
| sec-3 | medium | `tracking/views/barcode_views.py:161` | `scan_piece` is `@login_required` only (no `PRODUCTION_ROLES`); mutates `last_scanned_by`. Siblings use `ProductionRoleMixin`. |
| dbag-4 | medium | `tracking/models.py:87-90` | `BarcodeBatch` has no `CheckConstraint(start_seq<=end_seq)` and no range-overlap guard. Service is correct; DB has no backstop against raw/admin writes. |
| dbag-3 | medium | `production/models.py:998-1001` | `CuttingBundleItem.unique_together=(bundle,pattern,color)` excludes `source_breakup`. Service-guarded; no DB backstop. |
| prod rbac-1 | low (downgraded from *critical*) | `production/views/stage_views.py:262-307` | `StagePanelView` IS gated (`ProductionRoleMixin` + service-layer skill gates re-enforce). Only residue: panel render doesn't hide per-*skill* like `AddaDetailView` does — info-disclosure UI nit, not priv-esc. |

## C. Refuted — NOT defects (recorded so they aren't re-raised)

- **sec-1** export re-download "lateral access" → **refuted**: system is flat-role (`PRODUCTION_ROLES`), no per-Adda data-scoping exists *by design*; sibling `barcode_list` uses identical gate.
- **sec-2** WorkerAdvance MEDIA leak → **refuted**: `/media/` route is `if DEBUG:` only; `production.py` sets `DEBUG=False`; whitenoise serves static only. **Not production-reachable.** (Supersedes the "latent security" note in memory — it's safe in prod.)
- **payroll-1** `opening_advance` excluded from `advance_outstanding()` → **refuted**: intentional; `opening_advance` is informational, recoverable loans must be dated `WorkerAdvance` rows. Adding it would manufacture an unclearable phantom balance. Only a stale model-comment nit.
- **prod arch-1** `stage_service.py` stub → **refuted**: nothing imports it; `production/services/__init__.py` is the canonical re-export hub (exports all `reopen_*`).

## D. Feature gap vs the MASTER PROMPT (not a bug — new build)

The master prompt demands **ONE unified admin access-control page** managing user-types +
roles + skills + sidebar items + production stages + page URLs + module actions. Today this
is **5 separate pages** (Team Members, User Skills, Roles, Stages, Sidebar Access).

- The skeptic correctly noted no *prior internal spec* required consolidation — so it's not a
  spec *violation*. But the **user's master prompt today explicitly requires it**, so it's a
  real feature gap. (rbac-1, rbac-2)
- Related cleanups the unified page would absorb: `user_type` legacy field still editable in
  user forms (rbac-4); `is_superuser`/`is_staff` dual-auth path alongside role (rbac-5);
  `SidebarItemRule` doesn't cover every menu item, new items invisible until hand-seeded (rbac-3).

**Confirmed-clean separation (master-spec §RBAC):** `user_type` (1:1 display) ✅ separate from
`role`/`extra_roles` (M2M, gates pages) ✅ separate from `skills` (M2M, gates stages via
`access_service`) ✅. Role≠Skill is real and enforced. Only the *admin surface* is fragmented.

## E. Docs (master-spec doc structure)

| Item | Status |
|------|--------|
| `ARCHITECTURE.md`, `docs/production/RBAC.md`, `PAYROLL_ARCHITECTURE.md` | ✅ present, mostly in sync |
| `SYSTEM_DESIGN.md:116,422` claims `StageWorkAssignment` → M2M `through` | ✅confirmed **drift** (low) — code keeps standalone FK; `PAYROLL_ARCHITECTURE.md:18` already records the fix-TODO |
| `PAYROLL_ARCHITECTURE.md:3` header "ARCHITECTURE REVIEW — no code" | stale — feature is fully implemented |
| `CHANGELOG.md` at root | ❌ missing |
| `docs/PAGES/`, `docs/FLOWS/` dirs + per-page template | ❌ missing (only 2/21 docs have mandated sections) |
| `docs/QA/audit_log.md` (spec name) | named `AUDIT_2026_06_02.md` instead |

## F. Also from prior QA memory (still open)

- **`reverse_settlement` service** — none exists. With admin now read-only (delete blocked),
  the orphan-debit scenario is closed *unless* a delete path is added. So it's a **missing
  capability** (can't undo a settlement), not an active bug.

---

## Stage A verdict

Architecture sound. Single-writer, ledger-immutability, PROTECT FKs, Decimal money, cost-freeze
+ reopen-clear, role/skill separation — all hold. Net actionable: **4 real bugs (all ≤medium),
~4 hardening items, 1 feature gap (unified RBAC admin), doc sync.** No blocker to the user's
own functional testing. Next stages (B browser-QA, C fixes, D docs) gated on owner priority.

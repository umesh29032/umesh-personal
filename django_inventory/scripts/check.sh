#!/usr/bin/env bash
# Local CI gate (M0.2 / REMEDIATION_PLAN). Run:  bash scripts/check.sh
#
# Policy (owner decision 2026-06-09): LENIENT + RATCHET. BLOCKING checks are all
# green today, so the gate passes from day one. REPORT-ONLY checks surface legacy
# + the M4 cycle-break worklist without red-walling progress. Ratchet report-only
# checks into blocking as milestones land.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
PY=env/bin
SETTINGS=config.settings.local
APPS="accounts core raw_materials production tracking expense storefront inventory machines"
COVERAGE_FLOOR=65          # baseline 67% (2026-06-09); ratchet up as coverage grows
fail=0

echo "──────────── BLOCKING ────────────"
echo "[1/4] import-linter · foundation-purity (core + accounts import no domain app)"
( cd config && ../$PY/lint-imports --contract foundation-purity ) >/tmp/check_il.log 2>&1 \
  && echo "  ✓ foundation-purity KEPT" \
  || { echo "  ✗ foundation-purity BROKEN"; tail -20 /tmp/check_il.log; fail=1; }

echo "[2/4] tests + coverage run"
$PY/coverage run --source=config \
  --omit='*/migrations/*,*/tests/*,*/tests.py,*/apps.py,config/config/*,*/admin.py' \
  config/manage.py test $APPS --settings=$SETTINGS >/tmp/check_test.log 2>&1 \
  && echo "  ✓ $(grep -E '^Ran [0-9]+ test' /tmp/check_test.log) — OK" \
  || { echo "  ✗ tests FAILED"; tail -30 /tmp/check_test.log; fail=1; }

echo "[3/4] coverage floor ≥ ${COVERAGE_FLOOR}%"
$PY/coverage report >/tmp/check_cov.log 2>&1
if $PY/coverage report --fail-under=$COVERAGE_FLOOR >/dev/null 2>&1; then
  echo "  ✓ $(tail -1 /tmp/check_cov.log)"
else
  echo "  ✗ coverage below ${COVERAGE_FLOOR}%: $(tail -1 /tmp/check_cov.log)"; fail=1
fi

# V2-1d replacement invariant: the single-writer discipline survives the M2M.
echo "[4/4] WorkerStageTask single-writer (V2-1d: no task writes outside worker_task_service)"
strays=$(grep -rn "WorkerStageTask.objects.create(\|\.status = WorkerStageTask" config --include=*.py \
  | grep -v "worker_task_service.py" | grep -vE "/tests/|/migrations/")
if [ -z "$strays" ]; then
  echo "  ✓ worker_task_service is the sole WorkerStageTask writer"
else
  echo "  ✗ stray task writes (route through worker_task_service):"; echo "$strays"; fail=1
fi

# V2-2: financial-event tables have exactly one writer (CLAUDE.md rule 5).
echo "[4b/4] AddaSettlement single-writer (V2-2: no settlement writes outside adda_settlement_service)"
strays2=$(grep -rn "AddaSettlement.objects.create(\|AddaSettlementItem.objects.create(" config --include=*.py \
  | grep -v "adda_settlement_service.py" | grep -vE "/tests/|/migrations/")
if [ -z "$strays2" ]; then
  echo "  ✓ adda_settlement_service is the sole AddaSettlement/Item writer"
else
  echo "  ✗ stray settlement writes (route through adda_settlement_service):"; echo "$strays2"; fail=1
fi

# V2-3 PR-A (D-V3.4): SWA earning lines have exactly TWO writers — the legacy
# allocation path (create + era-A void) and the settlement path (create at
# finalize + void at reverse). Creation or voided_at writes anywhere else break
# the "settlement money only moves through the settlement lifecycle" invariant.
# ── pool_service.py exclusion (R1 gate repair, 2026-07-04) ──────────────────
# WHY CORRECT: the grep below matches ANY `.voided_at = ` assignment, but
#   pool_service's only match voids `WorkerStageAllocation` (the S4-P3
#   production-truth piece-pool row) — NOT StageWorkAssignment. pool_service
#   is that model's sole owner-locked writer (S4_PHASE3_RECEIPT), so the line
#   the gate flagged is the DESIGNED write path of a different table.
# WHY SAFE: pool_service is money-free by lock (PDD §31.3 / S4: "WSA ⊥
#   costing/earning/rate/settlement", owner-locked + tested). It imports no
#   expense model; an SWA write appearing there would already violate the
#   app-boundary contract before it violated this gate.
# REVISIT WHEN: (a) pool_service ever imports/creates StageWorkAssignment or
#   any expense model (then REMOVE this exclusion and route the write through
#   the two services), or (b) gate 4c is upgraded to model-aware matching
#   (e.g. match `StageWorkAssignment` within N lines of `.voided_at =`) —
#   the better long-term fix, which makes this exclusion obsolete.
# ── expense_service.py exclusion (R5, 2026-07-05) ────────────────────────────
# WHY CORRECT: its only `.voided_at =` match voids `FactoryExpense` (R5,
#   PDD §21 append-only cost record) — NOT StageWorkAssignment. expense_service
#   is FactoryExpense's designed sole writer (create/void, no edit).
# WHY SAFE: ADR-0011 locks expense_service as ledger/settlement/costing-free —
#   it imports no SWA/ledger model; a test pins zero ledger interaction
#   (test_adr_0011_zero_ledger_interaction). An SWA write appearing there
#   would violate ADR-0011 before it violated this gate.
# REVISIT WHEN: same (a)/(b) as pool_service above.
echo "[4c/4] StageWorkAssignment two-writer (V2-3: writes only in allocation_service + adda_settlement_service)"
strays3=$(grep -rn "StageWorkAssignment.objects.create(\|\.voided_at = " config --include=*.py \
  | grep -vE "allocation_service\.py|adda_settlement_service\.py|pool_service\.py|expense_service\.py" | grep -vE "/tests/|/migrations/")
if [ -z "$strays3" ]; then
  echo "  ✓ allocation_service + adda_settlement_service are the sole SWA writers"
else
  echo "  ✗ stray SWA writes (route through the two services):"; echo "$strays3"; fail=1
fi

echo ""
echo "──────────── REPORT-ONLY (never fails the gate) ────────────"
echo "[ruff] full-repo legacy (changed code is enforced blocking by pre-commit):"
echo "       $($PY/ruff check config 2>&1 | tail -1)"
echo "[import-linter] full acyclic-layers progress (this list IS the M4 worklist):"
( cd config && ../$PY/lint-imports 2>&1 | grep -E 'Contracts:' | tail -1 | sed 's/^/       /' ) || true
echo "[mypy] report-only — global lenient, service+stages typed island (P6.4 ratchet):"
echo "       $($PY/mypy config --config-file mypy.ini 2>&1 | tail -1)"
echo "       (full list: $PY/mypy config --config-file mypy.ini)"

echo ""
if [ "$fail" -eq 0 ]; then echo "GATE: ✓ PASS"; else echo "GATE: ✗ FAIL"; fi
exit $fail

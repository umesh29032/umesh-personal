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
APPS="accounts core raw_materials production tracking expense storefront inventory"
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

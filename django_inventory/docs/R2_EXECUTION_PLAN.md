---
id: r2-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# R2 EXECUTION PLAN — Layering Earnings (per-layer pay)

> Phase R2 of [IMPLEMENTATION_ROADMAP_PDD_V1.md](IMPLEMENTATION_ROADMAP_PDD_V1.md),
> derived from 🔒 [PDD v1.0](PRODUCT_DESIGN_DOCUMENT.md) §14/§17/§18, decisions
> §27-D1 (each worker reports OWN layers) + §27-D2 (good-only payable).
> STATUS: **✅ ACCEPTED by owner 2026-07-04 (uncommitted,
> per owner instruction: commits postponed to a stable checkpoint).**
> Owner resolutions honored: P-1 toggle included · P-2 3-patti layering
> UNGROUPED · P-3 flat ₹10 both roles · P-4 PAY-2 mandatory-reporting confirmed.
> Results: gate PASS 726 tests (+12) · golden OK · live browser E2E on
> 3-PATTI-006: worker reported 45 layers on a 360px phone → frozen Expected
> ₹450.00 (My Work + My Earnings agree). Deviation: My-Work unit label
> ("pcs"→schema unit) fixed in-scope.
> Anchors verified against code 2026-07-04 (post-R1, commit c957fa84).

## 0) What R1 recon already proved (changes almost nothing is missing)

| Fact | Evidence |
|---|---|
| Worker report page ALREADY renders for layering | schema-driven view; `LayeringHandler` inherits the base single-quantity schema (`stages/base/handler.py:125`) |
| report → complete → freeze works for layering E2E | R1 test froze ₹120 = 12 × ₹10 on a layering task (`test_r1_navigation.MyWorkSectionTests`) |
| Settlement pays completed layering lines unchanged | draft gate + resolver are stage-agnostic (verified in R1 button test with a layering draft) |
| `per_layer` cost method exists | `CostMethod.PER_LAYER` (`models/core.py`) |
| D1 (own-layers attribution) needs NO code | contribution lines already hang off each worker's own task |

**R2 is therefore a THIN phase:** label polish + reconciliation warn + config
enablement + an E2E money test. No new models, no migrations, no chokepoint edits.

## 1) Scope (PDD refs)

| # | Item | PDD |
|---|---|---|
| R2.1 | `LayeringHandler.contribution_schema` override — unit label **"layers"** (today inherits "pieces"; worker phone UI must say layers) | §14 |
| R2.2 | **Reconciliation WARN** at layering complete: Σ completed workers' `good_quantity` vs breakup `lay_count` → non-blocking warning naming the delta (mirrors M-6 philosophy; never blocks) | §14 |
| R2.3 | **Flow-editor `credits_workers` toggle** — the knob is NOT in the flow editor today (admin-only). PDD §6 lists it as a flow-editor knob. ❓ P-1 below: include here or defer (admin path works) | §6/§17 |
| R2.4 | **Config runbook step** (data, not code): 3-patti layering → `cost_method=per_layer`, `cost_rate=10`, `cost_billed_at=NULL` (UNGROUP — F2 zeroes grouped pay), `credits_workers=True` | §14/§27-C2 |
| R2.5 | **E2E money test**: 2 workers report layers independently → each frozen expected = own layers × 10 → settlement draft → finalize books ledger CREDITs → reverse restores | §17/§18 |

OUT of scope: C3 completion guard (=R3), alter/missing capture (D2 confirmed
good-only), any settlement/ledger/chokepoint code change, R3+ work.

## 2) Files to modify

| File | Change |
|---|---|
| `config/production/stages/layering/handler.py` | `contribution_schema` override: label "Layers laid", unit `layers` |
| `config/production/stages/layering/service.py` | complete-time reconciliation WARN (Σ WSC good vs `lay_count`; log + surfaced message; NON-blocking) |
| `config/production/views/flow_views.py` + `templates/production/product_flow.html` | credits_workers checkbox (ONLY if P-1 approved) |
| `config/production/tests/test_r2_layering_earnings.py` (new) | see §6 |
| docs | this plan status, production GUIDE rows, pool/worker docs N/A note |

## 3) Database migrations
**NONE.** All fields exist (`cost_method/cost_rate/cost_billed_at/credits_workers`,
WSC quantities, `AddaStageRoleRate`).

## 4) Prerequisites / owner decisions ❓

| ID | Question | Recommendation |
|---|---|---|
| P-1 | `credits_workers` toggle in the flow editor as part of R2, or keep admin-only config for now? | include (small; PDD §6 declares it a flow-editor knob; owner will need it per-product repeatedly) |
| P-2 | 3-patti layering is likely GROUPED (`cost_billed_at` set) in the live flow — confirm UNGROUP so layering pays its own ₹10 (grouped member structurally pays 0, §27-C2) | ungroup at config step |
| P-3 | ₹10/layer applies to ALL roles on layering (cutting master AND helper), or role-differentiated via `WorkflowStageRoleRate`? | same ₹10 both (add role rates later via existing editor if needed) |
| P-4 | Enabling `credits_workers` makes worker reporting MANDATORY before layering completes (existing PAY-2 guard: a paying stage refuses completion with zero completed contributions). Confirm this operational change. | confirm — it IS the point of paying the stage |

## 5) Behavior after R2 (the flow, end-to-end)

```
admin: flow editor → 3-patti layering: per_layer · ₹10 · ungrouped · pays
admin: start Adda → AddaStageRoleRate freezes ₹10 (S2 snapshot)
admin: assign workers (skill-gated)
worker phone: report page (existing) → "Layers laid: 45" → complete
   → expected_earning frozen = 45 × 10 = ₹450 (visibility; My Work + My Earnings)
2nd worker: reports OWN layers independently (D1)
layering complete: PAY-2 needs ≥1 completed report; WARN if Σ ≠ lay_count (R2.2)
settlement (existing queue): draft shows lines → finalize → ledger CREDIT ₹450
   → Expected→Earned→Paid progression on the worker portal (unchanged machinery)
```

## 6) Tests to add (`test_r2_layering_earnings.py`)

1. Schema: layering report schema carries unit "layers" (and cutting still "pieces").
2. Two-worker independence (D1): A reports 30, B reports 15 → A expected ₹300,
   B ₹150; A's page never shows B's numbers (reuse R1 leak pattern).
3. Reconciliation: lay_count=45, Σ reported=40 → complete succeeds + WARN
   recorded/surfaced; Σ=45 → no warn.
4. PAY-2: credits_workers=True + zero completed reports → layering complete
   refused with actionable message.
5. Settlement E2E: finalize books CREDIT stage_earning = layers × frozen rate
   per worker; item frozen; reverse nets to 0.
6. Grouped guard regression: grouped layering + stale ₹10 snapshot → pays 0 (F2).
7. Golden ₹225 byte-identical + full suite green.

## 7) Risks

| Risk | Mitigation |
|---|---|
| PAY-2 blocks layering completion once payable (operational surprise) | P-4 explicit; error names pending workers (existing F3 machinery); owner confirms |
| Grouped seed flow zeroes pay silently | P-2 ungroup in config runbook + test 6 pins the guard |
| Reconciliation warn accidentally blocking | test 3 asserts complete SUCCEEDS with mismatch |
| Rate entered wrong (₹10 typo) | existing S1.1 `rerate_stage_role` (super-admin, audited, until settlement) — no new code |
| Unit label regression on other stages | test 1 asserts cutting schema unchanged |

## 8) Rollback strategy
No migration ⇒ `git revert` restores code exactly. Config rollback = flow editor
(rate/method/grouping editable until an Adda settles; started Addas keep their
frozen snapshots — by design, PDD §12). Money rollback = existing settlement
REVERSE (never edit).

## 9) Acceptance criteria

- [ ] Worker phone report page for layering says **layers** and submits via the
      single chokepoint; each worker sees own expected ₹ immediately after complete.
- [ ] Two assigned workers earn independently (D1) — verified in browser on the
      3-patti flow, 360px.
- [ ] Layering complete warns (non-blocking) on Σ layers ≠ lay_count.
- [ ] Payable layering refuses completion with zero completed reports (PAY-2),
      message actionable.
- [ ] Settlement finalize pays layers × frozen ₹10 per worker; reverse restores;
      golden ₹225 byte-identical.
- [ ] `bash scripts/check.sh` PASS; docs synced same session.

## 10) Implementation order (estimated)

1. Schema override + test 1 — ~20 min
2. Reconciliation WARN + tests 3 — ~45 min
3. Flow-editor toggle (if P-1 approved) — ~40 min
4. Money tests 2/4/5/6 — ~1 h
5. Config runbook step on dev DB + browser verify (2 workers, 360px) — ~45 min
6. Docs sync + summary — ~20 min

Total ≈ half a working day. Single focused commit at acceptance (same as R1).

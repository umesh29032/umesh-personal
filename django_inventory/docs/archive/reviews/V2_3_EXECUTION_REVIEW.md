> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: [docs/PROJECT_KNOWLEDGE_MAP.md](../../PROJECT_KNOWLEDGE_MAP.md) (Post-Cutover ERP State reproduced there) + [ADR-0007 addendum](../../adr/0007-allocation-era-ledger-cutover.md).

# V2-3 Execution Review — settlement-primary cutover (SWA repurpose closeout)

Status: REVIEW — no implementation. Same rigor as V2-1d/V2-2 execution reviews.
Date: 2026-06-11. Owner locks honored (post-reassessment):
L1 V2-3 is next · L2 lever + era-A path NOT removed · L3 settlement-time
crediting becomes the primary/DEFAULT path · L4 physical deletion stays
soak-gated · L5 G6 before G5/G2 · L6 G4 thin read-model early · L7 ADR-0008
boundaries (no direct Order↔Adda).

Scope sentence: make settlement the only *default* way earnings book, keep the
legacy path as a fully-working env lever, and close the two integrity holes the
audit found where legacy correction paths can mutate settlement money outside
the V2-2 lifecycle. Zero schema change.

---

## 1) Current-state analysis (audited today, line-verified)

**The legacy allocation path is small and fully mapped:**
- ONE service entry: `allocate_stage_work` (expense/services/allocation_service.py:42)
  — already flag-gated (PR-D) + symmetric era-B guard.
- ONE UI entry: `CuttingBundleItemAllocateView` (production/views/stage_views.py:1399),
  URL `cutting-item-allocate` (production/urls.py:107). Form rendered in
  `_stage_panel_cutting.html` behind `can_allocate = is_management ∧ sr open`
  (stage_views.py:952) — NOT yet flag-aware.
- ONE void service: `void_allocation` (allocation_service.py:144), called from
  `CuttingAllocationDeleteView` (stage_views.py:1443, URL :108) and from the
  shared reopen skeleton (production/services/_shared.py:135-139, PAY-3 sweep).
- Flag touchpoints: exactly 2 (settings/base.py:181 default=True;
  allocation_service.py:66 gate). No template reads it.

**SWA read surfaces are already era-agnostic** — the §11.4 payoff is real:
`worker_assignments`, `worker_production_stats`, `worker_stage_earnings`,
`worker_adda_earnings` (payroll_service.py:215-280) all read non-voided SWAs
regardless of `adda_settlement` NULL-ness; settlement lines flow through every
rollup and the My Earnings/detail screens with no changes. The cutting
workspace allocation display reads per-item SWAs (bundle_item-keyed; settlement
SWAs have bundle_item NULL so they don't pollute it).

**Two integrity holes (NEW findings — live in today's code):**

**H1 — CRITICAL: reopen voids settlement money outside the lifecycle.**
`reopen_stage_record` (_shared.py:135-139) voids ALL non-voided SWAs on the
stage record — including era-B settlement earning lines. Reopening a settled
stage today: reverses the settlement's STAGE_EARNING credits one by one, voids
its SWAs (re-arming the era-B guard → lines look settleable again), while the
AddaSettlement stays FINALIZED, its recoveries stay active, and no
SETTLEMENT_* timeline event fires. The settlement status lies; a second
settlement could re-book the same lines while the first still reads finalized.
The pre-existing `FUTURE-STAGE-REDESIGN` comment at that exact spot predicted
this ("revisit this SWA void then"). Reachable since V2-2 PR-B shipped.

**H2 — HIGH: void_allocation accepts settlement SWAs.**
`CuttingAllocationDeleteView` resolves any SWA by pk within the Adda; the
service has no era check. A POST against a settlement earning line reverses
settlement money piecemeal, same corruption family as H1. The workspace UI
doesn't render buttons for them (bundle_item NULL), but the URL is open.

Both holes are *pre-V2-3 bugs*, not cutover side-effects — they must close
regardless of the default flip, and FIRST (PR-A below).

**Minor current-state facts that shape scope:**
- Legacy tests assume flag-ON default: test_expense, test_views,
  test_allocation_ui, test_reconciliation, test_reopen_voids_pay,
  test_stage_credit, test_open_closed_proof (+ CutoverLeverTests expectations).
- Worker visibility under flag OFF: My Earnings is 100% ledger-driven, so
  between "work completed" and "Adda settled" a worker sees no movement.
  WSC frozen `expected_*` (Option B visibility) exists but is surfaced only on
  the report screen and settlement preview — not on My Earnings.
- `worker_production_stats` derives "pieces produced" from SWAs → under
  settlement-primary this stat lags until settlement, though WSC production
  truth exists immediately.

---

## 2) Exact files affected

**PR-A (guards — bug fix, ships first, independent of cutover):**
| File | Change |
|---|---|
| config/expense/services/allocation_service.py | `void_allocation`: refuse `adda_settlement__isnull=False` → "this is a settlement earning line — reverse settlement ADST-X instead" |
| config/production/services/_shared.py | reopen: `select_for_update` the SR up front; BLOCK reopen if non-voided settlement SWAs exist on it (name the ADST refs); narrow the PAY-3 sweep to `adda_settlement__isnull=True` (era-A only) |
| config/expense/tests/test_v2_3_guards.py (new) | void-settlement-SWA refused; reopen-after-settle blocked w/ reference named; reopen-before-settle still voids era-A only; reverse-settlement-then-reopen succeeds |

**PR-B (cutover default + UI gating):**
| File | Change |
|---|---|
| config/config/settings/base.py | `default=True` → `default=False` (lever inverted: env `LEDGER_CREDIT_AT_ALLOCATION=True` = rollback) |
| .env.example | reflect new default; True documented as the rollback value |
| deploy/README.md | rollback section: cutover state is now code-default; lever semantics |
| config/production/views/stage_views.py | `can_allocate &= settings.LEDGER_CREDIT_AT_ALLOCATION` (creation only) |
| config/production/templates/production/_stage_panel_cutting.html | flag OFF: hide allocate forms, show one-line note "Earnings are booked at Adda settlement"; KEEP existing-allocation rows + void buttons (era-A corrections stay legal) |
| 7 legacy test files (list in §1) | pin `@override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)` — they become the lever's regression suite, not dead tests |
| config/expense/tests/test_adda_settlement_views.py | CutoverLeverTests expectations invert (OFF is default; ON via override) |

**PR-C (visibility + semantics closeout):**
| File | Change |
|---|---|
| config/expense/services/payroll_service.py | new read helper `unsettled_expected(worker)` — Σ WSC.expected_earning where settlement_line NULL, expected frozen (non-NULL), task status completed/verified |
| config/expense/views.py + templates/expense/my_earnings.html | "Unsettled (expected)" strip on My Earnings — Option B visibility finally surfaced where workers look |
| config/expense/services/payroll_service.py (optional, D-V3.3) | repoint `worker_production_stats` pieces to WSC production truth |
| docs/ARCHITECTURE_V2.md §11.4, docs/adr/0007, CLAUDE.md status line | status: cutover default flipped; deletion clause pending soak |
| scripts/check.sh (optional, D-V3.4) | gate [4c]: SWA writers = allocation_service + adda_settlement_service only |

**Migrations: NONE.** No model, no field, no data migration anywhere in V2-3.

---

## 3) Migration impact

Zero schema migrations. The cutover is a settings default + view/template
gating + service guards. Era-A rows are untouched; their population simply
stops growing by default. No backfill, no clone rehearsal needed (nothing to
rehearse), no `makemigrations` output expected — gate check will prove it.

Data-direction safety: rows created under flag OFF (settlement SWAs) are valid
under flag ON, and vice versa — the V2-2 cross-era guard is symmetric and
already test-proven in both flag states. Flipping the env lever back and forth
cannot create incoherent data.

---

## 4) Rollback strategy

| Layer | Rollback | Cost |
|---|---|---|
| PR-A guards | revert commit | none — guards are pure refusals, write nothing |
| PR-B default flip | set env `LEDGER_CREDIT_AT_ALLOCATION=True` (no deploy, restart only) or revert commit | none — symmetric guard keeps mixed data coherent |
| PR-C visibility | revert commit | none — read-only surfaces |

The lever's regression suite (the 7 pinned legacy test files) keeps the
rollback path *tested*, not just present — flag ON stays green in CI until the
soak-gated deletion PR removes it.

---

## 5) Invariant review (the V2-2 locked set, under V2-3)

| Invariant | Effect |
|---|---|
| Ledger append-only | unchanged; H1/H2 fixes strengthen it (no out-of-lifecycle reversals) |
| Double-credit impossible (symmetric) | strengthened — default OFF stops new era-A creation; guard machinery stays armed for lever-ON |
| Settlement single-writer (gate 4b) | unchanged; optional 4c extends discipline to SWA |
| Frozen snapshots never re-read as truth | unchanged |
| Draft gate: payable stages completed | gains its REVERSE protection — settled stages can no longer reopen (H1 fix); the qty-freeze rationale at finalize now holds permanently, not just during the transaction |
| D-S grain (one SWA per contribution line) | unchanged |
| D-R (recovery stamps, unsigned, append-only) | unchanged |
| Provenance spine (WSC.settlement_line ↔ SWA ↔ ledger) | unchanged; H2 fix protects it from piecemeal voiding |
| Era marker structural (SWA.adda_settlement) | unchanged; era-A becomes a closed historical set by default |
| §11.5 lock order | unchanged; reopen gains SR `select_for_update` BEFORE its settlement-line check to close the reopen-vs-finalize race (finalize already locks SRs) |

New invariant introduced by V2-3 (to be stated in §11.4):
**"Settlement money is only ever mutated by adda_settlement_service."** Reopen
and void become structurally incapable of touching era-B rows.

---

## 6) Interaction with ADR-0007

V2-3 *is* the Option A cutover act, executed exactly as the ADR prescribed:
era-A rows coexist untouched forever; the cross-era guard stays symmetric and
permanent; the flag remains the rollback lever — only its DEFAULT inverts,
which is the owner's explicit cutover decision (locks L3/L4 of this review).
The ADR's deletion clause (remove flag + legacy path + era-A code) is NOT
exercised — it stays soak-gated as a separate future PR. ADR-0007 gets a
status addendum, not an amendment: "cutover default flipped 2026-06-XX;
deletion pending true soak."

## 7) Interaction with V2-2 settlements

- Settlement becomes the sole default creditor; the queue's "waiting" gate,
  preview classes, and finalize/reverse lifecycle are untouched.
- The era-A "excluded" panel keeps working for historical rows; its population
  freezes, so the coarse worker+stage grain (known MED risk) stops mattering
  for new work and decays to a historical-display concern.
- H1/H2 fixes are V2-2's missing armor: the reversal lifecycle (PR-C of V2-2)
  becomes the ONLY door to settlement money, which was the design intent
  ("if an accountant makes a mistake today, what restores truth tomorrow") —
  reopen-a-settled-stage now answers "reverse the settlement first", same as
  every other correction.
- Recovery, payment narrowing, supersede chains: no interaction.

## 8) Interaction with future G1–G7 phases

- **G1 Costing-2:** labor truth becomes single-sourced (ADST) for all new
  Addas — material valuation joins a uniform labor side. The pre/post-G1
  costing-era stamp noted in the reassessment still applies; V2-3 adds none.
- **G3 Variance valuation:** consumes settlement variance counts — unchanged
  seam (§11.10 source-agnostic).
- **G4 Adda-360 (early thin slice, L6):** V2-3 simplifies its money panel —
  one provenance story for new Addas; era-A label logic already exists for
  history. Build G4 AFTER V2-3 lands so it never renders the dual-default era.
- **G5/G6/G2 (L5 order):** no interaction; nothing in V2-3 touches product,
  inventory, or revenue surfaces. ADR-0008 boundaries untouched (L7).
- **MissingPiece/Alter:** feed variance counts at settlement — V2-3 doesn't
  move the seam. The H1 reopen-block slightly tightens their future world:
  a settled stage's counts can only change via supersede, which is exactly the
  correction story those modules will rely on.
- **Reporting:** uniform earning path forward; historical windows still need
  the era label — already structural.

## 9) Risks discovered (this review's audit)

| # | Sev | Risk | Disposition |
|---|---|---|---|
| R1 | **CRITICAL** | H1: reopen voids settlement SWAs outside lifecycle — live today, reachable from the UI | PR-A fix (block + narrow sweep); test both directions |
| R2 | **HIGH** | H2: void_allocation URL-reachable on settlement SWAs | PR-A fix (era guard in service — defense at the single chokepoint, not the view) |
| R3 | MED | 7 legacy test files break on default flip | mechanical: pin override — they become the lever's regression suite |
| R4 | MED | Worker visibility gap under flag OFF (no My Earnings movement until settlement) — adoption risk during soak | PR-C "Unsettled (expected)" strip from WSC frozen fields; zero schema |
| R5 | LOW | reopen-check vs finalize race (check-then-save without SR lock) | PR-A: `select_for_update` SR first; finalize already locks SRs |
| R6 | LOW | "pieces produced" stat lags until settlement (SWA-sourced) | D-V3.3 — recommend repoint to WSC production truth in PR-C |
| R7 | LOW | dev `.env`s with no flag set silently flip behavior on pull | expected and intended (that IS the cutover); release note in commit body |

## 10) Phased PR plan

**PR-A — settlement-money armor (bug fix; ships even if cutover were cancelled)**
Guards H1+H2 + reopen SR lock + new guard test file. Suite + gate green.
Live dev check: attempt reopen of a settled 3-PATTI-001 stage → refusal names
ADST-0003; reverse ADST-0003 → reopen succeeds → re-settle.

**PR-B — cutover default + UI gating (the L3 act)**
Settings default False; allocation form gated in workspace (display + era-A
void retained); legacy tests pinned to lever-ON; CutoverLeverTests inverted;
.env.example + deploy/README updated. Live dev check: workspace shows the
note, allocation POST refused, settlement loop unaffected; export
LEDGER_CREDIT_AT_ALLOCATION=True restores the full legacy behavior.

**PR-C — visibility + closeout**
`unsettled_expected` + My Earnings strip; D-V3.3 stats repoint (if approved);
docs status sync (ARCHITECTURE_V2 §11.4, ADR-0007 addendum, CLAUDE.md);
optional gate 4c. Live dev check: worker with completed-unsettled work sees
the expected strip; after finalize it moves into earned.

Estimated: one session, three commits, zero migrations.

## 11) Decision points for the owner (before code)

- **D-V3.1 — default flip mechanics:** interpret L3 as `default=False` in
  base.py (env `True` = rollback lever). RECOMMENDED yes — anything weaker
  isn't "primary/default".
- **D-V3.2 — reopen-of-settled-stage policy:** BLOCK with "reverse settlement
  ADST-X first" (recommended; matches correction-lifecycle and
  work-that-happened immutability) vs auto-reverse the settlement on reopen
  (rejected: hides a money event inside a production action).
- **D-V3.3 — worker_production_stats pieces source:** repoint to WSC
  (production truth, immediate) vs leave SWA-sourced (settled pieces, lags).
  RECOMMENDED repoint, PR-C, read-only.
- **D-V3.4 — check.sh gate 4c (SWA single-writer):** cheap, optional,
  recommended.

## 12) Go/No-Go verdict

**GO — with PR-A mandatory first.** The cutover itself is small, reversible by
env var, schema-free, and its guard machinery is already live and tested. The
audit's real finding is that V2-2's settlement money is currently mutable
through two legacy correction doors (reopen, void) — that armor is needed
*today* independent of any cutover, and it defines the PR order. No blocker
found. Awaiting owner approval on D-V3.1–D-V3.4 to begin PR-A.

---

## 13) EXECUTED — closing record (2026-06-11, PR-A/B/C committed)

Owner locks D-V3.1–D-V3.4 all approved + implemented.
- **PR-A** settlement-money armor: reopen of settlement-credited stage BLOCKED
  (names ADST refs); void_allocation refuses era-B; PAY-3 sweep era-A-only;
  gate [4c/4]. Live proof: both refusals on settled 3-PATTI-001 named ADST-0003.
- **PR-B** cutover: default False; allocation UI hidden (era-A history readable,
  void on open stages); 8 legacy classes pinned = lever regression suite;
  CutoverLeverTests inverted (default proven without override). Live proof:
  fresh-process default False, allocation refused, workspace note rendered,
  era-A ₹135 visible, env lever restores True.
- **PR-C** visibility: `unsettled_expected` (era-aware, non-overlapping) +
  Expected (unsettled) → Earned (settled) → Paid (cash) labels on My Earnings +
  worker detail; D-V3.3 production stats repointed to WSC (settlement-timing
  independent). Lifecycle tests: expected 30 → settle 0 → reverse 30; era-A
  credited lines never show as expected.

### Responsive/mobile review (CLAUDE.md rule 11 — first review under the rule)
No new page introduced; PR-C touched existing mobile-first surfaces. The new
stat cards enter the existing `.stat-grid` (auto-fit minmax grid → stacks on
phones); verified at 360×740 (Android), 768 (tablet), 1280 (desktop): cards
wrap without horizontal scroll, labels readable, no fixed-width tables added.
The cutting-workspace cutover note is plain text in an already-responsive
panel. Workspace allocation forms (desktop-era flex) were REMOVED from the
default render — a net mobile improvement.

### Post-Cutover ERP State (owner-requested)
- **Production truth** = `WorkerStageTask` (who was assigned / participated) +
  `WorkerStageContribution` (what was reported; `verified_quantity` = accepted
  correction, both preserved). Written ONLY via worker_task_service. Frozen
  `expected_*` on contributions = visibility, never money.
- **Financial truth** = `WorkerLedgerEntry` (append-only; single writer
  ledger_service) created at **Adda settlement** (`finalize_adda_settlement`),
  reversed/superseded only through the settlement lifecycle. AddaSettlement +
  frozen items = the approval record; the ledger = the money.
- **Worker earnings** come from: settlement of their completed contributions
  (verified-else-reported × frozen rate) → STAGE_EARNING credits with line
  provenance (`WSC.settlement_line` → SWA → ledger). Display ladder:
  Expected (unsettled) → Earned (settled) → Paid (cash via payment-only
  PayrollSettlement). Era-A history remains readable/reversible.
- **Adda labor cost** comes from: AddaSettlement totals (settled truth) +
  era-A allocation credits for legacy rows (UI labels the split); frozen
  per-stage `processing_cost` remains the manufacturing-cost view (cost ≠ pay).
- **Future phases plug in:** MissingPiece/Alter = lifecycle modules reading
  production truth, feeding settlement variance through the §11.10
  source-agnostic seam (settlement consumes counts, never owns their flow).
  G1 material costing joins at the Adda on a now-uniform labor side. G4
  Adda-360 composes production truth + settlement timeline + ledger — all
  read-only, all existing. G5 finished goods will read completion/packing
  truth (later scan-derived under TM-2) — never coupled to settlement. TM-1
  tracking-mode config rides the locked WorkflowStage policy seam.

**V2-3 status: COMPLETE pending owner sign-off. Remaining on ADR-0007: the
soak-gated deletion PR (remove lever + era-A path) — after real-worker soak.**

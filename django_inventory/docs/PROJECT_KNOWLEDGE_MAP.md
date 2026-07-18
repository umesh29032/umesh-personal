---
id: project-knowledge-map
type: entry-index
status: active
owner: handwritten
scope: all — navigation/state
anchors: —
verified: 2026-07-13
---

# PROJECT KNOWLEDGE MAP — Kapil Enterprises ERP

> **Mandatory first read** for every new developer — and for the owner
> learning the system. Business flow → architecture → database → code.
> Companion reading order: [LEARNING_PATH.md](LEARNING_PATH.md) ·
> every active doc: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
> Stack: Django 5.0.1 + PostgreSQL, server-rendered, mobile-first (rule 11).

---

## 1) The business in one diagram

```
 CLOTH ROLLS ──▶ ADDA (production batch of ONE product) ──▶ GARMENTS
 (raw_materials)        moves through STAGES                (future G5 stock)
                Layering → Pattern Design → Cutting → Barcode-Gen
                     workers REPORT what they made (phones!)
                              │
            ┌─────────────────┴───────────────────┐
   PRODUCTION TRUTH                        FINANCIAL TRUTH
   "kitna kaam hua"                        "kitne paise bane/diye"
   WorkerStageTask/Contribution            WorkerLedgerEntry (append-only)
   (production app)                        written ONLY at SETTLEMENT
                                           (expense app)
```

One sentence: **workers report work → owner settles the Adda (earnings book)
→ owner pays cash later → everything is traceable forever.**

## 2) Request flow (what happens on one click)

> **CANONICAL** for the generic request pattern (View→Service→Model→history).
> Per-app specifics live in APPS/<app>/REQUEST_MAP; exact call chains in
> REQUEST_JOURNEYS. Those reference this; they don't redefine the pattern.

```
Browser ──▶ urls.py ──▶ SidebarAccessMiddleware (menu hidden ⇒ URL blocked)
        ──▶ View  (permission_service / skill+assignment gates;
        │          NEVER writes more than one row itself)
        ──▶ SERVICE  (config/<app>/services/ — ALL multi-row writes,
        │             @transaction.atomic, explicit — NO signals, ADR-0001)
        ──▶ Models / PostgreSQL (constraints enforce truth even against bugs)
        ──▶ history_service (timeline event, append-only)
        ◀── redirect + message → server-rendered template (base.html canon CSS)
```

## 3) Production-truth flow (the work story)

```
manager: set_stage_workers(sr, [ids])          ← SOLE WST writer (CI gate 4/4)
   └▶ WorkerStageTask rows  (≤1 ACTIVE per (stage_record, worker);
                              un-tick = CANCELLED, never deleted)
worker phone: report_contributions(task, lines)
   └▶ WorkerStageContribution rows (reported_quantity IMMUTABLE — owner §6)
worker: complete_worker_task
   └▶ FREEZES expected_rate / expected_earning   (visibility, NEVER money)
management (P1): set_verified_quantity          ← correction, reported untouched
stage completes: BLOCKS while workers are mid-work (C3, R3 — transitional
   IN_PROGRESS-only; auto-assignment is fully REMOVED (freeze closeout C-1,
   2026-07-05 — manager assignment = the ONLY roster source, PDD amendment 4);
   the strict-C3 flip to also block on ASSIGNED stays owner-gated pending
   manual testing); super-admin override w/ audited reason; untouched
   ASSIGNED still auto-cancel (F3)
```
**C-TM (locked):** every capture path — manual today, barcode scans tomorrow —
converges into WSC through worker_task_service. No second door, ever.

## 4) Financial-truth flow + settlement lifecycle

```
            (reads production truth; NEVER edits it)
 settlement queue ─▶ DRAFT (ADST-0007; scratchpad, no money)
        │ discard ok
        ▼ FINALIZE  — adda_settlement_service (strict lock order — canonical:
        │   docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md)
        ├─ per line:  SWA earning line + ledger CREDIT (stage_earning)
        │             qty = verified-else-reported × frozen expected_rate
        ├─ per chosen advance: ledger DEBIT (advance_recovery) + PSI row
        ├─ per worker: FROZEN AddaSettlementItem (what the owner approved)
        └─ AddaHistory: SETTLEMENT_FINALIZED
        ▼ mistake?
 REVERSE (or REVERSE+SUPERSEDE → successor draft, chain kept)
        └─ compensating ledger rows · SWA voided · PSI stamped reversed_at
        ▼ cash day (separate event!)
 PayrollSettlement (payment-ONLY) → ledger DEBIT (settlement_payment)
```
Worker sees three NON-overlapping numbers: **Expected (unsettled) → Earned
(settled) → Paid (cash)** — proven by tests.

**Eras (ADR-0007, cutover EXECUTED in V2-3):** old rows credited at
allocation = era-A (`SWA.adda_settlement` NULL, readable+reversible forever);
new world = settlement-first (`LEDGER_CREDIT_AT_ALLOCATION` default False;
env True = tested rollback lever; physical deletion soak-gated).

## 5) Adda lifecycle

```
START (one click: pick product → code auto e.g. 3-PATTI-003)
  └▶ AddaStageRecord per WorkflowStage (per-product flow, owner-configured
      in the Flow Editor: order, rate, billed-at grouping, pay-eligibility,
      future Tracking Mode TM-1)
LAYERING   rolls attach (weight verified) … leftovers MANDATORY at complete
           (production-INPUT stage — non-payable since the stage-trio spec)
PATTERN DESIGN  (code cutting_pattern) — pattern master phone CHECKLIST of
           ProductPatternAssignments + photos/video evidence; FIXED-per-Adda pay
CUTTING    breakup per size, bundles, workers report color/size/qty  ← first
           real quantities; duration auto from timestamps (owner rule)
BARCODE-GEN  BarcodeBatch ranges per (adda,color,size) — piece identity =
           (adda, seq), printed payloads PERMANENT (ADR-0010 §3)
COMPLETE → settle → pay.  REOPEN allowed until money: settlement-credited
           stage refuses reopen, names the ADST (V2-3 armor).
```

## 6) Database relationships (core ER sketch)

```
 ClothRoll ──(adda FK, 1 roll→1 adda)──▶ Adda ◀──(product FK)── Product
     │ leftovers                          │ stage_records          │
     ▼                                    ▼                        ▼
 RemainingCloth          AddaStageRecord ◀──(workflow_stage)── WorkflowStage
                              │ worker_tasks                  (order, rate,
                              ▼                               credits_workers,
                        WorkerStageTask ──▶ User              cost_billed_at)
                              │ contributions
                              ▼
                  WorkerStageContribution ──settlement_line──▶ SWA
                      (color,size,qty)                          │ adda_settlement
                                                                ▼
        WorkerLedgerEntry ◀──(assignment FK)── SWA      AddaSettlement
              ▲ (sole writer: ledger_service)               │ items (frozen)
              └── PSI.ledger_entry (recovery)               ▼
                                                   AddaSettlementItem
 AddaHistory / ClothRollHistory / ProductHistory  = append-only timelines
 BarcodeBatch (adda,color,size, seq range)        = piece identity
```
**FK policy:** PROTECT on every money/history anchor (a financial row's
parents can never vanish) · CASCADE only where a child is meaningless without
its parent · SET_NULL for optional references.

Full service-connection diagram: [LEARNING/04_SERVICE_LAYER.md](LEARNING/04_SERVICE_LAYER.md).

## 7) The chokepoint services (why they exist, what breaks without them)

> Canonical list of the single-writer services. Other docs say "the chokepoint
> services" and link here — this table (not a hard-coded count) is the source of
> truth, and the underlying `*_service.py` files are guarded against rename by
> `core.tests.PkalsNavigationGuardTests`.

| Service | Sole writer of | Who may call | Invariant it protects | If removed/bypassed |
|---|---|---|---|---|
| `worker_task_service` | WST + WSC (+expected freeze, verified qty) | views/stage services; workers only via report view | roster = participation; reported immutable; ALL capture paths converge (C-TM) | second truth source → settlement pays unverifiable numbers |
| `adda_settlement_service` | AddaSettlement(+Item), era-B SWAs | management UI only | a line is paid AT MOST ONCE; full provenance item↔SWA↔ledger↔WSC; strict lock order | double-pay, deadlocks, unauditable money |
| `ledger_service` | WorkerLedgerEntry | other expense services only | append-only money; reversal nets in-period | silent balance corruption, permanent |
| `allocation_service` | era-A SWAs (+era-A void) | lever-ON only (rollback) | symmetric double-credit guard; era-B lines refuse void | legacy path racing settlements |
| `cost_service` | processing_cost freeze; `role_rate_for`; `effective_pay_rate` = the F2 chokepoint (grouped→0 AND non-payable→0, one rule everywhere) | stage services + every expected recompute | standard-cost frozen price-at-time; grouped/non-payable stages yield rate 0 (C-1 + A360 one-rule — no double/phantom pay) | retro cost rewrites; grouped double-pay; hidden expectations |
| `stage_rate_service` | AddaStageRoleRate + RateCorrectionAudit | stage services; super-admin rerate | frozen per-(SR,role) payable rate; correct-until-settlement, audited | retro re-pricing of frozen work |
| `settlement_service` | PayrollSettlement(+Item incl. R7 write-offs) | management UI; fnf orchestration | payment-only event; write-off = audited PSI without ledger debit | cash without trail; silent loan forgiveness |
| `advance_service` | WorkerAdvance | management UI | separate loan pool; monthly workers refused (M-2 temporary rule) | unrecoverable loans |
| `payroll_service.set_pay_basis` | WorkerPayBasisAudit (+ the pay_basis write) | super-admin | audited monthly/piece-rate switches, settlement-lock-joined | unaudited pay-structure flips |
| `expense_service` | FactoryExpense | management create / super-admin void | factory-level cost only (ADR-0011) — zero ledger interaction, test-pinned | salary leaking into Adda cost |

(`history_service` also single-writes every `*History` row; `consume_leftover`
writes material consumption, C-1; `fnf_service` is ORCHESTRATION-only — it
writes nothing itself. The list above is the canonical set; it is not a fixed
number — phases may add a single-writer service.)

## 8) Phase history (how we got here)

| Phase | Shipped | One-line why |
|---|---|---|
| V2-1 a→d (2026-06-09→11) | WST/WSC truth layer; M2M dropped (0035) | per-worker truth instead of a bare roster |
| P2 + validation | schema-driven worker report UI, phone-first | workers can actually report |
| R1 | locked Stage Contract + archetypes + scan seam | stages stay open-closed forever |
| V2-2 PR-A→D (2026-06-11) | AddaSettlement event: finalize/reverse/supersede + mgmt UI | money at the RIGHT moment, corrections first-class |
| V2-3 (2026-06-11) | settlement-FIRST default + money armor + Expected/Earned/Paid | one default money path; legacy = lever |
| C-1 (2026-06-11) | grouped-member guard, leftover write path, ADR-0009/0010 | regret-prevention before real data |
| P1/P2/P3 (2026-06-12) | verified-qty surface, completion warning, duality hint | normal human mistakes stop costing pay |
| Frontend S1 + A-scope (2026-06-12) | mobile table fix, vendor central, canon CSS vocabulary | money screens = reference UI for G4/Missing/Alter |
| Foundation S1–S5 + F1–F4 (2026-06-14) | rate snapshots, good/alter/missing, piece pools, enforcement flags (default OFF) | production-truth foundation ahead of stitching |
| Production audit 01–17 (2026-06-14→15) | 92 findings, 45 fixed, 700 green — CLOSED baseline | stabilization before features |
| 🔒 PDD v1.0 + roadmap (2026-07-04) | product design frozen; R1–R11 derived | execution, not redesign |
| **PDD stream R1–R8 + A360 (2026-07-04→05)** | nav+F1 · layering earnings→later non-payable · C3 guard · MONTHLY pay basis · FactoryExpense+ADR-0011 · verified-qty audit · F&F (only_worker + write-off) · Pattern Design rename + checklist + FIXED pay + generic snapshots · A360 read-only hub + one-rule non-payable freeze | the complete earning/settlement/overview foundation (gate 811, all owner-accepted, uncommitted) |
| **R10 machines · OP-1 + hardening · pre-Phase-3 A-D · Phase-3 config + 3 journeys · excellence audits (2026-07-05→06)** | machines app + Stage.work_type/machine_type · multi-worker dim-scoped allocation (blind, verify-reduce, audited void) · damaged/machine_code/first_report_at · REAL flows T-SHIRT 16/LOWER 13/3-PATTI 12 settled ₹801.00/₹344.25/₹633.00 · UX+engineering sweeps (gate 885) | **MANUFACTURING V1 FROZEN — [MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md); next = AI Pattern Intelligence ([AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md](AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md); enterprise-era KICKOFF archived)** |

## 9) ADR summary (locked decisions — contradicting one needs a new ADR)

| ADR | Lock |
|---|---|
| 0001 | services own all multi-row writes; NO signals |
| 0002 | one writer per ledger/history table |
| 0003 | RBAC = type/role/skill; stage access skill-gated |
| 0004 | tracking = append-only history primitive |
| 0005 | production truth ≠ financial truth (Option B; expected_* = visibility) |
| 0006 | architect for scale, don't implement early |
| 0007 | era coexistence + lever; cutover EXECUTED; deletion soak-gated |
| 0008 | commerce boundary: Order↔Adda only via stock; revenue never in manufacturing (+margin addendum) |
| 0009 | cost duality NEVER additive; full-cost formula; labor-source rule; purchase-price semantics |
| 0010 | global references forever; multi-factory = one DB + site dim (never fork); barcode payloads permanent; rework case-scoped; no price fields in production |
| 0011 | monthly salary = factory-level FactoryExpense; NEVER allocated into per-Adda cost until an owner-approved allocation phase (which must not rewrite history) |

## 10) Roadmap (canonical: IMPLEMENTATION_ROADMAP_PDD_V1.md — the PDD-derived roadmap; ROADMAP_REVIEW_POST_C1_2026_06_11.md = pre-PDD historical source for R11/gated items)

```
DEPLOY ─▶ soak (G4 thin slice rides along; TM-1 week 1-2)
  ─▶ MissingPiece ─▶ Alter/Rework ─▶ G1 material costing ─▶ G3 variance ₹
  ─▶ [soak gate: ADR-0007 deletion PR]
  ─▶ G6 SKU ─▶ G5 finished-goods stock ─▶ G2 orders/revenue
  ─▶ Reporting (full) ─▶ G7 planning.   TM-2 = Barcode/Traceability review.
```

## 11) Standing rules every contributor inherits

Mobile-first is FUNCTIONAL (rule 11): worker flows phone-first; management
responsive; every UI review documents 360/768/1280 verification ·
honest-NULL (unknown ≠ zero) · backfill only known facts · work-that-happened
is immutable · soft-state over delete · one writer per truth table (CI gates
4/4, 4b/4, 4c/4) · gate must pass (`bash scripts/check.sh`).

---

> **This is the ONE overview** (H4) and the AI routing manifest's `entry.overview`.
> If any other doc disagrees on the big picture, this wins; deeper facets link
> down from here (§7 = the chokepoint canonical list; §2 = the request-flow
> canonical). Front door for all readers: [START_HERE.md](START_HERE.md).

### Verification Sources
Synthesized from the apps' models/services, the ADRs, ARCHITECTURE_V2, and the
chokepoint services. **Verified from code** (verified against commit f067daf0,
2026-06-12; re-verify the cited file if it changed). Finalized 2026-06-13 after
the consolidation + longevity-hardening sessions. Confidence: High.

---
id: docs-factory-operations-master
type: truth-lock
status: active
owner: frozen
scope: project
anchors: —
verified: 2026-07-18
---

# FACTORY OPERATIONS MASTER — Garment Manufacturing Blueprint

> **Status: 🔒 v3 UNDER MANUFACTURING V1 FREEZE (2026-07-06) — Phase-2 review + Phase-3 first-pass config EXECUTED; all three real flows proven + settled (§8–§12). Operations source of truth; changes via owner ruling/ADR ([MANUFACTURING_V1_FREEZE.md](MANUFACTURING_V1_FREEZE.md)).**
> **This document is the single source of truth for every manufacturing
> operation.** Once an operation's section is owner-approved, Phase 3 configures
> it through the existing engine (Stage row + flow entry + rate) — **zero new
> code**. Changes to an approved operation happen HERE first, then in config.
>
> v2 = v1 + a 5-lens adversarial review (43 findings incorporated). **v3 = v2 +
> the architecture destruction audit (owner-ruled 2026-07-06):** §7 Future
> Decision Register added (owner-approved future modules, NOT built) and the
> four pre-Phase-3 hardening items are now LIVE in the engine (gate 885):
> **Damaged/scrap** = 4th observation (pays nothing, never pools, counts as
> capacity) · **machine_code** stamped on every contribution · task
> **first_report_at** timestamp (passive) · audited manager-only
> **void-submitted-report** (the ONLY path that lets production go UP after
> submit — verification confirms/reduces, never increases; owner business rule).
> Governing engine docs: PDD v1.0 (frozen) · R10_MACHINE_STAGES_ARCHITECTURE
> (frozen rules 1-12) · ALLOCATION_WORKFLOW_AUDIT (OP-1 hardening receipts).

---

## 1. How an operation maps onto the engine (the ONLY vocabulary Phase 3 may use)

If a field can't be expressed in this table, it does not go into config — it
goes into §5 (open decisions).

| Blueprint field | Engine knob | Values available today |
|---|---|---|
| Operation Name | `Stage.name` (display, renameable — floor language welcome) + `Stage.code` (immutable slug) | free text / slug |
| Worker instruction | `Stage.description` — one line of floor language, rendered as a hint on the report page *(LIVE — report hero, §9)* | free text |
| Stage Category | `Stage.category` → `StageCategory` (DATA) | Pre Production · Stitching · Printing · Finishing · Dispatch (+ new rows) |
| Work Type | `Stage.work_type` | `manual` · `machine` (machine ⇒ machine_type mandatory) |
| Machine Type | `Stage.machine_type` → `MachineType` (DATA) + physical `Machine` registry + operator windows | Cutting · Overlock · Flatlock · Single Needle · Elastic Machine (+ new rows via UI) |
| Required Skills | `Stage.access_by_skill` — access ∩ assignment predicate | 10 skills after the §8 masters pass (+ new Skill rows via UI) |
| Assignment Strategy | manager roster (`set_stage_workers`) — **manager assignment is the ONLY roster source (PDD am.4)** | explicit picker, skill-filtered |
| Split Strategy | `WorkflowStage.allocation_dimensions` | `none` · `quantity` · `color_size` — grain may only COARSEN downstream (D1) |
| Pay Basis / Staffing | `WorkerProfile.pay_basis` (per-WORKER, never per-stage) — monthly workers' lines settle ₹0; salary = ADR-0011 `FactoryExpense` (factory-level, never allocated per-Adda) | `piece_rate` · `monthly` |
| Worker UI | generic stage report — Good/Alter/Missing/Damaged per allocated dim, prefilled rows, blind, machine chip (⚙ code) when on a machine. *(Checklist mode is NOT config: it exists only in the bespoke Pattern Design handler; a new checklist operation = code = [NEEDS-DECISION].)* | schema-driven |
| Manager UI | generic panel: roster · Split-the-work · machine holder · output board (Allocated/G/A/M/Damaged/Verified/Expected ₹) · complete; Report Review = verify (reduce/confirm) + audited void-report | no code per stage |
| Owner Visibility | A360 category chips + money strip · Manufacturing Costing (standard vs settled + variance) · Payroll · timeline | no code per stage |
| Verification Rules | Report Review `set_verified_quantity` — verified ≤ good, ≤ allocation where one exists; audited | global, H-1/J-1 hardened |
| Settlement Behaviour | `cost_method` (`per_piece` · `per_bundle` · `per_layer` · `fixed_cost`) × `credits_workers` × `cost_billed_at` (default **self** for every operation below) + role-rate overrides | pays verified-else-good × frozen rate |
| Quality Rules | Alter/Missing/Damaged observations (immutable) + verification + settlement reconciliation | rework/missing MODULES not built (M-7 = 0) |
| Special Business Rules | must be enforceable by existing guards, or honest floor discipline, or [NEEDS-DECISION] | — |
| Future Extension Notes | never built speculatively | — |

**Sequencing:** `Previous/Next` below = TYPICAL position. Real order = per-product
`WorkflowStage.order` in the flow editor. **One library, many product flows** —
each product picks and orders its subset.

## 2. Global rules (apply to EVERY operation — never restated per-op)

1. **Blind reporting — including the worker's own number.** A worker sees only
   their allocated Colour+Size labels; pool quantities AND their own allocated
   quantity are hidden by design (anti-anchoring: workers count physical
   pieces, never copy a target). The compensating control is the manager
   board's Allocated-vs-reported gap. One prefilled row per allocated pair.
2. **Good = pieces that PASSED this operation. Always. At every stage.**
   Non-negotiable invariant: Good feeds the next operation's pool and the
   worker's pay — inflating it (e.g. to "pieces inspected") corrupts the pool
   and trips the allocation bound. Pay problems are solved with rates or pay
   basis (§5.3), never by redefining Good.
3. **Four buckets, one meaning each (Good / Alter / Missing / Damaged):**
   **Alter** = a piece needing rework, found AT this operation — regardless of
   who caused the defect. A piece received already-defective is NOT
   self-reported as the receiver's Alter: the worker shows it to the manager,
   who corrects the UPSTREAM stage via verification (the audited H-1 path).
   **Missing = a piece you received and cannot hand back** — the clean
   theft/loss signal. **Damaged = scrap, beyond repair** (oil stain, scorch,
   needle-chew): pays nothing, never enters any pool, counts against the
   allocation like the others. A short handover = tell the manager (upstream
   correction), never Missing. Unfinished work = save draft, submit when YOUR
   pieces are done — never "balance the numbers". A WRONG submit (fat-finger)
   is recovered by the manager's audited **void-report** in Report Review —
   the worker re-enters; nothing is ever edited in place.
4. **Verified-else-good is the final business truth — and verification must
   happen BEFORE the stage advances.** The downstream pool freezes write-once
   at advance; a correction made after advance fixes PAY only (pool repair =
   reopen, which downstream consumption deliberately blocks). Manager
   discipline: Report Review, then Complete. The worker sees the corrected
   number on My Earnings; the manager tells them at verification time — never
   let payday be the first sight of a correction.
5. **Money moves only at settlement.** Machines never earn. **Machine helpers
   are NOT piece-rated** — the engine cannot split one contribution between
   two workers: helpers are salaried (ADR-0011 FactoryExpense) or own a
   separable credited operation (e.g. Thread Cutting). Rate-sharing
   (70/30-style) = [NEEDS-DECISION §5.9] if the owner's floor uses it.
6. **A "piece" = one garment-equivalent** (one complete panel set). The cutting
   snapshot (APSCPB) counts garments only; components/trims/ribs/collars are
   NEVER counted in the breakdown or any pool.
7. **Manager assignment is the only roster source.** No auto-assignment ever.
8. **Category is presentation-only.** Engine/money/access never read it.
9. **Operating model: staggered concurrent Addas.** The engine is strictly
   sequential per Adda (one active stage). Parallelism comes from several
   smaller Addas in flight, not from parallel stages within one Adda. Size
   Addas so one operation-crew clears a stage in ~a day. TM-2 (true parallel
   ops / bundles) waits for a measured trigger (finishing-crew idle % /
   lead-time), not speculation.
10. **Mobile-first, one-question surfaces.** Worker: "what work do I finish
    right now?" — operation names and the report hint line in floor language
    (Stage.name/description are free text); G/A/M rendered with colour coding
    (green/amber/red). Manager: "what is happening on my floor?" Owner:
    "status + cost?" — on long flows the category chip must show the current
    operation + k-of-n (presentation-only, Phase-3 UI audit).
11. **Integrity flags** stay OFF during operation build-out (owner rollout
    policy) and flip ON permanently at production hardening. **Dependency:
    the R11 rework module must land before/with that flip** (§5.7) — reworked
    alter pieces are otherwise permanently absent from downstream pools.
    Always-on guards (allocation ≤ pool, membership, verify ceilings, void
    guard, reopen guard) protect throughout.
12. **Standard UIs** (worker report / manager panel / owner A360+costing) are
    THE default; per-operation sections below state only DEVIATIONS.

## 3. Operations flow map

```
PRE PRODUCTION           STITCHING (standard flat-assembly order)   FINISHING           DISPATCH
──────────────           ─────────────────────────────────────────  ─────────           ────────
Layering                 T-SHIRT:  Shoulder Join                    Thread Cutting      Dispatch
→ Pattern Design                   → Neck Join (rib + back tape)    → Checking (QC)
→ Cutting                          → Sleeve Fold (hem, flat)        → Iron
→ Barcode Generation               → Sleeve Join (attach)           → Final Check? §5.10
                                   → Side Seam Close                → Packing
[PRINTING category                 → Bottom Fold (body hem)
 reserved — op defined             → Label Attach
 only when the factory   3-PATTI:  Panel Join (overlock)
 actually prints §5.8]             → Leg Binding (patti) §5.11
                                   → Elastic Attach
                                   → Label Attach
```

**3-Patti (brief):** Layering → Pattern → Cutting → Barcode → Panel Join →
Leg Binding → Elastic → Label → Thread Cutting → Checking → Packing →
Dispatch (12 ops; NO Iron — owner-confirmed 2026-07-06, §12). **T-shirt:** the stitching column above, then Finishing → Dispatch.
*(Executed 2026-07-06: the OP-1 engine-proof dev flow was retired via the
owner-approved teardown and the REAL 12-op flow above configured + settled —
see §12.)*

## 4. Operation blueprints

### 4.0 BUILT operations (live — recorded for completeness)

| Field | Layering | Pattern Design | Cutting | Barcode Generation |
|---|---|---|---|---|
| Purpose | lay relaxed cloth plies from rolls | verify pattern/marker vs design (checklist + photos) | cut plies into pieces → APSCPB colour×size = the piece truth | generate/attach barcodes + bundles |
| Category / Work type | Pre Production / Manual | Pre Production / Manual | Pre Production / Machine · Cutting Machine | Pre Production / Manual |
| Skills | cutting_master (+helper) | cutting_master (+helper completes) | cutting_master (+helper) | cutting_master |
| Split / Settlement | none · per_layer · **no pay** | none · fixed_cost · pays | color_size SOURCE · per_piece · pays | none · unpriced |
| Special | **relax knit rolls ≥12h before laying; never mix shade lots within one lay; record lot pairing in the layer note** (the Colour dimension cannot distinguish shade lots — floor discipline) | fixed pay goes to whoever completes — **floor convention: the designated master completes; manager states this at rostering** (engine can't split fixed pay) | breakups must match layered colours; **the cutting snapshot is the ceiling every later allocation obeys**; counts GARMENTS only (rule 6) | settlement-independent (proven) |

---

### 4.1 Seam-join family — Machine · Overlock Machine · overlock_operator · `color_size` · per_piece · pays

Four distinct operations (distinct rates on any real piece-rate card — never
one "Overlock" mega-stage; the machine is shared, the operations are not):

| Operation | Code | Purpose | Typical position |
|---|---|---|---|
| **Panel Join** | `panel_join` | join brief body panels (3-Patti) | first stitching op (brief) |
| **Shoulder Join** | `shoulder_join` | close shoulder seams | first stitching op (tee) |
| **Sleeve Join** | `sleeve_join` | attach sleeves (flat, after sleeve hem) | after Sleeve Fold |
| **Side Seam Close** | `side_seam_close` | close body + underarm in one pass | after Sleeve Join |

Shared blueprint: Standard UIs · global verification · Alter = re-stitchable
seam defects, Missing = lost/damaged panels · machine holder on the manager
panel. **[§5.12: owner keeps or renames the live "Overlock" stage — R10 rule
prefers operation names over machine names.]**

### 4.2 Sleeve Fold (sleeve hem) — Machine · **Flatlock Machine** *(new MachineType)* · **flatlock_operator** *(new Skill)*

Hem the sleeve opening FLAT, before Sleeve Join. `color_size` · per_piece ·
pays. Alter = skipped stitches / uneven fold.

### 4.3 Bottom Fold (body hem) — Machine · Flatlock Machine · flatlock_operator

Hem the body bottom (a tee with a raw bottom edge cannot ship — was MISSING in
v1, caught by review). After Side Seam Close. `color_size` · per_piece · pays.
Alter = wavy hem / stretched edge.

### 4.4 Neck Join — Machine · Overlock Machine (rib attach; flows that bind use Flatlock) · overlock_operator

Attach neck rib + back-neck tape. Early in the tee flow (flat). `color_size` ·
per_piece · pays. Alter = stretched/asymmetric neck — top checking emphasis.
**Honest note (v1 corrected):** neck ribs are cut from RIB fabric dyed
separately from the body — body-vs-rib SHADE matching is a manual floor
discipline (manager pairs rib bundles to body colour at allocation); software
only prevents mis-REPORTING, it cannot see which rib the worker picked up.

### 4.5 Collar Attach — Machine · **Single Needle Machine** *(new MachineType)* · **single_needle_operator** *(new Skill)*

Polo collar attach. `color_size` · per_piece · pays. Same honest shade-matching
note as 4.4 — collar/body pairing is manager floor discipline; Checking
re-verifies. Collar trims are bought/knitted and NOT tracked (§5.1).

### 4.6 Elastic Attach — Machine · **Elastic Machine** *(new MachineType)* · **elastic_operator** *(new Skill)*

Waistband elastic (briefs). `color_size` (size drives elastic length) ·
per_piece · pays. Alter = twisted/loose elastic (stretch-test at Checking).
Elastic CONSUMPTION (metres) is not tracked — piece counts only (§5.1).

### 4.7 Label Attach — Machine · Single Needle Machine · single_needle_operator

Brand + size labels. `color_size` — **size-split is quality-critical**: a
worker holding only Size-1 pieces cannot mis-report a Size-2 batch (membership
guard), though physically attaching a wrong label remains a Checking item.
per_piece · pays. Wrong-size-label = the most expensive late defect.

### 4.8 Thread Cutting — Manual · **finishing_helper** *(new Skill)*

First Finishing step; trims loose threads. `color_size` (keeps the trace —
§5.2) · per_piece · pays (low rate). **Roster guidance: allocate WHOLE colours
(1–3 dims) per helper so each report stays 1–3 rows** — the split is the
manager's simplification lever, not the worker's burden. Missing here = loss
between stitching and finishing (early theft/loss detector). Simplest screen
in the factory; floor-language hint line matters most here.

### 4.9 Checking (Quality Control) — Manual · **checker** *(new Skill)*

THE quality gate: Good = passed · Alter = needs rework · Missing = not in the
bundle. `color_size`. **Manager MUST Report-Review Checking daily and BEFORE
completing the stage** (rule 4 — the corrected number must feed Iron/Packing).
Checker never checks their own stitching (roster discipline). Checking
emphasis list: neck symmetry, rib/collar shade match, label-vs-size, elastic
stretch, press-risk flaws.
**Settlement [NEEDS-DECISION §5.3]:** Good-only pay penalises defect-finding.
Engine-native fixes: **(a) checker on MONTHLY pay basis (recommended — quality
staff on salary, zero perverse incentive, G/A/M data still captured, ₹0
lines);** (b) piece-rate with defect-adjusted rate (₹R ÷ expected pass-rate).
Option "report Good=inspected" is **FORBIDDEN** (violates rule 2: corrupts the
Iron pool with rejected pieces + trips the allocation bound 50+5>50 the day
the flag flips). Literal pay-per-inspected needs a quantity the engine doesn't
have → genuine new-infrastructure decision if the owner insists.
**Alter routing:** informal until R11 (manager memory); counts are captured
immutably today. R11 rework module (route back + `recovered_alter` pool
top-up) is the already-planned seam — and a hard prerequisite of the
permanent flag flip (rule 11).

### 4.10 Iron (Pressing) — Manual *(recommended; flip to Machine + "Iron Table" only if the owner wants table-utilisation tracking)* · **iron_master** *(new Skill)*

`color_size` · per_piece · pays. Alter = shine marks / stretched hems. Pool
arriving = post-Checking verified-else-good — the corrected quality numbers by
design. **Press defects after the quality gate → §5.10 Final Check decision.**

### 4.11 Packing — Manual · finishing_helper

Fold, polybag, carton-pack (often size-assorted dozens). `color_size` ·
per_piece · pays (per-dozen business rates → §5.4). **Floor practice
(mandatory): count/tally pieces per dim at FOLDING, before assorting into
cartons — count-then-pack, never unpack-to-count**; alternatively the manager
keys the report from the tally sheet. Prefill supplies row labels, not counts
— the tally discipline is what keeps the final shrinkage number honest
(§5.13: blank rows = honest count vs default-to-allocated = one-tap confirm;
owner picks). Missing at Packing = final shrinkage before goods leave. Carton/
lot identity not modelled — the Adda is the lot.

### 4.12 Dispatch — Manual · no worker roster (management-completed)

`none` grain · unpriced · no pay. Completing Dispatch completes the Adda
(dispatch date = completion timestamp; gives the real "ready-but-not-shipped"
state between Packing and Dispatch). **Manager UI (honest):** generic panel =
empty roster + Complete button; packed quantities live on the Packing panel /
A360 — a NONE-grain stage renders no pool table. The "No eligible workers —
wire skills" hint will show on a deliberately skill-less stage; suppressing it
for non-payable worker-less stages = small Phase-3 UI-audit item. Future:
storefront/inventory intake hook; dispatch documents.

---

## 5. Open decisions for Phase-2 review (owner rules on each)

| # | Topic | Question | Recommendation |
|---|---|---|---|
| 5.1 | Trims (collars, ribs, elastic, labels) | Bought/knitted trims + consumption are untracked. OK? | YES — attach counts ride the garment pool; trims inventory only on proven need |
| 5.2 | Finishing split grain | Keep `color_size` through Finishing (full trace; D1: once `quantity`, never back) or drop to `quantity`? | keep `color_size` + the 4.8 roster guidance (whole colours per helper). Manager bulk-split UI affordances ("assign colour X to W", "repeat previous split") pre-approved as pure-UI follow-ups WHEN split time measurably hurts (§6 measures it) |
| 5.3 | Checker pay | Good-only pay penalises defect-finding. | **Monthly pay basis for checkers** (engine-native, recommended) or defect-adjusted piece rate. Good=inspected is FORBIDDEN (rule 2). Literal pay-per-inspected = new infrastructure, only on owner insistence |
| 5.4 | Per-dozen rates (Packing etc.) | Engine is per_piece (4-decimal rates). | rate÷12 stored to 4dp — exact only for dozen-rates divisible by 3; worst drift ≈ ₹0.04 per 100 dozen. Quote per-piece or pick 3-divisible dozen rates when exactness matters. Revisit only if reconciliation ever bites |
| 5.5 | Dispatch as a stage | Stage vs plain Adda-complete at Packing? | Stage — "ready-not-shipped" is a real factory state |
| 5.6 | New masters (data, via UI at Phase 3) | — | MachineTypes: Flatlock, Single Needle, Elastic (+Iron Table if wanted). Skills: flatlock_operator, single_needle_operator, elastic_operator, checker, iron_master, finishing_helper |
| 5.7 | Alter rework loop | Informal routing until R11 acceptable? | YES — but R11 (rework + `recovered_alter` top-up) is a HARD prerequisite of the permanent `ENFORCE_ALLOCATION_BOUND` flip; until R11, packed-vs-cut shortfall includes un-recovered alters (Missing-at-Packing is not a clean shrinkage figure) |
| 5.8 | Printing | Category exists, no operation. | define only when the factory prints |
| 5.9 | Operator-helper pay | Does the floor share machine rates (e.g. 70/30)? | Engine cannot split a contribution's money. Recommended: helpers salaried (ADR-0011) or own credited op. If rate-sharing is the real convention → genuine [NEEDS-DECISION] for infrastructure |
| 5.10 | Final quality position | Checking sits before Iron; press defects reach Packing uninspected. | keep 4.9 as stitching-QC + add a light "Final Check" at/inside Packing (pure config: one more Stage row, or a Packing roster instruction). Owner picks placement |
| 5.11 | 3-Patti leg finish | Leg openings: self-fabric binding (patti) on Flatlock w/ binder, or leg elastic on Elastic Machine? | owner states what his line actually does — determines 4.6-vs-new-op config for Leg Binding |
| 5.12 | Live "Overlock" stage name | R10 rule: operation names, not machine names. | rename to Panel Join (or owner's floor term) at Phase-3 reconfiguration; `overlock` code stays (immutable, harmless) |
| 5.13 | Packing report convention | Blank quantity rows (honest independent count) vs prefill-default-to-allocated (one-tap confirm)? | blank rows + the 4.11 tally discipline — Packing is the last honest count |
| 5.14 | **Worker payment cadence on long flows** | Settlement opens only when ALL payable stages complete (verified adda_settlement_service.py:156-167). An 11-op Adda makes the cutting worker wait the whole pipeline. | (a) size Addas so end-to-end ≤ the pay period (couples Adda-sizing to payroll — write the sizing rule), (b) bridge with the existing owner-controlled advance pool, (c) if neither survives real volume → per-stage/periodic settlement = REAL new-infrastructure decision, proven first |
| 5.15 | Rate governance at scale | ~9 payable ops × N products = hundreds of rate cells; no cross-product view. | name a rate owner + revision procedure (edit flows; engine guarantees in-flight Addas keep frozen rates). Pre-approve a read-only rate matrix (operation × product) as presentation-only when maintenance measurably hurts |
| 5.16 | G/A/M labels + language | English labels for a low-literacy floor. | Phase-3 config uses floor-language Stage.name + description hint; G/A/M colour-coded (green/amber/red) with owner-picked floor terms; swatches already supported |

## 6. Phase-3 config procedure per approved operation (no code)

1. Masters: MachineType/Skill rows (§5.6). 2. Stage row (floor-language name,
code, category, work type, machine type, skills, description = worker hint).
3. Product flow: order + Work split + cost method/rate/pays (`cost_billed_at`
= self unless this doc says otherwise). 4. Machines register + operator
assignment. 5. **Reconfigure the production 3-Patti flow to §3 exactly;
retire test-only stages from it** (dev worlds keep theirs). 6. Prove the
OP-1 hardened path end-to-end (roster → split → blind report → verify →
advance → settle). 7. Continuous UI audit at each step: worker one-question
test @390 (floor-language hint visible), **manager split-time measured**
(feeds §5.2), A360 current-op chip readability (rule 10), dispatch-hint
suppression (4.12). Improve within the design system immediately.

---
*Maintained as the operations source of truth. Approved operations get ✅ per
section; config receipts link back here.*

## 7. FUTURE DECISION REGISTER (owner-ruled 2026-07-06 — approved as FUTURE modules, NOT built)

Source: architecture destruction audit (7 hostile vectors, ~60 attacks; core
survived — these are the product-scoped extensions). Each becomes real only
when its product/requirement arrives; each has a named additive path — none is
a teardown. **Rule: do not build until the business requirement is real.**

| # | Future module | Trigger | Owner ruling + additive path |
|---|---|---|---|
| 7.1 | **Wash re-grade** (post-wash size reclassification) | first washed-with-regrade product (washed lowers) | approved future module: audited manager ReGrade event, paired −old-dim/+new-dim entries through the reserved `recovered_alter` pool accessor (ADR-0010 D4 case pattern); Σout = Σin |
| 7.2 | **Print-design lot split** | printing where design ≠ product | standing business rule NOW: **one Adda = one product = one design** (design decided BEFORE cutting). Future module only if bulk-cut-then-print becomes economic necessity (child-lot entity — needs ADR-0010 amendment) |
| 7.3 | **Job-work / outsourcing** (vendor, challan, invoice) | first regular outsourced op (print/embroidery/wash) | approved future module: Vendor + Challan (out/return events, GST ITC-04) + JobWorkInvoice + ADR-0009 term-5 amendment (outwork cost). Interim if ever needed early: non-payable PRICED stage (standard cost) + acknowledged paper challan register |
| 7.4 | **Bundle-level progression (TM-series)** | measured trigger: finishing-crew idle % / lead-time pain on 6+-op flows (audit estimate: bites ~2x volume) | approved future architecture: incremental per-bundle pool feed replacing write-once-at-advance. Define the TM-2 pool contract BEFORE it's needed; Phase-3 configs stay stage-atomic until then |
| 7.5 | **Attendance + statutory wage layer** (min-wage top-up, wage register, OT) | headcount crossing registration thresholds / first inspection risk | flagged by the audit (not yet ruled): attendance model + audited top-up ledger credit (ADJUSTMENT enum exists, unwired) + wage-period report. Raise BEFORE the workforce formalises |
| 7.6 | **Seconds / B-grade sales path** | first lot sold as seconds | flagged (not yet ruled): Damaged now captures scrap; a SALEABLE-seconds classification + commerce hook is a separate future decision (ADR-0008 boundary) |

**Pre-Phase-3 hardening (owner-approved, LIVE 2026-07-06, gate 885):**
`damaged_quantity` (4th observation — §2 rule 3) · `machine_code` snapshot on
every contribution (resolved from the worker's open MachineAssignment of the
stage's machine type; worker sees "⚙ CODE" on the report page) ·
`WorkerStageTask.first_report_at` (passive productivity metadata; work window =
first_report_at → completed_at) · `void_submitted_report` (manager-only,
mandatory reason, refused after stage-complete or settlement; voided lines stay
as inert history on the CANCELLED task; AddaHistory `REPORT_VOIDED` carries the
line snapshot; fresh task lets the worker re-report). **Verification confirms
or reduces — NEVER increases; the void path is the one audited door for upward
corrections (owner business rule, locked).**

## 8. PHASE-3 CONFIG RECEIPT (2026-07-06 — first pass, ALL additive)

**Configured this pass (zero engine code, via masters/flow_service chokepoints):**
- Masters: MachineTypes Flatlock/Single Needle/Elastic · Skills flatlock_operator,
  single_needle_operator, elastic_operator, checker, iron_master, finishing_helper ·
  DEV placeholder machines FL-001/SN-001/EL-001 (**owner replaces with the real
  machine registry**).
- 14 new Stage rows with floor-language worker hints (`Stage.description`, now
  rendered on the report page hero — §1 worker-instruction line is LIVE):
  shoulder_join · neck_join · sleeve_fold · side_seam_close · bottom_fold ·
  collar_attach · leg_binding · elastic_attach · label_attach · thread_cutting ·
  checking · iron_press · packing · dispatch. Live `overlock` stage **renamed
  Panel Join** (§5.12 executed; code immutable).
- Junk stages `verify`/`verify-86f27f0a`/`cross_cutting` deactivated (F-5;
  picker-hidden, history-safe).
- **REAL T-SHIRT flow (16 ops)**: layering → Pattern Design → Cutting → Barcode →
  Shoulder Join → Neck Join → Sleeve Fold → Sleeve Join → Side Seam Close →
  Bottom Fold → Label Attach → Thread Cutting → Checking → Iron → Packing →
  Dispatch (§3 standard flat-assembly order).
- **NEW product LOWER (Track Pant) + REAL flow (13 ops)**: … Cutting → Barcode →
  Side Seam Close → Elastic Attach (waistband) → Bottom Fold → Label → Thread
  Cutting → Checking → Iron → Packing → Dispatch — pure library REUSE, zero new
  stages needed beyond the shared set.
- §5 defaults exercised: 5.11 Leg Binding configured as Flatlock self-fabric patti
  (stage ready; owner confirms method at 3-Patti config) · 5.2 color_size kept
  through Finishing · unpriced stages = honest-NULL rate.
- **⚠ ALL RATES ARE DEV PLACEHOLDERS** — owner enters the real rate card in the
  flow editors before production validation.

**BLOCKED — RESOLVED 2026-07-06 (owner approved the teardown; real flow configured + settled — see §12):** the REAL 3-Patti flow (…Panel Join → Leg
Binding → Elastic → Label → finishing…) cannot be completed because `sleeve_join`
cannot be removed from the product-1 flow while DEV Addas 011/013/014/015 hold
stage-record history on it (history guard, by design). Unblocking = the
owner-sanctioned DEV teardown batch (dependency-ordered purge of those 4 dev
worlds incl. their dev settlements/ledger rows, mirroring the R8 teardown).
Script ready; execution awaits explicit owner go.

## 9. LOWER BUSINESS-JOURNEY RECEIPT (2026-07-06 — first full new-product run)

**LOWER-001 run end-to-end (13 ops, brand-new product, ZERO engine code) — all 4
role lenses browser-audited, money-correct.** Pre-production (create→layering
w/ roll+monthly worker report) via real UI; cutting fixtured (DEV, bespoke
subsystem already validated); stitching+finishing via the OP-1-hardened generic
path. Cast: 8 workers across 8 distinct new skills/machine types.

- **Side Seam Close (representative new stitching op) — full browser audit:**
  manager panel = roster + Split-the-work + machine holder + board with the new
  **Damaged** column; worker @390 = **hinglish hint** ("Side + underarm ek pass…")
  + **⚙ OL-001 machine chip** + prefilled size row + all 4 quantity fields. Clean.
- **elastic / bottom_fold / label / thread_cutting** driven via service
  chokepoints — each a different new skill+machine, all config-only, no code.
- **Checking (the QC gate) — browser audit:** checker @390 gets the 4-way
  hinglish hint; reported the full split S(good17/alter1/damaged1) + M(good19/
  alter1); only Good (36) flowed to Iron's pool — Alter/Missing/Damaged correctly
  excluded from the downstream pool while captured as quality truth.
- **Dispatch** = management-completed, no roster → Adda auto-completed.
- **Settlement ADST-0004 finalized ₹344.25** across 10 payable stages (8 carrying piece-rate lines) =
  Σ StageWorkAssignment lines = ledger credits = per-worker breakdown (all 8 paid).
- **Owner lenses agree:** A360 13/13 100% (category chips 4/4/4/1, SETTLED
  ₹344.25, no @390 overflow); Costing Mfg ₹744.25 vs Settled ₹344.25, variance
  ₹400.00 = the non-payable layering standard labor exactly (ADR-0009 duality).

**UI improvement shipped this session (owner continuous-audit rule):** the §1
worker-instruction line is now LIVE — the report hero renders `Stage.description`
(floor-language, owner-editable per stage) instead of the generic English prompt.

**Journey findings (owner decisions, NOT bugs):**
- §5.3 checker pay: the checker was piece-rated good-only (₹27 for 36 good; the
  1 alter + 1 damaged she found earned nothing) — the documented perverse-
  incentive. Owner sets checkers to **monthly** or a defect-adjusted rate at
  real-rate-card time.
- §5.14 cadence: all 8 workers waited the full 13-op flow to be paid (settlement
  needs every payable stage complete). Real; owner's Adda-sizing / advance-bridge
  call.
- Partial-lot realism: LOWER-001's L-size (10 pcs) was never stitched — those
  pieces sit unallocated in the cutting pool, unpaid, no phantom (correct).
- Dev note: `dev.monthly` password was stale (pre-rename era) → reset to the
  standard DEV password; flag for the teardown batch.

## 10. T-SHIRT JOURNEY RECEIPT + 100-PRODUCT VERDICT (2026-07-06)

**T-SHIRT-001: 16 ops end-to-end, 2 colours × 2 sizes (4-dim pool, 60 pcs),
settled ₹801.00 = Σ 44 SWA lines.** New this run vs Lower: 4-dim manager
allocation (4 form-rounds — fine at this scale; §5.2 bulk-split affordance =
the pre-approved lever when dim-counts grow) · worker multi-row report @390
(exactly 2 prefilled rows Red+M / Red+L, hindi hint, ⚙ OL-001 chip) · **machine
moved between Addas** via release→assign (2 actions, natural) · full seam-join
family exercised (shoulder → neck → sleeve fold → sleeve join → side seam →
bottom fold) · **Checking with verification-before-advance: checker reported
Red·M good 18/alter 2; manager verified 17 → Iron's pool received exactly
17+10+20+9 = 56 AND settlement paid 17 (₹12.75)** — one correction, both
truths, one rule.

**100-product question — VERDICT: YES, config-only.** Evidence: Lower = an
entire 13-op product with ZERO new stages; T-Shirt reused the same library +
its 4 seam-family ops. A new garment product = flow rows (~12-16) + sizes +
pattern assignments + rates. The scaling cost is DATA ENTRY, not engine:
rate-cells (§5.15 rate-matrix report pre-approved) and pattern/marker setup
per product. No engine limitation found in either journey.

## 11. FUTURE CAPABILITY REGISTER — integration points (owner order 2026-07-06; document, do NOT build)

| Capability | Plugs into (existing seam) | Shape when built |
|---|---|---|
| Washing + re-grade | `recovered_alter` pool accessor (stubbed, formula-stable) + ADR-0010-D4 case pattern | audited ReGrade event module (§7.1) |
| In-house printing | Printing StageCategory (exists) + generic stage fallback | pure config op the day design==product (§7.2 rule: one Adda = one design) |
| Embroidery/print/wash VENDORS + subcontracting | non-payable PRICED stage (standard cost slot, ADR-0009-D2) as the flow gate; money = future `JobWorkInvoice` + ADR-0009 term-5 amendment; custody = future Vendor+Challan (GST ITC-04) | additive module (§7.3) |
| Bundle tracking / parallel progression | `BarcodeBatch` (adda,seq) ranges — ADR-0010-D3: piece identity must be BORN from these ranges; pool seam = incremental per-bundle feed replacing write-once-at-advance | TM-2 (§7.4); define pool contract before building |
| **AI Pattern Intelligence** (highest priority post-validation) | Pattern Design stage already captures: `CuttingPatternRecord` + verification photos, `ProductPattern`/`ProductPatternAssignment` masters, `CuttingPatternSizeAllocation` proportions, layering lay-counts, APSCPB actual-cut truth. Integration (D8-amended 2026-07-06, per ADR-H): the `patterns_ai` app READS those records + photos; it holds PROPOSALS + its own knowledge ONLY and NEVER writes any production table — humans re-enter accepted values through the existing production UIs; UI seam = link-out from the pattern console (ZERO production→patterns_ai imports, enforced by import-linter + runtime purity test). Governing docs: AI_PATTERN_INTELLIGENCE_KICKOFF · 06_BLUEPRINT_V3_FINAL · ADR pack A-H | separate project; seams stay clean (nothing else writes these tables) |
| Barcode evolution (scan-driven reporting) | C-TM convergence rule: every capture path (scans included) enters through `report_contributions` — the chokepoint is the contract | future Piece/ScanEvent born from existing ranges |
| Quality analytics | already CAPTURED per contribution: G/A/M/D × dim × op × worker × `machine_code` + task timestamps + verifier audit events | read-only reporting surface, zero writes |
| Production optimization (bottleneck/operator speed/machine utilisation) | `first_report_at`→`completed_at` task windows · stage start/complete · `MachineAssignment` windows | read-only analytics; data is being collected from today |
| Attendance + statutory wage layer / Seconds | §7.5 / §7.6 | as registered |

## 12. 3-PATTI REAL-FLOW JOURNEY RECEIPT (2026-07-06 — teardown → real flow → settled)

**DEV teardown executed (owner-approved):** Addas 3-PATTI-011/013/014/015 +
settlements ADST-0002/0003 (12 ledger rows, 12 SWA lines, 9 items, 21 allocations,
30 AddaStageRoleRate rows, machine windows, barcode chain, layering artifacts)
purged in one dependency-ordered atomic script (dry-run-first; v2 fixed 3 stale FK
assumptions in the ready script: `AddaSettlementItem.adda_settlement`, ledger→SWA
PROTECT, reconciliation-evidence PROTECT). Roll CR-000004 UNLINKED not deleted.
LOWER-001 / T-SHIRT-001 evidence untouched. Full gate suite green post-teardown.

**REAL 3-Patti flow configured (§3 exactly, 12 ops via flow_service):**
Layering → Pattern Design → Cutting → Barcode → **Panel Join** (renamed overlock,
code immutable) → **Leg Binding (Patti)** (§5.11 Flatlock self-fabric) → Elastic
Attach → Label Attach → Thread Cutting → Checking → Packing → Dispatch.
`sleeve_join` retired from the flow (history-free post-teardown; stays live in
T-SHIRT where it is a real op). Grain `color_size` through Packing (§5.2);
Dispatch `none`/no-credit. **Iron Press EXCLUDED for briefs — OWNER-CONFIRMED
2026-07-06: Checking → Packing → Dispatch IS the 3-Patti production flow; if a
customer ever requires ironing it becomes an optional configured operation
(config-only, never an engine change).** Rates = DEV placeholders
(PJ 5.00 · LB 1.50 · EL 2.00 · LA 0.75 · TC 0.50 · CHK 0.75 · PK 0.50).

**Journey 3-PATTI-016 (first Adda on the real flow) — settled ADST-0006 ₹633.00:**
- Cut truth 60 pcs (Red S1 24 · Red S2 18 · Blue S1 18); layering 30 plies × 1.50 m
  on CR-000004 (37″), honest LayeringRecord + roll entry.
- Panel Join: manager (dev.mgr) allocated via Split-the-work UI (24/18→OW-A,
  18→OW-B); OW-A phone report @390 (⚙ OL-001 chip, J-2 prefill, hinglish hint)
  Red S1 23g+1a · Red S2 18g; OW-B Blue S1 17g+1d. Pool materialized 23/18/17
  (verified-else-good). Frozen cost ₹290.
- **Leg Binding first-ever run** @390 (dev.flat.a, ⚙ FL-001, 3 prefilled dims) 58g.
- Elastic/Label/Thread via chokepoints (el.a / sn.a / fin.a) 58g each.
- Checking (dev.chk.a @390, 4-way): Red S1 21g/1a/1d · Red S2 18g · Blue S1 16g/1m;
  manager verify-REDUCE 21→20 via Report Review → flowed to BOTH pool and pay.
- Packing honest count 54 (20/18/16, §5.13) → Dispatch mgmt-complete → auto-completed.
- **Money: A360 Expected ₹633.00 = draft = finalized = Σ21 SWA = Σ21 ledger =
  Σ items (8 workers). Hand-calc identical. Golden settlement suite OK.**
  A360 @390: 12/12 stages, chips 4/4·4/4·3/3·1/1, Settled ₹633.00.

**Fixes shipped during the journey (continuous-audit rule):**
1. `production/_so_tile.html` — nullable `completed_by` crashed the WHOLE Adda
   page (filter-arg lookup on None = hard VariableDoesNotExist). Guarded. Why it
   matters: any legacy/imported stage record without a completer must never 500
   a management page. Future modules: template filter args never assume non-null FKs.
2. `production/_worker_report_body.html` — multi-line `{# #}` comment LEAKED as
   visible text on EVERY worker report page (known regression class; single-line
   only). Fixed + repo-wide sweep: `signup_otp.html` fixed (dormant page);
   3 top-level-in-extends occurrences are inert but should not be copied.
3. Journey-fixture lesson (affects future dev worlds + any import tooling):
   an AddaStageRecord created outside `adda_service`/stage-start MUST call
   `ensure_stage_role_rates(sr)` and set `completed_by` — otherwise A360 shows
   "std unpriced" and tiles have no completer. Real UI/service paths do this
   automatically; only fixtures bypass it.

**Verdict: the REAL 3-Patti flow is live and money-correct end-to-end. All three
real product flows (T-Shirt 16 · Lower 13 · 3-Patti 12) now proven on the frozen
engine. Remaining before freeze: owner real rate card → final business validation
→ production freeze + checkpoint commit.**

# Full-System Architecture Reassessment — post-V2-2 (2026-06-11)

Owner-requested reassessment of the live codebase after V2-2 (PR-A→D) shipped.
Baseline: docs/ARCH_CHECKPOINT_2026_06_11.md (post-validation scorecard).
Companion truth: ADR-0007 (cutover), ADR-0008 (commerce boundary),
docs/V2_2_EXECUTION_REVIEW.md (Parts 1–13). Assessment only — no work proposed.

Current state assumed (owner-confirmed): R0, R1, P2, P4.2, V2-1a→1d, V2-2 all
complete; ADR-0007 implemented; ADR-0008 locked; G1–G7 recorded; deploy stack
prepared; validation cycle closed; true soak pending deployment + real workers.
Evidence base: 475 tests green, 71% coverage, 6-check gate (incl. both
single-writer gates), live dev chain ADST-0001→0002→0003 (last loop UI-only),
ledger rows #2–#11 append-only.

---

## 1) Updated architecture scorecard (prev checkpoint → today)

| # | Dimension | Prev | Today | Driver |
|---|-----------|------|-------|--------|
| 1 | Architecture | 8.9 | **9.2** | The money question — when does financial truth exist — is now answered in code, not docs. Settlement-time crediting live, settlement≠payment real, corrections first-class. The riskiest design (§11) survived contact with implementation unchanged. |
| 2 | Scalability | 8.5 | **8.5** | Flat. Nothing structural changed. One new known cliff added to the register: `settlement_queue()` scans all payable Addas in Python; `finalize` locks every payable stage record + worker profile. Both fine at one-factory scale, both named. |
| 3 | Maintainability | 8.5 | **8.6** | Single-writer discipline extended (gate 4b); invariants encoded in service docstrings; queue/detail UI thin over services. Still capped by stage_views god-file (Phase 8 parked) and a growing expense/views.py. |
| 4 | Extensibility | 9.0 | **9.0** | Proven again, not just claimed: `variance_policy` TextChoices absorbed launch policy with zero schema risk; PSI XOR-parent let payment narrow without ledger churn; WSC.settlement_line gives per-line provenance any future report can use. |
| 5 | Tech Debt | 8.5 | **8.4** | Honest small regression. Deliberate transitional debt added: era-A path + flag + dual-semantics SWA — all with a named retirement (V2-3). mypy island regressed again (242→257 errors); the ratchet is not ratcheting. |
| 6 | RBAC/Security | 8.8 | **8.8** | Flat. New money screens management-gated, menu+URL gated together, POST+CSRF+confirm on every mutation, worker 403 sweep tested. F7 (assignable-pool policy duplication) still the cap. |
| 7 | Data Integrity | 9.0 | **9.3** | The big winner. Append-only correction loop proven live; XOR parenting, finalized⇒settled_at, recovered≤outstanding constraints; double-credit structurally impossible in both directions in both flag states; provenance spine item↔SWA↔ledger↔contribution closed. |
| 8 | Coupling | 8.7 | **8.6** | Slight honest dip. production→expense edge widened: WSC.settlement_line is a production-model FK into expense (string ref, PROTECT) — deliberate Part-13 adoption, but the acyclic contract stays broken (1 kept, 1 broken). Allocation-path coupling dies at V2-3; the provenance FK is permanent and accepted. |
| 9 | Observability | 8.3 | **8.4** | Settlement events on the Adda timeline (FINALIZED/REVERSED/SUPERSEDED), structured logs at every money write, deterministic references in ledger notes. Still capped: no error-reporting/metrics until the deploy bundle goes live. |
| 10 | Testing/Gates | 8.8 | **9.0** | 475 tests; invariants-as-tests (10 locked invariants executable); lifecycle, flag on/off, guard re-arm all characterized; live UI walkthrough on real data; 6-check gate. Cap: 71% coverage and no real-user behavior in the evidence base. |

**Net read:** the financial core moved from "designed" to "proven". The two dips
(tech debt, coupling) are both deliberate, named, and scheduled to die at V2-3 —
that is what controlled transitional debt is supposed to look like. The mypy
regression is the only undisciplined drift.

---

## 2) What V2-2 fundamentally changed

**Impossible before V2-2:**
- Booking a worker's earning from what they *actually reported and management
  verified*. Money could only enter at allocation — management guessing
  quantities up front, before the work was even measurable.
- Correcting a money mistake without editing history. Wrong allocation = edit
  or void the row and hope.
- Recovering an advance as a deliberate per-advance decision at a business
  event. Recovery was fused into payment.
- Saying anything financial *about an Adda*. The ledger was worker-keyed only.

**Possible now:**
- Production truth and financial truth are separate, bridged by frozen
  `expected_*` (visibility, never money) and joined only at finalize.
- The accountant's mistake-recovery sequence is a product feature:
  finalize → discover error → Reverse & settle again → corrected settlement.
  Proven live: ADST-0001 booked ₹240 on a wrong Size-2 count; superseded;
  ADST-0002 booked ₹225 off the corrected verified quantity; both frozen
  snapshots retained; ledger shows every step, nothing edited.
- The whole loop runs from management screens — draft, labeled preview,
  variance, per-advance recovery, finalize, reverse, supersede, discard.

**Truths that now exist in the system:**
- `AddaSettlement` + frozen items: *what was reviewed and approved, by whom,
  when* — immune to later rate/advance/policy changes.
- `WorkerLedgerEntry` chain: *what money actually moved* — append-only,
  category-tagged, reversal rows net in-period.
- `WSC.settlement_line`: *exactly which settlement line paid this contribution*.
- `SWA.adda_settlement` NULL/non-NULL: *which era credited this work* —
  structural, not inferred.
- The supersede chain: *the full correction narrative*, ordered.

**Business questions now answerable (with real examples):**
- "What do I owe worker utest right now?" → ledger SUM = ₹225.00, live.
- "What did 3-PATTI-001 cost in labor?" → ADST-0003 items: ₹225 settled, plus
  worker2's ₹135 era-A allocation = ₹360 total (the UI labels the split).
- "Who approved this and what did they see?" → settled_by + frozen snapshot.
- "Did we ever double-pay?" → structurally impossible; the draft screen shows
  *why* each excluded line is excluded.
- "What changed between ADST-0001 and ADST-0003?" → chain + two snapshots:
  ₹240 → ₹225, Size-2 count 30→15, reason in reversal notes.

---

## 3) Adda visibility assessment (one Adda, today)

What the owner can see and know for a single Adda:

| Facet | State | Where |
|---|---|---|
| Production status | ✅ Full | Stage records per workflow stage, started/completed stamps, auto-durations, Adda dashboard |
| Worker contributions | ✅ Full | WorkerStageTask/Contribution per worker per stage, color/size/qty grain, reported vs verified distinguished |
| Worker earnings | ✅ Full | Pre-settlement: frozen expected_* (visibility). Post-settlement: ledger credits with line-level provenance |
| Settlements | ✅ Full | ADST history per Adda, status pills, chain, frozen per-worker snapshots |
| Advance recovery | ✅ Full | PSI rows per settlement, reversed-state visible, outstanding always live SUM |
| Payment state | ⚠️ Worker-keyed only | Payable = ledger balance per worker; payments deliberately NOT linked to Addas (Model A — money fungible). "Adda settled but workers unpaid" is readable only by walking worker balances |
| Reversals | ✅ Full | Chain banner, compensating entries, timeline events, reasons on ledger notes |
| Labor liability | ✅ Per-Adda expected + settled; global per-worker payable | Settlement screens + payroll overview |
| Audit history | ✅ Full | Unified AddaHistory timeline incl. settlement events; who/when on every money row |

**Still missing:**
1. **Piece truth** — missing/rejected are manual variance *counts*, not tracked
   objects with lifecycle (MissingPiece/Alter modules pending). Today's counts
   are only as good as the manager's typing.
2. **Material cost** — cloth consumption is recorded (rolls, layering) but
   never *valued* into the Adda. Labor cost is known; total Adda cost is not (G1).
3. **One Adda-360 page** — every fact above exists, scattered across 4 screens.
   No single composed view (G4).
4. **Finished goods** — a completed Adda increments nothing; output vanishes
   into the physical world (G5).
5. **Revenue side** — nothing connects this Adda to a sale (G2; by ADR-0008,
   deliberately indirect via G5).

---

## 4) Remaining architectural risks (ranked within category)

**Architecture risks**
1. **MED — Dual-semantics StageWorkAssignment.** One table holds era-A
   allocation lines and era-B settlement earning lines, distinguished by FK
   NULL-ness. Every reader between now and V2-3 must know the era rule. The
   era-A guard is also coarse (worker+stage pair, not line) — correct-by-safety
   but a partially-allocated worker has their whole stage excluded.
2. **MED — production→expense coupling.** Acyclic contract still broken;
   allocation-path imports die at V2-3, but WSC.settlement_line is a permanent
   production→expense FK. Accepted (Part 13), should be re-stated in the
   contract config as a named exemption, not a standing violation.
3. **LOW — God-files.** stage_views (parked Phase 8) and expense/views.py
   (~460 lines, single module) — splitting is mechanical when it hurts.
4. **LOW — Variance valuation deferred.** Counts frozen, ₹ valuation choices
   deferred to G3. Schema reserved; no trap visible.

**Operational risks**
1. **HIGH — No production usage.** Everything validated by one developer on
   dev data. The system's hardest invariants are human ones (workers actually
   reporting, managers actually verifying) and none have been exercised.
2. **MED — Backup/restore never fire-drilled** end-to-end on a real VPS.
3. **MED — No error reporting/metrics** until the deploy bundle is live; a
   production exception today would be invisible.
4. **LOW — Settlement hot-path locking breadth** (all payable SRs + profiles) —
   irrelevant at current scale, on the register.

**Adoption risks**
1. **HIGH — Worker reporting discipline.** The whole Option-B edifice assumes
   contributions get reported before stage completion. P2 UI is built and
   auto-cancel (F3/F8) handles the lazy path, but the cultural question —
   will workers type numbers on phones — is unanswered until soak.
2. **MED — Settlement≠payment mental model.** Accountant must internalize
   two screens for what used to feel like one act. Labels and refusals
   mitigate; reality will test it.
3. **MED — Manual variance entry.** Optional inputs invite zeros. Until
   MissingPiece exists, missing/rejected data quality is operator-dependent.

**Deployment risks**
1. **MED — First real migration run.** Dev DB is small and clean; the factory's
   eventual data shape isn't. Clone-rehearsal discipline exists — it must hold
   for the first deploy too.
2. **LOW — Stack itself.** Pinned, health-gated, rollback documented, flag
   defaults safe. The prepared-but-unused stack only rots slowly (image pins).

**Future-roadmap risks**
1. **MED — Two product identities (G6).** production.Product is the real
   master; storefront.FeaturedProduct is free-text marketing copy with NO FK.
   No schema unwind needed (good), but every month of catalog growth raises
   the reconciliation cost, and G5/G2 *cannot build* on a split identity.
2. **MED — Reporting before lifecycle modules.** Reports baked on manual
   variance counts will silently change meaning when MissingPiece/Alter land.
   Sequence reports after, or stamp provenance.
3. **LOW — G7 MRP-lite.** Far out; nothing today forecloses it.

---

## 5) Roadmap validation

Remaining: V2-3 · MissingPiece · Alter/Rework · Reporting · G1 Costing-2 ·
G2 Revenue · G3 Variance valuation · G4 Adda-360 · G5 Finished goods ·
G6 Product master · G7 Planning.

**Order is broadly correct. Three adjustments, no new phases:**

1. **Deploy + true soak must be sequenced as a real phase gate, not background
   state.** It now blocks more value than any feature: the flag flip, V2-3's
   final deletion step, and adoption-risk retirement all wait on it. When the
   VPS decision lands, it preempts everything below.
2. **Move G4 (Adda-360) earlier — thin slice.** It is pure read composition
   over data that exists *today* (section 3 proves it), zero schema, and it is
   the best possible soak instrument: one page where the owner watches an Adda's
   production+money story live. Full G4 polish can stay late; the thin page
   should not.
3. **Move G6 (product master) ahead of G5/G2.** ADR-0008's spine — Order↔Adda
   indirect via finished-goods inventory — requires ONE product identity.
   Building G5 on a split master would be building on sand. G6 is also cheapest
   now (storefront side is unlinked free text; unification is additive FK work,
   not unwinding).

**Stays put:** MissingPiece before Alter (missing feeds settlement counts
directly; alter is a rework flow). G3 after MissingPiece (valuation needs real
counts). G1 after MissingPiece is preferable (losses affect cost) but G1 is
independent enough to run adjacent. Reporting stays late (after lifecycle
modules, per risk above). G7 last.

**Splits/merges:** none required. MissingPiece will naturally land as 2 PRs
(lifecycle model+entry, then settlement integration) — same phase. V2-3 stays
one phase but gets an explicit internal gate (below).

**Validated order:**
V2-3 (code) → **deploy+soak gate** → MissingPiece → Alter → G4 thin slice
(can ride alongside soak) → G1 → G3 → G6 → G5 → G2 → Reporting (full) → G7.

---

## 6) ERP maturity assessment

**A. Manufacturing ERP maturity: ~72%.**
The core manufacturing-ERP loop — material intake → staged production with
worker-level tracking → labor costing → settlement → payment — is complete,
auditable, and correction-capable. That is the half most ERPs get wrong, done
right. Held below 80 by: no material valuation into the product (G1), no piece-
loss lifecycle, no finished-goods ledger (G5), no planning (G7). The financial
spine being append-only and provenance-complete is worth more than the missing
modules cost.

**B. Factory operations maturity: ~58%.**
Different question: not "is the software good" but "does this factory run on
it". Answer today: no — zero production usage, deployment parked, no real
worker has touched the report screen, no real settlement has paid a real
person. The software *readiness* for operations is high (~85%); the realized
operational maturity is bounded by usage. This number moves only via deploy +
soak, not via more code.

**C. Long-term manufacturing + commerce vision maturity: ~40%.**
The manufacturing half of the vision is well advanced (A above). The commerce
half is *designed* — ADR-0008 locked the ownership boundary, G1–G7 name every
gap honestly — but essentially unbuilt: storefront is a marketing/catalog
shell, no orders, no inventory, no revenue object, split product identity.
40% reflects "architecturally de-risked, materially unstarted": the thinking
that usually sinks v2 commerce integrations has been done; the building has not.

---

## 7) Future-proofing review (brutal)

**Settlement design.** The standing regrets, honestly:
- *SWA dual history is permanent.* Even after V2-3, era-A rows live in the
  table forever, meaning "what is a StageWorkAssignment?" has a two-part answer
  for the lifetime of the database. Mitigated structurally (the FK marker) and
  by docs; it will still confuse a future developer once a year. Accepted cost
  of not rewriting the ledger FK.
- *Dual provenance paths.* Per-line truth on WSC.settlement_line, per-worker
  rollup on AddaSettlementItem.earning_assignment (nullable). Two ways to walk
  from settlement to ledger. Documented; mildly redundant; not a trap.
- *Frozen items cannot be revalued* — by design, that's the point — but it
  means a future "variance reduces pay" policy applies only forward. Correct
  behavior; stated so nobody "fixes" it later.
- No lock-in found in the correction model: reverse/supersede composes; partial
  settlements legal (no unique(adda)); policy is a choice field. Clean.

**Inventory future (G5).** No trap — *because nothing pretends to be
inventory*. Completed Addas write nothing, so there is nothing wrong to
migrate. The trap is adjacent: **split product identity (G6)**. Storefront
products are free-text; the moment G5 creates FinishedGood rows keyed to
production.Product while the storefront sells unlinked names, reconciliation
becomes a data-cleaning project that grows monthly. Sequence G6 first
(restated in §5).

**Commerce future.** Revenue appears nowhere in manufacturing models — exactly
right per ADR-0008. No Order model exists at all, so no premature shape to
regret. The one watch-item: when Orders arrive, resist any FK from Order to
Adda "just for traceability" — the locked design routes through G5 inventory,
and the temptation will come.

**Costing future.** Stage labor cost is frozen per stage record
(processing_cost, cost_billed_at grouping); settlements add true labor cost.
Material cost is absent, which means **pre-G1 and post-G1 Addas will have
incomparable "cost" numbers forever.** Not avoidable — but stamp the era
(a single `costing_version`-style marker or just the date cutoff documented)
when G1 lands, or profitability reports will silently mix regimes.

**Reporting future.** The append-only, category-tagged ledger + frozen
snapshots + AddaHistory mean essentially any historical report is derivable —
the hard part of reporting is already paid for. Two residual hazards:
(1) variance counts pre-MissingPiece are operator-typed — reports must label
provenance or they'll be trusted beyond their quality; (2) the mypy ratchet
failing (211→242→257) is the only place the codebase is drifting *away* from
future-proof — cheap to fix, embarrassing to ignore.

**No migration trap found** that requires action before its scheduled phase,
with one exception: G6 ordering (already corrected in §5).

---

## 8) V2-3 readiness verdict

**Yes — V2-3 is the correct next phase, with one sequencing rule inside it.**

**Why.** The single largest standing architectural liability is the dual-truth
window: two live write paths to worker money (allocation-time and
settlement-time), bridged by guards. Every session the window stays open,
every reader and every new feature must stay era-aware. V2-3 closes it.
The SWA-repurpose half of V2-3 is already real (V2-2 PR-B writes SWAs as
settlement earning lines); what remains is retiring allocation as an entry
point — remove the cutting-workspace allocation UI affordances, make the
settlement path the only documented flow, and shrink allocation_service to a
flag-gated legacy shim.

**Value unlocked.** Uniform provenance for every future earning; readers lose
the era rule; the cross-era guard becomes dead defense instead of active
machinery; production→expense allocation coupling dies, fixing the broken
acyclic contract; onboarding cost for the next developer drops.

**Risk removed.** Human error through the legacy path racing a settlement —
the only remaining way to create messy money — becomes impossible rather than
guarded-against.

**The internal gate:** V2-3 must NOT delete the flag or the era-A code path.
Deletion = the irreversible cutover act, and that is soak-gated (amended C2
covers dev-validation for mechanics, not production usage). Correct V2-3
shape: settlement-only becomes the *default and documented* flow; the flag
remains the rollback lever; physical deletion of the legacy path is a separate
small PR *after* the real-worker soak passes. If the VPS decision lands before
V2-3 starts, deploy first — soak data is worth more than the code tidiness,
and V2-3 is strictly easier to finish once soak proves nobody needs the lever.

---

## 9) Final executive summary

**Verdict: continue the roadmap — with the gravity shifted to deployment.**

Joining today as principal architect, I would change almost nothing about the
code direction and one big thing about priorities. The financial core is the
best part of this system: append-only ledger, settlement-time truth, frozen
approval snapshots, first-class corrections, structural double-pay prevention —
all live-proven, all gated. The transitional debt (era-A path, flag, dual-
semantics SWA) is the *good kind*: named, guarded, tested, with a scheduled
death. The remaining feature gaps (G1–G7) are honestly registered and correctly
fenced by ADR-0008.

What I would change:
1. **Treat deploy + true soak as the next milestone after V2-3's code lands —
   above any new feature.** The dominant risk class is no longer architectural;
   it is that zero real humans have used this. Every week of feature work
   before soak adds surface that soak must then validate.
2. **Pull G6 (product master) ahead of all commerce work**, and **a thin
   Adda-360 page forward as a soak instrument**. Both are cheap now and
   expensive later.
3. **Fix the mypy ratchet drift** in the next PR touching services — the only
   undisciplined trend line in an otherwise disciplined codebase.

Everything else: as planned. V2-3 next, lever retained until soak,
MissingPiece/Alter after, commerce only on a unified product master.

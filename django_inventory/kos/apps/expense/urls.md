---
id: app-expense-urls
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Any /expense/ URL — its full learning story: why it exists, everything it touches, everything it can teach me."
related: [app-expense]
---

# expense — URL Learning Pages (all 17, individually)

> 📂 [expense app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`expense` app ka kaam: **paisa** — settlement, ledger, advance, payroll. Yahan galti sabse mehngi padti hai.)*

**Reading Strategy** — *Beginner:* §1 → §17 → §8 (each simple, each says
WHY) → the README's Mental Model. *Intermediate:* §2–§5, §9–§12, §14–§16.
*Senior:* §4 (the two races) → §6 (isolating a money-behavior field) →
**§13 (the gate — the deepest section in the LOS)** → §7 (orchestration
without a second pen).
> Source of truth: `config/expense/urls.py` (app_name=`expense`, mounted `/expense/`).
> Every management URL is ALSO sidebar-rule gated (menu hidden ⇒ URL blocked).
> LOS law: every URL gets its own section — search THIS url, find THIS url.
> *(Har URL apna sabak — dhoondo wahi, milo wahi.)*

---

## 1. `/expense/my/` — `my-earnings`

**Business purpose:** the worker's own money window. Meena checks her phone:
kitna Expected, kitna Earned, kitna Paid — three non-overlapping numbers.
**Why it exists:** trust. A worker who can SEE the ladder disputes less and
catches errors early (visibility ≠ commitment — Option B's whole point).
**Method:** GET · **Entry:** `urls.py` → `MyEarningsView` (`views.py:75`,
LoginRequired, TemplateView) → `expense/my_earnings.html`.
**Permissions:** any authenticated user; shows ONLY their own data (self-scoping
in the view — no pk in the URL = nothing to tamper with).
**Validation / transaction / locks:** none — pure read. **Why that's safe:**
writers are atomic, so a reader can never see half a settlement
([transactions §6](../../concepts/django/transactions.md#6-how-this-project-uses-it)).
**Reads:** ledger sums (credits/debits) + unsettled WSC (`unsettled_expected`)
via `payroll_service`. **Writes / external APIs:** none.
**Failure modes:** none designed — an empty ladder for a new worker is correct.
**Performance:** FILTER-aggregates over indexed `(worker, entry_type)`; the
Expected sum reads frozen `expected_*` — no rate joins at request time.
**Security:** the self-scoping is the lesson — identity from `request.user`,
never from URL params.
**DSA:** log + fold — the balance IS a fold over the event log.
**Tests:** ladder non-overlap proofs (expected/earned/paid never double-count).
**Engineering lesson (why simple):** read-only surfaces over DERIVED truth
stay simple forever — no state to sync, no cache to invalidate. Simplicity
here was purchased by discipline elsewhere (append-only ledger).
**Required knowledge:** [ledger](../../features/ledger.md) · derived balances
([money-story](../../project/money-story.md)).
**Continue to:** §3 worker-detail (the management mirror of this page).

---

## 2. `/expense/payroll/` — `payroll-overview`

**Business purpose:** the owner's money board — every worker's payable +
outstanding advance, one screen.
**Why it exists:** settlement decisions are BATCH decisions; the owner needs
the whole board before choosing whom to settle/pay.
**Method:** GET · **Entry:** → `PayrollOverviewView` (`views.py:130`,
LoginRequired + `_ManagementOnly`) → `payroll_overview.html`.
**Permissions:** MANAGEMENT_ROLES (mixin) + sidebar rule.
**Transaction/locks:** none (read). **Reads:** `payroll_totals()` +
`outstanding_advances_bulk(workers)` — GROUPED aggregates: the whole board
in ~2 queries, not N per worker. **Writes/external:** none.
**Failure modes:** none designed. **Performance — the lesson of this URL:**
this is the repo's flagship bulk-aggregation surface; its query count is
PINNED ([query-performance §4](../../concepts/postgresql/query-performance.md)).
Add a per-row template call here and CI fails.
**Security:** wall #1-2 (menu+mixin); numbers are derived, so no stale-cache
leak class exists.
**DSA:** grouped fold — push the aggregation to the data.
**Tests:** `test_perf_settlement.py` count pins · view tests in `test_views.py`.
**Engineering lesson:** boards are where N+1 breeds; kill it with ONE grouped
query and pin the count.
**Required knowledge:** [query-performance](../../concepts/postgresql/query-performance.md).
**Continue to:** §3 (drill into one worker).

---

## 3. `/expense/workers/<pk>/` — `worker-detail`

**Business purpose:** one worker's complete money picture — ladder, ledger
rows, advances, settlements — the page disputes get settled on.
**Why it exists:** "why is my balance ₹X?" must be answerable in one place,
itemized, without manual math.
**Method:** GET · **Entry:** → `WorkerPayrollDetailView` (`views.py:98`,
LoginRequired) → `worker_detail.html`.
**Permissions — the interesting part:** NOT management-only:
`payroll_service.can_view_worker(viewer, worker_id)` allows management OR
the worker viewing THEMSELF. One URL, two audiences, one predicate.
**Validation:** pk resolved via `_WorkerFromPk`; unknown pk → 404.
**Transaction/locks:** none (read).
**Reads:** `worker_summary`, **`worker_balance_breakdown`** (gross −
reversals − debits-by-category = payable — the dispute tool),
`worker_ledger`, `worker_advances`, `worker_settlements`.
**Writes/external:** none. **Failure modes:** none designed.
**Performance:** `select_related` chains on ledger/assignment reads
(`worker_assignments` pulls 5 relations in ONE query).
**Security:** wall #4 relevance — what a WORKER sees here is their own
lane; management context adds `is_super_admin` flags for template display
only (service re-gates any action).
**DSA:** the breakdown = partitioned fold (fold by category).
**Tests:** `test_views.py` + breakdown correctness in service tests.
**Engineering lesson:** build the itemized-derivation call ONCE in the
service (`worker_balance_breakdown`) — every future "why is it ₹X" question
costs one function call, not an afternoon.
**Required knowledge:** [ledger](../../features/ledger.md) ·
[payroll](../../features/payroll.md).
**Continue to:** §4 (pay them) · [money-looks-wrong](../../debugging/money-looks-wrong.md) (dispute flow).

---

## 4. `/expense/workers/<pk>/settle/` — `settlement-create` 💰

**Business purpose:** hand the worker CASH against their payable.
**Why it exists as its OWN url:** settlement ≠ payment (Model A). The
obligation was born at Adda-settlement; this URL only moves cash — one
event, one meaning, one URL.
**Method:** GET (form) + POST · **Entry:** → `SettlementCreateView`
(`views.py:238`, LoginRequired + `_ManagementOnly` + `_WorkerFromPk`,
TemplateView) → `settlement_form.html`.
**Permissions:** management (mixin + sidebar); write-offs inside are
SA-only (service-enforced).
**Validation:** amount parsed `Decimal(str(x))`-style at the edge; `paid < 0`
refused; **`recoveries` refused entirely** (V2-2 re-homing — the refusal
message teaches where recovery lives now).
**Transaction boundary:** `settlement_service.create_settlement`
(`@transaction.atomic`).
**Locks — two real races live here (learn both):**
global advisory lock serializes `SETL-xxxx` numbering across ALL workers
(two clerks, different workers, same next-ref → IntegrityError 500 —
the comment in code tells the story); `WorkerProfile` row-lock serializes
per-worker payments (over-pay race — profile chosen because it ALWAYS
exists, unlike advances on a cash-only payment).
**Service calls:** `create_settlement` → `ledger_service.log_debit`.
**Writes:** `PayrollSettlement` + PSI (write-offs) + ledger DEBIT
(`settlement_payment`). **Reads:** live payable (re-read UNDER lock).
**External APIs:** none.
```
Journey: POST → view (gate, parse) → create_settlement
[@atomic · ref-lock → profile-lock → re-read payable → guard amount ≤ payable]
→ PayrollSettlement + DEBIT → redirect + banner
```
**Failure modes:** amount > payable (refused, names the numbers) ·
recoveries passed (refused, redirects your habit to Adda settlement) ·
concurrent payment (second waits, re-reads smaller payable, may refuse).
**Response:** redirect to worker-detail with message.
**Performance:** trivial writes; the lock window is tiny by design
(validate-first).
**Security:** management + CSRF + SA-only write-offs + audit trail (PSI +
reason).
**DSA:** check-then-act gap closed by lock-and-reread; ref allocation =
the classic unique-sequence race.
**Tests:** `test_views.py` + refusal pins (recovery-at-payment is PINNED).
**Engineering lesson:** pick lock targets that exist on EVERY path — the
tempting lock (advances) fails the cash-only path; the boring one
(profile) always works.
**Required knowledge:** [transactions](../../concepts/django/transactions.md) ·
[locks](../../concepts/postgresql/locks.md) · [payroll](../../features/payroll.md).
**Continue to:** §11–13 (where the obligation was born).

---

## 5. `/expense/workers/<pk>/profile/` — `worker-profile`

**Business purpose:** payout metadata — phone, bank account name.
**Why it exists:** cash-day needs contact/payout details; separating it from
pay-basis (§6) keeps a low-risk edit away from a money-behavior edit.
**Method:** GET+POST (FormView) · **Entry:** → `WorkerProfileEditView`
(`views.py:295`, mgmt + `_WorkerFromPk`) → `worker_profile_form.html`.
**Transaction:** `payroll_service.update_payout_profile` (atomic, narrow).
**Writes:** `WorkerProfile` metadata fields only. **Locks:** none needed —
metadata, last-write-wins acceptable. **Failure modes:** form validation.
**Why simple:** no money semantics ride on these fields — and the design
KEEPS it that way by exiling `pay_basis` to its own audited URL.
**Tests:** `test_worker_profile_form.py`.
**Required knowledge:** Django FormView basics.
**Continue to:** §6 (the field that is NOT here, and why).

---

## 6. `/expense/workers/<pk>/pay-basis/` — `worker-pay-basis` 🔐

**Business purpose:** flip a worker between piece-rate and monthly salary (R4).
**Why it exists as its own URL:** this one field changes MONEY BEHAVIOR
(monthly workers' lines are structurally excluded from settlement) — so it
gets its own POST endpoint, its own audit trail, its own SA gate.
**Method:** POST only (plain `View`) · **Entry:** → `WorkerPayBasisUpdateView`
(`views.py:337`, mgmt mixin; **super-admin enforced in the SERVICE**).
**Transaction/locks:** `payroll_service.set_pay_basis` — atomic AND **joins
advisory 5374**: a basis flip cannot race a settlement finalize (the flip
would change which lines are settleable mid-write).
**Writes:** `WorkerProfile.pay_basis` + `WorkerPayBasisAudit` (old→new,
actor, reason — sole writer).
**Failure modes:** non-SA refused · unconfirmed flip refused (`confirmed=`
two-step).
**Security:** the layered lesson — mixin says management MAY see the
surface; the service says only SA may ACT (wall #3 never trusts wall #2).
**DSA:** joining the money gate's lock = participating in the total order.
**Tests:** `test_r4_monthly_basis.py`.
**Engineering lesson:** when ONE field changes money behavior, isolate it:
own URL + own audit + service-level role check + the money lock.
**Required knowledge:** [locks](../../concepts/postgresql/locks.md) ·
[single-writer](../../concepts/architecture/single-writer.md).
**Continue to:** §8 (why monthly workers can't take advances either).

---

## 7. `/expense/workers/<pk>/fnf/` — `worker-fnf` 🔐

**Business purpose:** Full & Final — a worker is leaving; settle ONLY their
lines, pay them out, optionally forgive advance remainders.
**Why it exists:** leavers can't wait for the whole Adda's settlement day;
partial settlement (§11.8) made a per-worker exit legal.
**Method:** GET (preview) + POST (execute) · **Entry:** → `WorkerFnFView`
(`views.py:360`, mgmt + `_WorkerFromPk`) → `worker_fnf.html`.
**Permissions:** management sees; **SA-only executes** (service).
**Service calls:** `fnf_service.fnf_preview` / `fnf_execute(worker, user,
write_off_reason)` — an ORCHESTRATOR: it calls the settlement chokepoint
with `only_worker=` (a filter on the funnel OUTPUT — every guard runs
first), then cash, then audited write-offs.
**Writes:** via the chokepoints only — fnf_service itself writes NOTHING
(the single-writer lesson in orchestration form).
**Locks/transaction:** inherited from the chokepoints it calls (5374 etc.).
**Failure modes:** non-SA · missing write-off reason · nothing to settle.
**Write-off subtlety (teachable):** forgiven advance = audited PSI row with
**NO ledger debit** — a forgiven loan is not a payment; payable untouched,
outstanding derives to 0.
**Tests:** `test_r7_fnf.py`.
**Engineering lesson:** compose risky flows from EXISTING guarded verbs —
an orchestrator that writes nothing can't create a second money door.
**Required knowledge:** [settlement](../../features/settlement.md) ·
[advances](../../features/advances.md).
**Continue to:** §13 (the chokepoint FnF rides).

---

## 8. `/expense/advances/add/` — `advance-add`

**Business purpose:** record a loan to a worker (₹500 before settlement day).
**Why it exists:** loans are factory reality; recording them OUTSIDE the
earnings math is what keeps both numbers provable ([two pockets](../../features/advances.md)).
**Method:** GET+POST (FormView) · **Entry:** → `AdvanceCreateView`
(`views.py:218`, mgmt) → `advance_form.html`.
**Transaction:** `advance_service.record_advance` (atomic).
**Writes:** ONE immutable `WorkerAdvance` row. **NO ledger entry** — the
loan pool is ledger-free by design.
**Validation/failure modes:** amount > 0 (app + DB CHECK) · **monthly
workers refused** with a message that TEACHES (no recovery path exists for
them — a loan you can't recover is a write-off waiting).
**Attachment:** proof photo supported.
**Security:** management + CSRF; immutability = no edit endpoint exists at all.
**Tests:** refusal pin for monthly workers · recovery math in settlement tests.
**Engineering lesson (why simple):** one INSERT, no ledger, no locks —
because RECOVERY (the hard part) was exiled to the settlement gate where
locks already live. Simplicity by putting complexity where it's already paid for.
**Required knowledge:** [advances](../../features/advances.md).
**Continue to:** §13 (where recovery actually happens).

---

## 9. `/expense/expenses/` — `factory-expense-list`

**Business purpose:** the factory's running-costs book (rent, tea,
electricity) with monthly totals.
**Why it exists / why SEPARATE from worker money:** ADR-0011 — factory
costs are factory-LEVEL, never allocated per-Adda, never a ledger. Mixing
them into worker money would poison both books.
**Method:** GET · **Entry:** → `FactoryExpenseListView` (`views.py:419`,
mgmt) → `factory_expense_list.html`.
**Reads:** `expense_service.monthly_totals`. **Writes:** none (void action
posts elsewhere; SA-gated in service).
**Why simple:** a list over simple rows — the DESIGN keeps it simple by
refusing per-Adda allocation forever (the ADR is the complexity firewall).
**Tests:** `test_r5_factory_expense.py`.
**Required knowledge:** [ADR-0011](../../../docs/adr/0011-monthly-salary-factory-level.md).
**Continue to:** §10, §14–16 (the recurring-expense machine).

---

## 10. `/expense/expenses/add/` — `factory-expense-add`

**Business purpose:** record one running cost.
**Method:** GET+POST (FormView) · **Entry:** → `FactoryExpenseCreateView`
(`views.py:462`, mgmt) → `factory_expense_form.html`.
**Transaction:** `expense_service.record_expense` (sole writer; atomic).
**Writes:** `FactoryExpense`. **Corrections:** void-with-reason (SA), never
edit/delete — soft-state citizenship even outside the ledger.
**Failure modes:** validation; void without reason refused.
**Why simple:** money that never meets worker-money stays simple — the
boundary (ADR-0011) is doing the work.
**Tests:** `test_r5_*` + `test_expense.py`.
**Continue to:** §16 (generation writes THROUGH this same verb).

---

## 11. `/expense/settlements/` — `adda-settlement-list`

**Business purpose:** the settlement queue — which Addas are READY to
settle vs WAITING (and why).
**Why it exists:** the owner's settlement day starts here; readiness is
computed, not remembered.
**Method:** GET · **Entry:** → `AddaSettlementListView` (`views.py:682`,
mgmt) → `adda_settlement_list.html`.
**Reads:** `adda_settlement_service.settlement_queue()` — **PA-11-2 law:
this preview runs the SAME guards as finalize** (era, monthly, grouped→0).
A queue that lies about money is a money bug.
**Writes/locks:** none. **Failure modes:** none designed.
**Performance:** queue batching is count-pinned (`test_queue_batching.py`
— `assertNumQueries(2)` / cached `(0)`).
**Engineering lesson:** previews of money ARE money surfaces — share the
funnel, never approximate it.
**Required knowledge:** [settlement §Backend](../../features/settlement.md).
**Continue to:** §12 (start one).

---

## 12. `/expense/settlements/start/<adda_pk>/` — `adda-settlement-start`

**Business purpose:** open a DRAFT settlement (ADST-xxxx) for an Adda.
**Method:** POST only · **Entry:** → `AddaSettlementStartView`
(`views.py:698`, mgmt).
**Transaction:** `create_draft` (atomic; ref numbering under the settlement
advisory gate).
**Writes:** ONE `AddaSettlement` row, status DRAFT — **zero money, zero
frozen rows**; drafts are recomputable scratchpads and legally deletable.
**Failure modes:** duplicate-draft / bad adda → refused loudly.
**Why simple:** because the DESIGN pushed all cost into finalize — draft-
heavy/gate-thin ([settlement-lifecycle](../../flows/settlement-lifecycle.md)).
**Continue to:** §13 (the cockpit).

---

## 13. `/expense/settlements/<reference>/` — `adda-settlement-detail` 💰💰 THE GATE

**Mental Model — the airport.** Passengers (contribution lines) arrive at
the gate. Security checkpoints run IN ORDER (the funnel guards: era,
monthly, grouped). Only when every checkpoint passes does boarding begin
(the atomic write). Takeoff = COMMIT — everyone flies together. A cancelled
boarding = ROLLBACK — as if nobody ever queued. And once airborne, you
don't edit the passenger list — you schedule a RETURN FLIGHT (reversal).
Hold this picture; the rest of this section is just naming the checkpoints.

**Common misconception:** "finalize creates the worker's money out of
nothing." No — the CLAIM existed since the report (Expected); finalize
converts verified claims into ledger truth. Delete this section's rows and
the claims remain; that's why reverse is always possible.

**Business purpose:** the settlement cockpit — preview every worker's
lines, plan variance + advance recovery, then FINALIZE (money is born),
or reverse/supersede/discard.
**Why it exists:** the system's entire money philosophy needs exactly ONE
place where obligation becomes real — this is it.
**Method:** GET (cockpit) + POST (`action=` dispatch) · **Entry:** →
`AddaSettlementDetailView` (`views.py:726`, mgmt) →
`adda_settlement_detail.html`.
**Permissions:** management; reconciliation OVERRIDE = SA + mandatory
reason (S5, service-enforced, evidence row).
**Validation:** per-worker variance counts + per-advance recovery amounts
parsed as strings → service validates (PA-07-2 class).
**Actions & their services (all `adda_settlement_service`):**
`finalize` → `finalize_adda_settlement(variance=, recoveries=,
reconciliation_override=)` · `reverse`/`supersede` →
`reverse_adda_settlement` · `discard` → `discard_draft`.
**Transaction & locks (memorize — this is the lock-order canon):**
```
@atomic · pg_advisory_xact_lock(5374) → ADST row → its AddaStageRecords
→ their WSC rows of=('self',)  ← PA-11-3: the billed qty lives on WSC
→ WorkerProfiles (sorted by id) → WorkerAdvances
```
**Writes at finalize:** per line: era-B SWA + ledger CREDIT + provenance
stamp (`WSC.settlement_line`) · per recovery: ledger DEBIT + PSI · per
worker: frozen `AddaSettlementItem` · totals frozen · timeline event.
**Reads:** production truth via the funnel (`_settleable_lines`) +
resolver (`verified ?? reported`). **External APIs:** none.
```
Journey (finalize): POST action=finalize → view (gate, parse)
→ finalize [locks → funnel guards → validate ALL recoveries → write money
→ FINALIZED] → log_adda(SETTLEMENT_FINALIZED) → redirect + banner
```
**Failure modes (each one designed + tested):** not-a-draft · "nothing to
settle" (guards did their job — era/monthly/grouped) · recovery > remaining
· S5 reconciliation BLOCK (flag-gated; SA override audited) · double-
finalize (second waits on locks, sees FINALIZED, refuses).
**Response:** redirect with outcome message.
**Performance:** validate-first keeps the lock window small; preview reuses
pinned queue reads.
**Security:** the deepest defense stack in the repo — 4 walls + 4
concurrency layers + append-only corrections.
**DSA:** total lock ordering (deadlock-freedom by construction) ·
sorted worker locks.
**Tests:** `test_adda_settlement_service.py` · `test_adda_settlement_views.py`
· `test_v2_3_guards.py` · `test_s5_recon_block.py` · goldens ₹344.25/₹801/₹633.
**Why complex (own the answer):** it absorbs the complexity every other
money URL avoided — §4 is thin BECAUSE §13 is thick. That's the
draft-heavy/gate-thin principle in URL form.
**Engineering Decision.**
*Problem:* convert verified work into provable money, correctable without
lying. *Options considered:* (A) credit at allocation — the ORIGINAL
system; every production correction became a money correction; (B) editable
settlements — audit death; (C) event-log + one atomic gate + compensating
corrections. *Chosen:* C. *Trade-offs accepted:* more rows forever,
"just-edit-it" requests must be refused, reverse-then-redo is slower than
edit. *Would we still choose it today?* **Yes — with evidence:** the era
cutover FROM (A) is documented history (ADR-0007, rollback lever kept,
soak-gated deletion), and every hostile review since has attacked (C) and
lost. Few systems get to say their alternative was production-tested and
retired.
**Evolution Timeline.**
Originally: earnings credited at allocation (era-A) → *problem discovered:*
corrections tangled, provisional numbers hardened (paid-120/produced-105
class) → *refactor:* V2 two-truths + AddaSettlement (V2-2/V2-3, 2026-06),
then S-series armor (resolver, reconciliation, reopen guards, rate
corrections) → *current:* settlement-first default, era-A readable+
reversible → *future:* S6 column retirement + era-A physical deletion, both
soak-gated; balance snapshot table = registered seam if scale demands.
**Required knowledge:** [settlement](../../features/settlement.md) →
[transactions](../../concepts/django/transactions.md) →
[locks](../../concepts/postgresql/locks.md) →
[two-truths](../../concepts/architecture/two-truths.md).
**Continue to:** [settlement-lifecycle](../../flows/settlement-lifecycle.md)
(every state) · [money-looks-wrong](../../debugging/money-looks-wrong.md).

---

## 14. `/expense/templates/` — `expense-template-list`

**Business purpose:** recurring factory costs defined ONCE (rent every month).
**Method:** GET · **Entry:** → `ExpenseTemplateListView` (`views.py:511`, mgmt).
**Reads:** templates + audit context. **Writes:** none here; amount changes
require a REASON (audited — `ExpenseTemplateAmountAudit`).
**Why simple:** definitions, not money — the money happens at generation (§16).
**Tests:** `test_expense_templates.py`.
**Continue to:** §16.

---

## 15. `/expense/templates/add/` — `expense-template-add`

**Business purpose:** define one recurring expense (label, category, amount,
start date).
**Method:** GET+POST (FormView) · **Entry:** → `ExpenseTemplateCreateView`
(`views.py:565`, mgmt) · **Transaction:** `create_expense_template`.
**Writes:** `ExpenseTemplate`. **Failure modes:** validation.
**Why simple:** a definition row; all safety lives at generation +
amount-change (audited with reason).
**Continue to:** §16.

---

## 16. `/expense/generate/` — `expense-generate`

**Business purpose:** materialize a month's recurring expenses in one click.
**Why it exists:** typing rent/salaries every month = forgotten months and
typos; generation makes the recurring book complete and IDEMPOTENT.
**Method:** GET (preview) + POST (`confirm=`) · **Entry:** →
`GenerateExpensesView` (`views.py:602`, mgmt) → `generate_expenses.html`.
**Transaction:** `generate_monthly_expenses(year, month, confirm=)` (atomic).
**Writes:** `FactoryExpense` rows — **THROUGH `record_expense`, the sole
writer, even internally** — + `ExpenseGenerationRecord` (the per-period
idempotency receipt). Re-run = no duplicates (the record refuses).
**Failure modes:** already-generated period (refused, names the record) ·
unconfirmed (preview only).
**DSA:** idempotency via a uniqueness receipt — same pattern as the ledger's
partial-unique, application-level flavor.
**Tests:** `test_expense_generation.py`.
**Engineering lesson:** batch generators must be idempotent and must reuse
the single writer — a generator with its own INSERT is a second pen.
**Required knowledge:** [single-writer](../../concepts/architecture/single-writer.md).
**Continue to:** §9 (where the rows land).

---

## 17. `/expense/material-spend/` — `material-spend`

**Business purpose:** the cloth-spend window — what material value went out,
per period (RMX-D).
**Method:** GET only — **read-only BY DESIGN** (the view has no POST).
**Entry:** → `MaterialSpendView` (`views.py:659`, mgmt) → `material_spend.html`.
**Reads:** cross-app material figures. **Writes:** none, ever.
**Why simple (and why that's a feature):** reporting surfaces that WRITE
grow into second truths; this one is structurally incapable of it.
**Tests:** `test_material_spend.py`.
**Required knowledge:** [two-truths](../../concepts/architecture/two-truths.md)
(why report ≠ record).

---

## Learning Graph (this page)

**Before:** [money-story](../../project/money-story.md) ·
[README](README.md) Start-Here. **After:** [views.md](views.md) (the
handlers behind these URLs) → [services.md](services.md) (the verbs) →
walk §13's journey against real code.

## Direct paths

`config/expense/urls.py` · `config/expense/views.py` ·
`config/expense/services/` · `config/expense/models.py` ·
`templates/expense/` · `config/expense/tests/`

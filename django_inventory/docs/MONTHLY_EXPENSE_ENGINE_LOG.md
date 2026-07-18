---
id: docs-monthly-expense-engine-log
type: receipt
status: active
owner: append-only
scope: campaign
anchors: —
verified: 2026-07-18
---

# Monthly Expense Engine — Build Log (Campaign Phase 16)

> Evidence doc of record for Phase 16 (created at MEE-0, 2026-07-18, per the frozen
> execution contract [PHASE_16_MONTHLY_EXPENSE_ENGINE.md](campaign_contracts/PHASE_16_MONTHLY_EXPENSE_ENGINE.md)).
> Contract = procedure; THIS log = what was chartered, approved (U14 + census addendum),
> built, and proven. Append-only; corrections dated.
> Governing truth-locks: **ADR-0011** ([0011-monthly-salary-factory-level](adr/0011-monthly-salary-factory-level.md))
> · **R5 Money-Write census** ([R5_HOSTILE_REVIEW Part 2](R5_HOSTILE_REVIEW_2026_07_05.md))
> · `expense_service` = sole FactoryExpense writer · append-only posture (create/void, no edit).

## MEE-0 — Product charter + gate + ratification — _(executed 2026-07-18; ⏸ AWAITING OWNER CHARTER MEE-D1 + rulings D2–D9)_

### 0.1 Gate verification (all PASS, live)

| Gate item | State |
|---|---|
| Phase 15 closed (locked order) | ✅ 🏁 CLOSED 2026-07-18 (status row; BOD_BUILD_LOG §BOD-F verdict) |
| Battery entry baseline | ✅ **1795/1795** (10-app 1051 · patterns_ai 528 · devseed 138 · verification 78 — the P15 terminal baseline) |
| Ledger baseline (money do-no-harm anchor) | ✅ **170 rows / Σ ₹10,880.25** (live recount at MEE-0) |
| FactoryExpense baseline | ✅ **4 rows total · 2 non-voided** (electricity ₹1,500.00 · salary ₹9,000.00 — live) |
| Golden-journey references | ✅ ₹801.00 (T-SHIRT) · ₹344.25 (LOWER) · ₹633.00 (3-PATTI) + golden ₹225 byte-invariant (settlement suite) |
| Monthly-worker audience exists | ✅ 2 `pay_basis=monthly` profiles live; 1 user with the L-3 reference `User.salary` set (₹9,000) |
| No recurrence model exists (contract fact re-verified) | ✅ zero template/recurrence/period tables; expense migrations end at 0014; 0 matches for recurr/Template/schedule in expense/models.py |
| No scheduler infrastructure (contract fact re-verified) | ✅ R5 census: no celery/cron/queue anywhere; re-confirmed no new arrivals |
| Sole-writer wall intact | ✅ R5 Part-2 census verdict stands ("every money write flows through its single designated service"); `record_expense`/`void_expense` = the only FactoryExpense writers |
| Instruments live | ✅ U14 procedure (unexercised — this phase = first live use) · Money-Write census addendum mechanism (MEE-D3) · knowledge_sync diff-mode · verification engine 1.0.0 · dataset spec amendment path (A2 precedent, fresh from P15) |
| Git safety | ✅ HEAD 49404001 · 2 stashes · 0 staged · NO commits (U2) |

### 0.2 Dependency verification

- **ADR-0011 (ACCEPTED 2026-07-05)** — read in full; the reserved future this phase
  implements is its §"Future (reserved)" item 1-adjacent automation: recording recurring
  factory costs. Its guardrails bind every wave: factory-level only · `worker` FK
  audit-only, never a ledger/settlement relationship · no per-Adda allocation · salary
  never enters processing_cost/full-cost/settlement · frozen histories never rewritten.
- **R5 record** — FactoryExpense append-only (create/void; "No edit function EXISTS");
  void = SA + mandatory reason (MGT-C certified lever); M-3 duplicate-salary
  warn-and-confirm (`confirmed_duplicate`) lives in `record_expense`; M-2 advances
  blocked for monthly workers (temporary rule, untouched); **L-3: `User.salary` = a
  display-only prefill convenience, zero money consumers** — reaffirmed by the Phase-15
  F4 permanent law (never DERIVE obligations from it).
- **Prior handoffs into this phase:** P15 BOD-F ("engine KPIs enter the BOD only via the
  Ladder + Registry" — MEE-D8) · P13 VER-E (candidate checks adopted per the registry's
  own law) · P14 KS-E (sync diff per wave) · P12 SEED-F (dataset spec dated-amendment
  path; A2 precedent) · 2026-07-18 RM-review carry-in (**MEE-0 records: raw-material
  purchasing = an explicit NON-GOAL of this engine** — the RM domain's future, never MEE's).
- **PDD:** v1.0 frozen; §21 = the FactoryExpense product truth (category set LOCKED:
  rent/electricity/salary/other — extending it = PDD revision); the MEE-D1 charter enters
  via the amendment register (entry 7 expected).

### 0.3 Architecture review (what exists to build on)

- **Model:** `FactoryExpense` (category/amount/expense_date/notes/entered_by/worker
  [P-1: required iff salary]/void triple) + `amount > 0` CheckConstraint; ordering
  `-expense_date`.
- **Writer:** `expense_service.record_expense` (management-gated; category validation;
  M-3 duplicate-salary confirm; P-1 worker rule) · `void_expense` (SA + reason) ·
  `monthly_totals(y,m)` (void-aware; the BOD F1/F2 source). **All additive-only for this
  phase — contract §10 forbids touching them.**
- **Surfaces:** `expense:factory-expense-list` (list + month filter + totals + create
  POST + void; MGT-C certified: create=management, void=SA lever) — the engine's
  generated rows land in THIS list unchanged.
- **Engine shape (contract §6.1, ratification pending):** templates (new additive models)
  → generation (additive expense-service-family function; idempotent per (template,
  period), constraint-backed; preview-before-write) → surfaces (template admin +
  generate-trigger + review into the existing list; optional management command for
  external cron — MEE-D4).
- **Battery:** expense already a member — suite grows, no framework amendment.

### 0.4 Current expense-system analysis (facts a charter answer may lean on)

- Live data today: 2 non-voided rows (salary ₹9,000 · electricity ₹1,500) — exactly the
  monthly-shaped costs the owner re-types each month.
- 2 monthly-basis workers exist (the salary audience); 1 has the reference `User.salary`
  prefill set.
- The M-3 duplicate-salary guard ALREADY protects worker+month uniqueness for manual
  entries — the engine's (template, period) idempotency must COMPOSE with it, not bypass
  it (interview Q9; the generation path must decide how `confirmed_duplicate` interacts
  with generated salary rows when a manual row already exists that month).
- No backlog of voided-regeneration history exists (2 voided rows total, both DEV-era).

### 0.5 Business interview questions (→ MEE-D1; grouped; nothing defaults)

**A. The recurring catalog**
1. Which expenses recur? (Worker salaries? Rent? Electricity? Anything under "other"?)
2. Fixed set at launch, or must the owner be able to add/retire templates freely?

**B. Amounts**
3. Where does each template's amount come from — a fixed amount typed on the template,
   or (salary only) the `User.salary` reference field? ⚠ Note on record: `User.salary`
   is informational-only (L-3) and the Phase-15 F4 permanent law forbids DERIVING
   obligations from it. Reading it as a template's amount SOURCE at generation time is
   owner-ruling territory — explicitly allowed, explicitly refused, or fixed-amounts-only.
4. Can a template's amount change over time? (If yes: future periods only?)

**C. Cadence + period**
5. Monthly-only, or other cadences? Which day anchors a period (1st? owner's choice per
   template?)
6. When may a period be generated — only once the period starts, after it ends, or
   anytime (pre-generation of a future month)?

**D. Trigger + review**
7. WHO triggers generation (super-admin only? any manager?) and is preview→confirm the
   required flow (contract default)?
8. Should generation also be runnable as a management command for external cron
   post-deploy (MEE-D4 documentation-only default), or UI-only?

**E. Policy edges (MEE-D5/D9 content)**
9. If a manual salary row for the same worker+month already exists, should generation
   skip that worker (respect M-3), warn-and-confirm, or create alongside?
10. Proration: a template activated mid-month — full amount, skip the partial month, or
    prorate (formula = owner's)?
11. Backdating: may past periods be generated? How far back?
12. Voided-row policy: a generated row voided by SA — may that (template, period) be
    regenerated? Freely, or with confirmation?
13. Worker exit/FnF: what happens to that worker's salary template — auto-deactivate,
    owner deactivates manually, or generation refuses inactive workers?
14. Month with a deactivated template mid-period: generate or skip?

**F. Visibility**
15. Do generated rows need to be distinguishable from manual rows in the list (a "generated"
    marker), or indistinguishable ordinary rows?
16. BOD widgets for the engine (this-month recurring total · pending-generation state):
    build as this phase's final owner-gated wave, or hand off to a later session (MEE-D8)?

### 0.6 Decision Pack — MEE-D1..MEE-D9 (contract Appendix A; defaults binding unless overridden)

| # | Item | Default on the table | Needs |
|---|---|---|---|
| MEE-D1 | **Product charter** | NONE — owner-supplied (§0.5 answers → PDD register entry). Unanswered = phase blocked | **OWNER** |
| MEE-D2 | Data model + U14 gate | additive NEW tables only (template + period-coverage), (template,period) unique, soft-state lifecycle; per-migration approval BEFORE writing; reverse path proven on a disposable copy; owner sees the Phase-17 one-liner at approval | ratify |
| MEE-D3 | Writer discipline + census addendum | generation = additive function INSIDE expense-service family; UI/command write nothing; dated owner-approved addendum to the R5 Part-2 census | ratify |
| MEE-D4 | Trigger mechanism | management-triggered preview→confirm UI + a management command wrapping the SAME function; no in-repo scheduler; external cron = documented post-deploy ops decision | ratify |
| MEE-D5 | Period/idempotency semantics | one row per (template,period) constraint-backed; converging re-runs; template changes affect future periods only; proration/backdating/void-regeneration = D1 charter content | ratify |
| MEE-D6 | Permissions | template administration = SA-only (templates encode salary amounts); generation trigger = management; void unchanged (SA lever); certified double-gate | ratify |
| MEE-D7 | Tests + battery | expense-suite growth (constraints · idempotency · purity · permissions · ADR-0011 predicates); golden byte-checks at MEE-D; NO framework amendment | ratify |
| MEE-D8 | BOD widgets | engine KPIs only via the PHASE_15 Ladder + Registry — final owner-gated wave here OR a later session (owner's call, §0.5 Q16) | **OWNER** |
| MEE-D9 | Monthly-worker relationship | salary-template worker FK stays AUDIT-ONLY (ADR-0011); pay-basis/FnF levers untouched; exit behavior = charter policy (§0.5 Q13) | **OWNER** (via Q13) |

### 0.7 Risks

| # | Risk | Posture |
|---|---|---|
| R-1 | **ADR-0011 drift by convenience** — a chartered wish ("show salary in Adda cost", "% of output") crossing the wall | §16.5 stop: owner ADR-revision territory, never an edit |
| R-2 | **`User.salary` as amount source** collides with L-3 informational-only + the F4 never-derive law | surfaced verbatim at Q3; owner ruling required either way |
| R-3 | **M-3 composition** — generated salary rows vs the manual duplicate-salary guard (double-record of a month's salary) | Q9 makes the policy explicit; MEE-B tests pin whichever ruling lands |
| R-4 | **First live U14** — migration discipline never exercised; temptation to "just write it" | MEE-A hard-stops at the design gate; reverse path proven on a disposable copy |
| R-5 | **Census addendum skipped/informal** | MEE-B stop condition; addendum quoted verbatim + owner-approved before the function lands |
| R-6 | **Scope creep** toward disbursement/payroll/allocation/scheduling | contract §2.2 Out + §16.10; RM purchasing additionally recorded as a non-goal (§0.2) |
| R-7 | **Period-boundary correctness** (timezone/month edges — the completed_today lesson from P15) | period anchored on DateField semantics (expense_date is a date, no tz exposure); MEE-B tests cover month boundaries |
| R-8 | **Phase-17 corner-painting** via schema choices | MEE-D2: owner sees the P17 one-liner at approval; new tables reference nothing production-side |

### 0.8 Implementation waves (contract §7, restated for ratification)

MEE-A (model design → **U14 STOP** → approved migrations → battery) → MEE-B (generation
function; U8-hostile main-thread; census addendum; purity + idempotency + ADR-0011 proof
set v1; battery) → MEE-C (surfaces: template admin + preview→confirm trigger + review;
certified gating; mobile evidence; battery) → MEE-D (money certification wave: ledger/
golden/costing byte-checks · MGT-C re-proof · full permission matrices · policy proofs)
→ MEE-E (sync disposition · U6 docs · `seed_feature monthly-expense` P11 amendment ·
P13 handoff notes · MEE-D8 disposition · deployment note · charter-coverage census ·
VERDICT). One wave per session, STOP after each.

### 0.9 Battery strategy

Entry baseline **1795/1795**; sequential fresh-DB (U5) at every code-wave close
(MEE-A/B/C + any MEE-D fix wave); arithmetic = 1795 + expense-suite growth per wave,
recorded here; migration waves additionally prove fresh-DB migrate-forward + the
documented reverse on a disposable copy. No framework amendment (expense = existing
member; canonical 4-suite command list unchanged).

### 0.10 Documentation touch points

Per wave (U6, same session): this log (append-only) · status file row + battery dashboard
· `config/expense/README.md` + `docs/apps/expense/GUIDE.md` (owning docs; new files → GUIDE
rows) · CHANGE_IMPACT_MATRIX per changed file · DOCUMENTATION_INDEX (this log's row at
MEE-0 ✅) · **PDD amendment register** (MEE-0: the D1 charter = expected entry 7) ·
**R5_HOSTILE_REVIEW Part 2** (MEE-B: the dated census addendum) ·
**DEV_DATASET_ARCHITECTURE §12** (MEE-E: `seed_feature monthly-expense` amendment) ·
PHASE_16 Appendix A (Design Record fills + dated amendments) · campaign memory.

### 0.11 MEE-0 verdict

Mechanics COMPLETE — gates PASS, truths reconciled, zero ambiguities found beyond the
owner-decision surface itself (every unknown is a D1/D8/D9 charter question, listed at
§0.5). **⏸ BLOCKED BY DESIGN on the owner:** MEE-D1 charter (the §0.5 interview) + D8 +
D9(Q13) answers + ratification of D2–D7 defaults ("I accept the defaults" suffices for
D2–D7). No code, no models, no migrations, no services were touched this session.

_Next: owner answers §0.5 + rules the Decision Pack → PDD register entry recorded →
MEE-A (data-model design + the first live U14 gate)._

### 0.12 Owner charter direction + D1 design review (2026-07-18)

**Owner rulings received (verbatim-faithful):** MEE-0 methodology approved · **D2–D7
defaults ACCEPTED** · implementation still NOT authorized · this message = the product
charter DIRECTION + a design-review commission: permanent recurring-expense engine;
future-proof for multiple frequencies WITHOUT redesign, but **build no frequency beyond
what is approved**; template-driven; generated rows = ordinary FactoryExpense via the
existing certified writer; the engine never bypasses the money architecture. Boundaries
re-affirmed: RM purchasing · payroll · settlement · BOD changes · supplier management all
OUTSIDE Phase 16.

**The design review (recommendations only — full text delivered in-session, headline
record here):**

- **Future-proofing = ONE schema decision, not built features:** templates carry a
  `frequency` enum (V1: MONTHLY only) + an anchor/effective window; idempotency coverage
  is keyed by a frequency-agnostic **`period_key` string** (monthly "2026-07"; a future
  weekly "2026-W29", quarterly "2026-Q3", daily "2026-07-18" — same table, same
  uniqueness, zero redesign). One period-resolver seam derives period_key + due-ness from
  frequency. Adding a frequency later = an enum value + a resolver branch + a PDD
  change-control entry — never a schema rework.
- **Recurrence verdicts (V1 = MONTHLY only):** monthly BUILD (rent/electricity/salary —
  the live data is exactly this shape). One-time DEFER (manual entry already covers it).
  Daily/weekly DEFER (manual-trigger cadence impractical without a scheduler — MEE-D4;
  daily wages = payroll territory, out). 2-weekly DEFER (anchor-interval math; via the
  future custom mechanism). 2-monthly/quarterly/half-yearly/yearly DEFER (month-multiples
  of the same resolver; quarterly/yearly additionally need the owner's calendar-vs-
  financial-year definition — deferred WITH them). Custom interval DEFER (the enum +
  resolver design leaves room; enabling it = its own dated decision).
- **Template fields V1:** category (§21 LOCKED set) · **fixed amount only** (variable
  amounts DEFERRED — barely better than manual entry) · worker FK ONLY for
  category=salary (P-1 mirror; audit-only per ADR-0011/MEE-D9) · start date (anchor) ·
  optional end date (= expiry) · is_active soft-state · notes (carried onto generated
  rows). **Salary amounts = typed fixed amounts on the template** — `User.salary` stays
  informational (L-3 + the F4 never-derive law); at most a form-prefill sugar exactly like
  today's manual form (recommended D1 answer to the R-2 question). Supplier linkage NO
  (out of scope, no entity exists) · warehouse/raw-material linkage NO (future visions,
  never V1). **Template amounts IMMUTABLE — "edit" = retire (deactivate) + create a new
  template** (append-only philosophy; kills template-versioning machinery entirely;
  future periods follow the new template by construction).
- **Generation behavior:** mandatory read-only PREVIEW (what would generate + every skip
  with its reason) → explicit CONFIRM (management-gated POST) → atomic per period
  (all-or-nothing; failed generation = clean rollback, zero partial coverage) →
  idempotent ((template, period_key) uniqueness; re-runs create 0 and say why).
  **M-3 composition (Q9 recommendation):** a salary template SKIPS a worker+month that
  already has a non-voided manual salary row (skip reason shown); the engine NEVER passes
  `confirmed_duplicate` — if the template should win, the SA voids the manual row and
  regenerates. **Void→regenerate:** voiding a generated row does not silently free the
  period; regeneration = an explicit confirmed action allowed only when the covering row
  is voided — a NEW coverage row with a mandatory regeneration reason supersedes the old
  (append-only chain). **Template edits never touch covered periods** (immutability makes
  this structural).
- **Calendar rules:** anchor days 29-31 clamp to month-end (Feb/leap handled by clamping);
  all period math on local dates (Asia/Kolkata; the P15 completed_today lesson);
  financial-year/fiscal-quarter definitions = OWNER POLICY deferred with the frequencies
  that need them.
- **Audit trail V1:** coverage rows permanently record generated-at · generated-by ·
  template · period_key · the FactoryExpense FK · regeneration reason + supersession
  chain; `void_reason` stays on FactoryExpense (unchanged lever). Template versioning =
  unnecessary (immutability). Transient skip reasons (inactive/out-of-window/covered/
  manual-salary-exists) are RECOMPUTABLE facts — shown at preview + in command output,
  not persisted as rows in V1 (a persisted run-ledger = a deferred option, owner's call).
- **Reporting (design-only):** everything the owner listed derives READ-ONLY from
  templates + coverage + the existing `monthly_totals`: upcoming = active templates due;
  missed/overdue = active-window periods without coverage; generated-this-month =
  coverage join. V1 surfaces show per-template current-period status (pending/generated/
  skipped) on the template list; dedicated report pages + quarterly/yearly summaries +
  any BOD widgets = DEFERRED (BOD = owner boundary this phase).
- **Recommended V1 architecture (for the MEE-A U14 gate):** TWO additive tables —
  `ExpenseTemplate` (category · amount · worker? · frequency=MONTHLY · start/end ·
  is_active · notes · created_by) + `ExpenseGenerationRecord` (template FK · period_key ·
  expense FK · generated_by/at · supersedes?/regeneration_reason; **partial-unique
  (template, period_key) on current rows** — the codebase's conditional-constraint
  precedent) — plus ONE additive service function family member
  (`generate_monthly_expenses(year, month, actor, confirm)`) that writes ONLY via
  `record_expense`. No existing table/function touched.
- **New risks logged:** R-9 frequency creep (enum invites uncharted additions — every new
  frequency = PDD change-control) · R-10 template-immutability UX (retire+recreate may
  feel clunky — accepted trade-off vs versioning machinery; owner may overrule).

**State: ⏸ awaiting owner approval of this refined charter (→ PDD register entry 7 +
Appendix A D1 fill) → then MEE-A.** D2–D7 acceptance recorded above; D8 (BOD widget
disposition) already bounded by the owner ("BOD changes remain outside Phase 16" → the
handoff path); D9 exit/FnF policy still needs the owner's Q13 answer at charter approval.

## MEE-A — Data model + U14 gate — ⏸ DESIGN PRESENTED 2026-07-18, awaiting per-migration owner approval (U14). ZERO code/models/migrations written.

**Charter state at entry:** MEE-D1 APPROVED (PDD register entry 7) · D2–D7 accepted ·
D8 ruled (BOD outside phase → handoff) · D9 ruled (Q13: worker-inactive ⇒ generation
stops automatically at generation time; history untouched; FnF stays Payroll's) ·
**template-amount ruling: NOT immutable — evaluate versioning; recommend the safer
approach if versioning hurts simplicity/correctness.**

### A.1 The template-amount evaluation (owner-commissioned)

Three candidate designs against the owner's five requirements (stable identity · amount
changes allowed · every change traceable · generated months never change · historical
periods keep their generated amount):

| Design | Verdict |
|---|---|
| (a) Retire-and-recreate (MEE-0 proposal) | ❌ fails "stable identity" (new PK per change) — withdrawn per owner ruling |
| (b) Full versioning (template header + TemplateVersion rows; coverage FK→version) | ✅ correct but HEAVY: a second table in the template family, version-resolution logic in generation, version-aware UI/admin, more constraints. Its ONLY capability beyond (c): future-dated scheduled amount changes — **not chartered** |
| (c) **Mutable amount + append-only amount-audit trail** | ✅ ALL five requirements, minimum machinery — **RECOMMENDED** |

**Why (c) is safe and sufficient:** the generated `FactoryExpense` row already freezes
the amount forever (append-only money history) and the coverage row links template →
period → expense — so "historical periods retain the amount that was generated" is
STRUCTURAL, independent of template mutability. The one requirement mutability adds —
traceability of changes — is an append-only audit row per change (old → new · who ·
when · mandatory reason). This is the codebase's OWN certified pattern for exactly this
problem: `rerate_stage_role` + `RateCorrectionAudit` (S1.1) and `WorkerPayBasisAudit`.
The audit trail IS the version history ("versioned in effect"), without version tables.
If the owner ever wants future-dated amounts, the audit design grows into (b) by a dated
amendment — nothing built now blocks it.

### A.2 Final entity diagram

```
accounts.User ──┐ (created_by / generated_by / changed_by / worker — all PROTECT)
                │
   ┌────────────▼─────────────┐        ┌──────────────────────────────┐
   │ ExpenseTemplate          │ 1    * │ ExpenseTemplateAmountAudit   │
   │ (recurring config;       │◄───────┤ (append-only: old→new amount │
   │  stable identity, soft-  │        │  · changed_by · reason)      │
   │  state, MUTABLE amount)  │        └──────────────────────────────┘
   └────────────┬─────────────┘
                │ 1
                │ *
   ┌────────────▼─────────────┐  1   1 ┌──────────────────────────────┐
   │ ExpenseGenerationRecord  │────────►│ expense.FactoryExpense      │
   │ (coverage: period_key ·  │ OneToOne│ (EXISTING, untouched —      │
   │  supersession chain ·    │         │  the frozen money history)  │
   │  generated_by/at)        │         └──────────────────────────────┘
   └──────────────────────────┘
        │ supersedes (self-FK, regeneration chain)
```

No FK touches production/raw_materials/machines/settlement — the family references ONLY
`accounts.User` + `expense.FactoryExpense`.

### A.3 Table definitions (the U14 approval package)

**Table 1 — `expense.ExpenseTemplate`** (base `TimeStampedModel`: created_at/updated_at)

| Column | Type | Rule |
|---|---|---|
| id | bigint PK | stable identity (owner req. 1) |
| label | varchar(100) | human name ("Rent — Main Building"); descriptive, not unique |
| category | varchar(20), choices = FactoryExpense.Category (§21 LOCKED set) | no new categories |
| amount | numeric(12,2) | MUTABLE via the service only, every change audited |
| worker | FK accounts.User, null, PROTECT | ONLY for category=salary (P-1 mirror); AUDIT-ONLY (ADR-0011); IMMUTABLE after create (service-enforced — change of worker = retire + new template) |
| frequency | varchar(20), choices — V1 single value `monthly` | the future-proofing enum; new values = PDD change-control |
| start_date | date | anchor; first eligible period |
| end_date | date, null | optional expiry; last eligible period |
| is_active | boolean, default true | soft-state (deactivate, never delete) |
| notes | text, blank | carried onto generated rows |
| created_by | FK accounts.User, PROTECT | |

DB constraints: `amount > 0` (mirrors factoryexpense_amount_positive) ·
`(category='salary' AND worker IS NOT NULL) OR (category<>'salary' AND worker IS NULL)`
(the P-1 biconditional, DB-level) · `end_date IS NULL OR end_date >= start_date` ·
**partial UNIQUE (worker) WHERE category='salary' AND is_active** (one ACTIVE salary
template per worker — the M-3 spirit at template level).

**Table 2 — `expense.ExpenseGenerationRecord`** (coverage; base TimeStampedModel)

| Column | Type | Rule |
|---|---|---|
| id | bigint PK | |
| template | FK ExpenseTemplate, PROTECT | |
| period_key | varchar(20) | frequency-agnostic ("2026-07" for monthly) — the future-proof idempotency key |
| expense | **OneToOne** FK FactoryExpense, PROTECT | each coverage row ⇄ exactly one generated row |
| generated_by | FK accounts.User, PROTECT | |
| supersedes | self-FK, null, PROTECT | regeneration chain (old row's `superseded_at` set — the settlement-supersession pattern) |
| superseded_at | timestamptz, null | soft-state marker enabling the partial unique |
| regeneration_reason | varchar(200), blank | mandatory when supersedes set |

DB constraints: **partial UNIQUE (template, period_key) WHERE superseded_at IS NULL**
(THE idempotency law — one current coverage per template-period; regeneration = new row
+ old row marked, never violated) · `supersedes IS NULL OR regeneration_reason <> ''`
(reasoned regeneration, DB-level) · OneToOne(expense) unique by construction.

**Table 3 — `expense.ExpenseTemplateAmountAudit`** (append-only; base TimeStampedModel)

| Column | Type | Rule |
|---|---|---|
| id | bigint PK | |
| template | FK ExpenseTemplate, PROTECT | |
| old_amount / new_amount | numeric(12,2) | the change, both sides |
| changed_by | FK accounts.User, PROTECT | |
| reason | varchar(200) | MANDATORY (`reason <> ''` CheckConstraint — the RateCorrectionAudit pattern) |

DB constraints: `reason <> ''` · `old_amount <> new_amount` (a no-op "change" is not an
audit event) · both amounts `> 0`.

### A.4 Constraint review (why each exists)

Every business rule that CAN live in the DB does (the 26-CheckConstraint house style):
amount floors (corrupt totals impossible) · salary⇄worker biconditional (ADR-0011's
audit-only FK can never appear on a non-salary template, and salary templates can never
be worker-less) · one-active-salary-template-per-worker (double-salary at the TEMPLATE
level structurally impossible; the M-3 guard still protects the manual+generated
composition at generation time) · (template, period_key) partial-unique (idempotency is
a constraint, not a convention) · reasoned regeneration + reasoned amount changes
(auditability is a constraint) · PROTECT everywhere (no cascade can eat money config or
audit history). Django 5.0.1 note (house lesson): CheckConstraints use `check=`.

### A.5 Migration sequence + U14 gate

**ONE additive migration: `expense.0015_monthly_expense_engine`** — CreateModel ×3
(ExpenseTemplate → ExpenseTemplateAmountAudit → ExpenseGenerationRecord) + the
constraints above + indexes (template+period_key; worker partial). **NO existing table
is touched; no data migration; no RunPython.** Approval asked of the owner: this single
migration, per U14, BEFORE it is written.

### A.6 Reverse migration strategy

Additive-new-tables ⇒ reverse = `migrate expense 0014` (Django auto-reverses
CreateModel: drops the 3 tables; PROTECT FKs point OUTWARD from the new tables, so no
existing table blocks the drop). **Proof plan (at MEE-A execution, before battery):** on
a disposable copy of a scratch DB — migrate forward → insert nothing → migrate back to
0014 → schema diff clean vs pre-migration dump; then forward again fresh. Post-approval
law (contract §15): under U2 a landed migration is semi-irreversible once later waves
build on it — reverting then = owner decision.

### A.7 Money safety analysis (Money-Write impact review)

- **MEE-A itself writes NO money and creates NO writer:** tables only. FactoryExpense
  untouched (zero schema changes, zero rows).
- **New guarded tables:** ExpenseTemplate / ExpenseGenerationRecord /
  ExpenseTemplateAmountAudit join the purity-test guarded set — sole writers = the
  expense-service family additions coming at MEE-B (template create/deactivate/
  amount-change functions + the generation function). UI/command layers will hold zero
  ORM writes (purity-pinned).
- **The census addendum (MEE-D3) lands at MEE-B** with the function designs — quoted
  verbatim, owner-approved before the code exists. Scope preview: +3 config writers
  (template lifecycle) + 1 money-adjacent orchestrator (generation → `record_expense`)
  + 1 audit writer (amount change). `record_expense`/`void_expense` remain the ONLY
  FactoryExpense writers — the engine never gains its own.
- **Ledger/settlement/costing:** structurally unreachable — no FK, no import, no read
  of production/settlement state (contract §6.3); proof set (schema grep + costing-page
  byte-compare) runs at MEE-B/MEE-D as contracted.

### A.8 Phase-17 compatibility (MEE-D2's corner-painting check)

P17 = read-path raw-material → expense COST integration (models A/B/C; roll truth stays
the sole material record; aggregates derive at read time). This schema: (i) references
nothing material-side — no supplier/warehouse/material columns anywhere (deferred by
charter + the RM-V2 vision boundary); (ii) adds no FactoryExpense columns P17 would have
to reconcile; (iii) `monthly_totals` (P17's likely read seam) is untouched — generated
rows flow into it as ordinary rows, which is exactly what P17 expects. **No corner
painted; the owner sees this line per MEE-D2 when approving.**

### A.9 Battery impact

MEE-A is battery-bearing: expense-suite growth ≈ 10–14 tests (constraint violations ×6
[amount floor · biconditional both ways · date order · partial uniques ×2 incl.
regeneration path] · soft-state lifecycle · PROTECT behavior · migration
forward-on-fresh-DB smoke). Arithmetic: 1795 + growth (exact count recorded at the wave
close); full 4-suite sequential fresh-DB after migration lands; reverse proof on the
disposable copy is EXTRA-battery evidence (§A.6).

### A.10 Risks (this wave)

| # | Risk | Posture |
|---|---|---|
| A-R1 | First live U14 — precedent-setting; any deviation between approved DDL and written migration | migration written ONLY from the approved §A.3/A.5 text; diff quoted at close |
| A-R2 | Partial-unique semantics (regeneration) subtly wrong → duplicate current coverage | constraint tested both ways (violation + legitimate supersession) before any generation code exists |
| A-R3 | Mutable amount misused outside the audited service path | MEE-B purity test guards the table; until MEE-B, no writer exists at all |
| A-R4 | Salary-template ↔ M-3 interplay confusion (template-level unique vs row-level guard) | both layers documented here; generation-time behavior pinned at MEE-B per the charter (skip + reason) |
| A-R5 | Owner-approval drift (building beyond the approved DDL) | §16.3 stop condition: any need beyond this plan = STOP, new approval |

### A.11 Recommendation

**Approve design (c)** (mutable amount + append-only audit — all five of your
requirements at minimum machinery, on your own certified S1.1 pattern) **and the single
additive migration `expense.0015` exactly as §A.3/A.5 defines it.** Full versioning (b)
is not recommended: its only extra capability (future-dated amount schedules) is
unchartered, and it taxes every future wave (generation resolution, UI, tests) for a
feature nobody asked for. If you prefer (b) anyway, MEE-A re-presents before writing
anything.

_⏸ STOPPED per U14: no models, no migrations, no code written. Awaiting the owner's
per-migration approval of `expense.0015_monthly_expense_engine` (§A.3 DDL + §A.5–A.6
plan) — or a versioning override._

### A.12 Final implementation architecture review (owner-commissioned reuse audit, 2026-07-18)

**Full expense-module inspection performed (models · all 10 service files + `_shared` ·
forms · admin · views · templates · urls · management commands · core base classes ·
sidebar).** Verdict: the engine is buildable almost entirely as EXTENSIONS of certified
components — 6 existing files gain additive sections; new files = only what cannot exist
inside an existing one (migration · templates · tests · one command).

**Component reuse table:**

| Planned component | Existing implementation | Reuse | Extend | New code | Reason |
|---|---|---|---|---|---|
| Category enum | `FactoryExpense.Category` (§21 locked) | ✅ | — | ❌ | template.category uses the SAME choices object — zero duplicate enums |
| Amount rounding | `_shared.q_paisa` (THE expense rounding rule) | ✅ | — | ❌ | |
| Amount floor | `amount > 0` CheckConstraint pattern + form `min_value` | ✅ pattern | — | constraint rows only | mirrors factoryexpense_amount_positive |
| Management gate (services) | `_shared._ensure_management` | ✅ | — | ❌ | template lifecycle + generation gates |
| SA gate (amount change — the money-bearing config edit) | `void_expense`'s inline SA check pattern (`user_has_role(…{ROLE_SUPER_ADMIN})`) | ✅ pattern | — | ❌ | follows the existing lever idiom; no new helper |
| View gating | `_ManagementOnly` mixin (expense/views.py) | ✅ | — | ❌ | house pattern: view gates management, SERVICE enforces SA (the pay-basis/void precedent) — NO new mixin |
| FactoryExpense writing | `record_expense` | ✅ | — | ❌ | generation calls it row-by-row; the engine NEVER gains its own FactoryExpense writer |
| Duplicate salary detection | **M-3 inside `record_expense`** (`code='duplicate_salary'`) | ✅ | — | ❌ | generation CATCHES the existing refusal → skip-with-reason; zero second duplicate-detector |
| Monthly totals / reporting seam | `monthly_totals` | ✅ | — | ❌ | untouched; generated rows flow in as ordinary rows |
| Month parsing (?month=YYYY-MM) | `FactoryExpenseListView._month` | ✅ | ✅ promote to a module-level `_parse_month()` in expense/views.py, both views call it | ❌ | kills the one duplication the new trigger view would otherwise create; behavior identical (INERT 2-line change to the existing view) |
| Month-end clamp / period math | stdlib `calendar.monthrange` + the existing `f"{y:04d}-{m:02d}"` format (`month_value`) | ✅ | — | private resolver fn inside the service | no utils module; the resolver is the ONE new pure function (frequency seam) |
| Soft-state | `core.ActiveManager` + is_active (14-callsite pattern) | ✅ | — | ❌ | ExpenseTemplate gains `.active` |
| Model base | `core.TimeStampedModel` | ✅ | — | ❌ | all 3 tables |
| Audit table shape | `WorkerPayBasisAudit` (append-only, PROTECT, old→new, sole-writer) | ✅ pattern | — | 1 new model | different FK target/fields — pattern reuse, table necessarily new |
| Admin | `_MoneyReadOnlyAdmin` | ✅ | ✅ 3 subclass registrations | ❌ machinery | zero new admin base |
| Forms | `FactoryExpenseForm` thin-form idiom + `_worker_qs()` | ✅ | ✅ 2 thin forms beside it | ❌ clean() logic | rules stay in the service (house law); forms carry fields only |
| Transaction wrapper | `@transaction.atomic` (nested = savepoints) | ✅ | — | ❌ | no custom wrapper exists or is needed |
| Reference numbers | `next_reference` | — | — | ❌ | deliberately NOT used — templates need no reference series (avoid gratuitous reuse) |
| Management command | `reconcile_pay.py` shape (BaseCommand → service) | ✅ pattern | — | 1 new command | D4: wraps the SAME service function |
| Navigation | existing Payroll sidebar section + factory-expense pages | ✅ | ✅ links from the existing expense list header; sidebar row = owner Access Control action (MEE-D6) | ❌ parallel module | recurring screens live INSIDE the expense module (/expense/ urls, same views.py/templates dir) |
| UI templates | factory_expense_list/form.html = compose-from-canon references | ✅ canon | — | 2–3 new templates | new PAGES need new template files; they duplicate no component |

**Model necessity (owner's three questions):** existing models CANNOT hold this —
(i) extending FactoryExpense = altering an existing table (U14/contract-§10 breach) and
would fuse mutable CONFIG into immutable money HISTORY (append-only broken by
construction; a "template row" inside an expense table is a sentinel-row hack);
(ii) constraint-backed idempotency needs its own (template, period_key) uniqueness
domain — impossible to express on FactoryExpense without nullable-key hacks;
(iii) separate tables keep the ADR-0011 grep-proof trivial (no new columns on any money
table; the engine family is three clearly-bounded tables). Hence 3 new tables =
architecturally cleaner AND the only contract-legal option.

**Service-file ruling (owner's example):** NO `monthly_expense_service.py`. The engine
functions land INSIDE `expense_service.py` as a marked additive section — one
FactoryExpense-domain service, one purity-test scope, existing functions byte-untouched.
(~5 additive functions: `create_template` · `deactivate_template` ·
`change_template_amount` [SA, audited] · `generate_monthly_expenses(year, month, actor,
confirm=False)` [preview & confirm = ONE code path] · private `_period_key`/due resolver.)

**FINAL IMPLEMENTATION PLAN**

Files to MODIFY (all additive sections; existing code byte-untouched except the stated
INERT `_month` promotion):
1. `expense/models.py` — +3 models (§A.3). Why not existing: above.
2. `expense/services/expense_service.py` — +engine section (~5 functions). Why not new file: one domain, one writer family, one purity scope.
3. `expense/forms.py` — +2 thin forms. Why: new fields; zero duplicated validation (service enforces).
4. `expense/views.py` — +~4 views (template list · template form · amount-change · generate preview/confirm) + `_month` → `_parse_month` promotion (INERT). Why not new module: house structure = one expense views file; navigation extends existing pages.
5. `expense/urls.py` — +~4 routes under the existing /expense/ mount.
6. `expense/admin.py` — +3 `_MoneyReadOnlyAdmin` subclasses.

NEW files (only where a file cannot not-exist):
- `expense/migrations/0015_monthly_expense_engine.py` (the U14-approved DDL, §A.5)
- `expense/templates/expense/expense_template_list.html` · `expense_template_form.html` (+ generate-preview block/page — 2–3 files, compose-from-canon)
- `expense/management/commands/generate_monthly_expenses.py` (D4 command → same service fn)
- `expense/tests/test_expense_templates.py` · `test_expense_generation.py` (suite growth)

Files intentionally NOT created: `monthly_expense_service.py` · any utils/date-helpers
module · any new enum/constants module · any new permission mixin/decorator · any new
admin base · any new form-validation helper · any new app · any parallel navigation.

Duplicate code eliminated by this review: second category enum · second amount
validation · second duplicate-salary detector (M-3 stays THE rule) · second month parser
(promotion instead) · second audit utility · second management/SA guard · second
soft-state mechanism · second admin read-only base.

Simplifications: preview/confirm = one function, one code path · the frequency seam =
one private resolver, not a module · schema unchanged from §A.3 (this review found
nothing to add — only things NOT to build).

Final implementation sequence (on U14 approval): 0015 migration + models + constraint
tests → reverse proof on disposable copy → battery (= MEE-A close) → MEE-B service
section + census addendum → MEE-C surfaces → MEE-D money certification → MEE-E.

_⏸ STOPPED. Review complete; still zero code. The U14 ask stands: approve
`expense.0015_monthly_expense_engine` (§A.3/A.5) + this implementation plan._

### A.13 MEE-A IMPLEMENTATION — ✅ COMPLETE 2026-07-18 (U14 approval received: "U14 OWNER IMPLEMENTATION AUTHORIZATION… APPROVED"; 7 implementation principles LOCKED and honored)

**Wave-scope ruling applied:** this wave = the contract's MEE-A scope (migration + models
+ constraints + managers + admin + tests). The authorization's fuller artifact list
(forms · service extensions) executes at its contract-gated waves — service extensions =
MEE-B **behind the unapproved-yet Money-Write census addendum** (§16.4 stop law), forms =
MEE-C surfaces. Not a deviation: the gates ARE the approved design.

1. **Files modified (2, additive sections only):** `expense/models.py` (+3 models, the
   §A.3 DDL verbatim — incl. the locked responsibility banner; ActiveManager import) ·
   `expense/admin.py` (+3 `_MoneyReadOnlyAdmin` subclasses, inspection-only).
2. **New files (2):** `expense/migrations/0015_monthly_expense_engine.py` (makemigrations
   output matches the approved DDL 1:1 — 3 CreateModel + 10 constraints + 1 index; NO
   existing-table operation, no RunPython) · `expense/tests/test_expense_templates.py`
   (14 tests).
3. **No-duplication proof:** template.category binds `FactoryExpense.Category.choices`
   (grep: one enum) · only new choices class = `Frequency` (V1 monthly — the charter
   seam) · `FactoryExpense.objects.create` still exists in exactly TWO places
   (expense_service + the pre-existing R5 test fixture) — the engine added NO writer ·
   zero new service/view/form/util/mixin/admin-base files (git census: this wave's
   untracked = 0015 + the test file only).
4. **Reuse proof:** TimeStampedModel + ActiveManager (core) · §21 Category ·
   PayBasisAudit/RateCorrectionAudit audit shape · `_MoneyReadOnlyAdmin` · conditional-
   constraint house pattern (Django 5.0.1 `check=`) · tests create FactoryExpense
   fixtures THROUGH `record_expense` (the certified writer even in tests).
5. **Migration output:** `Applying expense.0015_monthly_expense_engine… OK` on the
   primary dev DB (additive; zero rows created — engine tables 0/0/0 live);
   `makemigrations --check` → "No changes detected" (models ⇄ migration exact).
6. **Reverse proof (disposable DB `inventory_mee_reverse_probe`, created+dropped,
   disclosed):** fresh migrate = 186 applied → schema dump → `migrate expense 0014` =
   "Unapplying expense.0015… OK", engine tables count 0 → forward again OK → **schema
   dump diff = byte-identical except pg_dump's random `\restrict` session nonces**.
7. **Battery: 1809/1809 — NEW BASELINE** (10-app S1 = 1065 [chain 1051 + 14 constraint
   tests] · patterns_ai 528 · devseed 138 · verification 78). Mid-battery incident,
   dispositioned in-wave (the P14 discipline, 2nd live catch — BOD-A precedent):
   SYNC-D4 INV-8 floor guards fired (graph stale vs 3 new models) → routine Phase-8
   rebuild (validator: ALL INVARIANTS PASS; new graph file-hash `b31ad2496fd6…`,
   builder-reported sha256 `96042d2757…`) → devseed 138/138 green + knowledge_sync
   **BLOCKER=0**, WARN 365 (baseline 361 + the 4 new campaign docs in the standing
   routed-venue residue classes — accepted queue unchanged in kind).
8. **Money safety verification:** ledger **170 / Σ ₹10,880.25 byte-identical** ·
   FactoryExpense **4 rows unchanged** · engine tables **0 rows on primary** · no new
   writer exists (grep proof above) · ADR-0011: zero production/settlement FKs in the
   new schema (§A.2 holds as built).
9. **U6 docs same-session:** expense README + GUIDE (engine sections) · this log ·
   status file · memory. Git: HEAD 49404001 · 2 stashes · no commits (0015 sits
   uncommitted in the tree per U2, like all campaign work).

_MEE-A closed. Next: **MEE-B** (generation + template-lifecycle service functions inside
`expense_service`, U8-hostile main-thread, **the Money-Write census addendum presented
for owner approval BEFORE the functions land**) — owner-gated._

## MEE-B — Generation service + census addendum — ⏸ PRE-IMPLEMENTATION MONEY-WRITE REVIEW presented 2026-07-18 (owner-ordered; ZERO code)

### B.0 The money-write safety package

#### B.0.1 Money-Write Census Addendum (DRAFT — becomes the dated R5 Part-2 addendum verbatim on owner approval)

> **ADDENDUM 1 to the R5 Part-2 payment-path census (2026-07-18, Campaign Phase 16
> MEE-B, owner-approved: _pending_).** The Monthly Expense Engine adds FIVE
> expense-service-family functions and THREE engine tables. The census invariant is
> UNCHANGED: every money write flows through its single designated service.
>
> | Table | Writes added | Writing function(s) — ALL in `expense/services/expense_service.py` | Gate |
> |---|---|---|---|
> | `FactoryExpense` | **NONE — no new writer.** Generation CALLS the existing `record_expense` (sole writer unchanged); generated rows are ordinary rows, voidable by the existing SA lever | `generate_monthly_expenses` / `regenerate_period` → `record_expense` | management / SA |
> | `ExpenseTemplate` | INSERT (create) · UPDATE `is_active` only (deactivate — soft-state) · UPDATE `amount` only (audited change) | `create_expense_template` · `deactivate_expense_template` · `change_template_amount` | SA-only (MEE-D6: templates encode salary amounts) |
> | `ExpenseTemplateAmountAudit` | INSERT only — append-only forever | `change_template_amount` (atomically WITH the amount UPDATE) | SA-only |
> | `ExpenseGenerationRecord` | INSERT (generate/regenerate) · UPDATE `superseded_at` only (regenerate — the voided_at-style soft-state flip) · never DELETE | `generate_monthly_expenses` (confirm=True) · `regenerate_period` | management / SA |
>
> No other field of any engine table is writable by any function (V1 has NO edit path
> for label/notes/dates/worker/category — a wrong template is deactivated + recreated).
> UI/forms/commands/admin write NOTHING (purity-pinned, §B.0.8). Ledger, settlement,
> costing, payroll, advances: structurally unreachable (no import, no FK, no read).

#### B.0.2 Write-path diagrams (all five functions)

```
create_expense_template                    deactivate_expense_template
  inputs (label…worker, actor)               inputs (template, actor)
  ↓ SA gate · §21 category · P-1 pair        ↓ SA gate · already-inactive → no-op
  ↓ q_paisa(amount) · window sanity          ↓ [atomic] UPDATE is_active=False
  ↓ [atomic] INSERT ExpenseTemplate          ↓ commit  (0 money rows touched)
  ↓ commit  (0 money rows touched)

change_template_amount
  inputs (template, new_amount, reason, actor)
  ↓ SA gate · reason≠'' · q_paisa · new≠old · template active
  ↓ [atomic]  UPDATE ExpenseTemplate.amount
  ↓           INSERT ExpenseTemplateAmountAudit(old→new, who, reason)
  ↓ commit — the pair is indivisible (an unaudited change cannot exist)

generate_monthly_expenses(year, month, actor, confirm)
  inputs → management gate → resolve due templates (active ∧ window covers period
           ∧ no CURRENT coverage ∧ (salary ⇒ worker.is_active — the Q13 auto-stop))
  confirm=False → RETURN preview rows + skips (PURE READ, zero writes)
  confirm=True →
  ↓ [outer atomic — the period]
  │   per template: [inner atomic — savepoint]
  │     ↓ record_expense(category, template.amount, period_date, actor,
  │                      notes, worker)            ← THE existing certified writer
  │     ↓ INSERT ExpenseGenerationRecord(template, period_key, expense, actor)
  │   ValidationError code='duplicate_salary' (M-3) → savepoint rollback → SKIP recorded
  │   any OTHER exception → re-raise → OUTER ROLLBACK (nothing of the period lands)
  ↓ commit → receipt {created:[…], skipped:[(template, reason)…]}

regenerate_period(template, year, month, reason, actor)
  inputs → SA gate · reason≠'' · CURRENT coverage exists ∧ its expense IS VOIDED
           (an unvoided expense refuses — void is the only door, the existing lever)
  ↓ [atomic]  UPDATE old coverage superseded_at=now
  ↓           record_expense(… template.amount as of NOW …)   ← current amount, stated policy
  ↓           INSERT new ExpenseGenerationRecord(supersedes=old, reason)
  ↓ commit — chain intact or nothing
```

#### B.0.3 Failure scenarios → rollback

| Failure | Result |
|---|---|
| record_expense raises mid-period (any non-M-3 error) | outer atomic rolls back — ZERO expenses, ZERO coverage from that run; ledger/FactoryExpense counts byte-identical; re-run converges |
| coverage INSERT fails after record_expense succeeded (e.g. concurrent duplicate) | same transaction ⇒ the just-created FactoryExpense row rolls back WITH it — an uncovered generated row cannot exist |
| audit INSERT fails in change_template_amount | amount UPDATE rolls back with it — an unaudited change cannot exist |
| crash mid-regenerate | supersession UPDATE + new rows share one atomic — the chain lands whole or not at all |
| concurrent double-confirm (two managers) | first commits; second hits the partial-unique on INSERT → IntegrityError → its OUTER atomic rolls back fully → clean "period already generated" error; the constraint = the serialization point, no advisory lock needed |

#### B.0.4 Idempotency proof (state walk)

1. **First run** (Jul, template ₹1500): due → FE#1 ₹1500 + coverage(tpl, "2026-07", FE#1) CURRENT.
2. **Second run:** resolver sees CURRENT coverage → skip "already generated" → **0 writes** (count-asserted in tests).
3. **Void:** SA voids FE#1 via the EXISTING `void_expense` lever (unchanged behavior). Coverage stays CURRENT → generate STILL skips ("covered; expense voided — regenerate explicitly"). A void never silently re-opens a period.
4. **Regenerate:** allowed ONLY because FE#1 is voided → old coverage superseded (timestamp) → FE#2 at the template's current amount + new CURRENT coverage(supersedes=old, reason).
5. **Supersede chain:** old row keeps FE#1 + history; the DB refuses a reason-less or duplicate-current chain (constraints live + tested since MEE-A).
6. **Any later run:** CURRENT coverage exists → skip. Converged at every step.

#### B.0.5 Manual-salary collision (M-3, exactly)

Worker W has a MANUAL non-voided salary row for 2026-07. Salary template for W, generate
Jul: `record_expense` itself raises `ValidationError(code='duplicate_salary')` (the
EXISTING M-3 guard — the engine adds no second detector and NEVER passes
`confirmed_duplicate`) → inner savepoint rolls back → skip recorded: *"manual salary
exists for 2026-07 — void it if the template should win"* → the rest of the period
proceeds. Preview shows the same skip BEFORE any write. If the template should win: SA
voids the manual row (existing lever) → coverage never existed for this template →
plain generate now succeeds (no regenerate needed). M-3's protection is symmetric:
manual-first blocks generated; generated-first blocks manual (the existing
warn-and-confirm fires on the manual attempt, naming the generated row).

#### B.0.6 Amount-change timeline (historical correctness)

| Time | Action | Template.amount | Money history |
|---|---|---|---|
| Jul 1 | generate Jul | 1500 | FE#1 ₹1500 (frozen forever) |
| Aug 5 | change_template_amount → 1800, reason "rent revised" | 1800 | audit row 1500→1800 (append-only) |
| Aug 5 | generate Aug | 1800 | FE#2 ₹1800 |
| — | Jul re-checked | — | FE#1 STILL ₹1500; coverage Jul→FE#1 untouched — covered periods never re-price |
| Sep 1 | SA voids FE#1 + regenerate Jul (reason) | 1800 | FE#1 voided (visible, struck) · FE#3 ₹1800 · Jul chain superseded→current |

**Stated policy (owner visibility):** regeneration prices at the template's CURRENT
amount — the usual reason to regenerate IS a corrected amount; the old figure survives
on the voided row + the audit trail.

#### B.0.7 Coverage lifecycle

`(no row)=PENDING → CURRENT (expense active) → CURRENT/expense-voided (generation still
skips; regenerate = the only door) → SUPERSEDED (terminal; new CURRENT row chains via
supersedes+reason)`. Rows never deleted; `superseded_at` = the single sanctioned state
flip (mirrors `voided_at`).

#### B.0.8 Purity proof plan

Already structural: admin = `_MoneyReadOnlyAdmin` (add/change/delete=False, landed
MEE-A). Pinned at MEE-B with the writers: a static purity test asserting ZERO ORM-write
tokens on FactoryExpense + the 3 engine tables anywhere in `expense/views.py`,
`expense/forms.py`, `expense/admin.py`, `expense/management/` — writes may exist ONLY
inside `expense/services/` (the same law the R5 census verified codebase-wide). The
command wraps `generate_monthly_expenses` (parse → call → print receipt); views delegate
+ redirect (`_ManagementOnly` + messages, house pattern); forms carry fields only.

#### B.0.9 Updated R5 Money-Write census (post-MEE-B state)

| Money/guarded table | Sole writer |
|---|---|
| WorkerLedgerEntry | `ledger_service` |
| StageWorkAssignment | `allocation_service` (era-A lever) + `adda_settlement_service` (era-B) |
| WorkerAdvance | `advance_service` |
| PayrollSettlement(+Item) | `settlement_service` + adda_settlement recovery lines |
| AddaSettlement(+Item) | `adda_settlement_service` |
| WorkerProfile.pay_basis + WorkerPayBasisAudit | `payroll_service.set_pay_basis` |
| AddaStageRoleRate / RateCorrectionAudit | `stage_rate_service` |
| FactoryExpense | `expense_service` (`record_expense`/`void_expense`) — **unchanged; generation is a CALLER, not a writer** |
| **ExpenseTemplate** (NEW) | `expense_service` (`create_expense_template` · `deactivate_expense_template` · `change_template_amount`) |
| **ExpenseTemplateAmountAudit** (NEW) | `expense_service` (`change_template_amount`) — append-only |
| **ExpenseGenerationRecord** (NEW) | `expense_service` (`generate_monthly_expenses` · `regenerate_period`) |

#### B.0.10 Implementation checklist (MEE-B, on approval)

1. Record §B.0.1 (dated + owner approval quoted) into R5_HOSTILE_REVIEW Part 2.
2. The 5 functions as ONE marked additive section in `expense_service.py` (existing
   functions byte-untouched) + the private `_period_key`/due resolver.
3. Tests: idempotency double-run (0-write count proof) · void→skip→regenerate chain ·
   M-3 skip both directions · Q13 worker-inactive auto-stop · outer-rollback on injected
   failure · concurrent-duplicate IntegrityError path · the B.0.6 timeline as a test ·
   static purity pin · ADR-0011 proof set v1 (ledger recount + no-new-FK grep +
   costing-page byte-compare on a seeded world).
4. Rollback-wrapped shell probe on a scratch world, then a landed probe round-tripped
   via the void lever (U13 disclosure).
5. Battery (1809 + growth) + sync diff + ledger/golden recounts + log/status/memory/U6.

_⏸ STOPPED — zero code. Awaiting owner approval of: (a) the census addendum §B.0.1,
(b) the write-path designs §B.0.2, incl. the two stated policies — regeneration prices
at the CURRENT template amount; M-3/duplicate skips continue the period while any real
failure rolls the whole period back._

### B.1 MEE-B IMPLEMENTATION — ✅ COMPLETE 2026-07-18 (owner approval: "MEE-B IMPLEMENTATION AUTHORIZATION — The architecture review is approved" + both policies ratified; U8-hostile, main-thread)

1. **Census ADDENDUM 1 RECORDED first** into R5_HOSTILE_REVIEW Part 2 (dated, approval
   quoted, full writer table + both owner policies of record).
2. **Changed files:** `expense/services/expense_service.py` (+the engine section: the 5
   functions + `_ensure_super_admin` [the void_expense idiom, one home] +
   `_month_bounds`/`_resolve_month` [THE single resolution path — preview and confirm
   read the same function; a future frequency = a branch here]; **every function carries
   the owner-mandated RESPONSIBILITY banner** [owns / writes / never]; existing functions
   byte-untouched — pure EOF append, and all 180 pre-engine expense pins incl. R5/MGT-C
   pass unchanged) · `expense/tests/test_expense_generation.py` (NEW, 19 tests) ·
   U6 docs (expense README + GUIDE). Nothing else — no views/forms/urls/admin/commands
   this wave (MEE-C surfaces).
3. **Reuse proof:** `record_expense` = the only money door (called, never bypassed;
   grep: `FactoryExpense.objects.create` still exactly 2 pre-existing sites) ·
   `void_expense` SA idiom · `q_paisa`-equivalent validation via record_expense ·
   M-3 = THE duplicate detector (engine catches `duplicate_salary`, never passes
   `confirmed_duplicate`) · stdlib `calendar.monthrange` (no util module) ·
   `select_for_update` row-lock idiom (void_expense pattern) on deactivate/change/
   regenerate. **Duplicate-code proof:** zero new validation/permission/date/audit
   helpers; one new 4-line SA gate helper shared by the three SA levers (single home,
   replaces three inline copies).
4. **Tests (19):** SA gates ×3 · create validations (P-1 both ways · window · inactive
   worker · friendly partial-unique) · deactivate idempotent · amount-change audit
   indivisible + reason + no-op refused · preview pure-read (count-asserted) ·
   first-run/second-run convergence (0 writes) · month-end clamp (Jan-31 anchor →
   Feb 28) + expiry skip · Q13 auto-stop · **M-3 both directions** (manual-first ⇒ skip
   + period continues; generated-first ⇒ manual blocked with `duplicate_salary`) ·
   **injected mid-period failure ⇒ whole-period rollback (counts byte-identical)** ·
   **concurrent duplicate ⇒ clean ValidationError + full rollback (stale-resolution
   mock)** · void-doesn't-free-the-period · regenerate guards (unvoided refused ·
   reason · SA) · **the B.0.6 amount timeline as a test** (Jul 1500 frozen · Aug 1800 ·
   regenerated Jul at CURRENT 1800 · chain + visibility) · **purity pin** (static: zero
   ORM-write tokens on the 4 guarded models in views/forms/admin/management) ·
   **ADR-0011 pins** (engine FK targets ⊆ {User, FactoryExpense, self} · generation
   leaves the ledger count+Σ untouched).
5. **Scratch probes (scratch_2; 0015 migrated there — routine additive):**
   **Rollback-wrapped:** full create+preview+confirm flow ran (1 row @ ₹111) → rollback →
   counts BYTE-IDENTICAL (fe 1 · cov 0 · tpl 0 · ledger 90/₹3,128.25). **Landed chain
   (U13 disclosure):** DEV-MEEB template ₹222 → generated (2026-07-01) → 2nd run 0 →
   void → generate still skips → regenerate (supersedes ✓, ₹222 current amount) —
   landed artifacts on scratch_2: 1 template, 2 FE rows (one voided), 2 coverage rows
   (one superseded). **Ledger 90/₹3,128.25 identical through everything** — the live
   ADR-0011 proof.
6. **Money-write census verification:** addendum recorded; purity pin green; sole-writer
   greps clean; UI/command layers don't exist yet (nothing to leak).
7. **Ledger verification (PRIMARY):** **170 / Σ ₹10,880.25 EXACT** · FactoryExpense 4 ·
   engine tables 0 rows — the primary was never touched by this wave.
8. **Battery: 1828/1828 — NEW BASELINE** (10-app S1 = 1084 [chain 1065 + 19] ·
   patterns_ai 528 · devseed 138 · verification 78). knowledge_sync --diff: BLOCKER=0,
   body_hash identical to the MEE-A close (0 new findings).

_MEE-B closed. Next: **MEE-C** (management surfaces: template admin + preview→confirm
trigger + review into the existing expense list; certified gating; mobile evidence) —
owner-gated._

## MEE-C — Management surfaces — ✅ COMPLETE 2026-07-18 (owner-authorized; surfaces strictly)

1. **Changed files:** `expense/forms.py` (+`ExpenseTemplateForm`, fields only) ·
   `expense/views.py` (+3 thin views + the approved `_parse_month` promotion — INERT,
   FactoryExpenseListView delegates to it) · `expense/urls.py` (+3 routes, same module) ·
   `accounts/services/permission_service.py` (+'Recurring Expenses' MenuItem, management
   predicate, Payroll section) · `production/tests/test_a360_overview.py` (conscious pin
   76→**78**, dated: a management-VISIBLE MenuItem costs its predicate's user_has_role
   extra-roles query AND the SidebarItemRule managed-check — the BOD item cost +1 only
   because its SA-only predicate hides it from a manager before the rule check). **New:**
   3 page templates (factory-expense canon: hero copper · month-nav · totals/table ·
   data-label mobile stack · details-box actions · form-shell + sticky bar + P-1/L-3
   sugar shared with Record Expense) + `tests/test_expense_surfaces.py` (8).
2. **Thin-view proof:** every POST = parse → ONE MEE-B service call → message +
   redirect (the factory-expense-list void pattern); GET preview = the SAME
   `generate_monthly_expenses(confirm=False)` the confirm uses — no second status/
   preview logic anywhere; the MEE-B static purity pin (zero ORM-write tokens on the 4
   guarded models in views/forms/admin/management) passes over the NEW code.
3. **Write-path proof by outcome:** page-driven create carries `created_by=actor`;
   page-driven amount change produces the indivisible audit row; manager attempting an
   SA lever via POST = refused by the SERVICE (view reachable, write refused — the house
   double posture); regenerate via the page only works on a voided-covered row.
4. **Review = the existing expense list** (generated rows land there with their
   template-stamped notes — no parallel review page, test-asserted).
5. **Screens (scratch_2 via a temporary :8004 server, dev cast, then stopped):** 5
   screens × 3 widths = 15 headless-chrome captures in the session scratchpad
   (`mee_{tpl_list,tpl_form,gen_preview,gen_covered,review}_{m,t,d}.png`): mobile = the
   certified data-label card stack, tablet/desktop = table + form-shell canon;
   FancySelect + fancy-date auto-upgrades live; worker field hidden for non-salary;
   confirm bar sticky; no horizontal overflow at 360.
6. **Battery: 1836/1836 — NEW BASELINE** (10-app S1 = 1092 [chain 1084 + 8] ·
   patterns_ai 528 · devseed 138 · verification 78). In-wave dispositions: the a360 pin
   (above) + the P14 guard's 3rd live catch (INV-8 floors on the 3 new urls → routine
   graph rebuild, validator ALL PASS, file hash `42f554fce59c`; sync back to
   **BLOCKER=0 / WARN=365, body_hash identical to the MEE-B baseline**). S2/S4 ran green
   in-close before the pin/graph fixes; those fixes touch only S1/S3 domains (both
   re-run green) — disclosed.
7. **Primary EXACT:** ledger 170/Σ₹10,880.25 · FactoryExpense 4 · engine tables 0.

_MEE-C closed. Next: **MEE-D** (money certification wave) — owner-gated._

## MEE-D — Money certification wave — ✅ CERTIFIED 2026-07-18 (owner-authorized "exactly as planned" + the added regression-certification section)

### D.1 Do-no-harm proof set (live, scratch_2 — main-thread)

- **Costing-page byte-compare (ADR-0011 wall):** `/production/costing/` captured
  CSRF-normalized (double-GET first PROVEN deterministic under normalization; raw bytes
  differ only by the rotating csrfmiddlewaretoken — method disclosed) →
  **BYTE-IDENTICAL through fresh generation (2026-10, ₹222 landed) AND through the void
  round-trip AND through a live regeneration.** Factory expenses never touch per-Adda
  cost, proven at the rendered page.
- **Ledger round-trip:** **90 rows / Σ ₹3,128.25 IDENTICAL** before → after generation →
  after void → after regenerate+cleanup. The engine cannot reach the ledger.
- **Regeneration policy live re-proof:** voided-covered 2026-10 → `regenerate_period` →
  supersession chain ✓, CURRENT template amount ✓ (owner policy), then probe cleanup via
  the void lever (U13: probe rows on scratch_2 disclosed — voided, visible, append-only).
- **Golden journeys:** `seed_factory` converged (created=0, skipped=234, assertions
  PASS) → **`verify_factory` = 19/19 PASS** (₹801.00 / ₹344.25 / ₹633.00 byte-asserted
  from certified sources with the engine tables present and populated on the same DB).

### D.2 Permissions certification (test-pinned, fresh DB)

New `MeeDFullIdentityMatrixTests` (+3): **every identity × every engine surface**
(anon 302 · worker/accountant/listing 302-or-403 · manager 200 · SA 200) ·
**POST negative controls** — anon/worker/accountant/listing firing confirm-generation
and deactivate POSTs write NOTHING (FactoryExpense 0 · coverage 0 · template untouched) ·
**MGT-C lever re-proof with the engine present** — manager void via the page refused,
SA + reason succeeds (create=management / void=SA unchanged). AJAX forks: N/A — the
engine surfaces expose no AJAX endpoints (full-page POSTs only; recorded).

### D.3 Idempotency + voided-period policy (standing pins re-run)

The MEE-B pins re-ran green in this wave's batteries: preview pure-read · double-run
0-write convergence · void-does-NOT-free-the-period · regenerate = SA + reason + only on
a voided cover + supersession chain · M-3 both directions · Q13 auto-stop · whole-period
rollback on injected failure · concurrency serialized by the partial unique.

### D.4 REGRESSION CERTIFICATION (owner-added section — replay of every MEE-A/B/C business scenario, immediately before the certificate)

**Named replay battery, fresh DB: `test_expense_templates` (14 — every MEE-A constraint/
soft-state/PROTECT scenario) + `test_expense_generation` (19 — every MEE-B money/
generation/policy scenario) + `test_expense_surfaces` (11 — every MEE-C surface/identity/
flow scenario) = 44/44 PASS.** Plus the live business-scenario chain re-proven on
scratch_2 this wave (D.1): template → generate → idempotent re-run → void → skip →
regenerate-at-current-amount → cleanup, with ledger + costing bytes frozen throughout.

### D.5 Battery + sync + primary

**1839/1839 — NEW BASELINE** (10-app S1 = 1095 [chain 1092 + 3 matrix] · patterns_ai
528 · devseed 138 · verification 78). In-wave disposition: P14 guard's 4th live catch
(doc floor 930→931 — the Phase-18A program doc) → routine graph rebuild (validator ALL
PASS; file hash `5fc3214ed824`) → guards green; sync **BLOCKER=0 / WARN=367** (365 + the
new 18A doc's standing residue rows). **PRIMARY EXACT: ledger 170/Σ₹10,880.25 ·
FactoryExpense 4 · engine tables 0 · users 48.**

### D.6 MEE-D CERTIFICATE

**The Monthly Expense Engine is MONEY-CERTIFIED:** single-writer preserved (census
ADDENDUM 1; record_expense = the only FactoryExpense door) · ADR-0011 walls proven at
schema, service, ledger, and RENDERED-PAGE levels · goldens byte-identical via the
verification instrument · append-only + idempotency + supersession constraint-backed and
replayed · permissions certified all-identity with negative controls · MGT-C levers
unchanged · **every MEE-A/B/C business scenario replayed green immediately before this
certificate (D.4).** Open by design: `seed_feature monthly-expense` dataset amendment +
BOD-widget handoff + charter-coverage census = MEE-E scope.

_MEE-D closed. Next: **MEE-E** (certification + handoffs — the phase-closing wave) —
owner-gated._

## MEE-E — Certification + handoffs — ✅ COMPLETE 2026-07-18 → 🏁 PHASE 16 CLOSED (the permanent closure package, owner-ordered)

### E.1 Closure implementation (the two owed deliverables, landed)

- **The MEE-D4 management command** (charter-census catch — approved at D4, not yet
  built): `expense/management/commands/generate_monthly_expenses.py` — a THIN wrapper
  over THE same service function (preview default, `--confirm` writes, `--actor` =
  management email; service enforces every gate; purity pin covers it). +2 tests
  (preview-writes-nothing/confirm-creates · bad-month + non-management refusals).
  **Live on scratch_2:** preview correctly reports 3 skips incl. the voided-example
  regenerate hint.
- **`seed_feature feature-monthly-expense`** (dataset-spec **dated amendment A3**;
  registry+CONTENT+spec three-surface agreement): DEV-MEE rent + salary templates via
  the ADDENDUM-1 writers → 2026-07 generated → ONE voided example via the existing
  lever; converging. +1 registry test. **Live scratch_2: created=8 PASS → second run
  created=0 (pure convergence) → `verify_feature` 7/7 PASS.**

### E.2 Handoffs

- **P13 (verification) candidates — notes only, adopted per P13's own registry law:**
  (a) coverage-uniqueness holds ((template, period_key) partial unique has no violators);
  (b) generated rows are factory-level (no-Adda-linkage predicate over the engine
  tables); (c) every non-superseded coverage row points at an existing FactoryExpense.
- **P19 (deployment):** migrations now include `expense.0015` (additive-new-tables only;
  reverse = migrate expense 0014, proven on a disposable copy); NO flags; NO in-repo
  scheduler — external cron MAY wrap `manage.py generate_monthly_expenses <YYYY-MM>
  --actor <email> --confirm` as a post-deploy ops decision (documented, not wired).
- **BOD widgets (MEE-D8, owner-ruled):** engine KPIs (this-month recurring total ·
  pending-generation count) enter the BOD ONLY via the PHASE_15 Metric Resolution
  Ladder + Widget Registry in a later owner-gated session. Nothing built.
- **Phase 18A (RCP):** the engine surfaces join RC-6 (expense app-by-app) + RC-9
  (financial certification) scope when that program executes.

### E.3 Charter-coverage census (every chartered item, counted: 14 built · 6 deferred · 0 declined)

| Chartered item | Status |
|---|---|
| Template-driven recurring expenses (never re-type) | ✅ built |
| Generated rows = ordinary FactoryExpense via `record_expense` | ✅ built (census ADDENDUM 1) |
| Monthly frequency V1 | ✅ built |
| Frequency-general schema (no redesign for future cadences) | ✅ built (enum + period_key) |
| Fixed template amounts; `User.salary` stays informational | ✅ built (prefill sugar only) |
| Stable identity + traceable amount changes; covered months never re-price | ✅ built (audit pair; timeline test) |
| Preview → confirm; idempotent; constraint-backed | ✅ built |
| M-3 skip-and-continue policy | ✅ built (both directions pinned) |
| Void → regenerate at CURRENT amount, supersession-chained | ✅ built |
| Q13 worker-inactive auto-stop; MEE never does FnF math | ✅ built |
| Month-end clamping (31st/Feb) | ✅ built |
| Management trigger UI + SA template admin + review in the existing list | ✅ built |
| Management command for external cron | ✅ built (E.1) |
| Dataset scenario | ✅ built (A3) |
| Non-monthly frequencies (daily…yearly, custom) | ⏸ deferred (owner; PDD change-control per addition) |
| One-time + variable amounts | ⏸ deferred (owner) |
| Supplier/warehouse/raw-material linkage | ⏸ deferred (owner boundaries; RM-V2 vision) |
| FY/fiscal-quarter definitions + report pages | ⏸ deferred (with their frequencies) |
| Persisted skip-ledger | ⏸ deferred (skips recomputable; owner option) |
| BOD widgets | ⏸ deferred (E.2 handoff) |

### E.4 Executive Summary (owner addition 1)

Phase 16 gave the ERP its permanent recurring-expense engine. The owner defines a
template once (rent, a worker's monthly salary, any §21 cost); each month, a preview
shows exactly what will be created and why anything is skipped; one confirm turns due
templates into ordinary FactoryExpense rows through the SAME certified writer that
manual entry uses. Idempotency is a database constraint, not a convention; every amount
change is audited; a voided month can be regenerated only explicitly, with a reason, at
the current amount, on an append-only supersession chain. Salaries stop generating
automatically when a worker leaves. The money architecture is untouched: no new
FactoryExpense writer, no ledger/settlement/costing contact (proven at the rendered
page), goldens byte-identical. Built in five gated waves (charter → U14 schema →
service → surfaces → money certification) with the first live use of the U14 migration
gate and the first sanctioned Money-Write census addendum.

### E.5 Deferred Features Register (owner addition 2)

The six ⏸ rows of §E.3, verbatim scope of record, all owner-ruled — each re-enters ONLY
via PDD change-control (frequencies explicitly so, per register entry 7). No deferred
item blocks Phase 17, 18A, or deployment.

### E.6 Future Extension Points (owner addition 3)

- **New frequency** = one `Frequency` enum value + one `_resolve_*` branch + a PDD
  register entry — coverage table/constraints/UI shells unchanged (`period_key` is
  frequency-agnostic by design).
- **FY/quarter semantics** land inside the same resolver seam when quarterly/yearly
  arrive.
- **Reports** (upcoming/missed/overdue/summaries) = pure reads over
  templates+coverage+`monthly_totals` — no schema needed.
- **BOD tiles** = the PHASE_15 ladder (L1: engine services already expose the numbers).
- **Persisted run-ledger** = an additive audit table beside AmountAudit if ever wanted.
- **Effective-dated amounts** = AmountAudit grows into scheduled versions by dated
  amendment (nothing built blocks it).

### E.7 Final Architecture Reuse Report (owner addition 4)

Locked principles held through all five waves: ZERO duplicated logic — one category enum
(FactoryExpense.Category reused) · one duplicate-salary detector (M-3, reused) · one
month parser (`_parse_month`, promoted not copied) · one preview/confirm path
(`_resolve_month`) · one SA-gate idiom + one management gate (reused) · one currency
renderer · audit tables on the house pattern · admin on `_MoneyReadOnlyAdmin` · forms
field-only · views parse→ONE-service-call→redirect · command wraps the same function.
New files = only what cannot not-exist (1 migration · 3 page templates · 1 command ·
4 test files). Existing service functions byte-untouched (EOF-append, 180 pre-engine
pins green throughout). Files intentionally NOT created: monthly_expense_service.py,
util/date/enum/permission/admin-base modules — all zero.

### E.8 PHASE 16 COMPLETION CERTIFICATE (owner addition 5)

| Dimension | Status |
|---|---|
| **Architecture** | CERTIFIED — 3 additive tables (config/orchestration/audit, responsibilities owner-LOCKED), 5 service functions with responsibility banners, thin surfaces, D4 command; zero duplication (E.7); frequency-general by schema |
| **Implementation** | COMPLETE — every chartered V1 item built (E.3: 14/14 buildable items; 6 owner-deferred; 0 declined); U14 exercised for real (per-migration approval, reverse proven) |
| **Money certification** | CERTIFIED (MEE-D, §D.6) — single-writer preserved (census ADDENDUM 1); ADR-0011 proven at schema/service/ledger/rendered-page; goldens 801/344.25/633 byte-verified via verify_factory with the engine present; ledger frozen through generate/void/regenerate live |
| **Regression certification** | CERTIFIED (owner-added §D.4) — all 44 MEE-A/B/C business scenarios replayed 44/44 immediately before the MEE-D certificate; all standing pins green at every wave |
| **Documentation** | COMPLETE — log (charter→census→waves→certificates) · PDD register entry 7 · R5 census ADDENDUM 1 · dataset amendment A3 · expense README/GUIDE · Appendix A filled · index rows; knowledge_sync BLOCKER=0 at close (WARN residue = the standing accepted classes) |
| **Battery** | **1842/1842 — TERMINAL PHASE-16 BASELINE** (10-app 1097 [chain: 1051 entry +14 A +19 B +8 C +3 D +2 E ✓] · patterns_ai 528 · devseed 139 [+1 A3 world] · verification 78); sequential fresh-DB; goldens inside |
| **Known deferrals** | The §E.5 register — all owner-ruled, none blocking |
| **Phase-17 readiness** | READY — gate satisfied (Phase 16 closed); schema left P17 clean (no material columns; `monthly_totals` untouched — its read seam intact; the RMX-0 compat observations from the RM review stand recorded) |

**VERDICT: PHASE 16 — MONTHLY EXPENSE ENGINE — CLOSED AND CERTIFIED.**

_Primary EXACT at close: ledger 170/Σ₹10,880.25 · FactoryExpense 4 · engine tables 0 ·
users 48. Git 49404001 · 2 stashes · NO commits (U2). Next: Phase 17 (RMX-0) — owner-gated;
then 18 → 18A (RCP) → 19–22 per the frozen roadmap._

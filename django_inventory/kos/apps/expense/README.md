---
id: app-expense
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "I'm about to work in the expense app — what does it own, where do requests enter, and which files matter?"
related: [feature-settlement, feature-ledger, feature-payroll, feature-advances]
---

# expense — the complete app map

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *yahan se app ke andar
> koodo: [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*

## Mental Model — read this before anything

> **A bank ledger.** Money never disappears. Corrections are NEW entries,
> never erasures. Balances are COMPUTED, never stored. History is
> preserved forever. Every design choice in this app follows naturally from
> those four sentences — when confused, return here. *(Bank ki kitaab:
> paisa gayab nahi hota, galti nayi entry hai, balance gina jaata hai.)*

## Common Misconceptions (save yourself weeks)

- **"Settlement creates money."** Wrong. Work created the CLAIM; settlement
  converts verified claims into LEDGER truth; payroll converts ledger truth
  into CASH truth. Settlement only starts the accounting chain.
- **"The balance is stored somewhere."** No column anywhere holds it —
  every balance is `SUM(credits) − SUM(debits)` computed live.
- **"Advances reduce earnings."** Never automatically — two pockets; only
  an owner-chosen recovery at settlement moves between them.
- **"Frozen totals on a settlement are live data."** They're write-once
  AUDIT snapshots (§11.9.4) — reconciling against them as truth is a bug.
- **"I can fix a wrong amount with an UPDATE."** Append-only: the fix IS a
  reversal row. An UPDATE forges history.

## Real Engineering Questions (how seniors enter this app)

**PM: "Can we let managers edit a settled amount?"**
Think: which invariant breaks? (append-only + frozen items) → which armor
fires? (`set_verified_quantity` refuses naming the ADST; reopen armor) →
the legal path = reverse & supersede → which tests pin it?
(`test_v2_3_guards`, goldens) → answer: "no edit — reverse-supersede flow
exists, here's the URL." *That chain IS the job.*

**PM: "Worker says balance is short ₹200."**
→ [money-looks-wrong](../../debugging/money-looks-wrong.md) First Five
Minutes: recompute, breakdown, name the ladder rung — before opening code.

**PM: "Can advances auto-deduct monthly?"**
→ which principle? (owner-chosen recovery, two pockets) → which refusal
teaches it? (`record_advance` monthly-refusal) → answer shape: policy
change = owner decision + new audited verb, not a cron.

## Reading Strategy

- **Beginner:** Mental Model → [urls.md](urls.md) §1 + §17 (the two
  simplest, each explains WHY simple) → [worker-gets-paid](../../flows/worker-gets-paid.md).
- **Intermediate:** Start Here table → urls.md §4, §8, §13 → [views.md](views.md) → [models.md](models.md).
- **Senior:** [services.md](services.md) sole-writer table → urls.md §13's
  lock canon → Change Impact + Engineering Checklist → the chokepoint doc.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Add a new endpoint | [urls.md](urls.md) (pick the lane) + the checklist in [views.md](views.md) §rules |
| Modify business/money logic | [services.md](services.md) → the owning service + its add-a-verb checklist |
| Change database schema | [models.md](models.md) → who writes it + [migrations](../../concepts/django/migrations.md) staging |
| Fix permissions / a 403 | [views.md](views.md) §gate-mixins + [access playbook](../../debugging/access-denied-or-invisible.md) |
| Understand the request flow | Request Journey on the URL's row in [urls.md](urls.md) → then the feature page |
| Debug a wrong number | [money-looks-wrong](../../debugging/money-looks-wrong.md) — First Five Minutes |
| Add tests | [testing-strategy](../../concepts/testing/testing-strategy.md) — the four-pin template for money changes |
| Add an export (CSV/XLSX/PDF) | copy the tracked-export pattern → [inventory §§17–19](../inventory/urls.md) (`_BaseExportTriggerView`: subclass, never fork) |

## Why a SEPARATE app (the senior question)

Money got its own app to **isolate the highest-risk domain behind the
smallest surface**: one app = one write-site census (CI gates), one
import-linter boundary, one place hostile reviews concentrate. Inside
production it would share migrations, tests, and reviewers with the
highest-CHURN domain — risk and churn must not cohabit. The two-truths
principle ([two-truths](../../concepts/architecture/two-truths.md)) made
the cut line obvious: this app is the financial-truth half, whole and
alone. Future evolution it enables: money UI can be rebuilt, or the whole
app lifted to its own service, without touching production code — the
service layer is the pre-marked seam.

## Technology Stack (each link = the concept page that teaches it)

| Layer | Used here | Learn it |
|---|---|---|
| Views | Django CBVs + gate mixins, server-rendered templates | [views.md](views.md) · [request-through-stack](../../flows/request-through-stack.md) |
| Business | service layer (kw-only verbs, atomic) | [service-layer](../../concepts/architecture/service-layer.md) · [transactions](../../concepts/django/transactions.md) |
| Data | Django ORM (FILTER aggregates, Coalesce) · `Decimal` money | [from-orm-to-sql](../../concepts/postgresql/from-orm-to-sql.md) · [orm-and-managers](../../concepts/django/orm-and-managers.md) |
| Database | PostgreSQL: advisory+row locks, CHECK/partial-unique armor, query-shaped indexes | [locks](../../concepts/postgresql/locks.md) · [constraints](../../concepts/postgresql/constraints.md) · [indexes](../../concepts/postgresql/indexes.md) |
| Testing | goldens (byte-identical ₹), refusal pins, count pins | [testing-strategy](../../concepts/testing/testing-strategy.md) |

## Security (linked, not re-taught)

- **Authn:** accounts app (OTP-first, Argon2, throttled) — [auth-hardening](../../concepts/security/auth-hardening.md)
- **Authz:** four walls — sidebar pair → `_ManagementOnly` mixin → **service re-gate** (`_ensure_management`, SA checks for pay-basis/F&F/override) → history strips ([rbac-access](../../features/rbac-access.md))
- **Validation:** edge-parsing (`Decimal(str(x))`, PA-07-2) + DB constraint floor
- **Threats this app defends:** double-pay (era guards + provenance + partial-unique) · over-pay races (locks) · forged history (append-only + PROTECT)
- **Audit:** every correction = a row (reversals, `RateCorrectionAudit`, `WorkerPayBasisAudit`, recon evidence, timeline events)

## Required Knowledge — before working here you should know

*Tick honestly; a gap = read that page first, then return (university-textbook style).*

- [ ] Python: `Decimal` vs float · keyword-only args → [service-layer §4](../../concepts/architecture/service-layer.md)
- [ ] Django: CBVs/mixins · `@transaction.atomic` semantics → [transactions](../../concepts/django/transactions.md)
- [ ] PostgreSQL: row vs advisory locks + lock ORDER → [locks](../../concepts/postgresql/locks.md) · constraints-as-armor → [constraints](../../concepts/postgresql/constraints.md)
- [ ] Architecture: single-writer → [single-writer](../../concepts/architecture/single-writer.md) · two-truths → [two-truths](../../concepts/architecture/two-truths.md)
- [ ] Domain: the money story end-to-end → [money-story](../../project/money-story.md)
- [ ] DSA shapes here: log+fold (ledger) · total ordering (deadlock-freedom) → [append-only §10](../../concepts/database-design/append-only-tables.md) · [transactions §9](../../concepts/django/transactions.md)

## Learning Graph

**Before this app:** [money-story](../../project/money-story.md) →
[worker-gets-paid](../../flows/worker-gets-paid.md) →
[transactions](../../concepts/django/transactions.md).
**After this app you're ready for:** [settlement-lifecycle](../../flows/settlement-lifecycle.md)
→ [money-looks-wrong playbook](../../debugging/money-looks-wrong.md) →
interview [Route C](../../README.md) (this app IS the system-design answer).

## What this app owns

**All worker money.** Settlement (obligation), ledger (the book), advances
(loans), payroll (cash), F&F, factory running expenses, recurring expense
templates, material-spend reporting. **Every rupee-write in the entire
system happens inside this app's services.**

## What it does NOT own

Production truth (work reports/verification → `production` app) · piece
capacity/pools (→ `production.pool_service`) · stage COST snapshots
(processing_cost = production's cost-truth, ADR-0009) · user identity/roles
(→ `accounts`). It READS production truth at settlement; never edits it.

## Where requests enter — 17 URLs, 4 lanes

| Lane | URLs | Who |
|---|---|---|
| Worker self-view | `/expense/my/` | any logged-in worker |
| Payroll management | `/payroll/`, `/workers/<pk>/…` (detail·settle·profile·pay-basis·fnf), `/advances/add/` | management (+SA-only inside) |
| Adda settlement | `/settlements/…` (list·start·detail) | management |
| Factory expenses | `/expenses/…`, `/templates/…`, `/generate/`, `/material-spend/` | management |

Full chain per URL: [urls.md](urls.md). Handlers: [views.md](views.md).

## The census

- **Views:** 17 classes (+2 gate mixins) in `config/expense/views.py` (888 lines) — ALL
  LoginRequired; management lanes via `_ManagementOnly` mixin
  (`user_has_role(MANAGEMENT_ROLES)`); super-admin checks INSIDE services.
- **Models:** 14 in `config/expense/models.py` (873 lines) — [models.md](models.md).
- **Services:** 10 modules in `config/expense/services/` — the ONLY money
  writers in the system — [services.md](services.md) (sole-writer table).
- **Tests:** 23 files in `config/expense/tests/` — guards (`test_v2_3_guards`,
  `test_reopen_voids_pay`, `test_s5_recon_block`), money flows
  (`test_adda_settlement_*`), R-series (`test_r4_monthly_basis`,
  `test_r5_*`, `test_r7_fnf`), perf pins (`test_perf_settlement`,
  `test_queue_batching`).
- **Templates:** `templates/expense/*.html` — one per view (names in [views.md](views.md)).

## The one law to carry in

**Single-writer + settlement-only money.** Views parse; these services
decide; `ledger_service` alone touches `WorkerLedgerEntry`; money is born
ONLY at `finalize_adda_settlement`. A new money-write path anywhere else =
STOP + report (owner standing rule).

## Change Impact — touching this app affects

- **Worker balances & My-Earnings ladder** (every surface derives from the ledger)
- **Payroll overview / worker detail** (count-pinned aggregates — perf tests fire)
- **Adda-360 timeline** (settlement events log there)
- **Production interlocks** (settled lines block `set_verified_quantity` + stage reopen)
- **Reconciliation (S1/S5)** + `SettlementReconciliationEvidence`
- **Goldens ₹344.25/₹801/₹633** — byte-identical or the change explains itself
- **23 test files** here + cross-app guard tests · **CI write-site gates 4b/4c**
- (No notifications/external APIs — this app is PG + timeline only)

## Engineering Checklist — pre-flight before ANY change here

- [ ] **Money-Write STOP rule:** does this create a write path outside the approved sole writers? → STOP, owner decision
- [ ] Which sole writer owns the table I'm touching? ([services.md](services.md) table) — the verb goes THERE
- [ ] Settlement-adjacent? My locks join the documented order (5374 FIRST) — never a new ad-hoc lock
- [ ] Preview surfaces (`settlement_queue`/`preview_lines`) updated WITH finalize? (PA-11-2: preview == money-write surface)
- [ ] Amounts parsed `Decimal(str(x))` at the boundary; direction stays in `entry_type`, never signs
- [ ] Test plan = the four-pin set: golden byte-identical + refusal pin + negative probe + (if read surface) count pin
- [ ] New URL? urls.py + sidebar rule (edited at [inventory §6 — the pair editor](../inventory/urls.md)) + [urls.md](urls.md) row + [views.md](views.md) group
- [ ] UI touched? mobile+tablet+desktop verified (owner rule 11)
- [ ] kos-sync: this app's pages + the feature page's Change Impact updated same session

## Learn it / debug it

- Understand: [money-story](../../project/money-story.md) →
  [settlement](../../features/settlement.md) · [ledger](../../features/ledger.md) ·
  [payroll](../../features/payroll.md) · [advances](../../features/advances.md)
- Story: [worker-gets-paid](../../flows/worker-gets-paid.md) ·
  [settlement-lifecycle](../../flows/settlement-lifecycle.md)
- Broken: [money-looks-wrong](../../debugging/money-looks-wrong.md)
- Business README (docs): [config/expense/README.md](../../../config/expense/README.md) —
  data-flow diagrams + per-table impact · deep dive:
  [CHOKEPOINTS/adda_settlement_service](../../../docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md)

---
id: concept-single-writer
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does exactly ONE service own each money/audit table, and how is that rule actually enforced?"
related: [concept-service-layer, feature-ledger, concept-append-only-tables]
---

# Single-Writer Discipline — one pen per book

> 📂 [Architecture concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

`WorkerLedgerEntry` holds every rupee. Imagine three code paths could INSERT
into it: the settlement service, a "quick fix" view, and a data migration.
Each enforces the invariants it remembers. A year later a balance is wrong
and there are three suspects, each with partial alibis. This project's
answer: **each ledger/audit table has exactly ONE writer service** (house
rule 5, ADR-0002). One suspect. Always.

## 2. 💡 Samjho Aise

Ghar ka hisaab ek hi banda likhe to galti turant pakdi jaati hai — "tumne
hi likha hoga." Chaar log likhein to mahina-bhar bahas: "maine nahi, usne."
Kitaab wahi bharosemand jiska munshi EK ho. Table = kitaab, service = munshi.

## 3. Mental Model

> **Invariants live with the pen, not the paper.** A table can't protect
> "amount always positive AND direction in entry_type AND every credit has
> a source" by itself — code enforces most of it. If N places write, the
> invariant is only as strong as the forgetful-est copy. One writer =
> invariants defined once, reviewed once, locked once.

## 4. Technical Deep Dive

**The registry** (who holds which pen — ADR-0002 + PKM §7):

| Table (the book) | Sole writer (the pen) |
|---|---|
| `WorkerLedgerEntry` | `ledger_service` |
| `AddaSettlement` + `Item` + era-B SWA lines | `adda_settlement_service` |
| `StageWorkAssignment` (allocation era) | `allocation_service` |
| `WorkerAdvance` | `advance_service` |
| `PayrollSettlement` + `Item` | `settlement_service` |
| `WorkerPayBasisAudit` | `payroll_service.set_pay_basis` |
| `AddaHistory` / `ClothRollHistory` / `ProductHistory` | `history_service.log_*` |
| `WorkerStageTask` | `worker_task_service` (C-TM: EVERY capture path converges here — manual today, barcode tomorrow; no second door, ever) |

**Enforcement — the part most codebases skip:** the rule is not a comment.
- **CI write-site gates** (e.g. 4b/4c for ADST/SWA) census every
  `objects.create`/`save` against the allowed writer; a stray write FAILS
  THE BUILD. The one legal exception (the chokepoint's provenance stamp via
  `update_fields`) is documented in the gate itself.
- **Tests build money through services only** — even fixtures. A test that
  raw-INSERTs a ledger row would pass today and hide a guard-bypass forever.
- **DB constraints as the last wall** — if all code fails, `CHECK amount>0`
  and the one-reversal partial-unique still refuse the worst corruptions
  ([pg/constraints](../postgresql/constraints.md)).

**Reads are free.** Anyone may SELECT. The discipline is about writes —
that's why derived values (`worker_balance`, `advance_remaining`) can live
in read helpers without violating anything.

## 5. Engineering Thinking

*Alternatives considered:* DB triggers (logic invisible to Python readers,
untestable in the battery) · table-level GRANTs per app user (heavy ops for
a one-team system, and Django runs as one DB user) · "just be careful"
(every corrupted ledger in history was written by careful people).
*The deep reason this works here:* single-writer converts a GLOBAL property
("no bad rows anywhere") into a LOCAL review ("is this one function
correct?"). Locality is the only thing that scales with a codebase.
*Assumption:* writers stay few and named. If a new domain needs a new money
table, it gets a new sole writer — the pattern replicates; it never widens.
*Evolution:* at real multi-team scale the same idea becomes "the service
that owns the topic" (ownership boundaries) — the discipline survives the
architecture that outgrows it.

## 6. How THIS project uses it

Real story #1 — **the rule caught real bugs**: RCP-1 certification censused
write-sites and found strays (view-level writes); extraction back to
services + goldens byte-identical = repair proven safe.
Real story #2 — **the owner's standing STOP rule**: any NEW money-write
path outside the approved writers ⇒ stop and report, never silently fix.
The rule survived a hostile review (R5 census is the baseline).
Real story #3 — C-TM convergence: when barcode scanning arrives, scans
will flow through `worker_task_service` like manual entry does today —
the pen was designed for doors that don't exist yet.

## 7. What breaks without it

The `ledger_service` docstring says it plainly: a stray INSERT silently
changes a worker's balance — no settlement reference, no reversal path, and
append-only means the mistake is *permanent history*. Bypass = double-pay,
unauditable money, and hours of forensic grep instead of one function read.

## 8. Common mistakes (humans)

- Fixtures/migrations that raw-write guarded tables ("it's just test data").
- A second writer added "temporarily" for an import script — temporary is
  how permanent bugs are born; write an importer that CALLS the service.
- Confusing single-writer with single-CALLER — many callers are fine; the
  funnel is the point.

## 9. AI Implementation Pitfalls

- ❌ `WorkerLedgerEntry.objects.create` / raw SQL INSERT anywhere outside `ledger_service` — including tests, migrations, seeds.
- ❌ Adding a convenience wrapper that itself writes ("ledger_utils.py") — a second pen with a different name is still a second pen.
- ❌ Bypassing `worker_task_service` for a new capture path — C-TM is locked.
- ✅ Always verify: CI write-site gates green; if a gate must change, that's an owner decision, not an edit.

## 10. DSA & Complexity

Funnel topology: N callers → 1 writer → 1 table is a **star graph**, and
auditing it is O(1) per table (read the center). The alternative — M writers
— makes every audit O(M) and every invariant change O(M) edits with O(M²)
drift pairs. Same reason the C-TM convergence rule exists: adding doors
must never add centers.

## 11. Interview corner

*Interview Signal: 🟠 Senior — ownership + enforced invariants = senior.*

**Q. "How do you guarantee data invariants that the database can't fully express?"**
- *Short:* Funnel all writes through one owning service; enforce the funnel mechanically (CI census); back the worst cases with DB constraints.
- *Senior:* Split invariants into three tiers — DB-expressible (CHECK/unique → database), row-local (model validation), and cross-row/cross-table business rules (the sole writer). Then make the funnel *executable law*: a census in CI, not a convention in a wiki. Convention decays; builds don't.
- *Project example:* ledger's positive-amount lives in ALL three tiers: service validation, model constraint, PG CHECK — plus the CI gate ensuring only `ledger_service` writes at all.
- *Follow-ups:* "Triggers instead?" (invisible to readers, hostile to tests) · "What about bulk imports?" (the importer calls the service in a loop or the service grows a bulk verb — the funnel never widens).

## 12. 🧠 Remember This

Ek kitaab, ek munshi, aur munshi ka naam CI ko pata hai. Invariant kalam ke
saath rehta hai, kagaz ke saath nahi. Naya darwaza khule to bhi raasta usi
munshi tak jaana chahiye (C-TM). Doosri kalam ka matlab hai: ek din do
sachchaiyaan.

## 13. 30-Second Revision

- Rule 5 / ADR-0002: one writer service per ledger/audit table
- Registry: ledger→ledger_service · ADST/SWA→adda_settlement_service · advances→advance_service · cash→settlement_service · histories→history_service · WST→worker_task_service (C-TM)
- Enforced: CI write-site census (4b/4c) + service-only test fixtures + DB constraint backstops
- Reads free, writes funneled; derived values live in read helpers
- Money-write STOP rule: new path outside writers ⇒ stop + report

## 14. What You Should Now Understand

Why one pen per book turns global correctness into local review, the three
enforcement layers that make it law instead of hope, and how the pattern
absorbs future doors (C-TM). Shaky? Re-read §4 + §6.

**Recommended next topic:** [append-only tables](../database-design/append-only-tables.md)
— what the pen is allowed to DO to the book.

## Implementation References

- ADR: [0002](../../../docs/adr/0002-single-writer-per-ledger-and-history-table.md) · rule: [CLAUDE.md](../../../CLAUDE.md) rule 5
- Census: [docs/PROJECT_KNOWLEDGE_MAP.md](../../../docs/PROJECT_KNOWLEDGE_MAP.md) §7 · chokepoint docs [docs/LEARNING_2_0/CHOKEPOINTS/](../../../docs/LEARNING_2_0/CHOKEPOINTS/README.md)

## Code References
- `config/expense/services/ledger_service.py` (docstring = the rule in the author's voice)

## Further Reading

- Concept sibling: Martin Fowler, *"Aggregate"* (DDD) — single-writer is
  aggregate-root thinking applied to tables; spot the mapping yourself.

## Related

[service-layer](service-layer.md) · [append-only-tables](../database-design/append-only-tables.md) ·
[ledger](../../features/ledger.md) · [pg/constraints](../postgresql/constraints.md)

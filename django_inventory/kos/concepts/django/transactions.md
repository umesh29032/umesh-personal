---
id: concept-django-transactions
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does settlement wrap everything in transaction.atomic, and what breaks without it?"
related: [feature-settlement, flow-worker-gets-paid]
---

# Django Transactions — sab hoga, ya kuch nahi hoga

> 📂 [Django concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

`finalize_adda_settlement` ek click mein yeh sab likhta hai: har contribution
line ka `StageWorkAssignment` + ledger CREDIT, har recovery ka ledger DEBIT +
`PayrollSettlementItem`, har worker ka frozen `AddaSettlementItem`, phir
settlement status FINALIZED. **50+ rows, 6 tables, ek business event.**

Ab socho: 30 rows likhne ke baad server crash ho gaya. Aadhe workers ko
credit mila, aadhon ko nahi; settlement ab bhi DRAFT. Agla finalize kya
karega — dobara credit? **Yeh nightmare hi transactions ka reason hai.**

## 2. 💡 Samjho aise (Beginner)

Transaction = **shaadi ka phera nahi, court marriage ka register**. Jab tak
SIGN nahi hua, kuch bhi final nahi — beech mein light chali jaaye to register
saaf ka saaf. Sign hote hi POORA contract ek saath lagoo.

Database mein: `BEGIN` … tumhare saare INSERT/UPDATE … `COMMIT` (sab dikha)
ya `ROLLBACK` (jaise kuch hua hi nahi). Beech ki adhoori halat duniya ko
kabhi nahi dikhti.

```python
from django.db import transaction

@transaction.atomic          # BEGIN yahan
def finalize_adda_settlement(*, settlement, user, ...):
    ...  # 50+ writes — sab ek saath commit, ya ek saath gayab
                             # function return = COMMIT; exception = ROLLBACK
```

## 3. Mental Model

Ek senior engineer transaction ke baare mein aise sochta hai:

> **"Ek business event = ek transaction = ek boundary."** Pehla sawal kabhi
> "kahan atomic lagau" nahi hota — pehla sawal hota hai *"is operation mein
> EK event kya hai?"* Boundary event ke shape se nikalti hai, code ke shape
> se nahi. Doosra sawal: *"is boundary ke andar kaun-si rows kisi aur ko
> nahi dikhni/badalni chahiye?"* — wahi rows lock hoti hain, fixed order mein.

Implementation padhne se pehle yeh do sawal pooch lo — phir har
`@transaction.atomic` aur har `select_for_update` khud apni jagah bata dega.

## 4. How it actually works (Intermediate — Technical Deep Dive)

- Django normally runs **autocommit**: har akela query apna chhota
  transaction hai. `@transaction.atomic` isse todkar ek explicit block
  banata hai.
- **Nesting = savepoints.** Atomic ke andar atomic → PostgreSQL `SAVEPOINT`.
  Inner fail → sirf inner rollback ho sakta hai. (Is repo mein
  batch-processing per-item savepoints isi se bante hain.)
- **Exception = rollback, return = commit.** Isliye validation FAIL loudly
  karna hi correct hai — raise karo, paisa apne aap wapas.
- **`transaction.on_commit(fn)`** — side effects (email, task queue) commit
  ke BAAD chalao, warna rollback ke baad bhi email chala jaayega.
- Transaction **isolation nahi deta concurrency ke liye kaafi** — do
  transactions ek saath same row padh sakte hain (PostgreSQL default =
  READ COMMITTED). Isliye locks alag cheez hai (§6).

## 5. Engineering Thinking (Advanced/Senior)

**Where do you PUT the boundary?** Is repo ka jawab: **service function par,
view par nahi** (CLAUDE.md rule 4). View parse karta hai, service decide
karta hai — aur jo function DECIDE karta hai wahi atomic hona chahiye,
kyunki wahi jaanta hai "ek event" kya hai.

| Alternative | Why this project rejected it |
|---|---|
| `ATOMIC_REQUESTS = True` (per-request transaction) | Boundary HTTP se bandh jaati; long views mein locks lambi der pakde rehte; read-only views ka bhi transaction |
| Signals for side-writes | Invisible writers, transaction ke andar surprise queries — is repo mein signals BANNED hain (rule 4) |
| Per-write autocommit + manual cleanup | The crash-at-row-30 nightmare; cleanup code khud bug source |
| Two-phase manual flags ("half-done" status columns) | State machine explosion; DB already yeh FREE deta hai |

**Atomicity ≠ race-safety.** Atomic block ke saath bhi do managers ek hi
settlement DOUBLE-finalize kar sakte hain (dono ne DRAFT padha, dono ne
likha). Isliye finalize **locks** leta hai — atomic + lock ordering ek
JODI hai, akela adhoora. Senior sawal hamesha: *"boundary kya hai, aur us
boundary ke andar kaun-si rows FREEZE honi chahiye?"*

## 6. How THIS project uses it

**206 `transaction.atomic` sites** across the codebase — every multi-row
service write. The flagship (`config/expense/services/adda_settlement_service.py`,
function `finalize_adda_settlement`):

```python
@transaction.atomic
def finalize_adda_settlement(*, settlement, user, ...):
    # 1. GLOBAL gate — poore settlement-system ka ek advisory lock
    cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])   # 5374
    # 2. Row locks, FIXED order (deadlock ka ilaaj ORDER hai, luck nahi):
    settlement = AddaSettlement.objects.select_for_update().get(...)
    AddaStageRecord.objects.select_for_update().filter(...)
    WorkerStageContribution.objects.select_for_update(of=('self',))...
    #    ^ PA-11-3: settled qty (verified_quantity) WSC par hai, SR par
    #      nahi — SR lock usse freeze NAHI karta, isliye WSC bhi lock
    WorkerProfile...select_for_update()      # sorted worker_id order
    WorkerAdvance...select_for_update()
    # 3. validate ALL recoveries BEFORE any money write
    # 4. write money (SWA + ledger credits/debits + frozen items)
    # 5. status = FINALIZED
# return = COMMIT: sab locks release, sab rows ek saath visible
```

**The real SQL** — balance kabhi store nahi hota; `ledger_service.worker_balance`
har baar ledger se ginta hai. Captured from the live dev DB (2026-07-19):

```sql
SELECT SUM("expense_workerledgerentry"."amount")
         FILTER (WHERE "expense_workerledgerentry"."entry_type" = 'credit') AS "credit",
       SUM("expense_workerledgerentry"."amount")
         FILTER (WHERE "expense_workerledgerentry"."entry_type" = 'debit')  AS "debit"
FROM "expense_workerledgerentry"
WHERE "expense_workerledgerentry"."worker_id" = 2
```

Kyun tez hai: index `(worker, entry_type)` exactly is query ke liye bana hai
(`WorkerLedgerEntry.Meta.indexes`); PostgreSQL sirf us worker ki entries
chhoota hai, `FILTER` dono SUM ek hi pass mein nikaalta hai. Yeh READ query
transaction ke BAHAR bhi sahi hai — kyunki writes atomic hain, reader ko
kabhi aadha settlement nahi dikhta. **Yehi asli gift hai.**

Where the money constraints back it up (DB armor if code ever slips):
`CHECK (amount > 0)` + partial-unique "one reversal per entry" on the ledger.

## 7. What breaks without it

Remove `@transaction.atomic` from `finalize_adda_settlement` and crash it
mid-way (kill -9, OOM, network blip to PG):

- Worker A ko credit mila, Worker B ko nahi — par settlement DRAFT hi hai.
- Retry → A ko DOUBLE credit (provenance stamp bhi aadha hi laga tha).
- `AddaSettlementItem` snapshots kuch workers ke hain, kuch ke nahi —
  four-way reconciliation identity (ledger ≡ totals ≡ Σitems ≡ Σsnapshots)
  ab kabhi match nahi hogi.
- Aur kyunki ledger **append-only** hai, yeh corruption *permanent history*
  ban jaata hai — UPDATE karke chhupa bhi nahi sakte.

Ek decorator ka farak: provable money vs unprovable barbaadi.

## 8. Common mistakes (humans)

- Boundary VIEW mein rakhna, service mein nahi — phir koi aur caller
  (management command, dusra view) service ko bina transaction ke bula leta hai.
- Atomic block ke andar **external calls** (email, HTTP) — rollback hua to
  email phir bhi gaya. `transaction.on_commit` use karo.
- `select_for_update` on a **nullable-FK `select_related`** — PostgreSQL
  refuses (`FOR UPDATE cannot be applied to the nullable side of an outer
  join`); is repo ne yeh seekha: `of=('self',)`. *(Real bug, chokepoint doc.)*
- Lock order ad-hoc rakhna — kabhi A→B, kabhi B→A = production deadlock lottery.
- Lambi computation locks pakad kar — validate/compute pehle jitna ho sake,
  lock window chhota rakho.

## 9. AI Implementation Pitfalls

- ❌ Removing `transaction.atomic` "kyunki tests phir bhi pass ho rahe hain"
  — tests crash-at-row-30 simulate nahi karte.
- ❌ Splitting ledger writes across two atomic blocks (credit ek mein,
  provenance stamp dusre mein) — the gap IS the bug.
- ❌ Updating balances/totals before ledger rows — is system mein stored
  balance hota hi nahi; agar AI add kare, reject karo.
- ❌ Adding a new lock without joining the documented order (5374 FIRST).
- ❌ Calling the service from a new path without checking it's still inside
  ONE atomic event.
- ✅ Always verify: goldens byte-identical (₹344.25/₹801/₹633) + four-way
  identity after ANY change inside an atomic money path.

## 10. DSA & Complexity

Deadlock = **cycle in a wait-for graph**: T1 holds A wants B; T2 holds B
wants A → cycle → PostgreSQL kills one. Is repo ka cure: **total ordering** —
saare settlement ops locks isi sequence mein lete hain (5374 → ADST → SR →
WSC → profiles-sorted-by-id → advances). Sorted order = graph mein cycle
ban hi nahi sakta (edges sirf "chhote se bade" jaate hain). Wahi reason hai
worker profiles `sorted(by_worker)` mein lock hote hain — O(n log n) sort
kharido, deadlock-freedom FREE milo. Balance query: O(rows-per-worker) with
index, ledger grows forever — registered seam = snapshot table (deferred).

## 11. Interview corner

*Interview Signal: 🟠 Senior — boundaries + the atomic≠concurrency trap = senior filter.*
**Q1. "What does `transaction.atomic` actually do?"**
- *Short answer:* Breaks autocommit into an explicit BEGIN…COMMIT/ROLLBACK
  block; nested atomics become savepoints; exception = rollback.
- *Senior answer:* It's a boundary-declaration tool — the real skill is
  choosing WHAT is one event. Boundary on the deciding function (service),
  isolation still READ COMMITTED, so atomicity solves crash-consistency,
  not races.
- *Project example:* `finalize_adda_settlement` — 50+ rows, 6 tables, one
  event; crash mid-way leaves nothing.
- *Follow-ups:* "What happens on nested atomic failure?" (savepoint rollback) ·
  "Exception swallowed inside the block?" (block still marked for rollback
  if the savepoint context saw it).

**Q2. "Is atomic enough for concurrency?"**
- *Short answer:* No — atomicity ≠ race-safety.
- *Senior answer:* Under READ COMMITTED two transactions can both read
  DRAFT and both write. You add locks: an advisory lock for the system-wide
  gate, `select_for_update` for rows you read-and-bill, and a documented
  lock ORDER for deadlock-freedom.
- *Project example:* 5374 → settlement → stage records → WSC `of=('self',)`
  → profiles (sorted) → advances.
- *Follow-ups:* "Why not SERIALIZABLE isolation?" (retry storms; locks are
  targeted and predictable here) · "Why lock WSC when SR is already locked?"
  (settled qty lives on WSC — PA-11-3, a real fix in this repo).

**Q3. "Where do you put the transaction boundary?"**
- *Short answer:* On the function that represents ONE business event.
- *Senior answer:* Service layer, not the view and not `ATOMIC_REQUESTS` —
  the HTTP request is the wrong unit: boundaries must follow business
  events, and request-wide transactions hold locks through rendering.
- *Project example:* CLAUDE.md rule 4 — views parse, services decide; all
  206 atomic sites live in services.
- *Follow-ups:* "Management command calls the service — still safe?" (yes,
  boundary travels with the service, that's the point).

**Q4. "How do you handle side effects (email/tasks) near transactions?"**
- *Short answer:* `transaction.on_commit` — never inside the block.
- *Senior answer:* Inside the block, a rollback un-writes the rows but not
  the email. on_commit defers until the data is durable; on rollback the
  callback never fires.
- *Project example:* The no-signals rule exists for the same reason —
  invisible writers inside transactions are how half-events escape.
- *Follow-ups:* "What about retries of the on_commit callback?" (must be
  idempotent — same discipline as the provenance stamp).

## Mock Interview Walkthrough

**Interviewer:** "Explain database transactions."
**You:** All-or-nothing execution: BEGIN, writes, COMMIT or ROLLBACK — no half-states visible. In Django, `@transaction.atomic` on the function that represents ONE business event. Ours is settlement finalize: 50+ rows, 6 tables, one event. *(→ §2, §6)*

**Interviewer:** "So atomic makes it concurrency-safe?"
**You:** No — that's the classic trap. READ COMMITTED lets two transactions both read DRAFT and both write. Atomicity handles crashes; races need locks: advisory for the system-wide gate, `select_for_update` on rows we read-and-bill, in a fixed order. *(→ §5)*

**Interviewer:** "Why lock contribution rows if their parent stage records are locked?"
**You:** Because the billed quantity lives on the child — locking the parent doesn't freeze it. We shipped that fix: a verified-quantity edit racing finalize was a lost update on money. Lock what you bill, not what feels parental. *(→ PA-11-3, §6)*

**Interviewer:** "Where do side effects like emails go?"
**You:** `transaction.on_commit` — inside the block, a rollback un-writes rows but not emails. Same reason we banned signals: invisible writers inside transactions are how half-events escape. *(→ §4, §8)*

**Interviewer:** "Prove a claim from your system's SQL."
**You:** The balance read is a single FILTER-aggregate over an append-only ledger, safe OUTSIDE any transaction — because writes are atomic, readers never see half a settlement. I can show you the captured plan. *(→ §6)*

## 12. 🧠 Remember This

Transaction ek vaada hai: **sab hoga, ya kuch nahi hoga.** Boundary business
event ke shape se nikalti hai (service function), code ke shape se nahi.
Atomic crash se bachaata hai, race se nahi — race ke liye locks, aur locks
ka ilaaj ORDER hai, luck nahi. Side effects commit ke BAAD (`on_commit`).
**Ek event, ek boundary, ek lock-order.**

## 13. 30-Second Revision

- `@transaction.atomic` = BEGIN…COMMIT/ROLLBACK; nesting = SAVEPOINT
- Exception → rollback; return → commit; validate loudly, raise freely
- Boundary = ONE business event = service function (never view/request)
- Atomicity ≠ race-safety: READ COMMITTED → need `select_for_update` + advisory locks
- Deadlock cure = fixed lock ORDER (this repo: 5374 → ADST → SR → WSC → profiles → advances)
- Lock what you READ-and-bill (WSC `of=('self',)` — PA-11-3)
- Side effects: `transaction.on_commit`, idempotent
- Real SQL: FILTER-aggregate balance, index `(worker, entry_type)`

## 14. What You Should Now Understand

You can now explain: what atomic does, where boundaries belong and why,
why atomicity alone doesn't stop double-finalize, how this project's lock
order prevents deadlocks, and why the balance query is safe outside any
transaction. If any of those feels shaky — re-read §5–§7.

**Recommended next topic:** *PostgreSQL locks* (Phase 3 — `pg/locks`:
advisory vs row locks, the 5374/5375 namespaces) · then *single-writer
discipline* (why one service owns each money table).

## 15. Evolution / Future design

Volume 100× → same boundaries; the lock window is already minimal
(validate-first design). If finalize ever gets slow: the registered seam is
splitting money-write from snapshot-freeze via on_commit chaining — NOT
loosening atomicity. Any such change re-proves the goldens byte-identical.

## Implementation References

  (`finalize_adda_settlement`, `reverse_adda_settlement`) ·
  `ledger_service.py` (`worker_balance`, `_create_entry`) · 206 atomic sites repo-wide
- ADR: [0005](../../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md) · [0002](../../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)
- Deep dive: [chokepoint: adda_settlement_service](../../../docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md) (verified trace + lock order) · [LEARNING/03 transactions & locks](../../../docs/LEARNING/03_TRANSACTIONS_AND_LOCKS.md)

## Code References
- `config/expense/services/adda_settlement_service.py`
- Tests: `config/expense/tests/test_adda_settlement_service.py` · `test_v2_3_guards.py` · goldens in devseed scenarios

## Further Reading

- Official: [Django — Database transactions](https://docs.djangoproject.com/en/5.0/topics/db/transactions/) · [PostgreSQL — Explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- One article: *"PostgreSQL isolation levels"* (any current deep-dive) — read
  AFTER you can retell §5 from memory.

## Related

[features/settlement.md](../../features/settlement.md) ·
[flows/worker-gets-paid.md](../../flows/worker-gets-paid.md) ·
(Phase 3): pg/locks · single-writer · append-only-tables

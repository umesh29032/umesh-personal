---
id: concept-query-performance
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Where does query time actually go in this app, and how does the repo make performance regressions impossible to miss?"
related: [concept-from-orm-to-sql, concept-pg-indexes, concept-django-transactions]
---

# Query Performance — count queries, not milliseconds

> 📂 [PostgreSQL concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)

## 1. The project hook

`config/production/tests/test_perf_baseline.py`, line 3, states this
repo's whole philosophy: *"Locks query counts on hot read paths so an
accidental N+1 (or a prefetch removed) fails CI."* Not benchmarks. Not
milliseconds. **Counts.** This page teaches why that's the senior move,
and the three diseases the counts guard against.

## 2. 💡 Samjho Aise

Doodhwale se roz 1 baar doodh lena theek hai. Par agar 30 glass ke liye
30 BAAR jaana pade — har glass alag chakkar — to samasya doori nahi,
CHAKKAR hain. Database bhi doodhwala hai: har query ek chakkar (network +
parse + plan). Dheemi app ka ilaaj aksar "tez doodhwala" nahi, "kam
chakkar" hota hai. Aur chakkar GINE ja sakte hain — isliye repo unhe CI
mein ginta hai.

## 3. Mental Model

> Query cost = **round trips × per-trip work**. The killer is almost always
> round trips (N+1), not per-trip work — and round trips are DETERMINISTIC
> for a given code path, while milliseconds depend on machine, cache, and
> moon phase. So: pin the count (stable, CI-able), profile the milliseconds
> only when a count-clean path is still slow.

## 4. Technical Deep Dive

**Disease 1 — N+1.** Django querysets are lazy and relations
auto-fetch on access:

```python
for item in settlement.items.all():      # 1 query
    print(item.worker.email)             # +1 query PER item — the trap
```

The repo's cures, from real code:
- `select_related('worker')` — SQL JOIN, one trip
  (`s.items.select_related('worker')` — the real settlement detail view).
- Deep chains in one go: `.select_related('stage_record__adda', 'bundle',
  'size', 'color', 'pattern')` (`worker_assignments` — five relations,
  still ONE query).
- `prefetch_related` for many-to-one-reversed/M2M — second query + Python
  stitch, still O(1) trips.
- **Aggregate instead of iterate**: `outstanding_advances_bulk` computes
  the whole payroll board in one grouped query — the strongest cure is not
  fetching rows at all.

**Disease 2 — recompute-per-row in templates.** A template calling a
method per row = hidden N+1 the view never sees. Cure: compute in the
view/service (annotate or bulk map), pass finished data to templates.
The `test_perf_baseline` fixture proves pages hold a FIXED count for 3
Addas — "same fixed cost for 3 Addas → no N+1."

**Disease 3 — premature caching.** The repo's rule (from the
`worker_balance` P5.2 comment): derive-at-read with an index until
NUMBERS prove otherwise; the O(1) snapshot table is a REGISTERED,
DEFERRED seam — "don't add it speculatively." Caching money creates an
invalidation problem worse than the read cost
([two-truths](../architecture/two-truths.md): derived values are the law).

**The enforcement — pins, not hopes** (12 `assertNumQueries` sites):

```python
with self.assertNumQueries(2):    # test_perf_settlement.py — the queue
    ...                            # batches its lookups: 2 trips, pinned
with self.assertNumQueries(0):    # and the cached path does NOTHING
    ...
```

`test_perf_baseline.py` pins hot pages with named constants and this
comment discipline: *"A silent move = a template/queryset N+1 regression —
update CONSCIOUSLY."* A pin failure is not noise; it's the system asking
"did you MEAN to add a query?"

## 5. Engineering Thinking

*Why counts, not time?* Time-based CI perf tests flake (shared runners,
cold caches) until someone deletes them; counts never flake and catch the
dominant disease. *What counts DON'T catch:* one monstrous query (count=1,
cost=huge) — that's what EXPLAIN habits are for
([from-orm-to-sql](from-orm-to-sql.md)); the two tools cover each other.
*The dev-DB trap:* 170 rows make everything fast — this repo's honest
posture is that latency/load testing was consciously DEFERRED and
registered as an accepted risk at certification ("record what you did NOT
measure"), while count-pins hold the line that never depends on scale.
*When someone says "just cache it":* the senior asks what invalidates it —
in a system where settlement finalize/reverse changes balances, a stale
cached balance is a MONEY bug, not a UX bug.

## 6. How THIS project uses it

Real repair, preserved in the perf suite's history: the A360/overview
class of pages batched from per-row queries to grouped aggregates + fixed
prefetches — then PINNED so the fix can't silently rot. The pattern to
copy for any new list page: (1) build the page, (2) `CaptureQueriesContext`
its view, (3) kill per-row queries with select_related/prefetch/aggregate,
(4) pin the final count with a named constant and a comment saying what
each query IS. Four steps, and the page stays fast forever or fails loudly.

## 7. What breaks without it

The classic slow-rot: every sprint adds one innocent `.worker.name` in a
template; nothing fails; eighteen months later the payroll board makes 400
trips and "Django is slow." With pins, trip #3 fails CI the day it's
introduced, with a diff pointing at the exact view.

## 8. Common mistakes (humans)

- Fixing N+1 with `select_related` on EVERYTHING — joins widen rows;
  prefetch may beat join for wide relations; measure.
- Pinning counts without naming what each query is — the next dev can't
  tell a legit +1 from a regression.
- "Optimizing" a page nobody uses while the settlement queue does the real
  work — pins go on HOT paths (the repo pins queue, overview, worker board).
- Profiling in DEBUG mode (DEBUG keeps `connection.queries` forever —
  memory balloons; also toolbar overhead lies).

## 9. AI Implementation Pitfalls

- ❌ Adding a queryset/method call inside a template loop — the invisible
  N+1; compute in the view.
- ❌ "Fixing" a failing `assertNumQueries` by bumping the number — the pin
  is asking a question; answer it in the comment or fix the regression.
- ❌ Introducing caching on money-derived values — derived-live is
  architectural law; the seam is owner-gated.
- ❌ Dropping a `select_related` during a refactor because "tests still
  pass" — the PERF test is the one that catches it; run the battery.
- ✅ Always verify: new list page ships with its count pinned + named.

## 10. DSA & Complexity

N+1 = turning one O(n)-row query into n O(1) queries — same data, n×
round-trip constant, and the constant (network+parse+plan ≈ ms) dwarfs
row work (µs). `select_related` = the JOIN does a hash/merge in C instead
of your loop in Python. `prefetch_related` = 2 queries + an O(n) hash-map
stitch — you're choosing WHERE the join happens. Aggregation = pushing the
fold to the data instead of pulling rows to the fold
([append-only §10](../database-design/append-only-tables.md) — same
log/fold idea, performance edition).

## 11. Interview corner

*Interview Signal: 🟡 Mid — N+1 diagnosis is asked in almost every mid screen.*

**Q. "A Django list page is slow. Your process?"**
- *Short:* Count queries first (debug toolbar / CaptureQueriesContext). N+1 → select_related/prefetch/aggregate. Count-clean but slow → EXPLAIN the big one. Then pin the fixed count in a test.
- *Senior:* Separate trip-dominated from work-dominated slowness — different tools. Fix trip-dominated at the call site (it's a code-shape bug, not a DB bug); fix work-dominated with plans/indexes. Institutionalize the win: a count pin with named constants turns a one-time fix into a permanent property. And refuse ms-based CI assertions — they decay into deleted tests.
- *Project example:* pinned queue at exactly 2 queries (+0 for the cached path); the fixed-cost-for-3-Addas fixture proving N+1-freedom; five-relation select_related in `worker_assignments`; the deliberately-deferred snapshot seam.
- *Follow-ups:* "select_related vs prefetch_related?" (JOIN vs 2-query stitch; FK/O2O vs M2M/reverse) · "When is caching right?" (immutable/frozen data — this repo caches nothing money-derived, by law) · "How do you catch template-level N+1?" (fixed-fixture count pins on the PAGE, not the queryset).

## 12. 🧠 Remember This

Chakkar gino, milliseconds nahi. N+1 template mein chhupta hai, pin CI
mein pakadta hai. Ilaaj teen: JOIN le aao (select_related), do trip mein
saanth lo (prefetch), ya row laana hi band karo (aggregate). Aur paise ke
number kabhi cache nahi — derived-live kanoon hai.

## 13. 30-Second Revision

- Cost = trips × per-trip; trips dominate; trips are pinnable, ms aren't
- N+1 cures: select_related (JOIN) · prefetch_related (2q+stitch) · aggregate (no rows)
- Real pins: queue=2 queries, cached=0; fixed-cost-for-3-Addas fixture; 12 pins total
- Template loops = where N+1 hides; compute in views
- Money derived-live ALWAYS; snapshot seam registered + deferred
- Count-clean but slow → EXPLAIN ([from-orm-to-sql](from-orm-to-sql.md))

## 14. What You Should Now Understand

The three diseases and their cures from real repo code, why count-pins
beat benchmarks in CI, and the four-step recipe every new list page
follows. Shaky? Open `test_perf_baseline.py` — it's this page in
executable form.

**Recommended next topic:** [django/orm-and-managers](../django/orm-and-managers.md)
— the queryset machinery underneath everything you just tuned.

## Implementation References

- The deferred seam: `ledger_service.worker_balance` P5.2 comment

## Code References
- Pins: `config/production/tests/test_perf_baseline.py` (read its header comment) · `config/expense/tests/test_perf_settlement.py` · `test_queue_batching.py` · `test_a360_overview.py`
- Cures in code: `payroll_service.worker_assignments` (5-relation select_related) · `outstanding_advances_bulk` (grouped aggregate) · settlement views' select_related chains

## Further Reading

- Official: [Django — Database access optimization](https://docs.djangoproject.com/en/5.0/topics/db/optimization/)

## Related

[from-orm-to-sql](from-orm-to-sql.md) · [indexes](indexes.md) ·
[payroll](../../features/payroll.md) · [append-only-tables](../database-design/append-only-tables.md)

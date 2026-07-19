---
id: concept-append-only-tables
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why are the money and history tables never UPDATEd or DELETEd — and how do corrections work then?"
related: [concept-single-writer, feature-ledger, concept-pg-constraints]
---

# Append-Only Tables — history that cannot lie

> 📂 [Database-design concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)

## 1. The project hook

2026-06-14, pre-staging audit headline: **workers were paid for 120 pieces
when 105 were produced.** The only reason that leak was FINDABLE months
later: nothing in the money trail had ever been overwritten. Every row
still said exactly what happened and when. An UPDATE-happy system would
have shown a tidy, wrong, unfalsifiable present.

## 2. 💡 Samjho Aise

CCTV recording samjho. Chori pakadni hai to purani footage chahiye — JAISI
THI waisi. Jo system purani footage par naya scene chipka deta hai (UPDATE),
uske paas saboot nahi, sirf aaj ki kahani hai. Append-only matlab: har frame
recorded, koi frame edit nahi. Galti bhi record, sudhaar bhi record.

## 3. Mental Model

> **State is a claim; events are evidence.** An append-only table stores
> evidence. Any state you need (balance, remaining, status) is derived by
> folding over the evidence. Corrections don't change evidence — they add
> counter-evidence. Design question for any table: *"will someone ever need
> to prove what happened?"* Yes → append-only.

## 4. Technical Deep Dive

**The append-only citizens of this repo:**

| Table | Corrections happen via |
|---|---|
| `WorkerLedgerEntry` | `reverse_entry` — opposite-direction row, `reverses` FK, one-reversal-per-entry enforced by partial unique |
| `AddaSettlement` | never edited after FINALIZE — `reverse` / `reverse+supersede` chain (`supersedes` self-FK) |
| `WorkerAdvance` | immutable; recovery/write-off = separate linked rows (PSI) |
| `AddaHistory` / `ClothRollHistory` / `ProductHistory` | pure timelines — no correction concept; a wrong event is followed by its correcting event |
| `WorkerStageTask` | cancel = status CANCELLED, **never deleted** ("un-tick ≠ erase") |
| `MachineAssignment` | possession windows — closed, never rewritten |

**The three implementation rules that make it real:**
1. **Positive amounts + direction column** — reversal math stays SUM-friendly
   ([ledger](../../features/ledger.md)).
2. **Reversal carries the ORIGINAL entry_date** — the correction lands in
   the same accounting period as the mistake ("galti June ki, sudhaar bhi
   June me ginega" — `ledger_service.reverse_entry`).
3. **Soft-state over delete everywhere else** — `is_active`, `reversed_at`,
   `CANCELLED`: the row stays, its standing changes. (Owner standing rule:
   work-that-happened = immutable append-only history.)

**Derived state, always:** balance, advance remaining, settlement standing —
computed by folding rows. The moment you store the fold, you own a cache
with no invalidation story ([ledger](../../features/ledger.md) pitfalls).

## 5. Engineering Thinking

*Alternatives:* audit-log tables alongside mutable data (double-write drift:
which one is true?) · temporal tables / triggers (invisible to the ORM,
untested by the battery) · event sourcing frameworks (this IS event
sourcing's core idea, minus the framework tax — the project needed the
property, not the ecosystem). *The real trade-off:* append-only tables grow
forever and reads become folds. This repo accepts that consciously — the
`worker_balance` comment registers the O(1) snapshot-table seam as DEFERRED,
"don't add it speculatively." *Assumption:* writers respect the rule — which
is why append-only rides on [single-writer](../architecture/single-writer.md)
+ DB backstops; paper rules don't stop UPDATEs, one reviewed function does.

## 6. How THIS project uses it

Walk the reversal path in `ledger_service.reverse_entry` (read it — 30
lines): refuses reversing a reversal → refuses double-reversal at app level
→ the DB partial-unique `uniq_one_reversal_per_entry` catches the race the
app can't see → the reversal row copies the original's `entry_date`. Then
look at `AddaSettlement.supersedes` — a wrong settlement's replacement
POINTS AT its predecessor, so the chain of "what did we believe, when"
survives every correction. This is why disputes end in minutes: the
question is never "what is true," only "read the rows in order."

## 7. What breaks without it

One UPDATE on a ledger amount: every reconciliation identity that involved
the old value is now unexplainable; the four-way certification identity
(ledger ≡ totals ≡ Σ items ≡ Σ snapshots) breaks retroactively; and the 120
-vs-105 class of leak becomes undetectable — the evidence would have been
edited into agreement with the mistake.

## 8. Common mistakes (humans)

- "Fixing" a typo amount in the DB shell — you just forged history; write
  the reversal.
- Deleting test/demo rows from guarded tables in a shared DB — soft-state
  exists for exactly this.
- Storing derived standing ("is_settled") on the event row — standing
  changes, events don't.

## 9. AI Implementation Pitfalls

- ❌ UPDATE/DELETE on any table in the §4 list — including data migrations
  ("backfill only known facts" is the owner's standing data principle).
- ❌ Adding an `is_deleted` that actually deletes downstream (filters that
  hide rows from reconciliation) — soft-state must stay visible to audits.
- ❌ "Cleaning up" reversal pairs that net to zero — the pair IS the record.
- ✅ Always verify: negative probes (attempted UPDATE/DELETE refusals where
  pinned) and the four-way identity stay green.

## 10. DSA & Complexity

An append-only table is a **log**; derived state is a **fold** (reduce) over
it. Balance = fold(+credit/−debit). Cost: O(n) per fold, mitigated by
indexes that let PG fold only one worker's slice
([transactions §6](../django/transactions.md#6-how-this-project-uses-it)) —
and the classic log optimization, **snapshotting** (checkpoint + fold the
tail), is exactly the registered-but-deferred seam. You already know this
pattern from prefix sums: same math, different clothes.

## 11. Interview corner

*Interview Signal: 🟠 Senior — evidence-vs-state design = senior.*

**Q. "Design a system where financial history must be tamper-evident."**
- *Short:* Append-only event log; corrections as compensating events; derived state; single writer; DB constraints as backstop.
- *Senior:* Separate evidence from claims. Evidence (events) is immutable and complete; claims (balances, statuses) are derived and disposable. Corrections add counter-evidence dated to the original period so accounting windows stay truthful. Enforce with one writer + partial-unique idempotency + refusal tests.
- *Project example:* `reverse_entry`'s three-layer double-reversal defense; `supersedes` chains on settlements; the 120-vs-105 leak that stayed provable months later.
- *Follow-ups:* "Table grows forever?" (snapshot seam — checkpoint + tail) · "True tamper-proofing?" (hash-chaining rows — not needed at this trust level, know the escalation path).

## 12. 🧠 Remember This

Saboot kabhi mat badlo — naya saboot jodo. Balance kahani hai, rows gawah
hain. Galti ka ilaaj reversal, reversal ki date = galti ki date. Aur jo
table kal adaalat mein kaam aa sakti hai, wo aaj append-only honi chahiye.

## 13. 30-Second Revision

- Evidence (events) immutable · claims (state) derived — always
- Corrections: reversal rows (original entry_date!) · supersede chains · soft-state
- One-reversal-per-entry: app check + partial unique (race-proof)
- Never UPDATE/DELETE the §4 list; cancel = status, not erase
- Growth cost accepted; snapshot seam registered, deferred
- Log + fold = the DSA shape; indexes fold one slice

## 14. What You Should Now Understand

Which tables are evidence and why, how corrections work without edits, why
derived-state is the twin rule, and what the growth trade-off costs. Shaky?
Re-read §4 + §6.

**Recommended next topic:** [pg/constraints](../postgresql/constraints.md) —
the database-level backstops that hold even when code fails.

## Implementation References

- ADR: [0004 tracking append-only](../../../docs/adr/0004-tracking-is-append-only-history-primitive.md) · [0002](../../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)
- The leak story: [docs/PRODUCTION_TRUTH_FOUNDATION_REVIEW.md](../../../docs/PRODUCTION_TRUTH_FOUNDATION_REVIEW.md)

## Code References
- `config/expense/services/ledger_service.py` (`reverse_entry`) · `AddaSettlement.supersedes` in `config/expense/models.py`

## Further Reading

- Official: [PostgreSQL — partial unique indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- One essay: Pat Helland, *"Immutability Changes Everything"* — the industry
  version of what this repo practices.

## Related

[ledger](../../features/ledger.md) · [single-writer](../architecture/single-writer.md) ·
[settlement](../../features/settlement.md) · [pg/constraints](../postgresql/constraints.md)

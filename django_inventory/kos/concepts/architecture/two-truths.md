---
id: concept-two-truths
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does this system refuse to let 'work happened' and 'money is owed' be the same fact?"
related: [project-money-story, feature-settlement, feature-stage-tracking, feature-allocation]
---

# Two Truths — the architecture's deepest decision

> 📂 [Architecture concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)

## 1. The project hook

Pre-V2, this system credited the ledger the moment work was allocated.
Result: every production correction became a money correction; provisional
numbers hardened into permanent ledger rows; the paid-120-produced-105 leak
had no structural defense. The V2 redesign's core act was a SEPARATION:
**production truth** (what work happened) and **financial truth** (what
money exists) became different systems with different rules, meeting at
exactly one gate. [ADR-0005](../../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md).

## 2. 💡 Samjho Aise

Cricket scoreboard aur match-fees ka hisaab. Scoreboard live badalta hai —
umpire ne catch check kiya, run wapas liye. Fees ka register match KHATAM
hone par likha jaata hai, final scorecard dekh ke. Agar har run par fees
likhte jao, har umpire-review par paisa bhi kaatna padega — scoreboard aur
tijori dono jhoothi ho jaayengi. Alag rakho: khel khatam, phir hisaab.

## 3. Mental Model

> **Different truths have different change rules.** Production truth is
> *observational* — it should be easy to correct (people mistype). Financial
> truth is *contractual* — it should be nearly impossible to change (money
> promised). A system that stores both in one place must pick ONE change
> rule, and both choices are wrong. Separate stores, one explicit
> conversion event, and each side gets the mutation semantics it needs.

## 4. Technical Deep Dive

**The two systems:**

| | Production truth | Financial truth |
|---|---|---|
| Lives in | `production` app: WST / WSC / pools | `expense` app: ledger / settlements |
| Unit | observed work (good/alter/missing per dim) | ledger events (credit/debit) |
| Change rule | correctable until consumed (`verified_quantity`, void report, reopen) | append-only, reverse-don't-edit |
| Guarded by | single-writer `worker_task_service` (C-TM) | single-writer `ledger_service` + settlement armor |
| Visibility number | frozen `expected_*` (Option B: NO ledger row) | derived balance |

**The gate:** `finalize_adda_settlement` — the ONLY code path that reads
production truth and writes financial truth. Direction is one-way: expense
reads production, **never edits it**; production never touches expense.

**The interlocks that keep the truths honest ACROSS the boundary:**
- A settled line refuses production correction
  (`set_verified_quantity` names the ADST — reverse money first).
- A settlement-credited stage refuses reopen (V2-3 armor, names the ADST).
- The resolver rule (`verified ?? reported/good`) is applied INDEPENDENTLY
  per concern — settlement for money, pool for capacity — so one correction
  propagates to both without either system reading the other's tables.
- Eras (ADR-0007): the old credit-at-allocation world survives as era-A
  rows (readable, reversible), new world is settlement-first —
  `LEDGER_CREDIT_AT_ALLOCATION=False` with a tested rollback lever. Even
  the ARCHITECTURE CHANGE respected both truths' histories.

**Actually four concerns, not two** (the S4 lock): allocation (capacity) ⊥
cost_method (stage costing, ADR-0009) ⊥ earning (worker pay) ⊥ settlement
(the boundary). Each independently correctable; none reads another's
tables. Two-truths is the headline; orthogonality is the full law.

## 5. Engineering Thinking

*Alternative — one table with a `paid` flag:* every correction now races
payment state; audits can't tell claim from commitment. *Alternative —
credit immediately, adjust later:* the adjustment stream becomes a second
ledger nobody designed (this WAS the pre-V2 gap). *The real principle:*
**separate data by its rate-and-rules of change, not by its topic.** Work
and pay share a topic (the same 38 pieces!) but have opposite change
physics — that's why they split. *Assumption:* the gate stays singular. Ten
gates = ten conversion semantics = the separation quietly dies; hence
single-writer + CI gates on the boundary services. *Evolution:* new
consumers of production truth (barcode traceability, QC analytics) attach
WITHOUT touching money — the separation is what makes them cheap.

## 6. How THIS project uses it

Trace one correction end-to-end: manager changes Meena's 38 → 35 in Report
Review. Production truth updates in place (observational). The pool a
downstream stage offers recomputes to 35 (capacity resolver). Her Expected
shows the frozen visibility number until settlement. At finalize, money
books 35 (settlement resolver). Nobody wrote a compensating money entry —
**because money didn't exist yet.** Now try it AFTER settlement: refused,
with the ADST name — reverse first, and the reversal is itself append-only
financial history. One correction, two regimes, zero contradictions.

## 7. What breaks without it

The pre-V2 world, documented: provisional numbers in the permanent book;
corrections needing synchronized edits in two places (one always forgotten);
and no structural answer to "why did we pay for more than we produced."

## 8. Common mistakes (humans)

- "Simplifying" by joining production rows to ledger rows in a report and
  editing from there — the report is fine; the EDIT path is the sin.
- Backfilling expected_* from current rates ("they drifted") — they're
  frozen history, drift is the point.
- Treating Expected as money owed in conversations with workers — it's
  visibility; the ladder's labels exist to keep the promise honest.

## 9. AI Implementation Pitfalls

- ❌ Any expense-app write from production services or vice versa — the
  boundary has ONE gate.
- ❌ "Optimizing" the resolver by storing the resolved quantity — each
  concern derives it independently, on purpose.
- ❌ Reading pool/allocation tables in money code (or settlement tables in
  capacity code) — four-concern orthogonality is owner-locked.
- ✅ Always verify: the cross-boundary interlocks (settled-line refusal,
  reopen armor) + goldens after ANY change near the gate.

## 10. DSA & Complexity

This is an **isolation-by-construction** argument, not an algorithm — but
note the shape: two state machines with different transition rules,
connected by a single directed edge (the gate). Reasoning about either side
is local; reasoning about the system is the edge. Minimizing cut edges
between subsystems = minimizing what you must hold in your head — the
graph-theory version of "why this architecture is debuggable."

## 11. Interview corner

*Interview Signal: 🔴 Staff — boundary-drawing by change-physics — staff-level architecture.*

**Q. "Where would you draw the boundary between operational data and financial data?"**
- *Short:* By change semantics: freely-correctable observations vs append-only commitments, converted at one explicit, atomic, audited event.
- *Senior:* Ask "what are this data's change physics?" — not "what is it about." Same 38 pieces appear on both sides with opposite rules. Then defend the boundary: one gate, one direction, interlocks where late corrections would contradict early commitments, and a shared derivation rule so corrections propagate without cross-reads.
- *Project example:* Option B end-to-end — the 38→35 story above; the settled-line and reopen refusals; era cutover preserving both histories.
- *Follow-ups:* "Real-time earnings display without crediting?" (frozen expected_* — visibility ≠ commitment) · "What forces the gate to stay singular?" (single-writer + CI census — law, not convention).

## Mock Interview Walkthrough

**Interviewer:** "Your system tracks work AND pay. One table with a paid flag — why not?"
**You:** Because the same fact has opposite change rules on each side. Work reports need cheap corrections — people mistype. Money needs near-immutability — it's a commitment. One table forces one rule, and both choices are wrong. We split into two systems joined at a single gate. *(→ §3, §5)*

**Interviewer:** "Give me a concrete correction scenario."
**You:** Manager fixes a report from 38 to 35. Before settlement: production truth updates in place, the next stage's capacity recomputes, money doesn't exist yet — free. After settlement: the edit is refused BY NAME with the settlement reference; you reverse the money first, and the reversal is itself append-only history. One correction, two regimes, zero contradictions. *(→ §6)*

**Interviewer:** "How does the correction reach both pay and capacity without coupling the systems?"
**You:** A shared derivation rule — `verified ?? reported` — applied independently in each concern. Settlement computes it for money, the pool computes it for capacity; neither reads the other's tables. Derive, don't copy. *(→ §4)*

**Interviewer:** "What keeps the gate singular over years of development?"
**You:** Law plus machinery: single-writer services with a CI write-site census. A convention would decay; a failing build doesn't. *(→ single-writer)*

**Interviewer:** "You changed this architecture once — how did that go?"
**You:** The era cutover: old rows credited-at-allocation stayed readable and reversible (era-A), the new settlement-first world went live behind a tested rollback flag. Both histories intact — the architecture change itself respected the two-truths rules. *(→ ADR-0007)*

## 12. 🧠 Remember This

Kaam ki sachchai aur paise ki sachchai ke badalne ke NIYAM alag hain —
isliye ghar alag, darwaza ek (settlement). Darwaze se pehle: sudharo
aazaadi se. Darwaze ke baad: pehle paisa ulto, phir kaam chhuo. Aur chaar
concern (capacity·cost·earning·settlement) ek doosre ki almari kabhi
nahi kholte.

## 13. 30-Second Revision

- Production truth = observational, correctable; financial = contractual, append-only
- ONE gate: finalize; one direction: expense reads production, never edits
- Interlocks: settled-line refusal · reopen armor · resolver applied per concern
- Option B: complete freezes expected_* — visibility, NO ledger row
- Eras (ADR-0007): cutover with rollback lever, both histories intact
- Full law: 4 concerns orthogonal (allocation ⊥ cost ⊥ earning ⊥ settlement)

## 14. What You Should Now Understand

Why "one table with a paid flag" fails, how change-physics (not topic)
draws boundaries, what the interlocks protect, and how one correction
propagates through both regimes without contradiction. Shaky? Re-run the
38→35 trace in §6.

**Recommended next topic:** [settlement](../../features/settlement.md) if
you haven't read the gate itself; else Phase-5's `from-orm-to-sql` starts
the database-depth track.

## Implementation References

- ADRs: [0005](../../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md) (the decision) · [0007](../../../docs/adr/0007-allocation-era-ledger-cutover.md) (the cutover) · [0009](../../../docs/adr/0009-cost-truth.md) (cost = third concern)
- Locked design: [docs/ARCHITECTURE_V2.md](../../../docs/ARCHITECTURE_V2.md) · teaching source: [docs/LEARNING/05](../../../docs/LEARNING/05_PRODUCTION_TRUTH.md) + [06](../../../docs/LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md)

## Code References
- the gate `adda_settlement_service.py` · interlock `worker_task_service.set_verified_quantity`

## Further Reading

- Sibling idea: CQRS/event-sourcing literature — this repo is the
  no-framework version; compare what it DIDN'T need (buses, projections).

## Related

[money-story](../../project/money-story.md) · [settlement](../../features/settlement.md) ·
[stage-tracking](../../features/stage-tracking.md) · [allocation](../../features/allocation.md) ·
[append-only-tables](../database-design/append-only-tables.md)

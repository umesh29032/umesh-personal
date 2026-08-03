---
id: concept-service-layer
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does every write in this project go through a service function instead of views, forms, or signals?"
related: [concept-single-writer, concept-django-transactions, project-system-map]
---

# The Service Layer — where decisions live

> 📂 [Architecture concepts](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)

## 1. The project hook

`finalize_adda_settlement` is called from a view today. Tomorrow a
management command replays it for a migration; next month a barcode-scan
flow triggers it. If the money logic lived IN the view, every new caller
would need a copy — and copies drift. This project has **one place where
every business decision lives**: `config/<app>/services/`. Views parse,
services decide, models store (house rule 4).

## 2. 💡 Samjho Aise

Bank ki branch samjho. Counter-clerk (view) form checkta hai, token deta
hai — par PAISA clerk nahi chhoota. Paisa sirf cashier (service) ke haath
se hilta hai, chahe request counter se aayi ho, ATM se, ya app se. Cashier
ek, raaste anek. Isliye galti bhi ek jagah pakdi jaati hai.

## 3. Mental Model

> A service function = **one business verb with a contract**. Its signature
> says what the business needs (keyword-only, primitives + model instances);
> its docstring declares its side effects; its body owns the transaction.
> If you can't name the verb, it isn't a service — it's a helper.

## 4. Technical Deep Dive

The shape (every service in this repo follows it):

```python
@transaction.atomic                      # the verb owns its boundary
def record_advance(*, user, worker, amount, advance_date=None, notes='',
                   attachment=None):
    """Record an immutable advance (a loan to the worker). No ledger debit —
    advances are recovered at settlement, not netted against earnings here."""
    _ensure_management(user)             # permission re-check AT the write
    ...validate loudly...                # raise = rollback, free of charge
    return WorkerAdvance.objects.create(...)
```

Five properties, each load-bearing:
1. **Keyword-only args** (`*`) — call sites stay readable, refactors safe.
2. **Docstring = contract** — side effects declared ("Side effects:" blocks
   in the money services are census-able; CI write-site gates read the code).
3. **`@transaction.atomic` on the verb** — the boundary follows the business
   event ([transactions](../django/transactions.md)).
4. **Permission re-check inside** — the service is wall #3 of the four walls
   ([people-and-roles](../../project/people-and-roles.md)); hiding the
   button was only politeness.
5. **Loud validation** — `raise ValidationError` with a sentence a human can
   act on (see the monthly-advance refusal in `advance_service` — it
   explains WHY and what to do instead).

**What is banned, and why:**

| Banned | Why (real reasoning, not dogma) |
|---|---|
| Signals (ADR-0001) | Invisible writers — a `post_save` that writes money is a second door no reviewer sees. This repo: ZERO signal writers |
| Multi-row writes in views | Every new caller (command, cron, another view) re-implements or bypasses |
| `form.save()` on money fields | Forms are wall #2 (strip), not decision-makers |
| Business logic in model `save()` | Hides multi-row consequences inside a single-row API |

## 5. Engineering Thinking

*Why not "fat models" (Django's classic advice)?* Model methods work until
a verb spans MODELS — `finalize_adda_settlement` touches 6 tables across 2
apps. A verb that owns several tables can't live on one of them without
privileging it. *Why not a class-based command bus / CQRS?* One factory,
one process — a module of functions delivers the same seam without the
ceremony. The seam is what matters: **when the project grows, services are
the amputation line** (extract to a worker, an API, a queue — callers
unchanged). *Assumption this design makes:* everyone enters through the
service. That's why it's machine-enforced — CI write-site gates census who
writes the money tables, import-linter walls the layers. Rules that only
live in docs die; these are executable.

## 6. How THIS project uses it

- ~30 service modules across 9 apps; **206 `transaction.atomic` sites**, all
  in services.
- The census-able registry: [PKM §7](../../../docs/PROJECT_KNOWLEDGE_MAP.md)
  chokepoint table — each row: sole writer of, who may call, invariant,
  what breaks if bypassed.
- Cross-service guards live in `_shared.py` helpers (e.g. the
  downstream-consumer reopen guard) — shared logic WITHOUT a second writer.
- Real repair story: RCP-1 certification found view-level writes that had
  crept in; they were extracted back into services and the goldens
  (₹344.25/₹801/₹633) proved byte-identical behavior after the move. That's
  the payoff: **you can relocate decisions safely when they live in one place.**

## 7. What breaks without it

Delete the layer and watch three months later: a management command
credits a worker without the era guard (double pay); a new view calls
`form.save()` and skips the permission re-check (worker edits a rate); a
signal "helpfully" logs history twice. Every one of these is a REAL class
of bug this architecture was built to make impossible.

## 8. Common mistakes (humans)

- Writing a "service" that's just `Model.objects.create` passthrough — the
  verb must own validation + boundary or it's noise.
- Calling one service from another WITHOUT checking lock-order implications.
- Returning querysets from services that views then mutate — decisions leak back.
- Forgetting the permission re-check because "the view already checked."

## 9. AI Implementation Pitfalls

- ❌ Writing model rows directly in a view/test/migration because "it's just one row" — the chokepoint exists for the guards, not the row count.
- ❌ Adding a signal for a side-write — ADR-0001; the repo has zero and CI reviewers hunt them.
- ❌ New money-write path outside approved single-writer services ⇒ **STOP + report** (owner standing rule), never silently proceed.
- ✅ Always verify: new write-sites appear in the chokepoint census; goldens unchanged.

## 10. DSA & Complexity

Not an algorithmic page — the one relevant note: services enable the
**O(1)-places-to-look** property. Debugging money = reading ONE function per
table, not grepping the codebase. That's a complexity win measured in
engineer-hours, the currency that actually matters here.

## 11. Interview corner

*Interview Signal: 🟠 Senior — where-does-logic-live is the senior judgment question.*

**Q. "Where do you put business logic in Django — models, views, or services?"**
- *Short:* Services own multi-row decisions; models own row-level invariants; views only parse/authorize/render.
- *Senior:* The question is really "what is your unit of correctness?" Ours is the business verb — it needs a transaction boundary, permission re-check, and a stable contract for many callers. Fat models break down when verbs span tables; fat views break down at the second caller.
- *Project example:* `finalize_adda_settlement` — 6 tables, 2 apps, one verb; RCP-1 extraction proved relocatability with byte-identical goldens.
- *Follow-ups:* "When is a signal acceptable?" (here: never for writes — cache invalidation-class things only, and even those are explicit) · "How do you ENFORCE it?" (CI write-site census + import-linter — rules must be executable).

## 12. 🧠 Remember This

View darwaza hai, service dimaag. Har business verb ka EK ghar, apna
transaction, apna permission check, apna contract. Signal = chupa darwaza,
isliye band. Aur rule wahi zinda rehta hai jise machine roz check karti hai.

## 13. 30-Second Revision

- Views parse · services decide · models store (rule 4)
- Service shape: keyword-only args · docstring contract · atomic · perm re-check · loud raise
- No signals (ADR-0001), no view multi-writes, no form.save on money
- 206 atomic sites, ~30 service modules, chokepoint census = PKM §7
- Services = the amputation line for future scale

## 14. What You Should Now Understand

Why every write path funnels through a named verb, what each of the five
service properties buys, why fat-models/fat-views fail at this project's
shape, and how the rule survives (machine enforcement). Shaky? Re-read §4–§6.

**Recommended next topic:** [single-writer discipline](single-writer.md) —
the service layer's sharpest special case.

## Implementation References

- Rule: [CLAUDE.md](../../../CLAUDE.md) rule 4 · ADR [0001](../../../docs/adr/0001-service-layer-owns-writes-no-signals.md)
- Census: [docs/PROJECT_KNOWLEDGE_MAP.md](../../../docs/PROJECT_KNOWLEDGE_MAP.md) §7 · deep dive [docs/LEARNING/04_SERVICE_LAYER.md](../../../docs/LEARNING/04_SERVICE_LAYER.md)

## Code References
- Exemplar code: `config/expense/services/` (read `advance_service.py` first — smallest complete specimen)

## Further Reading

- Official: [Django — Signals (know what you're banning)](https://docs.djangoproject.com/en/5.0/topics/signals/)
- One article: James Bennett, *"Against service layers in Django"* — read the OPPOSING view, then check which of his assumptions this project violates (multi-table verbs, many callers, money). Disagreeing well > agreeing blindly.

## Related

[single-writer](single-writer.md) · [transactions](../django/transactions.md) ·
[settlement](../../features/settlement.md) · [system-map](../../project/system-map.md)

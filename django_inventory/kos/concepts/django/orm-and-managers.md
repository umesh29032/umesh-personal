---
id: concept-orm-and-managers
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "What is a Manager really, and why does this repo add `Model.active` instead of filtering `objects` everywhere — or swapping the default?"
related: [concept-from-orm-to-sql, concept-query-performance, concept-service-layer]
---

# ORM & Managers — the tap the queries flow from

> 📂 [Django concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Master data here is never deleted — suppliers, stages, products get
`is_active=False` (soft-archive, [append-only](../database-design/append-only-tables.md)
thinking for master data). So EVERY dropdown and lookup must filter
archived rows… and every audit screen must NOT. Repeating
`.filter(is_active=True)` at 50 call sites = the 51st forgets. This repo's
answer is 14 characters: `Model.active` — a custom manager in `core`.

## 2. 💡 Samjho Aise

Manager = paani ka nal. `objects` = purana nal, sab kuch aata hai.
`active` = filter laga nal — wahi paani, chhanke. Ghar mein dono nal rakho:
peene ke liye filter wala, safai ke liye khula. Galti tab hoti hai jab
kisi ko pata hi na ho ki nal mein filter laga hai — isliye is repo mein
filter wala nal ALAG naam se hai, chupke se default nahi badla.

## 3. Mental Model

> A Manager is the **named entry point** into a table; a QuerySet is a
> lazy, chainable DESCRIPTION the manager hands you. Custom managers
> encode "which slice of this table does this codepath mean by default?"
> The design question is never "can I filter here?" — it's "should this
> default be visible or invisible to the reader?" Invisible defaults on
> the DEFAULT manager are how ORMs lie to you.

## 4. Technical Deep Dive

**The repo's implementation** (`config/core/models.py` — read the
docstring, it's the policy):

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

# usage on a master-data model:
#   objects = models.Manager()      # default stays honest — ALL rows
#   active  = ActiveManager()       # opt-in filtered tap
```

Its own docstring states the two design rules:
- *"Default `objects` ko swap NAHI karte (regression risk) — har model
  OPT-IN karta hai."* Swap the default and every `.objects` call in admin,
  shell, migrations, and third-party code silently loses rows — the
  worst class of ORM bug because nothing errors.
- Only on models that HAVE `is_active` — else `FieldError` (loud, good).

**What every Django developer must know about the machinery
(the parts this repo leans on):**

- **QuerySets are lazy** — build-up is free; the SQL fires at iteration
  ([from-orm-to-sql](../postgresql/from-orm-to-sql.md)). Chaining clones:
  `qs.filter(a).filter(b)` = one AND query, not two queries.
- **The first manager defined = default** (used by admin, dumpdata,
  related descriptors). Order of declaration is semantics.
- **Related managers inherit none of your custom filtering** —
  `adda.stage_records` uses the related model's DEFAULT manager. An
  `active`-style manager does NOT protect reverse accessors; that's
  another reason services own lookups ([service-layer](../architecture/service-layer.md)).
- **`update()` vs `save()`** — `qs.update(...)` is one SQL UPDATE:
  no model `save()`, no `auto_now`. This repo's chokepoint uses it
  deliberately: `c.save(update_fields=['settlement_line', 'updated_at'])`
  — narrow writes, explicit fields, `updated_at` consciously included.
- **`get_or_create` under concurrency** — two callers can both miss; the
  loser needs the unique constraint to bounce it. The repo pairs it with
  locks (WorkerProfile) — never bare on hot paths.

## 5. Engineering Thinking

*Why not default-manager filtering (the "SafeDeleteManager" pattern many
libraries ship)?* Because a default that hides rows changes the meaning of
EVERY existing call, including ones written before the manager existed —
retroactive semantics. The repo's opt-in `active` is grep-able: you can
census every place that CHOSE the filtered view. *Why not database views?*
A `WHERE is_active` view would hide the choice even deeper — same
invisibility, plus migration friction. *The general law:* **defaults must
be boring; sharpness must be named.** Same philosophy as `objects.create`
being banned on guarded tables — entry points carry meaning, so name them.
*Evolution:* if soft-archive ever needs per-user visibility (drafts,
tenants), the manager approach scales to `for_user(u)` QuerySet methods —
named, chainable, testable.

## 6. How THIS project uses it

The `active` pattern serves ~14 call sites (form dropdowns, service
lookups) while admin/audit read `objects` untouched. The discipline shows
up in reviews: a dropdown showing an archived supplier is a BUG with a
one-word fix (`objects` → `active`), and the census of who-uses-which is
one grep. Meanwhile the money tables go further — no manager tricks at
all: their entry point is a SERVICE, because "which rows" is a weaker
question there than "who may write" ([single-writer](../architecture/single-writer.md)).
Managers filter reads; services gate writes; the two tools don't compete.

## 7. What breaks without it

The 51st call site: an archived stage appears in a flow-editor dropdown,
someone attaches it to a product, and now production has a stage nobody
can staff. Soft-archive without a named filtered tap = archived data
leaking into live choices, one forgotten filter at a time.

## 8. Common mistakes (humans)

- Swapping the default manager to a filtering one (the classic) — silent
  row loss in admin/shell/related lookups.
- Assuming related accessors respect your custom manager — they don't.
- `len(qs)` when you meant `qs.count()` — fetches all rows to count them.
- Building "just in case" `.all()` copies — querysets are lazy; the copy
  is free but the ITERATION isn't; pass querysets, not lists.
- Putting business filtering in managers (e.g. `settleable()`) — that's a
  service question wearing a manager costume; keep managers to visibility
  slices.

## 9. AI Implementation Pitfalls

- ❌ Replacing `objects` with a filtered default "for safety" — regression
  risk is the documented reason it's forbidden here.
- ❌ Adding `ActiveManager` to a model without `is_active` — FieldError at
  first use (by design; don't "fix" by adding the field speculatively).
- ❌ Using `Model.active` inside audit/history/reconciliation code — those
  must see EVERYTHING; archived ≠ nonexistent.
- ❌ `qs.update()` on guarded tables to dodge service guards — the
  single-writer census treats it as a write-site.
- ✅ Always verify: dropdown/service lookups use `active`; audit surfaces
  use `objects`; one grep confirms the split.

## 10. DSA & Complexity

A chained queryset is a **persistent immutable builder** — each `.filter()`
clones the description (cheap, O(size-of-AST)), and evaluation compiles it
once to SQL. That's why passing querysets around is free and why
`|`/`&` composition works: you're composing predicate trees, not row sets.
Rows only exist at iteration — the whole API is call-by-need.

## 11. Interview corner

*Interview Signal: 🟡 Mid — ORM/manager depth is the mid-level staple.*

**Q. "How would you implement soft delete in Django?"**
- *Short:* `is_active` flag + an opt-in filtered manager (`Model.active`); keep the default manager honest; archive = flag flip, audit sees all.
- *Senior:* The hard part isn't the flag — it's default semantics. A filtering DEFAULT manager silently rewrites every existing call and doesn't protect related accessors anyway, so name the filtered view and census its adoption. Separate visibility (manager) from write-authority (service). And decide upfront who must ALWAYS see archived rows: audit, history, reconciliation.
- *Project example:* `core.ActiveManager`, opt-in on master data, default untouched (docstring documents the regression-risk reasoning); money tables skip manager games entirely — service-gated instead.
- *Follow-ups:* "Why do related accessors ignore custom managers?" (they use the related model's default; `base_manager_name` exists but deepens the invisibility) · "Soft-delete FK integrity?" (PROTECT still fires — archived parents keep children safe) · "When is hard delete OK here?" (drafts that never carried truth — `discard_draft`).

## 12. 🧠 Remember This

Manager = naam wala nal, QuerySet = lazy farmaish. Default nal ko kabhi
mat chhedo — filter wala nal ALAG naam se lagao (`active`), aur yaad rakho
reverse-accessor tumhara filter nahi jaanta. Padhna manager chhaante,
likhna service rokta hai — do alag pehredaar.

## 13. 30-Second Revision

- Manager = entry point; first-declared = default (admin/related use it)
- Repo law: never swap default; `active = ActiveManager()` opt-in, ~14 sites
- Related accessors use the related model's DEFAULT manager — always
- Lazy + clone-on-chain; SQL at iteration; pass querysets freely
- update()/update_fields = narrow explicit writes (chokepoint stamp pattern)
- Managers slice READS; services gate WRITES

## 14. What You Should Now Understand

What managers/querysets actually are, why opt-in beats default-swap, where
manager filtering CAN'T protect you (related accessors), and the
manager-vs-service division of labor. Shaky? Read `core/models.py`'s
docstring — the policy in 10 lines.

**Recommended next topic:** [django/migrations](migrations.md) — how this
schema evolves without ever betraying the data.

## Implementation References

- Pattern memo: ActiveManager pattern (14 call sites) — repo memory + grep `\.active\.`

## Code References
- `config/core/models.py` (`ActiveManager` + docstring) · narrow-write exemplar: `adda_settlement_service` provenance stamp

## Further Reading

- Official: [Django — Managers](https://docs.djangoproject.com/en/5.0/topics/db/managers/) · [QuerySets are lazy](https://docs.djangoproject.com/en/5.0/topics/db/queries/#querysets-are-lazy)

## Related

[from-orm-to-sql](../postgresql/from-orm-to-sql.md) · [service-layer](../architecture/service-layer.md) ·
[single-writer](../architecture/single-writer.md) · [query-performance](../postgresql/query-performance.md)

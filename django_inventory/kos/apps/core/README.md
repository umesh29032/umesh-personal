---
id: app-core
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does this project FEEL the way it does? — core is 89 lines of code and the entire engineering philosophy."
related: [project-system-map, concept-single-writer, concept-two-truths]
---

# core — the architectural conclusion

> 📂 [Apps](../README.md) · [LOS home](../../README.md) — *andar:
> [URLs](urls.md) · [Views](views.md) · [Models](models.md) · [Services](services.md)*
> **This app's engineering lesson: THE FRAMEWORK ITSELF** — shared
> abstractions, dependency direction, composition, and why every other
> chapter of this LOS rhymes.

## Mental Model — read this before anything

> **The grammar of a language.** Core doesn't say anything itself — it
> defines how everything else speaks: every sentence gets a timestamp
> (TimeStampedModel), every archive keeps its books visible (ActiveManager),
> every memory is written the same way (AbstractHistoryEntry), and the
> grammar police are AUTOMATED (the purity tests). You never visit the
> grammar; you feel it in every sentence. *(Vyakaran dikhta nahi — har
> vaakya mein sunai deta hai.)*

## Why does this project feel the way it does?

Nine apps, one recurring sensation: refusals that teach, numbers that
recompute, history that never lies, rules that machines enforce. That
feeling is FIVE VALUES applied without exception:

1. **Provability over convenience.** Any figure re-derives from raw rows
   years later (ledgers, snapshots, goldens). Convenience that costs
   provability is refused — the "just edit it" requests die here.
2. **Loud over silent.** Missing config crashes boot; bad data hits a
   CHECK; guards refuse with sentences that NAME the fix. Silence is the
   only forbidden failure mode.
3. **One pen per book.** Single-writer everywhere — money, history, tasks,
   pools, possession. Global correctness became local review, and that's
   why one person can hold this system.
4. **Evidence over state.** Events + folds instead of mutable flags:
   ledger, windows, timelines, streams. State is a claim; rows are proof.
5. **Rules are executable or they're dead.** import-linter contracts,
   CI write-site censuses, purity tests, navigation guards, 1,878 pins —
   every law you've met in this LOS is ENFORCED by a machine, and core
   hosts the enforcers ([services.md](services.md)).

Everything else — two truths, the service layer, frozen snapshots,
config-over-code, honest absences — is these five values meeting a
specific problem. *(Project ka swabhav = paanch usool, bina exception.)*

## Common Misconceptions

- **"core is a utils dump."** 89 lines, four abstractions, ZERO tables —
  the opposite of a dump: a jealously guarded floor. Things earn their way
  in by being universal, not by being homeless.
- **"Dependency direction is a diagram."** It's a TEST —
  `FoundationPurityTests` fails the build if core imports anything
  domain-specific. The arrow points one way because CI says so.
- **"Cross-cutting concerns live in core."** Split deliberately: core
  holds model-layer cross-cuts; request-layer cross-cuts live where
  requests live (inventory's middleware); settings-layer in config/. Each
  concern sits at ITS layer.
- **"No URLs means no importance."** core's absence of surface IS its
  design — foundations don't have doors.

## Real Engineering Questions

**PM: "Add a shared helper — where does it go?"**
The core test: is it universal AND dependency-free? Both → core (rare;
the bar is the point). Domain-flavored → the owning app's `_shared`/utils.
Request-flavored → middleware/context processor. When in doubt: NOT core —
the floor stays small because everything leans on it.

**"Why do all nine apps look alike?"**
Composition: every app = urls → gated views → service verbs → models on
core's bases → history via tracking's pen. The sameness is inherited
grammar ([system-map](../../project/system-map.md) request lifecycle) —
and it's why the LOS's frozen template FIT all nine.

**"Where's the transaction philosophy WRITTEN?"**
In grammar, not core code: verbs own boundaries
([transactions](../../concepts/django/transactions.md)), atomic lives on
services (206 sites), on_commit for side effects, locks in documented
orders. Core's contribution: making models cheap enough (timestamps,
histories) that verbs stay about BUSINESS.

## Reading Strategy

- **Beginner:** Mental Model → [models.md](models.md) (the four
  abstractions — 89 lines, read them ALL tonight).
- **Intermediate:** [services.md](services.md) (the enforcement suites) →
  the five values above, checked against any app you know.
- **Senior:** this README as the closing argument of the
  [engineering-journey](../../project/engineering-journey.md) — then
  re-read [two-truths](../../concepts/architecture/two-truths.md) and
  watch the values underneath it.

## Start Here — common tasks

| Need to… | Go to |
|---|---|
| Use the shared bases | [models.md](models.md) — TimeStampedModel · ActiveManager · AbstractHistoryEntry · FieldChangeMixin |
| Add something to core | the REQ above — the bar is deliberately brutal |
| Understand the layering rules | [services.md](services.md) purity tests + `config/.importlinter` |
| Observability hooks | `config/core/observability.py` + its tests |
| The request lifecycle | [system-map](../../project/system-map.md) (canonical) |

## What this app owns

The four model-layer abstractions · the enforcement suites (purity,
doc-accuracy, LOS/PKALS navigation guards, observability, media serving)
· observability plumbing. **Zero tables. Zero URLs. Zero views.**

## What it does NOT own

Any business noun · request-layer cross-cuts (inventory) · settings
(config/) · the history PEN (tracking — core only defines the SHAPE).

## The census

- **Code:** `models.py` 89 lines (4 classes) · `observability.py` · templatetags
- **Tests:** 5 suites in `tests.py` — the constitution's police ([services.md](services.md))
- **URLs/Views/Tables: 0 / 0 / 0** — by design

## The laws to carry in

1. Core imports NOTHING domain-specific — enforced by test, forever.
2. Abstractions enter core only when universal + dependency-free.
3. The bases are opt-in and honest (ActiveManager never swaps the default).

## Engineering Checklist — pre-flight

- [ ] Does the addition import from ANY app? → it doesn't belong here
- [ ] Is it needed by 3+ apps TODAY? (rule-of-3, the floor's version)
- [ ] Purity + doc-accuracy suites green after ANY core change
- [ ] kos-sync: this chapter + [system-map](../../project/system-map.md)

## Change Impact — touching this app affects

**Every model in every app** (the bases) · every build (the enforcement
suites) · the LOS itself (navigation guards protect kos/docs routing
files). Smallest-diff discipline applies doubly here.

## Learning Graph

**Before:** everything — this is the LAST chapter; the journey's other 113
pages are its evidence. **After:** [engineering-journey](../../project/engineering-journey.md)'s
graduation question — you're ready for it now.

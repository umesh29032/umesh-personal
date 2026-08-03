---
id: readme-debugging
type: system
verified: 2026-07-19
---

# Debugging — playbooks for real incidents

*(Part of the [KOS](../README.md).)*

## Teacher's note

Production problems arrive as SYMPTOMS, never as file names — nobody
searches "transaction.atomic" at 11 PM; they search *"paisa galat kyun
dikh raha hai."* So every playbook here starts from the symptom and walks
you to root cause: **First Five Minutes** (how a senior THINKS before
touching anything) → decision tree → concrete checks → known real causes
from this repo's own history → the concept pages that explain why. No
invented bugs — every "known cause" actually happened here.

| Playbook | Symptoms it covers | Signal |
|---|---|---|
| [money-looks-wrong.md](money-looks-wrong.md) | balance/settlement/payroll numbers off; screens disagree | the one you'll use most |
| [counts-mismatch.md](counts-mismatch.md) | piece counts differ across stages/screens; reported vs shown | five numbers, five meanings |
| [access-denied-or-invisible.md](access-denied-or-invisible.md) | 403s, missing menus, invisible stages, OR seeing too much | four walls, four signatures |
| [page-slow-or-erroring.md](page-slow-or-erroring.md) | slow pages, 500s, deadlocks, works-locally-not-prod | slow ≠ erroring — different lanes |

## The universal habits (before any playbook)

1. **Reproduce as the right USER** — half of all bugs are identity confusion.
2. **Never trust a screen** — recompute from the source (ledger, APSCPB, the predicate).
3. **Refusals are features** — read the error text; this repo's errors name
   their fix *(yahan ki galti-message hamesha agla kadam batati hai)*.
4. Unknown URL? → [request-through-stack](../flows/request-through-stack.md)
   debug recipe. Unknown territory? → [reading-the-docs](../project/reading-the-docs.md).

**After every real incident:** if a playbook was missing a branch, ADD it
(Law 6 — rewrite freely). The playbooks grow from incidents, not planning.

---
id: app-core-services
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "core has no business services — its 'services' are the five enforcement suites that police the whole architecture."
related: [app-core, concept-testing-strategy]
---

# core — service knowledge (the constitution's police)

> 📂 [core app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> No service verbs — core acts at BUILD time. `tests.py` hosts five suites
> that make the architecture's laws executable:

> 💡 **Samjho aise** — Services = **counter ke peeche baitha clerk**
>
> **Asli kaam yahin hota hai** — database mein likhna, hisaab lagana, rules lagana. Is project ka sabse bada niyam: *har likhne ka kaam service mein hoga, view mein kabhi nahi*. Isi wajah se paisa surakshit rehta hai — har table ka **ek hi** likhne wala hota hai.
>
> *(`core` app ka kaam: saara project jo cheezein baar-baar use karta hai (jaise har table ka created_at/updated_at) — iska apna koi table nahi.)*

| Suite (line) | Enforces |
|---|---|
| `FoundationPurityTests` (47) | **dependency direction**: core imports nothing domain-specific — the one-way arrow as a failing build, not a diagram |
| `DocAccuracyTests` (69) | documentation claims that MUST stay true (drift = red build — the docs-sync philosophy with teeth) |
| `PkalsNavigationGuardTests` (156) | the knowledge-routing files' paths stay valid (canonical_manifest etc.) — the LOS/docs bridge can't silently rot |
| `ObservabilityTests` (318) | the logging/metrics plumbing behaves |
| `MediaServingTests` (338) | private-media-through-views stays gated |

**The doctrine (say it once, it explains the repo):** *a rule that only
lives in prose is a suggestion; every law in this system has a machine
that fails when the law breaks.* Import boundaries → import-linter
(`config/.importlinter`, 109 lines) + purity tests. Write ownership → CI
censuses. Money math → goldens. Refusals → pins. Navigation → guards.
The LOS could FREEZE its template because the system underneath enforces
its own shape.

**Plus `observability.py`** — the logging/metrics cross-cut at the infra
layer (its request-layer sibling lives in inventory; its money-layer
sibling is the ledger's own logger lines).

## Adding/changing here — the checklist

A new LAW deserves a new ENFORCER (test/linter/census) — prose alone is
debt · purity suite green after any core diff · never weaken a guard to
merge faster (the guard IS the merge review).

## Required Knowledge (this page)

- [ ] Pins-not-hopes → [testing-strategy](../../concepts/testing/testing-strategy.md)
- [ ] The layered enforcement census → [single-writer §4](../../concepts/architecture/single-writer.md)

## Learning Graph

**Before:** [models.md](models.md). **After:** you've finished the ninth
app — return to [README](README.md)'s five values, then the
[engineering-journey](../../project/engineering-journey.md) graduation
question. The LOS's argument is complete.

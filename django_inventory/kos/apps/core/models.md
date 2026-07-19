---
id: app-core-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "The four abstractions every table inherits — 89 lines that shape hundreds."
related: [app-core, concept-orm-and-managers]
---

# core — model knowledge (`models.py`, 89 lines · 4 classes · 0 tables)

> 📂 [core app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> All abstract — core creates NO tables; it creates SHAPE.

## `TimeStampedModel` (line 18)

`created_at` / `updated_at` on effectively every table in the system.
One decision, made once: **time is not optional metadata** — stalled-Adda
detection, auto durations (owner rule), history ordering, debugging all
lean on it. The cheapest universal abstraction in the repo.

## `ActiveManager` (36)

The soft-archive tap — `Model.active` filters `is_active=True`, OPT-IN,
never swapping the default (the docstring states the regression-risk
reasoning). Full teaching: [orm-and-managers](../../concepts/django/orm-and-managers.md)
(this class is that page's specimen). Grammar note: core DEFINES the
manager; each master model CHOOSES it — shared abstraction without imposed
behavior.

## `AbstractHistoryEntry` (55)

The SHAPE of memory: actor + change_type + timestamp base every `*History`
table extends (tracking's three). Core defines the grammar of history;
tracking holds the PEN (`history_service`); domains own their subjects —
three apps, one concern, each at its layer.

## `FieldChangeMixin` (77)

Old→new field-diff capability for history rows (roll/product histories
use it). Change AS DATA, standardized once.

## The composition lesson

Every concrete model in nine apps = business fields + these bases. That's
application composition in practice: apps compose foundation grammar +
domain nouns + service verbs — which is why a new app in this repo is
mostly BUSINESS thinking ([configuration-over-code](../../concepts/patterns/configuration-over-code.md)
at the architecture scale).

## Required Knowledge (this page)

- [ ] Abstract models / inheritance → Django docs via [orm-and-managers](../../concepts/django/orm-and-managers.md)
- [ ] Why no tables here → README's floor doctrine

## Learning Graph

**Before:** README. **After:** [services.md](services.md) — the police
that keep these 89 lines pure.

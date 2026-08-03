---
id: readme-concepts-architecture
type: system
verified: 2026-07-19
---

# Architecture — the three decisions everything follows

*(Part of [Concepts](../README.md) → the [KOS](../../README.md).)*

## Teacher's note

Strip this system to three decisions: every write goes through a named service verb; every critical table has one pen; work-truth and money-truth are different physics joined at one gate. Every other pattern in the repo is a consequence. Learn WHY each was chosen over its alternatives and you can defend (or correctly attack) any architecture in an interview. *(Architecture ratta nahi — faisla + thukraye hue vikalp + wajah.)*

| Page | Real question it answers |
|---|---|
| [service-layer.md](service-layer.md) | Why do all writes go through service functions? |
| [single-writer.md](single-writer.md) | Why exactly ONE service per money table — and how is it ENFORCED? |
| [two-truths.md](two-truths.md) | Why can't 'work happened' and 'money owed' be one fact? |

**After this folder you can:** explain this system's shape from first principles, and reason about boundaries by change-physics instead of topic.

*Read order: service-layer → single-writer → two-truths (the deepest page in the KOS).*

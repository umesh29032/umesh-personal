---
id: app-core-readme
type: app-readme
status: active
owner: handwritten
scope: core
anchors: config/core/
verified: 2026-07-13
---

# `core` app — Shared Foundations (no tables)

> The bottom of the import pyramid. Foundation-purity is CI-enforced
> (gate [1/4]: core + accounts import NO domain app).

## Purpose

Abstract building blocks every domain app inherits — nothing domain-specific.

## Contents

| Piece | What | Why |
|---|---|---|
| `TimeStampedModel` | abstract `created_at`/`updated_at` (auto_now_add / auto_now) | har row ka janm + last-touch time, ek hi jagah define |
| `ActiveManager` | `.active` manager (`is_active=True`) | soft-delete pattern: masters kabhi DELETE nahi hote, deactivate hote hain; default `.objects` untouched so nothing hides accidentally |
| `observability.py` | logging helpers | shared infra |

## What tables: none (abstract = fields copied INTO each child's table).

## Django Learning Notes

- **Abstract base models**: `class Meta: abstract=True` — inheritance copies
  columns into children; no JOIN, no extra table.
- **Non-default managers**: `.active` opt-in keeps queries explicit —
  14 call-sites chose it deliberately (2026-05-29); a default override would
  have silently hidden rows everywhere.
- **Import-linter contract**: architecture as CI — the dependency direction
  is a TEST, not a convention.

## Common mistake

Putting anything domain-flavored here. If it knows what an Adda is, it does
not belong in core.

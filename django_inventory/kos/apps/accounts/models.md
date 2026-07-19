---
id: app-accounts-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "accounts' models — identity, Role, SidebarItemRule, skills: who writes, who consumes, what's sacred?"
related: [app-accounts, app-inventory-models]
---

# accounts — model knowledge (`config/accounts/models.py`)

> 📂 [accounts app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## Identity

**User (custom user domain)** — email-first identity; role FK; skills M2M;
Argon2-hashed credentials (hashers config in settings). Created ONLY via
superuser CRUD (S2). Deletion guarded by PROTECT anchors everywhere
(money/history) — deactivate over delete.

## Authorization custody (relocated HERE 2026-06)

**`Role`** — THE role source of truth (FK on user). Role SETS
(MANAGEMENT_ROLES etc.) live as code in `permission_service` — a role
gains powers via reviewed code, not row edits.

**`SidebarItemRule` (line ~260)** — one row per managed url_name: the
roles/skills that SEE the menu item AND may HIT the URL. Written by
inventory's sidebar_service (the editor lives there); read by the
middleware + context processor on every request.
Custody story + the shim: [inventory models.md](../inventory/models.md) —
the relocation is the repo's cleanest layering lesson.

## Capability masters

**Skill** — production-stage capability tokens (`skills.py` helpers);
consumed by production's access_service (access ∩ assignment).
**UserType** — classification rows (configuration-over-code).

## Cross-model laws

Foundation depends on NOTHING domain-specific (that's WHY custody moved
here) · identity anchors are PROTECTed system-wide · policy rows are read
hot on every request — keep them lean.

## Required Knowledge (this page)

- [ ] Three-concept model → [people-and-roles](../../project/people-and-roles.md)
- [ ] The custody/relocation lesson → [inventory models.md](../inventory/models.md)

## Learning Graph

**Before:** README. **After:** [services.md](services.md) — the brain that
turns these rows into every gate's answer.

# ADR 0003 — Three-concept RBAC; stages skill-gated; menu + URL co-gated

**Status:** Accepted (CLAUDE.md rule #6)

## Context
"What a user is" (a label), "what modules they may access", and "what factory work they can
perform" are three different questions. Collapsing them into one field (the old `user_type`
Char choices) made access logic ambiguous and un-auditable.

## Decision
Three orthogonal concepts, all on `accounts`:
- **`UserType`** — display label only; **never** gates access.
- **`Role`** (+ `extra_roles`) — the RBAC grant. `permission_service.user_has_perm` order:
  authenticated → `is_superuser` → `role.code == super_admin` → role permission codename →
  Django fallback. Roles: `super_admin`, `manager`, `worker` (renamed from `karigar`),
  `accountant`, `listing_team`.
- **`Skill`** — production capability. **Stage access is skill-gated**, data-driven via
  `access_service.user_can_access_stage` (reads `Stage.access_by_skill`/`access_by_role`)
  with super_admin + manager hardcoded bypass and fail-closed on a missing/inactive Stage.
  The same gate guards both the stage **view** and the **mutation** services.
- **Menu + URL are gated together**: `SidebarItemRule` decides menu visibility, and
  `SidebarAccessMiddleware` enforces the *same* rule at the URL layer — hiding a menu item
  also blocks its route. Items with no DB rule fall back to in-code predicates (new features
  are never silently hidden). RBAC reads are request-cached on the `user` instance.

## Consequences
- RBAC models + `permission_service` were relocated `inventory → accounts` (2026-06);
  `inventory.{models,services}` are re-export shims. `inventory` owns no domain tables.
- Adding a stage's access = data (Stage M2Ms), not code.
- Object-level "Assignment" (worker sees only their assigned Adda) is enforced via
  `WorkerStageTask` membership — see [ADR 0005](0005-production-truth-vs-financial-truth-option-b.md).

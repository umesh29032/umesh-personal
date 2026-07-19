---
id: debug-access-denied
type: debugging
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Someone can't see a page/stage/button — or sees one they shouldn't. Which of the four walls fired?"
related: [feature-rbac-access, project-people-and-roles]
---

# Playbook: "Dikh kyun nahi raha / dikhna nahi chahiye tha"

> 📂 [Debugging](README.md) · [LOS home](../README.md)

## Symptoms this playbook covers

- 403 / 302-to-login on a URL the user "should" reach
- Menu item missing for a role
- Worker can't see a stage they work on
- A user sees data/buttons meant for another role (the SCARY direction)
- Accountant blocked from a financial page

## First Five Minutes

1. **Establish WHO, exactly:** role (super_admin/manager/worker/accountant
   — composite?) + skills + assignments. Most tickets die here — the user
   isn't who the reporter assumed. *(Pehle pehchaan, phir jaanch.)*
2. **Which wall answered?** The response tells you: menu missing = sidebar
   rule · 302/403 on URL = SAME sidebar rule (paired!) or view gate ·
   form saved but field ignored = form-strip wall · write refused with
   message = service re-gate. Four walls, four signatures.
3. **Stage visibility is a different axis:** stage screens = skill ∩
   assignment (`access_service` + WST roster) — NOT the sidebar system.
4. **Run the universal recipe** ([request-through-stack](../flows/request-through-stack.md)):
   URLConf row → sidebar rule → view gate → service gate. In order, stop at
   the first NO.
5. **Wrong-direction leak (sees too much)?** Treat as security incident:
   which wall SHOULD have fired? Certifications prove all four held — a
   real leak means a NEW path bypassed them (the S2/S3 class).

## Decision tree

```
Can't reach a URL?
├─ menu also missing        → SidebarItemRule for that URL × role
│                             (one row = both effects; edit the rule, both fix)
├─ menu visible, URL 403    → SHOULD BE IMPOSSIBLE (paired rule) —
│                             a view-level gate beyond the rule? or a NEW
│                             unpaired gate someone added = the drift bug
├─ page ok, action refused  → service re-gate (_ensure_management etc.) —
│                             correct behavior; fix the ROLE, never the service
Can't see a stage?
├─ has the skill?           → Stage library access rules
├─ on the roster?           → WST exists? (manager assignment = ONLY source;
│                             un-assign = CANCELLED task, screen gone)
└─ both yes, still hidden   → the ONE predicate (access ∩ assignment) —
                              if ANY surface disagrees with another surface,
                              someone added a second predicate = frozen-rule violation
Sees too much?
└─ SECURITY LANE: which wall should have fired? new route/field writer
   without the guard set? → S2/S3 pattern; pin the refusal after fixing
```

## Which checks, concretely

| Check | How |
|---|---|
| Role reality | user's Role FK + composite add-ons (accountant = ADD-ON; pure accountant is dispatch-blocked from rm pages BY DESIGN) |
| The pair | SidebarItemRule row for the URL — menu hidden ⇒ URL blocked, one row |
| Stage predicate | `access_service.user_can_access_stage` + `stage_access_map` — the same call every surface uses |
| Financial fields | FINANCIAL_ROLES only; form-strip + service re-gate proven (OFF-C) |
| History strips | workers never see financial CHANGE rows — wall #4 |

## Known real causes

- **"Manager can't add rolls/products"** — correct: SuperAdmin-only since the
  master-data lockdown (MGT-A). Not a bug.
- **Worker lost a stage mid-day** — roster change: their WST got CANCELLED
  with a note (read it).
- **Composite accountant confusion** — capability shows only where a
  page-role admits them; pure vs composite lanes differ by design (OFF-A D1).
- **The real findings:** S2 (open signup) and S3 (email shadow-route) — the
  template for what a REAL wall-bypass looks like; both closed + pinned.

## Where to learn the concepts

[rbac-access](../features/rbac-access.md) (the machinery) ·
[people-and-roles](../project/people-and-roles.md) (the model) ·
[auth-hardening](../concepts/security/auth-hardening.md) (the front door)

## Implementation References

- Canonical walls: [docs/production/RBAC.md](../../docs/production/RBAC.md) · certified matrices: [WORKER](../../docs/WORKER_ROLE_CERTIFICATION.md) / [MANAGEMENT](../../docs/MANAGEMENT_ROLE_CERTIFICATION.md) / [OFFICE_SUPPORT](../../docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md)

## Code References

- `inventory/middleware.py` (the pair) · `accounts/services/permission_service.py` · `production/services/access_service.py`
- Tests already covering: certification suites + sidebar middleware tests — a fix without a new pin isn't done

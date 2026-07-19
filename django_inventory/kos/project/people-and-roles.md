---
id: project-people-and-roles
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Who can see and do what — and how does the system actually enforce it?"
related: [project-system-map, project-business-story]
---

# People & Roles — who may do what, and the walls that enforce it

> 📂 [Project — the WHY layer](README.md) · [KOS home](../README.md)

## Business Purpose

A factory floor has clear social rules: workers don't see each other's pay,
managers don't change master prices, only the owner touches product
definitions. The software encodes those rules as **three separate concepts**
that must never be conflated:

1. **Role** — who you are in the company (super_admin, manager, worker,
   accountant, listing_team).
2. **Skill** — what production stages you can work (stage access is
   SKILL-gated, not role-gated — a worker with "cutting" skill sees cutting).
3. **Sidebar rule** — which menu items (AND their URLs) exist for you.

## 💡 Samjho Aise

Shaadi ka ghar samjho. **Role** = rishta (ghar ka malik, bhai, mehmaan).
**Skill** = hunar (khana banana aata hai to rasoi mein entry). **Sidebar
rule** = kis kamre ka darwaza tumhe dikhta hi hai. Aur sabse zaroori baat:
darwaza chhupa diya to *deewar bhi bandh* — sirf menu hide karna kaafi
nahi, URL bhi wahi rule block karta hai.

## Technical Deep Dive

**Role sets** (`accounts/services/permission_service.py` — no raw
`is_superuser` anywhere, house rule 6):

```python
ADMIN_ROLES      = {super_admin}
MANAGEMENT_ROLES = {super_admin, manager}
FINANCIAL_ROLES  = {super_admin, accountant}   # supplier / cost-per-kg
PRODUCTION_ROLES = {super_admin, manager, worker}
```

**What each role can do** (from the CERTIFIED gate matrix, 2026-07-13):

| Role | Sees | Can | Cannot |
|---|---|---|---|
| `super_admin` | everything | product CRUD, roll bulk-add (both SA-only), settle, override (audited) | — |
| `manager` | operations | Adda CRUD, stage advance, assign workers, verify quantities | product CRUD, roll bulk-add, financial masters (hidden + service re-gated) |
| `worker` | own work only | report own assigned stage work (phone), see own Expected→Earned→Paid | ALL management pages (sidebar = Main only; URLs 302/403 — certified across 9 apps) |
| `accountant` | add-on capability | view+edit supplier / cost-per-kg where a page-role admits | pure accountant is dispatch-blocked from rm pages BY DESIGN |

**The four walls** (layered defense — any one can fail and money stays safe):

```
1. TEMPLATE   — field/menu hidden (worker never sees the button)
2. FORM       — fields the user can't edit are STRIPPED server-side
3. SERVICE    — re-checks permission at the write (the wall that matters)
4. HISTORY    — financial CHANGE rows stripped from what workers can read
   + SidebarAccessMiddleware: menu hidden ⇒ URL BLOCKED (one rule, both effects)
```

**Stage access is a separate axis:** `access_service.user_can_access_stage`
— skills decide which production stages you can even open; **manager
assignment is the ONLY roster source** (PDD amendment 4). Visibility on a
stage = access ∩ assignment — ONE live predicate, everywhere.

**Auth hardening** (accounts app): Argon2 hashing, per-IP+email login rate
limiting, self-lockout protection, closed public signup (S2), email-takeover
shadow-route closed (S3) — all certified + pinned by tests.

## 🧠 Remember This

Teen alag cheezein: **role (kaun ho) · skill (kya kar sakte ho) · sidebar
(kya dikhta hai).** Chaar deewarein: template → form → service → history,
aur menu chhupa = URL bandh. Asli security service wali deewar hai — baaki
teen sirf tameez hain. Worker sirf apna kaam, apna paisa dekhta hai — yeh
poore 9 apps mein certified hai.

## Implementation References

- Canonical: [docs/production/RBAC.md](../../docs/production/RBAC.md) (roles, walls, visibility law)
- Certifications: [docs/WORKER_ROLE_CERTIFICATION.md](../../docs/WORKER_ROLE_CERTIFICATION.md) · [docs/MANAGEMENT_ROLE_CERTIFICATION.md](../../docs/MANAGEMENT_ROLE_CERTIFICATION.md) · [docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md](../../docs/OFFICE_SUPPORT_ROLE_CERTIFICATION.md)
- ADR: [0003 three-concept RBAC](../../docs/adr/0003-three-concept-rbac-skill-gated-stages.md)

## Code References
- `config/accounts/services/permission_service.py` · `config/inventory/middleware.py` · `config/production/services/access_service.py`


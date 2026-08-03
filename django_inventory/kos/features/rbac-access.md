---
id: feature-rbac-access
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "When a worker opens the app, WHAT decides exactly which stages, pages, and buttons they see — mechanically?"
related: [project-people-and-roles, feature-stage-tracking, project-system-map]
---

# Access Control in Action — the machinery behind "you can't see that"

> 📂 [Features](README.md) · [LOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

[people-and-roles](../project/people-and-roles.md) explains the MODEL
(role · skill · sidebar — three concepts, four walls). This page is the
FEATURE view: the actual machinery that fires on every request, and the one
law that keeps it honest: **what decides visibility also decides access —
one predicate, never two.**

## Mental Model

> Access bugs are almost never missing checks — they're **two checks that
> drift**. A menu test here, a URL test there; a template `if` here, a view
> gate there. This system's answer: pair every hide with its block in ONE
> rule object, and compute stage visibility with ONE shared function that
> every surface calls.

## 💡 Samjho Aise

Shaadi mein bouncer aur guest-list. Galat design: gate par ek list,
buffet par doosri — koi gate se ghusa nahi par buffet par khada hai. Sahi
design: EK hi list, har jagah wahi padhi jaati hai. Yahan wahi hai —
`SidebarItemRule` ek list hai jo menu BHI hai aur URL-block BHI.

## Technical Deep Dive

**Layer 1 — the paired gate:** `SidebarItemRule` rows define menu items;
`inventory.middleware.SidebarAccessMiddleware` enforces them on every
request — **menu hidden ⇒ URL blocked, same row.** Sidebar edits are
access-control edits, by construction. (This is why the repo has no
"hidden but reachable" class of bug — the pair can't drift.)

**Layer 2 — role gates in views/services:** `permission_service.user_has_role`
/ `user_has_perm` (never raw `is_superuser` — house rule 6). Services
re-check at the write: `_ensure_management` in every money service is wall
#3 doing its job even if a view forgot.

**Layer 3 — stage access is SKILL-gated:**
`access_service.user_can_access_stage(user, stage_code)` — the Stage
library holds required skills/roles; a worker with the cutting skill can
open cutting stages. Bulk variant `stage_access_map` powers stage lists
without N queries; `eligible_stage_workers(stage_code)` feeds the manager's
roster picker with exactly-those-who-may.

**Layer 4 — the ONE visibility predicate (frozen foundation rule):**
what a worker SEES on a stage = **access ∩ assignment** — skill says "may
work this kind of stage", manager assignment says "works THIS stage".
Every surface (stage list, panel, report screen) computes it via the same
service call. RBAC.md's "Visibility vs Action" section is the canonical
statement; the certifications prove it held across 9 apps (worker
meta-audit: mgmt URLs 302/403 everywhere, universal walls).

**The proof culture:** role behavior isn't asserted, it's CERTIFIED —
per-role × per-app matrices, browser-proven CSRF-valid POST probes,
dual-identity sweeps (WORKER/MANAGEMENT/OFFICE_SUPPORT certifications).
Real finding class it caught: S2 (public signup created live users) and
S3 (email-takeover shadow-route) — both closed + pinned.

## Three tiers, not two (accountant READ TIER, 2026-08-02)

**One idea first:** this system used to know only **management** and **everyone else**.
So an accountant — who is neither a manager nor a worker — fell into "everyone else" and
got the **worker** experience: a dashboard saying *"Jab manager aapko kaam dega"* and an
earnings page reading *"Pieces Produced 0"*. An accountant never produces pieces.

**💡 Samjho aise:** accountant **munshi** hai. Bahi-khata *dekhta* hai, kharcha *likhta*
hai — par **tankhwah baantne ka faisla malik ka**. Dekhna ek cheez, dene ka faisla doosri.
Pehle system ke paas sirf do darwaze the: malik ka, ya mazdoor ka. Munshi ke liye koi
darwaza hi nahi tha. Ab teesra darwaza hai — **padho sab, likho sirf kharcha**.

| Tier | Who | What |
|---|---|---|
| **Floor** | worker | own assigned stage + own earnings |
| **Books (new)** | accountant | **read** all financials · **record** a cost · nothing else |
| **Management** | manager · super admin | everything, incl. settlement |

**The rule that keeps it safe: reads widened, writes did not move.**

An accountant can **add** a cost record but never **erase** one — `void_expense` is
super-admin-only *inside the service*, not just in the view. That is append-only
bookkeeping: corrections belong to the owner.

### The subtle bug this exposed (worth remembering)

`generate_monthly_expenses` is **two functions behind one name**:

- `confirm=False` → returns the plan, **writes nothing** (a preview)
- `confirm=True` → creates the rows

Both were gated as a write. So the recurring-expenses **register** — a read page that
renders per-template status *from that preview* — returned **403** for an accountant.

> **Gate on what a call WRITES, not on what it is named.** Same lesson as the sidebar:
> a rule that fires on the safe operation teaches people to ignore it.

### Where the switch lives

Access Control → **Sidebar Access**. Any menu item with a `SidebarItemRule` row is
governed by the **DB**, and the DB **overrides** the in-code predicate — which is why
widening `Cloth Rolls` in code was not enough and needed a migration too.

## Debugging Guide

| Symptom | Start |
|---|---|
| "Menu hai par 403" / "menu nahi par URL khulta hai" | Should be impossible — SidebarItemRule row vs middleware; if real, it's a NEW rule bypassing the pair: alarm |
| Worker can't see a stage | access ∩ assignment: has the skill? on the manager's roster (WST exists)? |
| Accountant can't reach a page | **Fixed 2026-08-02** — they now have a READ TIER (see below). If it still happens: is it a *write* page (correct to refuse), or does the page have a `SidebarItemRule` row that omits accountant? The **DB row overrides the in-code predicate**. |
| Permission works in view, fails in service | Correct — service re-gates; fix the caller's role, don't loosen the service |

## Change Impact

Any new URL → its SidebarItemRule (or it's invisible AND unreachable) ·
role-set changes → re-run certification matrix mindset · stage skill edits
→ roster pickers + visibility everywhere (one predicate = one blast radius)
· tests: certification suites + sidebar middleware tests.

## AI Implementation Pitfalls

- ❌ `request.user.is_superuser` anywhere — `permission_service` only (rule 6).
- ❌ A template-only hide, or a view-only block — every gate pairs with its
  visibility via the rule row or the shared predicate.
- ❌ A second stage-visibility computation "for this one screen" — the ONE
  live predicate is a frozen-foundation rule.
- ❌ Adding roster sources besides manager assignment (auto-assignment was
  REMOVED — PDD amendment 4).
- ✅ Always verify: new page = rule row + wall probes (403 the CSRF-valid
  POST, not just the GET).

## Interview Notes

*Interview Signal: 🟡 Mid — authorization consistency — mid, trending senior.*

**Q. "How do you keep authorization consistent between what users SEE and what they can DO?"**
- *Short:* One source object per gate — the rule that hides is the rule that blocks; one shared predicate for contextual visibility.
- *Senior:* Authorization drift is a data-model problem, not a diligence problem — if hide and block are two artifacts, they WILL diverge. Collapse them into one row read by both middleware and renderer. Then certify per-role behavior with hostile probes (POST with valid CSRF, dual identities), because gates you haven't attacked are assumptions.
- *Project example:* SidebarItemRule + middleware pairing; access ∩ assignment as the single stage predicate; S2/S3 findings caught by exactly this probe culture.
- *Follow-ups:* "Object-level permissions?" (assignment IS the object-level half here) · "Cache the predicate?" (bulk map exists; invalidation = why the predicate stays a function, not a stored flag).

## 🧠 Remember This

Chhupana aur rokna EK hi row se. Stage dikhna = hunar ∩ roster, EK function
se. Service hamesha dobara poochhta hai. Aur bharosa certificate se aata
hai, ummeed se nahi — POST maar ke dekho, 403 aana chahiye.

## 30-Second Revision

- SidebarItemRule + middleware: menu hidden ⇒ URL blocked (one row, both effects)
- permission_service only; services re-gate at the write
- Stage access = SKILL-gated; visibility = access ∩ assignment (ONE predicate)
- Roster = manager assignment ONLY (PDD am.4); auto-assignment removed
- Proof = certifications: per-role matrices, CSRF-valid POST probes

## DSA & Complexity

Stage visibility = **set intersection**: `may_see = has_skill ∩ assigned`.
Two lessons ride on it. (1) Computing the intersection in ONE place
(`access_service`) instead of per-screen is the same O(1)-places argument
as single-writer — n screens × 1 predicate, never n predicates.
(2) `stage_access_map` is the **bulk-evaluation** pattern: evaluate the
predicate for a SET of stages in one pass (one query) instead of n
lookups — the authorization version of killing N+1. Interview framing:
"authorization models are set algebra (roles ∪, skills ∩, assignments ∩);
performance comes from evaluating the algebra in bulk, correctness from
evaluating it in one canonical place."

## Implementation References

- Canonical model: [docs/production/RBAC.md](../../docs/production/RBAC.md) · project view: [people-and-roles](../project/people-and-roles.md)
- Proof: [WORKER](../../docs/WORKER_ROLE_CERTIFICATION.md) / [MANAGEMENT](../../docs/MANAGEMENT_ROLE_CERTIFICATION.md) certifications

## Code References
- `config/inventory/middleware.py` · `config/accounts/services/permission_service.py` · `config/production/services/access_service.py`

## Related Concepts

[people-and-roles](../project/people-and-roles.md) · [stage-tracking](stage-tracking.md) ·
[system-map](../project/system-map.md)

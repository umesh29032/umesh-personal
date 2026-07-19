---
id: flow-request-through-stack
type: flow
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "When Meena taps 'Submit report' on her phone, what code runs, in what order, and where could it stop her?"
related: [project-system-map, feature-stage-tracking, concept-service-layer]
---

# Flow: One Tap Through the Stack

> 📂 [Flows](README.md) · [LOS home](../README.md) — *kahani yaad rakho, files nahi.*

One REAL request, hop by hop: Meena submits her cutting report from her
phone. Same skeleton for every click in the system
([system-map](../project/system-map.md)) — learn it once here, reuse it on
any URL you ever debug.

```
Meena taps Submit  (POST, CSRF token in form)
│
├─ 1. urls.py           production URLConf matches the worker-report route
│
├─ 2. SidebarAccessMiddleware
│      Is this URL behind a menu rule Meena's role can't see?
│      Worker sidebar = Main only — but worker report routes are
│      worker-legal. Menu hidden ⇒ URL blocked, ONE rule. → pass
│
├─ 3. View (thin — parses, gates, never multi-writes)
│      • auth: logged in? role gate via permission_service
│      • stage gate: access ∩ assignment — has the skill AND on the
│        roster (her WorkerStageTask exists)?
│      • parse lines: color/size/good/alter/missing (strings → validated)
│
├─ 4. SERVICE  worker_task_service.report_contributions(task, lines, actor=…)
│      the ONE door for work capture (C-TM):
│      • @transaction.atomic — this business event = one boundary
│      • _ensure_task_actor: the task is HERS (wall #3 re-check)
│      • validates every line loudly (PA-07-2: Decimal(str(x)) —
│        a tampered/locale-comma quantity raises a clean
│        ValidationError, not a 500)
│      • writes WSC rows — the ONLY writer that may
│
├─ 5. Models → PostgreSQL
│      constraints stand guard even if all code above failed:
│      wsc_gam_nonneg_sum_positive (good/alter/missing ≥ 0, sum > 0)
│      → violation = whole transaction rolls back
│
├─ 6. (on the later "complete" tap) history/timeline events append;
│      expected_* freezes — see stage-tracking for THAT tap's guards
│
└─ 7. redirect + Django message → server-rendered template
       (base.html canon; mobile-first — she's on a phone)
```

## Where it can stop her (each stop = a designed wall)

| Hop | Refusal | The wall's name |
|---|---|---|
| 2 | 302/403 on a management URL | sidebar rule pair ([rbac-access](../features/rbac-access.md)) |
| 3 | stage not visible | access ∩ assignment — the ONE predicate |
| 4 | "not your task" | service re-gate (never trusts the view) |
| 4 | bad quantity | loud validation, actionable message |
| 5 | negative/zero-sum counts | DB CHECK — the wall that never sleeps |

## Why each layer is thin except one

The view could do everything — Django allows it. This repo forbids it:
tomorrow the same report arrives from a barcode scanner, a management
command, a test. **Only hop 4 is shared by all futures** — so hop 4 owns
the rules ([service-layer](../concepts/architecture/service-layer.md)).
Middleware answers "may this role be HERE", view answers "is this request
well-formed and authorized", service answers "is this ACTION legal", DB
answers "is this DATA possible". Four different questions — that's why
four layers, not one fat one.

## Interview corner

*Interview Signal: 🟢 Junior — the screening round — every backend interview opens here.*

**Q. "What happens when a user hits a URL in Django?"** *(the screening classic — answer with YOUR stack, not the textbook)*
- *Short answer:* URLConf match → middleware chain → view (auth/parse) → service (the business event, atomic) → ORM/PostgreSQL → response; in this repo, plus a sidebar-rule gate and an append-only history write.
- *Senior answer:* The textbook lists layers; the senior explains WHY each is thin except one — middleware answers "may this role be here," view answers "well-formed + authorized," service answers "is this action legal," DB answers "is this data possible." Four different questions, four walls.
- *Project example:* Meena's report tap on this page, hop by hop, including where each wall can stop her.
- *Follow-ups:* "Where would you add caching?" (never on money-derived values here — derived-live law) · "Where do you debug a 403?" (the recipe below — in order).

## Debug recipe (any URL, any user)

1. Which URLConf row matched? (`urls.py` grep the name)
2. Sidebar rule for that URL + user's role? (middleware layer)
3. View's gates — which service does it call?
4. Read THAT service's docstring — side effects + guards are declared there
5. Still confused? The service's tests are worked examples of every refusal

## Implementation References

- The canon: [docs/PROJECT_KNOWLEDGE_MAP.md](../../docs/PROJECT_KNOWLEDGE_MAP.md) §2 · per-journey call chains: [docs/LEARNING_2_0/REQUEST_JOURNEYS/](../../docs/LEARNING_2_0/REQUEST_JOURNEYS/README.md)
- Walls: [rbac-access](../features/rbac-access.md) · [pg/constraints](../concepts/postgresql/constraints.md)

## Code References
- Code hops: `config/inventory/middleware.py` · `config/production/services/worker_task_service.py` (`report_contributions`)


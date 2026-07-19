---
id: project-system-map
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How is the codebase organized, and what path does every single click take through it?"
related: [project-business-story, project-money-story, concept-django-transactions]
---

# System Map — how the code is organized and how a click travels

> 📂 [Project — the WHY layer](README.md) · [KOS home](../README.md)

## Business Purpose

The factory's domains are separate in real life — cloth store, production
floor, cash book, dispatch. The codebase mirrors that: **one Django app per
business domain**, with machine-enforced boundaries so money code can't
quietly grow roots into production code.

## 💡 Samjho Aise

Ghar ke kamre samjho: rasoi (production), godaam (raw_materials), tijori
(expense), darwaza (accounts). Har kamre ka apna kaam; kamre ke beech
DARWAAZE fixed hain (services), deewar tod ke aana mana hai (import-linter
+ no signals). Aur ghar ka ek hi MAIN GATE hai jahan har mehmaan ki checking
hoti hai (middleware + permissions).

## Technical Deep Dive

**The apps (9 domains + 1 infra):**

| App | Owns | Money? |
|---|---|---|
| `accounts` | Users, roles, skills, auth hardening (Argon2, rate limits), permission_service | — |
| `inventory` | Shared UI shell (base.html canon), sidebar rules + middleware, dashboards | — |
| `raw_materials` | ClothRoll, suppliers, storage, leftovers | cost side |
| `production` | Adda, stages, workflow editor, worker tasks/contributions, cutting, patterns | **production truth** |
| `tracking` | BarcodeBatch/BatchBarcode (piece identity), append-only *History timelines | — |
| `expense` | Ledger, advances, settlements, payroll, factory expenses | **financial truth** |
| `machines` | Physical assets + operator possession windows (R10-A) | — |
| `storefront` | Listing-team catalog surfaces | — |
| `patterns_ai` | Pattern digitization side-product (own docs, own boundary ADR-H) | — |
| `core` | Infra only: `TimeStampedModel`, `ActiveManager` — **no tables** | — |

**The universal request path** — every click in the system takes this road
(canonical: [PKM §2](../../docs/PROJECT_KNOWLEDGE_MAP.md)):

```
Browser
  ─▶ urls.py
  ─▶ SidebarAccessMiddleware        # menu hidden ⇒ URL blocked (same rule!)
  ─▶ View                          # permission_service / skill gates;
  │                                 # parses input; NEVER multi-row writes
  ─▶ Service (config/<app>/services/)  # ALL multi-row writes,
  │                                 # @transaction.atomic, NO signals
  ─▶ Models → PostgreSQL           # constraints enforce truth even vs bugs
  ─▶ history_service               # append-only timeline event
  ◀─ redirect + message → server-rendered template (base.html canon CSS)
```

Server-rendered Django templates, **mobile-first as a functional requirement**
(workers use phones on the factory floor) — no SPA, no REST layer; internal
service functions ARE the API.

**The three iron rules that make the map trustworthy:**
1. **Service layer owns all multi-row writes** — views thin, signals banned.
2. **Single-writer discipline** — each money/history table has exactly ONE
   writer service (`ledger_service` → `WorkerLedgerEntry`, `history_service`
   → `*History`); CI gates census the write-sites.
3. **Layering is machine-checked** — import-linter contracts
   ([config/.importlinter](../../config/.importlinter)) fail the build on
   forbidden imports, ENFORCED vs REPORT-ONLY tiers.

**Two truths, two apps** (THE architectural split — details:
[money-story](money-story.md)):

```
 PRODUCTION TRUTH (production app)      FINANCIAL TRUTH (expense app)
 "kitna kaam hua"                       "kitne paise bane/diye"
 WorkerStageTask/Contribution           WorkerLedgerEntry (append-only)
 corrections allowed until settled      written ONLY at settlement
```

## Interview corner

*Interview Signal: 🟠 Senior — the architecture opener, judged at senior depth.*

**Q. "Walk me through your project's architecture."** *(the opener you WILL get)*
- *Short answer:* Domain-per-app Django monolith, server-rendered, one universal request path: middleware gate → thin view → service (all writes, atomic) → PostgreSQL (constraints as armor) → append-only history.
- *Senior answer:* The interesting part isn't the layers, it's the three enforced rules — services own writes (no signals), one writer per money table, machine-checked import boundaries — and the two-truths split keeping production data correctable while money stays immutable. Everything else follows.
- *Project example:* 9 domain apps + a tableless `core`; 206 atomic service sites; the click-path diagram on this page IS the answer — draw it.
- *Follow-ups:* "Why a monolith?" ([tech-stack](tech-stack.md) rejected-table) · "How do you keep boundaries real?" (import-linter + CI write census) · "Where does money live?" ([money-story](money-story.md)).

## 🧠 Remember This

Ek app = ek domain. Har click ka ek hi raasta: **middleware → view →
service → model → history.** Paisa sirf expense app mein, kaam sirf
production app mein, aur dono ke beech ka pul = settlement. Deewarein
machine todne nahi deti (import-linter, CI gates, constraints).

## Implementation References

- Canonical request pattern: [docs/PROJECT_KNOWLEDGE_MAP.md](../../docs/PROJECT_KNOWLEDGE_MAP.md) §2 · ER sketch §6 · chokepoints §7
- House rules: [CLAUDE.md](../../CLAUDE.md) (rules 4–7) · boundaries: [config/.importlinter](../../config/.importlinter)
- Deep architecture: [docs/ARCHITECTURE_V2.md](../../docs/ARCHITECTURE_V2.md) (🔒) · per-app: [docs/apps/](../../docs/apps/)
- Concepts (Phase 3): service-layer · single-writer · [transactions](../concepts/django/transactions.md)


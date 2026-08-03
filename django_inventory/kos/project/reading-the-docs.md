---
id: project-reading-the-docs
type: project
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "docs/ has 1,100+ files of Claude's engineering memory — as a human, where do I start, what is each pile, and when do I actually need to go in there?"
related: [project-system-map, project-business-story]
---

# Reading the docs/ — a human's guide to Claude's engineering memory

> 📂 [Project — the WHY layer](README.md) · [LOS home](../README.md)

> 💡 **Samjho aise:** `docs/` aur `kos/` do alag cheezein hain, aur farq yaad
> rakhna zaroori hai:
>
> - **`docs/` = kaam ka purana record** — kab kya banaya, kyun banaya, kaunsa
>   bug mila. Hazaar se zyada files. Yeh **history** hai, padhne ki kitaab nahi.
> - **`kos/` = samajhne ki jagah** — yahin se seekho.
>
> Isliye `docs/` mein *ghoomna* nahi hai. Wahan tab jao jab koi **specific
> sawaal** ho ("yeh decision kyun liya gaya tha?"). Warna aap 1,000 files mein
> kho jaoge — aur wo aapki galti nahi hogi, wo us folder ka kaam hi nahi hai.

## Business Purpose

`docs/` holds everything that happened while building this system —
1,100+ markdown files of plans, decisions, receipts, audits, and
generated reference. It is **optimized for AI resumability, not human
reading** — which is exactly why you feel lost in it, and exactly why kos
exists. But docs/ is also the SOURCE: every kos page's Implementation
References point there. This page teaches you to walk into that library
without drowning *(library band nahi karni — bas naksha chahiye)*.

## Mental Model

> docs/ is a **courthouse archive**, kos is the **textbook written from
> it**. The archive has verdicts (truth locks), reasoning (ADRs), case
> files (receipts/audits), and an index clerk (routing files). You go to
> the archive for EVIDENCE and HISTORY — "what exactly was decided, when,
> why" — never for orientation. Orientation is kos's job. If you're
> opening docs/ to "understand the system," you're in the wrong building;
> come back here first.

## The seven piles (what 1,100 files actually are)

| Pile | What it is | Human-useful? |
|---|---|---|
| **Truth locks** (~15) | frozen contracts: [PRODUCT_DESIGN_DOCUMENT](../../docs/PRODUCT_DESIGN_DOCUMENT.md) · [ARCHITECTURE_V2](../../docs/ARCHITECTURE_V2.md) · [MANUFACTURING_V1_FREEZE](../../docs/MANUFACTURING_V1_FREEZE.md) · [FACTORY_OPERATIONS_MASTER](../../docs/FACTORY_OPERATIONS_MASTER.md) | ⭐ YES — these are LAW; kos explains them, they remain the letter |
| **ADRs** ([docs/adr/](../../docs/adr/)) | 11 locked decisions with alternatives-considered | ⭐ YES — the best "why" reading in the repo; short |
| **Routing/indexes** (~40) | START_HERE, DOCUMENTATION_INDEX, PROJECT_KNOWLEDGE_MAP, canonical_manifest.json, PROJECT_BRAIN | [PKM](../../docs/PROJECT_KNOWLEDGE_MAP.md) is genuinely great; the rest mostly serve AI |
| **Teaching (pre-kos)** | [LEARNING/](../../docs/LEARNING/) 01–10 · [LEARNING_2_0/](../../docs/LEARNING_2_0/) (ARCHITECTURE_EXPLAINED, DATABASE_GUIDE, CHOKEPOINTS, DATA_FLOWS, REQUEST_JOURNEYS) | YES as deep-dives — kos pages link the exact ones worth your time (esp. **CHOKEPOINTS/** — verified execution traces) |
| **Evidence** (~130+ at root) | dated receipts (S1–S5…), audits, hostile reviews, certification logs, campaign status | Only when you need HISTORY: "when did this change and what proved it safe" |
| **Generated** (~576) | [docs/features/](../../docs/features/) URL cards + knowledge_graph.json — machine-built structural reference | As LOOKUP only: exact route → view → service chain for one URL |
| **Ops + apps** | [docs/release/](../../docs/release/) (the v1.0 Operations Handbook — Hinglish, human-first!) · [docs/apps/](../../docs/apps/) GUIDEs · [docs/production/](../../docs/production/) | ⭐ release/ is written FOR humans (deploy/troubleshoot); apps/ GUIDEs = per-app file maps |

*(Plus docs/archive/ — superseded history; and AI_PATTERN_INTELLIGENCE/ —
a different product's docs. Ignore both for ERP understanding.)*

## The routing rule — kos first, docs second, code third

```
Question about the system
  → kos page (orientation, the WHY, the mental model)
      → its "Implementation References" (the EXACT docs worth reading:
        the ADR, the receipt, the chokepoint trace — 3-5 files, not 1,100)
          → the code (file + function named on the kos page)
```

**"What is the purpose of this URL?"** — the full recipe:
1. [kos/README "Find it by app"](../README.md) → the owning feature page
   → its **Related URLs** table = the WHY of that URL.
2. Structural chain (route → view → service → models, machine-maintained):
   its generated card under [docs/features/](../../docs/features/).
3. History ("when was this built, what decided it"): the feature page's
   Implementation References → receipts + ADRs.

**"kos doesn't have a page for X yet?"** Then docs/ is the source, in
this order: [PROJECT_KNOWLEDGE_MAP](../../docs/PROJECT_KNOWLEDGE_MAP.md)
§-lookup → [DOCUMENTATION_INDEX](../../docs/DOCUMENTATION_INDEX.md) (grep
X) → the app's GUIDE in [docs/apps/](../../docs/apps/) → and if the docs
genuinely lack it, we read the CODE and extract the knowledge into a new
kos page (that's the standing pipeline: project → docs → kos, nothing
understood twice).

## What to actually READ from docs/ as a learner (the shortlist)

In order of value-per-minute for you *(sirf yeh — baaki reference hai)*:
1. All 11 [ADRs](../../docs/adr/) — each ≈ 1 page, alternatives + why.
2. [CHOKEPOINTS/](../../docs/LEARNING_2_0/CHOKEPOINTS/) — one per money/truth
   service, with verified traces and lock orders.
3. [docs/release/](../../docs/release/) handbook — operating the real system.
4. [PKM](../../docs/PROJECT_KNOWLEDGE_MAP.md) §7 (chokepoint census) + §9
   (ADR summary) — the two best tables in the archive.

## The future (recorded; one item now planned)

**Planned (owner-ordered 2026-07-19):** every major docs/ folder eventually
gets its own human-oriented README — what the folder is · why it exists ·
when to read it · important vs ignorable files · which kos pages reference
it. That work is a scheduled phase of the kos program (it writes INSIDE
docs/, so it will be reconciled with docs/' own constitution — frontmatter,
index registration, knowledge-graph — at that phase's gate).



The standing division stays: **future implementation plans/receipts → docs/
(AI memory); future human understanding → kos/**. Any future agent — Claude
or otherwise — reads CLAUDE.md + docs/ for rules-and-history and kos/ for
comprehension; both layers are plain markdown, agent-agnostic by design. A
full docs→kos migration is a possibility the owner has floated — it stays
a someday-decision at an owner gate, never a side effect *(abhi ke liye:
docs jahan hai wahin, kos usse PADHNA sikhaata hai)*.

## 🧠 Remember This

docs/ adaalat ka record-room hai, kos teri kitaab. Kitaab se shuru karo;
record-room mein sirf SABOOT lene jao (ADR, receipt, trace) — aur hamesha
kos page ki References se pata leke jao, khali haath bhatakne mat jao.
1,100 files mein se tumhare kaam ki roz ki sirf ~20 hain — upar ki
shortlist wahi hai.

## 30-Second Revision

- 7 piles: locks (law) · ADRs (why) · routing · teaching · evidence (history) · generated (lookup) · ops
- Route: kos → its References → docs → code; never browse docs/ raw for orientation
- URL purpose: kos feature page's Related URLs; structure: generated card; history: receipts
- Learner shortlist: 11 ADRs · CHOKEPOINTS/ · release/ · PKM §7+§9
- Future: plans→docs, understanding→kos; full migration = someday, owner-gated

## Implementation References

- The archive's own front doors: [docs/START_HERE.md](../../docs/START_HERE.md) · [docs/DOCUMENTATION_INDEX.md](../../docs/DOCUMENTATION_INDEX.md)
- The two-layer ruling: kos/[STANDARDS.md](../STANDARDS.md) · this page's twin: [system-map](system-map.md)


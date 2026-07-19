---
id: project-business-story
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "What business does this software actually run, and what problem was it built to solve?"
related: [project-money-story, project-system-map, flow-worker-gets-paid]
---

# The Business Story — what Kapil Enterprises actually does

> 📂 [Project — the WHY layer](README.md) · [KOS home](../README.md)

## Business Purpose

Kapil Enterprises is a **garment manufacturing factory**. Cloth rolls come in;
finished garments (T-shirts, lowers, nikkars) go out. Between those two points
sit people and processes this software exists to make **provable**: which cloth
went where, which worker did what, and exactly how much money everyone earned.

Before this system: registers, memory, and disputes. The software's founding
problem was never "we need an app" — it was **"six months later, nobody can
prove any number."**

## 💡 Samjho Aise

Factory ko ek dhaba samjho. Kapda = kachcha saaman. **Adda = ek order ki
poori taiyari** (jaise "aaj 200 T-shirt banani hain" ek Adda hai). Har Adda
kitchen ke fixed steps se guzarta hai — bichhao (layering), naap-nakka
(pattern design), kaato (cutting), tag lagao (barcode). Har step par workers
bolte hain "maine itna kiya". Mahine ke end pe malik hisaab karta hai —
**wahi hisaab is poore software ka dil hai.**

## Technical Deep Dive

The one-sentence engine (memorize this):

> **Workers report work → owner settles the Adda (earnings book) →
> owner pays cash later → everything is traceable forever.**

The cast:

| Who | Does | In the system |
|---|---|---|
| **Owner (Malik)** | Configures products/flows/rates, settles money, pays cash | `super_admin` |
| **Manager** | Runs Addas day-to-day: assigns workers, verifies quantities, advances stages | `manager` |
| **Worker** | Reports work from a PHONE at their station | `worker` — mobile-first is a functional requirement here |
| **Accountant** | Sees/edits financial master data (supplier, cost/kg) as an add-on capability | `accountant` |

The production spine (one Adda's life):

```
ClothRolls ──▶ ADDA (one batch of ONE product, e.g. 3-PATTI-003)
                 │  moves through owner-configured stages:
                 ▼
   Layering → Pattern Design → Cutting → Barcode-Gen → (future stages)
   rolls attach   checklist +    first REAL      piece identity
   leftovers      photo proof    quantities      (adda, seq)
   tracked        fixed pay      (size/color)    printed = permanent
                 │
                 ▼
   workers report on phones → manager verifies → owner settles → cash
```

Two vocabulary rules that unlock every model name
(full glossary: [GLOSSARY.md](../../GLOSSARY.md)):
- **Adda** = one production batch of one product — THE central noun.
- **Stage vs WorkflowStage vs AddaStageRecord** = library definition →
  attached-to-a-product with order+rate → the execution row for one Adda.
  Same word "stage", three precision levels.

## What this project deliberately is NOT

- Not a storefront/e-commerce system (storefront app exists for listings,
  but manufacturing ≠ catalog — `Product` here is a manufacturing master).
- Not a generic ERP — every screen exists because this one factory asked.
- Not an accounting package — it proves **worker money** and **production
  truth**; factory-level running costs are simple `FactoryExpense` rows,
  never allocated into per-Adda cost (ADR-0011).

## 🧠 Remember This

Ek factory, ek software, ek sawaal: **"prove karo."** Adda central noun hai,
settlement central event hai, ledger central kitab hai. Baaki sab kuch —
stages, barcodes, roles — is ek sawaal ke jawab ke liye hai.

## Implementation References

- Canonical overview: [docs/PROJECT_KNOWLEDGE_MAP.md](../../docs/PROJECT_KNOWLEDGE_MAP.md) §1
- Vocabulary: [GLOSSARY.md](../../GLOSSARY.md) · why the project exists: [ABOUT_THIS_PROJECT.md](../../ABOUT_THIS_PROJECT.md)
- Product truth (frozen): [docs/PRODUCT_DESIGN_DOCUMENT.md](../../docs/PRODUCT_DESIGN_DOCUMENT.md)
- Operations reality: [docs/FACTORY_OPERATIONS_MASTER.md](../../docs/FACTORY_OPERATIONS_MASTER.md)


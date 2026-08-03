---
id: app-machines-views
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "machines' single views.py — 5 views, a form, a gate."
related: [app-machines, app-machines-urls]
---

# machines — handler knowledge (`config/machines/views.py`)

> 📂 [machines app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

> 💡 **Samjho aise** — Views = **reception counter**
>
> Browser se request aati hai to sabse pehle yahin aati hai. View ka kaam sirf teen cheezein hai: **request padho → permission check karo → service ko bhej do**. View khud database mein likhta **nahi** — isiliye yeh files patli hoti hain. Moti view = design ki galti.
>
> *(`machines` app ka kaam: factory ki machinein aur kis worker ke paas kaunsi machine hai.)*

## Handler groups at a glance

- **READ (1):** MachineListView (50) — the derived board
- **WRITE (4):** MachineCreateView (81) · MachineUpdateView (110) ·
  MachineAssignView (145) · MachineReleaseView (165)
- **ADMIN / DELETE / ASYNC:** none — no delete route exists (units retire
  by status; windows are history — learn from absence)

All behind `_ManagementOnly` (21) + LoginRequired; `MachineForm` (26) =
the registry form.

## Rules of thumb

1. Possession mutations = the two service verbs only.
2. The board never computes holders itself — `machines_with_holder` does.
3. A new surface (e.g. per-worker "what do I hold") = a read view over the
   same service reads; no new state.

## Required Knowledge (this page)

- [ ] Windows-not-pointers → [feature: machines](../../features/machines.md)

## Learning Graph

**Before:** [urls.md](urls.md). **After:** [services.md](services.md) →
`views.py` (191 lines — a pleasant read).

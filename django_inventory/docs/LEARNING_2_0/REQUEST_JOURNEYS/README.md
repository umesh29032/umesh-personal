---
id: l2-request-journeys-readme
type: entry-index
status: active
owner: handwritten
scope: documentation system
anchors: —
verified: 2026-07-13
---

# REQUEST JOURNEYS — exact call chain for every workflow

> Each journey documents (owner-mandated 16 sections):
> 1 URL · 2 View/Handler · 3 Forms · 4 Services called · 5 Models READ ·
> 6 Models WRITTEN · 7 Transaction boundaries · 8 Permissions/RBAC ·
> 9 ADRs affecting it · 10 Database tables affected · 11 Example request payload ·
> 12 Example DB rows before/after · 13 Common debugging points · 14 Common
> mistakes · 15 Why this architecture · 16 What breaks if bypassed.
> EXACT file paths, classes, functions. **Template = [settlement_finalize.md](settlement_finalize.md).**
>
> QUALITY STANDARD v2 (owner 2026-06-12) — every journey ALSO adds: ASCII
> sequence diagram · ASCII data-flow diagram · files touched in EXECUTION ORDER
> · DB tables touched in EXECUTION ORDER · common debugging commands · common
> breakpoints · how to trace end-to-end in VS Code · related tests + test files
> · related ADRs · related roadmap items. (settlement_finalize + adda_creation
> currently have the 16-field core; v2 diagram/trace/test sections are the next
> upgrade pass.)

| # | Journey | File | Status |
|---|---|---|---|
| 1 | Settlement finalize | [settlement_finalize.md](settlement_finalize.md) | ✅ full (16-field) |
| 2 | Adda creation | [adda_creation.md](adda_creation.md) | ✅ full (16-field) |
| 3 | Worker reporting | [worker_reporting.md](worker_reporting.md) | ✅ v2 |
| 4 | Login (OTP/password) | [login.md](login.md) | present (core) |
| 5 | Worker assignment | [worker_assignment.md](worker_assignment.md) | present (core) |
| 6 | Stage completion | [stage_completion.md](stage_completion.md) | present (core) |
| 7 | Settlement draft | [settlement_draft.md](settlement_draft.md) | present (core) |
| 8 | Settlement reverse/supersede | [settlement_reverse.md](settlement_reverse.md) | present (core) |
| 9 | Advance | [advance.md](advance.md) | present (core) |
| 10 | Payment (cash) | [payment.md](payment.md) | present (core) |
| 11 | Barcode flow | [barcode_flow.md](barcode_flow.md) | present (core) |
| 12 | Costing flow | [costing_flow.md](costing_flow.md) | present (core) |

> Rows 4–12 index-repaired 2026-07-13 (Phase-7 Q-C5, F-D-03/B.3-3): the journey FILES
> exist and are linked here; "present (core)" = file present with core content, NOT a
> claim of the v2 diagram/trace/test upgrade (that quality pass is a future authoring task,
> DC-D1 venue — cleanup links existing docs, never authors).

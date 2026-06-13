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
| 4 | Login (OTP/password) 
| 5 | Worker assignment 
| 6 | Stage completion 
| 7 | Settlement draft 
| 8 | Settlement reverse/supersede 
| 9 | Advance 
| 10 | Payment (cash) 
| 11 | Barcode flow 
| 12 | Costing flow 

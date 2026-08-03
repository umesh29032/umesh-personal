---
id: pages-readme
type: entry-index
status: active
owner: handwritten
scope: page contracts
anchors: —
verified: 2026-07-13
---

# docs/PAGES/ — per-page documentation

One markdown file per significant page. Each must cover the master-spec sections:

- **Purpose** — what the page is for, in one paragraph.
- **Route** — URL, URL name, view, template, sidebar entry.
- **Permissions** — mixins / gates; what a direct-URL hit does for the unauthorized.
- **Role access** — which roles can reach it.
- **Skill access** — which skills (if any) gate it.
- **Form behavior** — fields, validation, submit path, autosave.
- **Data saved** — models/rows written, by which service.
- **Edge cases** — reopen, empty state, race, idempotency.
- **Mobile behavior** — responsive layout, overflow handling.
- **Risks** — what could go wrong; trust boundaries.

[`ACCESS_CONTROL.md`](ACCESS_CONTROL.md) is the filled-in exemplar.

## Backlog (pages still to document)
Costing (`/production/costing/`), Payroll Overview (`/expense/payroll/`),
Worker detail + Settlement (`/expense/workers/<pk>/`, `.../settle/`), Record
Advance (`/expense/advances/add/`), My Earnings (`/expense/my/`), the four stage
workspaces (layering / cutting_pattern / cutting / barcode_generation), Sidebar
Access (`/inventory/sidebar-access/`), Roles editor, Stage library. Existing
feature docs in `docs/production/` cover most of these at the flow level; migrate
them into this per-page template as they're touched.

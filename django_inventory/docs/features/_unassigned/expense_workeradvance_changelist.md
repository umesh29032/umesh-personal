---
id: url-card-admin-expense-workeradvance-changelist
type: url-card
status: generated
owner: generated
scope: route — url:admin:expense_workeradvance_changelist
anchors: config/config/urls.py
verified: graph:56207d76ed26
---

# URL card — `expense_workeradvance_changelist`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `expense_workeradvance_changelist` |
| Namespace | `admin` |
| Mount | `/admin/expense/workeradvance/` |
| Pattern | *(empty — the mount root itself)* |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `ModelAdmin.changelist_view` |
| Module | `django.contrib.admin.options` |
| Defined in | `/admin/account/emailaddress/` |
| Vendor | true |

## App

Not derivable — the view module matches no project app label (vendor or config-level view).

## Gates

Not machine-known — the graph carries no `gated_by` edges (no certified gate register exists;
Phase-8 residual R-2). Gate truth remains in code.

## Services invoked

Not machine-known — the graph carries no `calls` edges (no certified view→service register
exists; Phase-8 residual R-1).

## Models written

Not machine-known at route grain — single-writer truth is recorded at service grain
(`writes` edges); see the app documentation above.

## Feature

None machine-provable — no `belongs_to_feature` edge for this url (fix at source: enrich FEATURE_INDEX, rebuild, regenerate).

## Governing docs

None machine-known at route grain — see the app documentation above.

## Mobile strategy

Not machine-known — the graph carries no mobile-strategy data for this route.

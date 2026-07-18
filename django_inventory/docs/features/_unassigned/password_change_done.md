---
id: url-card-admin-password-change-done
type: url-card
status: generated
owner: generated
scope: route — url:admin:password_change_done
anchors: config/config/urls.py
verified: graph:56207d76ed26
---

# URL card — `password_change_done`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `password_change_done` |
| Namespace | `admin` |
| Mount | `/admin/password_change/done/` |
| Pattern | `password_change/done/` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `AdminSite.password_change_done` |
| Module | `django.contrib.admin.sites` |
| Defined in | `/admin/password_change/done/` |
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

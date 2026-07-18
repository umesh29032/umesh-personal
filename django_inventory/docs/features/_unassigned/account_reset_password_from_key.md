---
id: url-card-account-reset-password-from-key
type: url-card
status: generated
owner: generated
scope: route — url:account_reset_password_from_key
anchors: config/config/urls.py
verified: graph:56207d76ed26
---

# URL card — `account_reset_password_from_key`

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: url-card v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

## Route

| Field | Value |
|---|---|
| URL name | `account_reset_password_from_key` |
| Namespace | — (none) |
| Mount | `/accounts/^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$` |
| Pattern | `^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$` |
| Named | true |

## View

| Field | Value |
|---|---|
| View | `PasswordResetFromKeyView` |
| Module | `allauth.account.views` |
| Defined in | `/accounts/^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$` |
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

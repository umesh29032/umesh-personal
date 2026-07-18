---
id: feature-login
type: feature-doc
status: generated
owner: generated
scope: feature — login
anchors: docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md
verified: graph:56207d76ed26
---

# Feature — Login (OTP/password)

> ⚙️ GENERATED — an index, not truth. Do not hand-edit; fix the source, rebuild the graph, regenerate.
> Generator: `scripts/generate_docs.py` · source: `docs/knowledge_graph.json` · graph: `56207d76ed26` · schema: 1.0.1 · template: feature-doc v1.0.0
> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`

| Field | Value |
|---|---|
| Slug | `login` |
| Label | Login (OTP/password) |
| Seed source | `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` |

## Member routes

| Route | Mount | View | Card |
|---|---|---|---|
| `accounts:login` | `/app/` | `LoginView` | [login.md](login.md) |

## Member models

| Model | Table | Single writer |
|---|---|---|
| `accounts.User` | `accounts_user` | not machine-known |

## Apps touched

- `accounts` — [config/accounts/README.md](../../../config/accounts/README.md) · [docs/apps/accounts/GUIDE.md](../../apps/accounts/GUIDE.md)

## Governing docs

Seed row: `docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` (the feature's source of truth).

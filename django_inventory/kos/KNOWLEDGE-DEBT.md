---
id: kos-knowledge-debt
type: system
verified: 2026-07-19
---

# Knowledge Debt Register

> The ONLY source of future LOS improvements (owner law; constitution: [LOS-MANIFEST](LOS-MANIFEST.md)).
> Every certification/validation failure lands here; every fix cites its
> evidence. Format: Description · Priority · Reason · Owner · Resolved In · Evidence.

| # | Description | Pri | Reason (evidence) | Owner | Resolved In | Evidence of fix |
|---|---|---|---|---|---|---|
| KD-1 | No dev-environment onboarding page (fresh machine → first commit) | P0 | Cert T18 FAIL (conf 20) | LOS | Hardening A | [project/dev-setup.md](project/dev-setup.md) |
| KD-2 | Sidebar-rule EDITING location not linked from expense/production checklists | P1 | Cert T1 PARTIAL | LOS | Hardening A | both checklists → inventory §6 |
| KD-3 | Tracked-export precedent invisible from expense | P1 | Cert T12 PARTIAL | LOS | Hardening A+B | expense Start-Here row + [pattern card](concepts/patterns/tracked-export.md) |
| KD-4 | barcode_service had no source path; tracking app had no LOS pages | P1 | Cert T3 PARTIAL | LOS | Hardening A+C | path line + [apps/tracking/](apps/tracking/README.md) |
| KD-5 | production views.md lacked template names | P1 | Cert T9 PARTIAL | LOS | Hardening A | workspace template names added (verified; panel = dynamic, stated) |
| KD-6 | accounts app had no LOS pages | P1 | Cert T2 minor friction | LOS | Hardening C | [apps/accounts/](apps/accounts/README.md) |
| KD-7 | Cross-app pattern discovery had no home | P1 | Cert recurring theme | LOS | Hardening B | [concepts/patterns/](concepts/patterns/README.md) |
| KD-8 | Remaining apps unpaged: raw_materials · machines · storefront · core | P2 | planned scope | LOS | V2 RC (apps 6–9) | [apps/README](apps/README.md) — 9/9 ✅ LOS, lessons per owner spec |
| KD-9 | Independent fresh-eyes certification never ran (account limits) — author-bias caveat on V1 cert | P1 | validation method | owner+LOS | SCHEDULED: V2 independent certification phase | — |

| KD-10 | No from-scratch first-deploy teaching page (runbook = commands; beginner needs the WHY per step) | P1 | Owner request 2026-07-19 (pre-first-deploy) | LOS | same day | [first-deploy-from-scratch](concepts/deployment/first-deploy-from-scratch.md) |

**Adding an entry:** only from a real validation/usage failure, with the
failing task/incident as Reason. **Closing an entry:** name the change +
link it. No entry, no LOS change — that's the law now.

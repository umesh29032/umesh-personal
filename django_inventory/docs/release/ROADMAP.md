---
id: release-roadmap
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: —
verified: 2026-07-19
---

# Roadmap — ERP v1.1 planning (sirf soch, implementation NAHI)

> Yeh document candidates describe karta hai — priority, dependency, business
> value. Koi bhi item BUILD tabhi hoga jab owner charter dega (PDD
> change-control / ADR discipline v1.0 mein jaisa tha, waisa hi rahega).
> Frozen cheezein frozen hain: PDD v1.0, design system, money boundaries.

## Priority 0 — release ko poora karna (deploy-blockers nahi, deploy-FINISHERS)

| Item | Kya | Value | Dependency |
|---|---|---|---|
| P0.1 | **First production deployment** (runbook 4–11 + `verify_production`) | system LIVE hota hai | owner: VPS + DNS + `.env` + restic creds |
| P0.2 | **Monitoring menu** (Sentry DSN · `/healthz` + app healthcheck · uptime probe · log alerts) | C2 temporary acceptance band hoti hai; raat ko neend | P0.1 (ya usse pehle bhi ho sakta hai) |
| P0.3 | **DEP-F1 one-liner** (settings-module fail-fast default) | bare-metal debug-leak vector band | none |
| P0.4 | **Owner data decision** execute (start CLEAN recommended) + 3-Patti config pass | production data hygiene + last config debt | P0.1 |

## Priority 1 — soak-gated hardening (deploy ke baad ka natural sequence)

| Item | Kya | Value | Dependency |
|---|---|---|---|
| P1.1 | **Enforcement flags ON** (allocation-bound → settlement-recon), runbook ke staged path se | money boundaries advisory se enforced ho jaati hain | 2–4 hafte clean soak + preview commands zero-violation |
| P1.2 | **S6: reported_quantity retirement** | dual-write hatata hai, schema saaf | IRREVERSIBLE — soak + owner gate |
| P1.3 | **Era-A path deletion** (ADR-0007 ka last chapter) | dead code kam, lever retire | real-worker soak PASS |
| P1.4 | Load/latency baseline (ek din ka simple probe) | RR-7 close; capacity numbers mil jaate hain | P0.1 |

## Priority 2 — business value modules (owner-charter candidates)

| Item | Kya | Value | Dependency / fence |
|---|---|---|---|
| P2.1 | **Pattern tool phases 4–6** (interactive workspace → locked-piece re-nest → PDF/print/validation) | cutting efficiency, marker paper-savings — vision doc ready hai | PRODUCT_VISION_V2 roadmap; Foundation v1.0 stable base |
| P2.2 | **RM-V2 read-path** (raw-material insights behind the recorded seam) | material analytics deeper | seam documented; no schema |
| P2.3 | **MEE frequencies** (weekly/quarterly) | recurring expenses poora automation | enum seam ready; owner charter |
| P2.4 | **TM-2: barcode/both tracking modes** (worker report capture via scan) | data-entry friction ghatata hai | C-TM chokepoint convergence law; barcode review doc |
| P2.5 | **Material holdings view** (kitna kapda pada hai — valuation) | inventory-value visibility | RMX deferred register; ADR-0009 basis rules |
| P2.6 | **Accountant role definition** | S-R1 close; back-office delegation ready | owner ruling on surfaces |

## Priority 3 — fenced/large (design-first, kabhi chupke se nahi)

| Item | Fence |
|---|---|
| Multi-factory (site dimension) | ADR-0006 — schema untouched until real second site |
| Commerce G1–G7 (orders/pricing/e-comm) | ADR-0008 boundary — production models commerce-free rahenge |
| Piece-level tracking models | ADR-0010 — ranges se derive hote rahenge jab tak business case na ho |
| KOS consolidation | owner-deferred program; pointer-only on disk |

## Sequencing logic / Kram ki wajah

```
 deploy (P0.1) ──▶ monitoring (P0.2) ──▶ soak ──▶ flags ON (P1.1)
                                             └──▶ S6 (P1.2) ──▶ era-A delete (P1.3)
 business modules (P2.x) — soak se independent, owner-priority se parallel chal
 sakte hain, BAS money-boundary/frozen-module ko na chhuen bina charter ke.
```

Do rules jo v1.1 mein bhi nahi badlenge:
1. **Naya money-write path = STOP + design review.** (Standing owner order.)
2. **Har feature 7-step factory-driven format se** (real problem → why →
   ownership → smallest impl → browser → tests → STOP) — invented milestones
   nahi.

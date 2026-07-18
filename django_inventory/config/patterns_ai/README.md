---
id: patterns-ai-readme
type: app-readme
status: active
owner: handwritten
scope: patterns_ai — pattern layout tool (photo → geometry → marker layout)
anchors: config/patterns_ai/services/, config/patterns_ai/urls.py
verified: 2026-07-13
---

# patterns_ai — Pattern Layout Tool

**State (refreshed 2026-07-13, Phase-7 Q-A5; sources: [GUIDE](../../docs/apps/patterns_ai/GUIDE.md)
state line · [PRODUCT_VISION_V2](../../docs/AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) ·
[PLATFORM_STATUS](../../docs/AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md)):**
🔒 **Vision V2 (owner reset 2026-07-07, PERMANENT): a simple photo → geometry → marker-layout
tool.** Foundation v1.0 STABLE (owner M8.1 approval; architecture phase over). Eras P1–P5 +
V2-Phases 4 (interactive workspace) and 5 (AI layout optimization) COMPLETE + FROZEN — 15-model
pin, 188 tests, zero pending migrations. The enterprise direction (advisor/insights/yield) is
frozen research-only, never extended. Remaining roadmap: Phase 6 PDF/print/export (owner-gated).
Worker-blocked by construction (management/admin-only; certified — worker-cert Phase I).

**Governing docs (live chain):** [PRODUCT_VISION_V2](../../docs/AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md)
(🔒 source of truth) → [ROADMAP_V2](../../docs/AI_PATTERN_INTELLIGENCE/ROADMAP_V2.md) →
[PRODUCT_INTEGRATION_DESIGN](../../docs/AI_PATTERN_INTELLIGENCE/PRODUCT_INTEGRATION_DESIGN.md)
(integration ruling — ACTIVE per owner ruling Q-0b(2), 2026-07-13) → the ADR pack
(`docs/AI_PATTERN_INTELLIGENCE/ADR/`, A–H) → [PLATFORM_STATUS](../../docs/AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md)
(§8a = doc of record). *The founding-era chain (KICKOFF → BLUEPRINT_V3 → master plan) is
archived history: `docs/archive/patterns_ai_enterprise_era/`.* File-by-file map:
[docs/apps/patterns_ai/GUIDE.md](../../docs/apps/patterns_ai/GUIDE.md).

## Constitution (short form — unchanged, still enforced)
- Proposals + own knowledge only — this app NEVER writes a production table.
- Production NEVER imports this app — zero exceptions (import-linter, no
  ignores + `tests/test_purity.py`).
- FKs point INTO production only. Single-writer services own every write
  (`services/` — I-1: import/backfill tooling included).
- Money: none. Honest-AI vocabulary. Append-only knowledge; deletion classes
  per ADR-G. Mobile-first @390 for capture flows; management desktop-first.

## Media
Knowledge-class originals live under `media/patterns_ai/<product>/originals/`
(immutable + checksummed); derived renditions under `derived/` (regenerable). See ADR-G.

## Layout
`services/` single writers · `templates/patterns_ai/` · `static/patterns_ai/`
· `tests/` (purity + smoke + per-block suites) · `management/commands/`
(sidebar seed; integrity sweep) · P0 harness lives in `poc/patterns_ai/`
(non-production, permanent).

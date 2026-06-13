# PKALS v2 — ADR PROPOSALS (Discovery, design-only)

> **PROPOSALS, not locked decisions.** These would become real ADRs (numbered in
> the existing `docs/adr/` sequence — next free is 0011+) ONLY if the owner approves
> building v2. Until then they record the design stance. They govern v2 only; v1 ADRs
> are untouched.

## ADR-V2-P1 — v2 is a read-only layer on frozen v1
**Context.** v1 is released + frozen; its docs/guard/contract are the source of truth.
**Decision.** v2 (automation + skills + sync) only READS v1 artifacts and the code;
it never modifies v1 canonicals, navigation, the CI guard's existing checks, or the
maintenance contract except normal maintenance-mode updates. New v2 checks may be
ADDED to `scripts/check.sh`/`core.tests` but must not weaken existing ones.
**Consequence.** v2 can be reverted wholesale without touching v1. v1 stays the
stable base a future maintainer can trust.

## ADR-V2-P2 — detect-and-notify, never auto-rewrite
**Context.** "Self-healing docs" is tempting but prose correctness is judgment.
**Decision.** v2 tooling DETECTS drift (stale route/model/canonical, missing
CHANGE_IMPACT) and NOTIFIES (report / checklist / failing CI line). It never
auto-edits doc prose. A human or AI agent writes the actual content.
**Consequence.** No risk of confidently-wrong machine-written docs; the irreducible
human/agent-judgment boundary (v1 release "known limitations") is respected.

## ADR-V2-P3 — skills and tools wrap v1 canonicals, never copy them
**Context.** v1's hardest-won property is single-source. A skill/tool that embeds a
copy of (e.g.) the chokepoint list or the canonical map would drift from it.
**Decision.** Every v2 skill/tool reads the live v1 artifact (manifest, matrices,
journeys, resolver, `apps.get_models`) at run time. No v2 component caches v1
knowledge as its own copy.
**Consequence.** v2 cannot become a second source of truth; when v1 updates, v2 keeps
working. The v1 manifest-chokepoint single-source guard already enforces this for the
manifest; v2 inherits the discipline.

## ADR-V2-P4 — automation uses Django introspection, not regex
**Context.** Route/model drift detection could parse `urls.py`/`models.py` textually.
**Decision.** v2 drift checks use `django.urls.get_resolver()` and
`apps.get_models()/_meta.get_fields()` — the real runtime structures — not regex over
source files.
**Consequence.** Robust against includes, decorators, abstract bases, dynamic routes;
low false-positive rate (a false alarm that cries wolf gets disabled, defeating the
point). Slightly heavier (loads Django) — acceptable, runs in CI alongside tests.

## ADR-V2-P5 — reject an online-learning expansion; extend LEARNING/10 only
**Context.** v1 already teaches Django/SQL/architecture-as-used-here (`LEARNING/`) and
maps official external docs to project usage (`LEARNING/10_ONLINE_RESOURCES`); the
owner scope-rejected generic re-teaching (the retired "14 Django pages").
**Decision.** v2 does NOT build a separate online-learning system. Genuinely missing
external topics are added as curated, project-mapped links in `LEARNING/10` (a v1
maintenance update), never as new parallel learning trees.
**Consequence.** No content bloat; no duplication; the one learning route
(`LEARNING_PATH`) stays canonical.

## ADR-V2-P6 — v2 ships in independently-revertible phases, each CI-green
**Context.** v1's commit discipline (docs-only, per-group revertible, guard-green).
**Decision.** v2 ships as small phases (v2-A foundation → v2-B drift-CI → v2-C sync →
v2-D optional), each leaving `scripts/check.sh` green and revertible by commit, with
new blocking checks added only when low-false-positive.
**Consequence.** v2 can stop after any phase with a coherent, stable result; a noisy
check can be demoted to report-only or reverted without unwinding the rest.

---
*If approved, these become `docs/adr/0011…` (binding). The v1 ADR set (0001–0010)
stays unchanged — adding 0011+ keeps the sequence contiguous (the v1 guard checks
contiguity, so v2 ADRs must be added in order).*

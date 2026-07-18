"""devseed.knowledge — the knowledge_sync detector core (Campaign Phase 14).

PURE DETECTOR (pkals_v2 ADR-V2-P2, permanent law): detects · classifies ·
reports · names the owning repair venue. It NEVER modifies source code,
documentation, the graph, manifests, generated outputs, or the git index —
and a `--fix` flag will never exist (owner/ADR to ever change that).

KS-A state: architecture + severities + venues + the Finding shape only.
Detector domains land wave-by-wave (KS-B: 1, 6, 5-as-rescoped · KS-C: 2, 3, 4
· KS-D: 7, 8) — every detector implements an ALREADY-BINDING rule and maps to
its inherited contract (unmapped detectors don't merge, SYNC-D2).
"""

from dataclasses import dataclass, field

# ── severities (SYNC-D3; ratified threshold = any BLOCKER fails the exit) ────
BLOCKER = "BLOCKER"   # knowledge LIES (hand-edit-in-fence · dead CI-guarded path · invariant violation)
WARN = "WARN"         # knowledge is stale but honest
INFO = "INFO"         # hygiene
SEVERITIES = (BLOCKER, WARN, INFO)

# ── the 8 detector domains (SYNC-D2 inventory; §6.3 + the A-1 owner ruling) ──
DOMAINS = {
    "code-docs": "PHASE_05 §6.1.17 / pkals_v2 MUST list (change-impact · route-map · model-map)",
    "code-graph": "PHASE_08 §6.7 (graph staleness tiers + validator re-run)",
    "docs-graph": "PHASE_08/09 (doc nodes vs frontmatter · supersession · reachability)",
    "generated-drift": "PHASE_09 §6.6 stale-output contract (graph-hash · fences · hand-edits)",
    # A-1 owner ruling 2026-07-17 (dated amendment, PHASE_14 Appendix A): the
    # manifest stays HANDWRITTEN+CI-guarded — domain 5 = path validation +
    # topic coverage vs graph + consistency; regenerate-compare DOES NOT EXIST.
    "manifest-sync": "GEN-D Amendment A1 + PkalsNavigationGuardTests concern (report-side)",
    "ownership-metadata": "DOC_STANDARDS / OWNERSHIP_MATRIX / R2 frontmatter scope",
    "dataset-spec": "PHASE_12 SEED-F handoff (spec registry vs implemented registry vs SPEC_VERSION)",
    "verification-registry": "PHASE_13 §VER-E.3.1 (check citations resolve; registry machine-readable)",
}

# ── owning repair venues (§6.5 — every finding names exactly one) ────────────
VENUES = {
    "docs": "U6 same-session repair via CHANGE_IMPACT_MATRIX row + the app GUIDE (Phase-7-style)",
    "generated": "Phase-9 regeneration runbook: env/bin/python scripts/generate_docs.py --out docs/features",
    "graph": "Phase-8 rebuild: env/bin/python scripts/build_knowledge_graph.py (then validate)",
    "code": "Phase-4 protocol intake (observation → U12 backlog/CONFIRMED_FINDINGS ledger)",
    "spec-registry": "dated amendment to the owning frozen contract/spec — never silent divergence",
    "money": "U8 STOP + report (Money-Write rule) — never 'verify by correcting'",
}


@dataclass(frozen=True)
class Finding:
    """One drift finding. Immutable; `venue` MUST be a VENUES key; `evidence`
    carries the path/line/hash pair that makes the finding checkable by a
    human without re-running the sweep."""

    id: str
    domain: str          # DOMAINS key
    severity: str        # SEVERITIES member
    evidence: dict = field(default_factory=dict)
    venue: str = "docs"  # VENUES key — the owning repair venue
    accepted: bool = False  # acceptance-list status (always VISIBLE, never a filter)

    def as_body_row(self):
        return {"id": self.id, "domain": self.domain, "severity": self.severity,
                "evidence": self.evidence, "venue": self.venue,
                "accepted": self.accepted}

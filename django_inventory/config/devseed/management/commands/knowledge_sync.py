"""knowledge_sync — the standing drift detector (Campaign Phase 14, KOS v3
core element 5). PURE DETECTOR: detect · classify · report · route — it never
repairs, and a --fix flag will never exist (stated here so nobody adds one
casually; owner/ADR to ever change).

Dev-only by STRUCTURE (devseed is absent under production settings — drift
detection is a repo-side maintenance concern). Read-only by the purity suite.

KS-A state: full report/exit plumbing over an EMPTY detector registry (the
8 domains land KS-B..KS-D); an empty sweep is the runtime identity proof.
"""

from django.core.management.base import BaseCommand, CommandError

from devseed.knowledge.acceptance import apply_acceptance
from devseed.knowledge.report import (
    SYNC_ENGINE_VERSION,
    build_sync_report,
    exit_code,
    render_stdout,
    write_report,
)

from devseed.knowledge.d1_code_docs import (
    detect_change_impact,
    detect_model_map,
    detect_route_map,
)
from devseed.knowledge.d2_graph import (
    detect_graph_deep_rebuild,
    detect_graph_validator,
)
from devseed.knowledge.d3_graph_census import (
    detect_graph_census,
    detect_graph_completeness,
    detect_graph_consistency,
)
from devseed.knowledge.d4_generated import (
    detect_fence_integrity,
    detect_generated_stale,
    detect_hand_edits,
)
from devseed.knowledge.d5_manifest import (
    detect_manifest_consistency,
    detect_manifest_coverage,
    detect_manifest_paths,
)
from devseed.knowledge.d6_ownership_metadata import (
    detect_lifecycle,
    detect_metadata,
    detect_ownership,
)
from devseed.knowledge.d7_dataset_spec import (
    detect_dataset_registry,
    detect_golden_spec_agreement,
    detect_spec_version_pins,
)
from devseed.knowledge.d8_verification_registry import (
    detect_citation_integrity,
    detect_report_schema_dependency,
    detect_verification_registry,
)

# The detector registry: {detector_id: callable(diff=, deep=) -> Finding[]}.
# KS-B: documentation domains (1 · 6 · 5-as-A-1-rescoped).
# KS-C: graph + generation domains (2 · 3 · 4). Registries (7, 8) land KS-D.
DETECTORS = {
    "code-docs.change-impact": detect_change_impact,
    "code-docs.route-map": detect_route_map,
    "code-docs.model-map": detect_model_map,
    "ownership.matrix": detect_ownership,
    "ownership.metadata": detect_metadata,
    "ownership.lifecycle": detect_lifecycle,
    "manifest.paths": detect_manifest_paths,
    "manifest.coverage": detect_manifest_coverage,
    "manifest.consistency": detect_manifest_consistency,
    "graph.validator": detect_graph_validator,
    "graph.deep-rebuild": detect_graph_deep_rebuild,
    "graph.census": detect_graph_census,
    "graph.completeness": detect_graph_completeness,
    "graph.consistency": detect_graph_consistency,
    "generated.stale-banner": detect_generated_stale,
    "generated.fences": detect_fence_integrity,
    "generated.hand-edit": detect_hand_edits,
    "dataset.registry": detect_dataset_registry,
    "dataset.spec-version": detect_spec_version_pins,
    "dataset.golden-agreement": detect_golden_spec_agreement,
    "verification.registry": detect_verification_registry,
    "verification.citations": detect_citation_integrity,
    "verification.report-schema": detect_report_schema_dependency,
}

# SYNC-D7 (ratified): the expensive tiers live behind --deep — and a deep-gated
# detector that doesn't run is RECORDED in the envelope, never silently skipped.
DEEP_ONLY = frozenset({"graph.deep-rebuild", "generated.hand-edit"})


class Command(BaseCommand):
    help = ("Detect knowledge drift across code/docs/graph/generated/registry "
            "boundaries — read-only; findings name their owning repair venue; "
            "no --fix exists, by design.")

    def add_arguments(self, parser):
        parser.add_argument("--diff", action="store_true",
                            help="Changed-files scope (read-only git) instead of the full sweep.")
        parser.add_argument("--deep", action="store_true",
                            help="Include expensive tiers (declared per detector).")
        parser.add_argument("--report", default=None, metavar="DIR",
                            help="Report directory (default var/knowledge_sync_reports/).")
        parser.add_argument("--skip", action="append", default=[], metavar="DETECTOR",
                            help="Exclude a detector — recorded in the report envelope, never silent.")

    def handle(self, *args, **options):
        mode = "diff" if options["diff"] else ("deep" if options["deep"] else "sweep")
        self.stdout.write(f"knowledge_sync — engine v{SYNC_ENGINE_VERSION} — mode: {mode} "
                          f"(pure detector; findings are routed, never repaired)")
        skips = sorted(set(options.get("skip", [])))
        findings, skipped = [], [s for s in skips if s in DETECTORS]
        for det_id, detector in sorted(DETECTORS.items()):
            if det_id in skips:
                continue
            if det_id in DEEP_ONLY and not options["deep"]:
                skipped.append(f"{det_id} (deep-gated)")
                continue
            findings.extend(detector(diff=options["diff"], deep=options["deep"]))
        findings = apply_acceptance(findings)
        from devseed.knowledge.acceptance import ACCEPTED_FINDINGS
        stale_acceptance = sorted(set(ACCEPTED_FINDINGS)
                                  - {f.id for f in findings})
        report = build_sync_report(mode=mode, findings=findings,
                                   skipped_detectors=skipped,
                                   registered_detectors=len(DETECTORS),
                                   stale_acceptance=stale_acceptance)
        path = write_report(report, options.get("report"))
        render_stdout(report, self.stdout.write)
        self.stdout.write(f"report: {path}")
        self.stdout.write(f"NOTE: {len(DETECTORS)} detectors registered "
                          "(all 8 domains: docs KS-B · graph/generation KS-C · registries KS-D).")
        code = exit_code(report)
        if code:
            raise CommandError(
                f"knowledge drift at/above threshold: {code} unaccepted BLOCKER(s) — "
                f"repair via the venues named per finding (the detector never fixes).")

"""Domain 7 — dataset-specification drift (KS-D; inherited contract: the
PHASE_12 SEED-F handoff §SEED-F.5.2 — registry drift, declared-vs-implemented,
SPEC_VERSION pinning — over the frozen DEV_DATASET_ARCHITECTURE spec §7/§10).

EXTEND-NEVER-FORK: the registries are READ from their single sources
(`devseed.scenarios.SCENARIOS` · `devseed.core.CONTENT` · `devseed.guard.
SPEC_VERSION` · `verification.report.SPEC_VERSION` · the spec document) —
nothing is redefined here. READ-ONLY; injection parameters for tests."""

import os
import re

from devseed.knowledge import INFO, WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT

SPEC_PATH = os.path.join(REPO_ROOT, "docs", "DEV_DATASET_ARCHITECTURE.md")

# The spec §7 closed taxonomy (six classes — DATA-D4 ratified).
TAXONOMY = ("minimal", "full-demo", "feature", "performance", "regression", "edge-case")


def _spec_text(reader=None):
    if reader is not None:
        return reader()
    return open(SPEC_PATH, encoding="utf-8").read()


def detect_dataset_registry(diff=False, deep=False, *, scenarios=None, content=None):
    """Registry shape · implemented-state · completeness (SEED-F: declared vs
    implemented, four-surface agreement — here the two machine surfaces)."""
    if scenarios is None:
        from devseed.scenarios import SCENARIOS as scenarios
    if content is None:
        from devseed.core import CONTENT as content
    findings = []
    goldens = {}
    for slug, meta in sorted(scenarios.items()):
        if meta.get("class") not in TAXONOMY:
            findings.append(Finding(
                id=f"d7.registry.invalid-class:{slug}", domain="dataset-spec",
                severity=WARN,
                evidence={"slug": slug, "class": meta.get("class"),
                          "taxonomy": list(TAXONOMY)},
                venue="spec-registry"))
        if meta.get("implemented") and slug not in content:
            findings.append(Finding(
                id=f"d7.registry.declared-without-content:{slug}", domain="dataset-spec",
                severity=WARN,
                evidence={"slug": slug,
                          "rule": "implemented:True requires engine CONTENT (SEED-F drift class)"},
                venue="spec-registry"))
        if meta.get("expected"):
            goldens.setdefault(meta["expected"], []).append(slug)
    for slug in sorted(set(content) - set(scenarios)):
        findings.append(Finding(
            id=f"d7.registry.implemented-not-declared:{slug}", domain="dataset-spec",
            severity=WARN,
            evidence={"slug": slug,
                      "rule": "engine CONTENT without a registry declaration (SEED-F drift class)"},
            venue="spec-registry"))
    for value, slugs in sorted(goldens.items()):
        if len(slugs) > 1:
            findings.append(Finding(
                id=f"d7.registry.duplicate-golden:{value}", domain="dataset-spec",
                severity=INFO,
                evidence={"expected": value, "slugs": slugs,
                          "note": "two regression worlds share one golden — ambiguity hygiene"},
                venue="spec-registry"))
    return findings


def detect_spec_version_pins(diff=False, deep=False, *, devseed_pin=None,
                             engine_pin=None, spec_reader=None):
    """The THREE-WAY SPEC_VERSION pin (SEED-F: spec-version pinning; the P13
    cross-pin extended to the frozen document itself, spec §10 semver)."""
    if devseed_pin is None:
        from devseed.guard import SPEC_VERSION as devseed_pin
    if engine_pin is None:
        from verification.report import SPEC_VERSION as engine_pin
    m = re.search(r"\*\*v(\d+\.\d+\.\d+)", _spec_text(spec_reader))
    doc_pin = m.group(1) if m else None
    if devseed_pin == engine_pin == doc_pin:
        return []
    return [Finding(
        id="d7.spec-version.mismatch", domain="dataset-spec", severity=WARN,
        evidence={"devseed.guard": devseed_pin, "verification.report": engine_pin,
                  "DEV_DATASET_ARCHITECTURE §10": doc_pin},
        venue="spec-registry")]


def detect_golden_spec_agreement(diff=False, deep=False, *, scenarios=None,
                                 spec_reader=None):
    """Scenario drift (SEED-F golden three-way, the two document surfaces):
    the registry's regression expected values must all appear in the frozen
    spec §7 text (owner change-control — a value moved on one side only =
    drift, dated-amendment territory)."""
    if scenarios is None:
        from devseed.scenarios import SCENARIOS as scenarios
    text = _spec_text(spec_reader)
    findings = []
    for slug, meta in sorted(scenarios.items()):
        exp = meta.get("expected")
        if exp and f"₹{exp}" not in text and exp not in text:
            findings.append(Finding(
                id=f"d7.golden.spec-disagreement:{slug}", domain="dataset-spec",
                severity=WARN,
                evidence={"slug": slug, "registry_expected": exp,
                          "rule": "spec §7 golden values = owner change-control"},
                venue="spec-registry"))
    return findings

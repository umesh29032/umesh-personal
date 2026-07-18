"""Domain 8 — verification-registry drift (KS-D; inherited contract: the
PHASE_13 handoff §VER-E.3.1/3.2 — the certified 19-check census · the VER-D4
citation law · the VER-D certified report schema).

EXTEND-NEVER-FORK: the live registry is the Phase-13 `verification.checks`
package itself (statically read — running dev-world checks needs seeded
worlds); the certified CENSUS and SCHEMA baselines below are the P13
CERTIFICATION artifacts quoted as drift references (VER-E §1 · VER-D §1) —
references, not re-implementations. READ-ONLY; injection for tests."""

import os
import re

from devseed.knowledge import WARN, Finding
from devseed.knowledge.d1_code_docs import REPO_ROOT

CHECKS_DIR = os.path.join(REPO_ROOT, "config", "verification", "checks")

# THE CERTIFIED CHECK-ID CENSUS (PHASE_13 VER-E §1 — 19 ids; the drift baseline).
CERTIFIED_CHECK_IDS = frozenset({
    "dev.manifest.spec-version", "dev.manifest.database-match",
    "dev.manifest.assertions-recorded", "dev.assertions.rerun",
    "dev.golden.settlement-total", "dev.golden.worker-items",
    "dev.smoke.app-registry", "dev.smoke.urlconf", "dev.smoke.render-critical",
    "prod.contamination.dev-namespace", "prod.safety.flags-vs-declaration",
    "prod.safety.migrations-consistent", "prod.safety.settings-sanity",
    "prod.integrity.settlement-items-sum", "prod.integrity.ledger-reversals-net",
    "prod.integrity.constraint-ledger-amount-positive",
    "prod.integrity.constraint-wsc-gam-nonneg", "prod.integrity.supersession-chain",
    "all.composition",
})

# THE CERTIFIED REPORT SCHEMA (PHASE_13 VER-D §1 — engine 1.0.0 key sets).
CERTIFIED_ENVELOPE_KEYS = frozenset({
    "command", "engine_version", "spec_version", "environment", "totals",
    "skipped_categories", "body_hash", "ran_at"})
CERTIFIED_BODY_KEYS = frozenset({"id", "citation", "category", "status", "measured"})

# Citation → resolvable repo target (the A-4 resolution table, KS-D design
# within VER-D4's wording: cited sources must EXIST).
CITATION_TARGETS = (
    ("DEV_DATASET_ARCHITECTURE", "docs/DEV_DATASET_ARCHITECTURE.md"),
    ("ARCHITECTURE_V2", "docs/ARCHITECTURE_V2.md"),
    ("PHASE_13", "docs/campaign_contracts/PHASE_13_VERIFICATION_ENGINE.md"),
    ("PHASE_12", "docs/campaign_contracts/PHASE_12_SEEDER_ENGINE.md"),
    ("SEED-D5", "docs/campaign_contracts/PHASE_12_SEEDER_ENGINE.md"),
    ("U10", "docs/campaign_contracts/README.md"),
    ("DB-Integrity", "docs/adr"),                     # the CheckConstraints record family
    ("SEED-C W2", "docs/SEEDER_ENGINE_LOG.md"),
)

# id/citation extraction from the checks source (ids are literals or f-strings
# with the {prefix} hole; the citation is the next string literal).
_CALL = re.compile(
    r'(?:_r|CheckResult)\(\s*(?:id=)?f?"(?P<id>[^"]+)",\s*\n?\s*'
    r'(?:citation=)?"(?P<cite>[^"]*)')


def extract_registry(source_by_file=None):
    """(check_id, citation, file) triples statically read from the P13 checks
    package — the machine-readable registry surface."""
    if source_by_file is None:
        source_by_file = {}
        for fn in sorted(os.listdir(CHECKS_DIR)):
            if fn.endswith(".py"):
                source_by_file[fn] = open(os.path.join(CHECKS_DIR, fn),
                                          encoding="utf-8").read()
    rows = []
    for fn, src in sorted(source_by_file.items()):
        for m in _CALL.finditer(src):
            cid = m.group("id").replace("{prefix}", "").replace("{pfx}", "")
            rows.append((cid, m.group("cite"), fn))
    return rows


def detect_verification_registry(diff=False, deep=False, *, rows=None):
    """Census drift both directions vs the CERTIFIED 19-id baseline (VER-E §1)
    + machine-readability (an empty extraction = the registry stopped being
    statically readable)."""
    if rows is None:
        rows = extract_registry()
    live = {cid for cid, _, _ in rows}
    findings = []
    if not live:
        return [Finding(id="d8.registry.unreadable", domain="verification-registry",
                        severity=WARN,
                        evidence={"rule": "P13 registry must stay machine-readable (VER-E handoff)"},
                        venue="spec-registry")]
    for cid in sorted(live - CERTIFIED_CHECK_IDS):
        findings.append(Finding(
            id=f"d8.registry.uncertified-check:{cid}", domain="verification-registry",
            severity=WARN,
            evidence={"check": cid,
                      "rule": "a check outside the VER-E certified census = registry drift "
                              "(census change ⇒ dated P13 amendment)"},
            venue="spec-registry"))
    for cid in sorted(CERTIFIED_CHECK_IDS - live):
        findings.append(Finding(
            id=f"d8.registry.missing-check:{cid}", domain="verification-registry",
            severity=WARN,
            evidence={"check": cid, "rule": "certified check vanished from the registry"},
            venue="spec-registry"))
    return findings


def detect_citation_integrity(diff=False, deep=False, *, rows=None,
                              path_exists=None):
    """VER-D4: every check carries a citation, and cited sources RESOLVE
    (file-level, per the A-4 table). Empty citation or dead target → WARN."""
    if rows is None:
        rows = extract_registry()
    exists = path_exists or (lambda p: os.path.exists(os.path.join(REPO_ROOT, p)))
    findings = []
    for cid, cite, fn in sorted(rows):
        if not cite.strip():
            findings.append(Finding(
                id=f"d8.citation.missing:{cid}", domain="verification-registry",
                severity=WARN,
                evidence={"check": cid, "file": fn,
                          "rule": "VER-D4: uncited checks don't merge"},
                venue="spec-registry"))
            continue
        for token, target in CITATION_TARGETS:
            if token in cite and not exists(target):
                findings.append(Finding(
                    id=f"d8.citation.broken:{cid}:{token}",
                    domain="verification-registry", severity=WARN,
                    evidence={"check": cid, "cites": token, "expected_target": target},
                    venue="spec-registry"))
    return findings


def detect_report_schema_dependency(diff=False, deep=False, *, envelope_keys=None,
                                    body_keys=None):
    """The VER-D certified schema (engine 1.0.0) is a DEPENDENCY of Phases
    19/20/21 (they cite envelope + body-hash): key-set drift without a dated
    amendment = registry drift. The hard tripwire lives in the P13 battery;
    this is the report-side re-check."""
    if envelope_keys is None or body_keys is None:
        from verification.report import CheckResult, build_report
        sample = build_report(command="knowledge_sync.schema-probe",
                              environment="dev",
                              results=[CheckResult(id="x", citation="probe",
                                                   category="integrity", status="pass")])
        envelope_keys = frozenset(sample["envelope"])
        body_keys = frozenset(sample["body"][0])
    findings = []
    if envelope_keys != CERTIFIED_ENVELOPE_KEYS:
        findings.append(Finding(
            id="d8.schema.envelope-drift", domain="verification-registry",
            severity=WARN,
            evidence={"extra": sorted(envelope_keys - CERTIFIED_ENVELOPE_KEYS),
                      "missing": sorted(CERTIFIED_ENVELOPE_KEYS - envelope_keys),
                      "rule": "VER-D certified schema; P19/20/21 depend on it"},
            venue="spec-registry"))
    if body_keys != CERTIFIED_BODY_KEYS:
        findings.append(Finding(
            id="d8.schema.body-drift", domain="verification-registry",
            severity=WARN,
            evidence={"extra": sorted(body_keys - CERTIFIED_BODY_KEYS),
                      "missing": sorted(CERTIFIED_BODY_KEYS - body_keys)},
            venue="spec-registry"))
    return findings

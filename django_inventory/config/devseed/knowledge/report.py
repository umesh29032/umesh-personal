"""devseed.knowledge.report — sync reports (SYNC-D5: the P13 envelope/body
CONVENTIONS reused verbatim as FORMAT law — deterministic sorted body, no
timestamps/randomness in the body, sha256 body-hash in the envelope, the run
timestamp as the ONLY volatile field, skips always printed. The row shape is
sync-specific (findings carry domain/severity/venue, not pass/fail), which is
why this module implements the conventions rather than importing the P13
CheckResult pipeline — the single-source law of THIS contract targets
validators/generators/registries, and those are imported, never re-implemented.

THE ONLY WRITE SITE in the knowledge package: `write_report` → the report
directory (default repo-root `var/knowledge_sync_reports/`, gitignored
runtime). The purity suite pins this module as the sole writer and pins the
target out of the corpus."""

import hashlib
import json
import os
from datetime import datetime, timezone

from devseed.knowledge import BLOCKER, SEVERITIES

# The sync engine's own version (envelope field; certified at KS-D).
SYNC_ENGINE_VERSION = "0.1.0"

# Repo-root var/ (gitignored) — cwd-independent (the P12/P13 pattern).
DEFAULT_REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "var", "knowledge_sync_reports")

# SYNC-D3 ratified default: any BLOCKER fails the exit code.
FAILURE_THRESHOLD = BLOCKER


def build_sync_report(*, mode, findings, skipped_detectors=(), registered_detectors=0,
                      stale_acceptance=()):
    """Envelope + deterministic body. Body = finding rows sorted by id;
    envelope carries totals per severity, acceptance count, STALE acceptance
    entries (an acceptance for a finding that no longer fires = hygiene drift,
    KS-D — surfaced, never silently carried), the body hash and the ONLY
    timestamp."""
    body = [f.as_body_row() for f in sorted(findings, key=lambda f: f.id)]
    body_json = json.dumps(body, sort_keys=True, separators=(",", ":"))
    totals = {sev: sum(1 for f in findings if f.severity == sev) for sev in SEVERITIES}
    totals["accepted"] = sum(1 for f in findings if f.accepted)
    envelope = {
        "command": "knowledge_sync",
        "engine_version": SYNC_ENGINE_VERSION,
        "mode": mode,                       # sweep | diff | deep
        "threshold": FAILURE_THRESHOLD,
        "registered_detectors": registered_detectors,
        "totals": totals,
        "skipped_detectors": sorted(skipped_detectors),  # never silent
        "stale_acceptance": sorted(stale_acceptance),    # never silent either
        "body_hash": hashlib.sha256(body_json.encode("utf-8")).hexdigest(),
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }
    return {"envelope": envelope, "body": body}


def write_report(report, report_dir=None):
    d = report_dir or DEFAULT_REPORT_DIR
    os.makedirs(d, exist_ok=True)
    stamp = report["envelope"]["ran_at"].replace(":", "").replace("+", "Z")
    path = os.path.join(d, f"knowledge_sync-{stamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    return path


def render_stdout(report, write):
    e = report["envelope"]
    write(f"knowledge_sync — engine v{e['engine_version']} · mode={e['mode']} "
          f"· threshold={e['threshold']} · detectors={e['registered_detectors']}")
    for row in report["body"]:
        flag = " (accepted)" if row["accepted"] else ""
        write(f"  [{row['severity']:7}] {row['id']} — {row['domain']} → {row['venue']}{flag}")
    if e["skipped_detectors"]:
        write(f"  skipped detectors (explicit): {', '.join(e['skipped_detectors'])}")
    if e.get("stale_acceptance"):
        write(f"  STALE acceptance entries (no matching finding): "
              f"{', '.join(e['stale_acceptance'])}")
    t = e["totals"]
    write(f"totals: BLOCKER={t['BLOCKER']} WARN={t['WARN']} INFO={t['INFO']} "
          f"accepted={t['accepted']} body_hash={e['body_hash'][:16]}…")


def exit_code(report):
    """0 = nothing at/above the ratified threshold (unaccepted); nonzero = the
    count. Accepted findings never fail the exit — they are still PRINTED."""
    if FAILURE_THRESHOLD == BLOCKER:
        n = sum(1 for row in report["body"]
                if row["severity"] == BLOCKER and not row["accepted"])
        return min(n, 250)
    raise AssertionError("unratified threshold")  # SYNC-D3 change = owner + dated amendment

"""verification.report — report envelope + deterministic body (VER-D5).

Machine report = JSON: ENVELOPE (command, engine/spec versions, environment,
run timestamp, totals, body-hash) + BODY (sorted check results — id, citation,
category, status, measured values; NO timestamps or randomness). Determinism =
body-stable: two runs on an unchanged world produce byte-identical bodies, so
the body-hash in the envelope is the comparison surface (VER-D wave proof).
Reports land in repo-root `var/verification_reports/` (gitignored runtime);
binding results are QUOTED into campaign/deployment records by the humans who
cite them. No silent skips: skipped categories are recorded in the envelope.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

# The engine's version (envelope field). 1.0.0 = the VER-D certification
# (report schema + determinism certified; schema changes from here = a new
# engine version + a dated Design-Record amendment).
ENGINE_VERSION = "1.0.0"

# The dataset-spec pin (DEV_DATASET_ARCHITECTURE.md §10). Mirrors
# devseed.guard.SPEC_VERSION — devseed is dev-only, so the production-present
# engine carries its own copy; the cross-pin test keeps them identical
# (divergence = a Phase-14 drift signal, red battery here).
SPEC_VERSION = "1.0.0"

# Repo-root var/ (gitignored) — cwd-independent, devseed manifest-dir pattern.
DEFAULT_REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "var", "verification_reports")


@dataclass(frozen=True)
class CheckResult:
    """One check outcome. `citation` = the certified invariant it codifies
    (VER-D4: manifest rule / spec § / ADR / golden value / CheckConstraint
    class) — a result without a citation must never be constructed."""

    id: str
    citation: str
    category: str          # smoke | golden | production-safety | dev-contamination | integrity
    status: str            # pass | fail | skip
    measured: dict = field(default_factory=dict)

    def as_body_row(self):
        return {
            "id": self.id, "citation": self.citation, "category": self.category,
            "status": self.status, "measured": self.measured,
        }


def build_report(*, command, environment, results, skipped_categories=()):
    """Assemble envelope + body. Body = results sorted by id (deterministic);
    envelope carries totals, the body hash, and the ONLY timestamp."""
    body = [r.as_body_row() for r in sorted(results, key=lambda r: r.id)]
    body_json = json.dumps(body, sort_keys=True, separators=(",", ":"))
    totals = {
        "pass": sum(1 for r in results if r.status == "pass"),
        "fail": sum(1 for r in results if r.status == "fail"),
        "skip": sum(1 for r in results if r.status == "skip"),
    }
    envelope = {
        "command": command,
        "engine_version": ENGINE_VERSION,
        "spec_version": SPEC_VERSION,
        "environment": environment,
        "totals": totals,
        "skipped_categories": sorted(skipped_categories),  # no silent skips
        "body_hash": hashlib.sha256(body_json.encode("utf-8")).hexdigest(),
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }
    return {"envelope": envelope, "body": body}


def write_report(report, report_dir=None):
    d = report_dir or DEFAULT_REPORT_DIR
    os.makedirs(d, exist_ok=True)
    stamp = report["envelope"]["ran_at"].replace(":", "").replace("+", "Z")
    path = os.path.join(d, f"{report['envelope']['command']}-{stamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    return path


def render_stdout(report, write):
    """Human view (one line per check + totals). `write` = command stdout.write."""
    e = report["envelope"]
    write(f"{e['command']} — engine v{e['engine_version']} · spec v{e['spec_version']} "
          f"· env={e['environment']}")
    for row in report["body"]:
        write(f"  [{row['status'].upper():4}] {row['id']} — {row['citation']}")
    if e["skipped_categories"]:
        write(f"  skipped categories (explicit): {', '.join(e['skipped_categories'])}")
    t = e["totals"]
    write(f"totals: pass={t['pass']} fail={t['fail']} skip={t['skip']} "
          f"body_hash={e['body_hash'][:16]}…")


def exit_code(report):
    """0 = all green; nonzero = any red (count, capped for shell safety)."""
    return min(report["envelope"]["totals"]["fail"], 250)

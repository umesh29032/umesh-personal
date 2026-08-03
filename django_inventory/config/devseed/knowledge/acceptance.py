"""devseed.knowledge.acceptance — the VISIBLE acceptance-list mechanics
(SYNC-D3/D5: known-and-accepted findings are a REPORT feature — dated,
owner-attributed, ALWAYS printed — never a silent filter; acceptance decisions
are owner records quoted into KNOWLEDGE_SYNC_LOG, the var/ copy is never the
only record).

Entries live HERE in code (reviewed like any change; the owner attribution is
part of the entry). An accepted finding keeps its severity and stays in every
report — acceptance only exempts it from the exit-code threshold.

KS-A state: mechanics + an EMPTY list.
"""

# finding-id → {"date": "YYYY-MM-DD", "owner": "<who accepted>", "reason": "<why>"}
ACCEPTED_FINDINGS = {}


def apply_acceptance(findings):
    """Mark accepted findings (immutable Finding → replaced copy). Unknown
    acceptance entries are surfaced by the sweep (a stale acceptance is itself
    hygiene drift — wired with the detectors at KS-D)."""
    from dataclasses import replace
    out = []
    for f in findings:
        out.append(replace(f, accepted=True) if f.id in ACCEPTED_FINDINGS else f)
    return out

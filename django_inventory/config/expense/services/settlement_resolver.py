"""Settlement quantity resolver (Foundation S1 — addendum M-5/M-6/M-7 seam).

The SINGLE place that decides which quantity a settlement pays for one
`WorkerStageContribution`. Extracting it now (behaviour-preserving) means future
policies (packed / hybrid) plug in HERE without touching the money-write, and the
good/alter/missing split (S3) changes exactly one line.

Default `STAGE_GOOD` == `verified_quantity if set else good_quantity` (S3). Because
`good_quantity` is NOT NULL + backfilled = `reported_quantity` and dual-written equal
through S3→S5, this stays behaviour-preserving — the golden ₹225 supersede chain
reconciles byte-identically (the merge gate). Settlement pays GOOD, never the raw
claim: the structural close of the B-1 leak (pay 105 good, not 120 claimed).
"""

STAGE_GOOD = 'stage_good'   # the only implemented policy (= verified-else-good)


def settlement_quantity(contribution, policy=STAGE_GOOD):
    """Quantity a settlement pays for `contribution` under `policy`.

    STAGE_GOOD: verified_quantity (management correction) if set, else good_quantity
    (the payable-good production truth, S3). good_quantity is NOT NULL so no fallback
    needed. Future policies (packed / hybrid) plug in here without touching the money-write.
    """
    if policy == STAGE_GOOD:
        c = contribution
        return (c.verified_quantity
                if c.verified_quantity is not None
                else c.good_quantity)
    raise ValueError(f"Unknown settlement quantity policy: {policy!r}")

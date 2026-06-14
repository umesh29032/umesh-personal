"""Settlement quantity resolver (Foundation S1 — addendum M-5/M-6/M-7 seam).

The SINGLE place that decides which quantity a settlement pays for one
`WorkerStageContribution`. Extracting it now (behaviour-preserving) means future
policies (packed / hybrid) plug in HERE without touching the money-write, and the
good/alter/missing split (S3) changes exactly one line.

Default `STAGE_GOOD` == today's rule (`verified_quantity if set else
reported_quantity`), so the golden ₹225 supersede chain must reconcile
byte-identically before/after this extraction (the S1 merge gate).
"""

STAGE_GOOD = 'stage_good'   # the only implemented policy in S1 (= current behaviour)


def settlement_quantity(contribution, policy=STAGE_GOOD):
    """Quantity a settlement pays for `contribution` under `policy`.

    STAGE_GOOD: verified_quantity (management correction) if set, else the
    worker's reported_quantity. (Post-S3 `reported_quantity` becomes `good_quantity`
    — this is the single line that will change; settlement money-write stays put.)
    """
    if policy == STAGE_GOOD:
        c = contribution
        return (c.verified_quantity
                if c.verified_quantity is not None
                else c.reported_quantity)
    raise ValueError(f"Unknown settlement quantity policy: {policy!r}")

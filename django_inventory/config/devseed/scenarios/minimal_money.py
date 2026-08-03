"""Scenario content — `feature-settlement` (spec §7 feature class, layers
2·3·4·6·7·8): THE minimal deterministic money world. Its golden value is
COMPUTED FROM ITS OWN SEEDED CONFIG (owner Wave-1 ruling — deterministic, no
invented history): 50 good @ ₹2/pc (cutting) + 50 good @ ₹1/pc (stitching)
= **₹150.00** settled, credited to dev.min.worker via the single writer.

Also extends `minimal` with its declared layer-7 journey (no money)."""

from devseed.scenarios.minimal import MINIMAL

_JOURNEY = {
    "adda_code": "DEV-MIN-TEE-001",  # deterministic service-issued code on a fresh world (product code + seq)
    "manager": "dev.min.mgr@test.local",
    "worker": "dev.min.worker@test.local",
    "layering": {
        "completer": "dev.min.sa@test.local",  # SA bypass for the cutting_master_helper gate
        "width_inch": 36, "weight_kg": "25.00",
        "layers": 40, "leftover_kg": "2.50",
        "duration_minutes": 30, "layer_length_m": "1.10",
    },
    "cutting": {"pieces": 50},  # legacy single-shot completion (NIKKAR-style)
    "stages": [
        {"stage": "dev-min-stitching", "good": 50},
    ],
}

# ONE cost config for the whole DEV-MIN world family. minimal and
# feature-settlement CONVERGE on the SAME world (same adda handle) — on a
# shared DB either may seed it first, so the journey must complete under
# identical config regardless of order (SEED-D finding: a rate-less minimal
# journey freezes expected_earning=0 and the ₹150 golden dies). Cost config is
# layer-4 CONFIG, not money — settlement stays the only money boundary.
_STAGE_COSTS = [
    # layering + cutting: no cost config (rate must be >0 when set —
    # flow_service law); ONE payable stage keeps the golden arithmetic
    # single-sourced: 50 good × ₹3 = ₹150.00.
    {"stage": "dev-min-stitching", "method": "per_piece", "rate": "3", "credits": True},
]

# minimal (layers 2,3,4,6,7): the journey WITHOUT money movement.
MINIMAL_WITH_JOURNEY = {
    **MINIMAL,
    "cast": [
        {**MINIMAL["cast"][0]},
        {**MINIMAL["cast"][1]},
        {**MINIMAL["cast"][2], "skills": "*"},  # worker needs skill-gated stage access
    ],
    "stage_costs": _STAGE_COSTS,
    "adda_journey": _JOURNEY,
}

# feature-settlement (layers 2,3,4,6,7,8): the same world + settle.
MINIMAL_MONEY = {
    **MINIMAL_WITH_JOURNEY,
    "slug": "feature-settlement",
    "settlement": {
        # 50 × 3 — derived from THIS file's config, asserted byte-exact.
        "expected_total": "150.00",
        "manager": "dev.min.mgr@test.local",
    },
}

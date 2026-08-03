"""devseed.scenarios — the scenario registry (spec §7 taxonomy, machine-readable).

SEED-A state: registry DECLARES every spec scenario id; nothing is implemented
yet (implemented=False everywhere). Implementations land wave-by-wave
(SEED-B..E); `seed_feature <slug>` validates against THIS dict; Phase 14 reads
it for spec⇄implementation drift detection (PHASE_12 §6.7 handoff).
"""

# The spec pin (SPEC_VERSION) is deliberately NOT re-exported here — it lives in
# devseed.guard and every consumer imports it from there. It used to be imported into
# this namespace purely to document that fact, which ruff correctly read as an unused
# import (F401); a comment documents it without creating a second import path.

# Each entry: class per spec §7 + the layers (spec §2 numbering) it will drive.
# Golden expected values are quoted from the spec §7 (owner-change-control).
SCENARIOS = {
    # core worlds
    "minimal": {"class": "minimal", "layers": (2, 3, 4, 6, 7), "implemented": True},
    "demo": {"class": "full-demo", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
             "note": "seed_demo target — minimal-plus single settled journey (SEED-D2 ruling; layers = actual, SEED-D)"},
    "factory": {"class": "full-demo", "layers": (2, 3, 4, 5, 6, 7, 8), "implemented": True,
                "note": "seed_factory target — composite: T-SHIRT + LOWER + 3-PATTI golden worlds + machines slice (SEED-D2)"},
    # feature slices (spec §7 feature class)
    "feature-allocation": {"class": "feature", "layers": (2, 3, 4, 6, 7), "implemented": True,
                           "note": "QUANTITY grain + real WorkerStageAllocation via pool_service (SEED-D)"},
    "feature-settlement": {"class": "feature", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                           "note": "THE deterministic money world — golden ₹150.00 computed from its own seeded rates (SEED-C wave-1)"},
    "feature-fnf": {"class": "feature", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                    "note": "dedicated leaver cast dev.min.leaver (spec §11 class) → fnf_execute deactivates (SEED-D)"},
    "feature-machines": {"class": "feature", "layers": (2, 3, 5), "implemented": True,
                         "note": "machine + open possession window via machine_service.assign (SEED-D)"},
    "feature-patterns-ai": {"class": "feature", "layers": (2, 3, 4, 10), "implemented": True,
                            "note": "sizes + register_pattern_definition (SEED-D)"},
    "feature-storefront": {"class": "feature", "layers": (2, 3, 9), "implemented": True,
                           "note": "Category/FeaturedProduct — audited plain-ORM exception, purity-pinned (SEED-D)"},
    "feature-tracking-exports": {"class": "feature", "layers": (2, 3, 4, 6, 7, 11), "implemented": True,
                                 "note": "no barcode stage in flow → cutting inline-generates; post asserts BarcodeBatch>0 (SEED-D)"},
    "feature-bod": {"class": "feature", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                    "note": "BOD demo world (D8, spec amendment A2, BOD-F 2026-07-18): settled journey + one DEV factory expense; post asserts the board's owning services light up (digest/monthly_totals)"},
    "feature-monthly-expense": {"class": "feature", "layers": (2, 3), "implemented": True,
                                "note": "Monthly Expense Engine world (MEE-E, spec amendment A3, 2026-07-18): rent+salary templates via the certified writers → generated 2026-07 period → one voided example; converging (skip-not-duplicate)"},
    "feature-rm-expense": {"class": "feature", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                           "note": "Phase-17 proof world (RMX-F, spec amendment A4, 2026-07-18): unpriced-consumed roll (banner world) + priced unconsumed roll + damaged roll + the REAL leftover chain (journey remnant consume_leftover'd into a second adda) — the one-rupee-once fixtures"},
    # regression worlds (golden values = business truth, owner-change-control)
    "regression-tshirt": {"class": "regression", "expected": "801.00", "implemented": True, "layers": (2, 3, 4, 6, 7, 8),
                          "note": "W2-F5 replay-only adjustment (owner 2026-07-17)"},
    "regression-lower": {"class": "regression", "expected": "344.25", "implemented": True, "layers": (2, 3, 4, 6, 7, 8),
                          "note": "W2-F5 replay-only adjustment (owner 2026-07-17)"},
    "regression-3patti": {"class": "regression", "expected": "633.00", "implemented": True, "layers": (2, 3, 4, 6, 7, 8),
                          "note": "W2-F5 replay-only adjustment (owner 2026-07-17)"},
    # Spec amendment A1 (2026-07-17, owner option (b)): ₹225 = HISTORICAL evidence,
    # not a standalone executable regression until an authoritative recipe exists.
    "regression-settlement-225": {"class": "regression", "expected": None, "implemented": False,
                                  "note": "historical-evidence-only per spec §12 A1; living guard = settlement-suite goldens"},
    # edge-case worlds (spec §7 — the certified hard cases; all SEED-D)
    "edge-overallocation-m6": {"class": "edge-case", "layers": (2, 3, 4, 6, 7), "implemented": True,
                               "note": "pool_service refusal captured verbatim (always-on, beyond M-6 flag)"},
    "edge-damaged-rolls": {"class": "edge-case", "layers": (2, 3, 6), "implemented": True,
                           "note": "mark_roll_damaged → restore_damaged_roll, audited both ways"},
    "edge-monthly-worker": {"class": "edge-case", "layers": (2, 3), "implemented": True,
                            "note": "set_pay_basis MONTHLY via the payroll chokepoint (audited)"},
    "edge-inactive-users": {"class": "edge-case", "layers": (2, 3), "implemented": True},
    "edge-reopen-guard": {"class": "edge-case", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                          "note": "reopen_layering refusal on settled world (S4-P5 downstream guard)"},
    "edge-composite-roles": {"class": "edge-case", "layers": (2, 3), "implemented": True,
                             "note": "manager + extra_roles accountant (PHASE_03 D1 class)"},
    "edge-rate-correction": {"class": "edge-case", "layers": (2, 3, 4, 6, 7), "implemented": True,
                             "note": "rerate_stage_role pre-settlement + RateCorrectionAudit (S1.1)"},
    "edge-settlement-supersession": {"class": "edge-case", "layers": (2, 3, 4, 6, 7, 8), "implemented": True,
                                     "note": "reverse(supersede=True) → finalized successor chain (ADST-0007→0008 class)"},
    # performance class — targets OWNER-DEFERRED (spec §7 / DATA-D6 ruling
    # 2026-07-17); arrives only via a dated spec amendment.
    "performance": {"class": "performance", "implemented": False,
                    "note": "volume targets owner-deferred — dated spec amendment required"},
}


def valid_slugs():
    return sorted(SCENARIOS)


def spec_classes_present():
    return sorted({s["class"] for s in SCENARIOS.values()})

"""SEED-C Wave-2 — the three executable golden-journey RECIPES, extracted
2026-07-17 read-only from the certified primary DB (ADST-0004/0005/0006) +
FACTORY_OPERATIONS_MASTER §9/§10/§12. NOTHING invented: flows, rates,
rosters, per-line dims (good/alter/missing/verified), cutting breakdowns
(= the APSCPB aggregates), and completion modes all transcribe production
truth. The golden totals are NOT hardcoded into the replay — they are the
ASSERTION targets; the totals must EMERGE from rates × good quantities
through the certified services (owner Wave-2 mandate).

Input-reconstruction notes (classified in SEEDER_ENGINE_LOG §SEED-C W2):
- W2-F2: roll/cloth-master identities are money-invariant (layering pays
  nothing in these journeys) — reconstructed with DEV-marked masters.
- W2-F5 (owner-approved 2026-07-17, REPLAY-ONLY classified adjustment):
  cutting/cutting_pattern carry `credits: False` IN THESE RECIPES ONLY.
  Historical state: the certified journeys completed those PAYABLE stages
  with zero worker credit and no cost freeze (all six SRs:
  processing_cost=None, cost_frozen_at=None) — possible under the then-live
  completion paths. Current law: ensure_worker_credit (PA-10-1) refuses
  completing a payable stage with no completed contribution — the two cannot
  coexist. Why truth is preserved: the certified settlements contain ZERO
  cutting/cutting_pattern earnings (per-worker items = exactly the per-piece
  stages), so payability-off reproduces the historical MONEY byte-identically
  while every current validation stays fully armed. Primary production
  configuration is untouched; no service modified; no validation bypassed.
- Breakup source rows were cleaned post-completion by the streams redesign;
  the APSCPB aggregate IS the preserved truth; the pattern dimension is
  collapsed-by-design (cutting service docstring) — one assigned pattern is
  used for reconstruction.
"""

W = "@test.local"

_CAST = [
    {"handle": "dev.jrn.sa" + W, "role": "super_admin", "first_name": "DevJrn", "last_name": "Admin"},
    {"handle": "dev.jrn.mgr" + W, "role": "manager", "first_name": "DevJrn", "last_name": "Manager", "skills": "*"},
    {"handle": "dev.monthly" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.ow.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.ow.b" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.sw.b" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.flat.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.sn.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.el.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.chk.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.iron.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.fin.a" + W, "role": "worker", "skills": "*"},
    {"handle": "dev.fin.b" + W, "role": "worker", "skills": "*"},
]

_MASTERS = {
    "cloth_type": None,  # per-recipe (isolation)
    "cloth_color": None,
    "storage": "DEV-JRN-RACK",
    # the dim colors the journeys report against (WSC.color = ClothColor):
    "extra_colors": ["Red", "Blue"],
    "stage_category": {"code": "dev-jrn", "name": "DEV-JRN"},
    "stages": [],  # trio+barcode come from the migration-seeded library
    # UI-created machine types + stage-library rows (extracted 2026-07-17;
    # layer-3 masters — machine types via the certified machine_service writer,
    # stages via the spec §3 plain-ORM exception):
    "machine_types": ["Elastic Machine", "Flatlock Machine",
                       "Overlock Machine", "Single Needle Machine"],
    "library_stages": [
        {"code": "shoulder_join", "name": "Shoulder Join", "category": "stitching", "work_type": "machine", "machine_type": "overlock_machine"},
        {"code": "neck_join", "name": "Neck Join", "category": "stitching", "work_type": "machine", "machine_type": "overlock_machine"},
        {"code": "sleeve_fold", "name": "Sleeve Fold", "category": "stitching", "work_type": "machine", "machine_type": "flatlock_machine"},
        {"code": "sleeve_join", "name": "Sleeve Join", "category": "stitching", "work_type": "machine", "machine_type": "overlock_machine"},
        {"code": "side_seam_close", "name": "Side Seam Close", "category": "stitching", "work_type": "machine", "machine_type": "overlock_machine"},
        {"code": "elastic_attach", "name": "Elastic Attach", "category": "stitching", "work_type": "machine", "machine_type": "elastic_machine"},
        {"code": "bottom_fold", "name": "Bottom Fold", "category": "stitching", "work_type": "machine", "machine_type": "flatlock_machine"},
        {"code": "label_attach", "name": "Label Attach", "category": "stitching", "work_type": "machine", "machine_type": "single_needle_machine"},
        {"code": "overlock", "name": "Panel Join", "category": "stitching", "work_type": "machine", "machine_type": "overlock_machine"},
        {"code": "leg_binding", "name": "Leg Binding (Patti)", "category": "stitching", "work_type": "machine", "machine_type": "flatlock_machine"},
        {"code": "thread_cutting", "name": "Thread Cutting", "category": "finishing", "work_type": "manual", "machine_type": None},
        {"code": "checking", "name": "Checking", "category": "finishing", "work_type": "manual", "machine_type": None},
        {"code": "iron_press", "name": "Iron", "category": "finishing", "work_type": "manual", "machine_type": None},
        {"code": "packing", "name": "Packing", "category": "finishing", "work_type": "manual", "machine_type": None},
        {"code": "dispatch", "name": "Dispatch", "category": "dispatch", "work_type": "manual", "machine_type": None},
    ],
}


def _j(slug, product, sizes, patterns, flow, layering, cutting_breakup,
       stages, golden, roll=True, tag=""):
    return {
        "slug": slug,
        "dev_prefixes": ("dev.", "DEV-", "dev-"),
        "cast": _CAST,
        "sa_handle": "dev.jrn.sa" + W,
        "manager_handle": "dev.jrn.mgr" + W,
        "masters": {**_MASTERS, "cloth_type": f"DEV-JRN-{tag}-COTTON", "cloth_color": f"DEV-JRN-{tag}-BASE"},
        "product": product,
        "sizes": sizes,
        "patterns": patterns,
        "flow": flow["codes"],
        "stage_costs": flow["costs"],
        "rolls": {"cloth_type": f"DEV-JRN-{tag}-COTTON", "storage": "DEV-JRN-RACK",
                  "rolls": ([{"color": f"DEV-JRN-{tag}-BASE", "qty": 1}] if roll else [])},
        "journey": {
            "layering": layering,
            "cutting_breakup": cutting_breakup,   # [(size, color, pattern-index, count)]
            "stages": stages,
            "golden": golden,
        },
    }


# ── LOWER — ADST-0004 · ₹344.25 (FOM §9) ────────────────────────────────────
LOWER = _j(
    "regression-lower",
    {"code": "LOWER", "name": "Lower (Track Pant)"},
    sizes=["s", "m", "l", "xl"],
    patterns=["Lower Front Panel", "Lower Back Panel"],
    flow={
        "codes": ["cutting_pattern", "cutting", "barcode_generation",
                   "side_seam_close", "elastic_attach", "bottom_fold", "label_attach",
                   "thread_cutting", "checking", "iron_press", "packing", "dispatch"],
        "costs": [
            {"stage": "layering", "method": "per_layer", "rate": "10", "credits": False},
            {"stage": "cutting_pattern", "method": "fixed_cost", "rate": "500", "credits": False},  # W2-F5 replay-only
            {"stage": "cutting", "method": "per_piece", "rate": "2", "credits": False},  # W2-F5 replay-only
            {"stage": "side_seam_close", "method": "per_piece", "rate": "2.50", "credits": True},
            {"stage": "elastic_attach", "method": "per_piece", "rate": "2", "credits": True},
            {"stage": "bottom_fold", "method": "per_piece", "rate": "1", "credits": True},
            {"stage": "label_attach", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "thread_cutting", "method": "per_piece", "rate": "0.50", "credits": True},
            {"stage": "checking", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "iron_press", "method": "per_piece", "rate": "1", "credits": True},
            {"stage": "packing", "method": "per_piece", "rate": "0.50", "credits": True},
        ],
    },
    layering={"mode": "full", "roster": ["dev.monthly" + W],
              "report": {"worker": "dev.monthly" + W, "good": "40"},
              "roll_colors": ["Red"],  # W2-F4: GAP-2 law — roll color must cover the breakup dims
              "width_inch": 36, "weight_kg": "25.00", "layers": 40,
              "leftover_kg": "2.50", "duration_minutes": 9, "layer_length_m": "1.20"},
    cutting_breakup=[("s", "Red", 0, 20), ("m", "Red", 0, 20), ("l", "Red", 0, 10)],
    stages=[
        {"stage": "side_seam_close", "roster": ["dev.ow.a" + W, "dev.ow.b" + W],
         "reports": {"dev.ow.a" + W: [{"good": "19", "color": "Red", "size": "s"}],
                     "dev.ow.b" + W: [{"good": "20", "color": "Red", "size": "m"}]}},
        {"stage": "elastic_attach", "roster": ["dev.el.a" + W],
         "reports": {"dev.el.a" + W: [{"good": "19", "color": "Red", "size": "s"},
                                       {"good": "20", "color": "Red", "size": "m"}]}},
        {"stage": "bottom_fold", "roster": ["dev.flat.a" + W],
         "reports": {"dev.flat.a" + W: [{"good": "19", "color": "Red", "size": "s"},
                                         {"good": "20", "color": "Red", "size": "m"}]}},
        {"stage": "label_attach", "roster": ["dev.sn.a" + W],
         "reports": {"dev.sn.a" + W: [{"good": "19", "color": "Red", "size": "s"},
                                       {"good": "20", "color": "Red", "size": "m"}]}},
        {"stage": "thread_cutting", "roster": ["dev.fin.a" + W],
         "reports": {"dev.fin.a" + W: [{"good": "19", "color": "Red", "size": "s"},
                                        {"good": "20", "color": "Red", "size": "m"}]}},
        {"stage": "checking", "roster": ["dev.chk.a" + W],
         "reports": {"dev.chk.a" + W: [{"good": "17", "color": "Red", "size": "s", "alter": "1"},
                                        {"good": "19", "color": "Red", "size": "m", "alter": "1"}]}},
        {"stage": "iron_press", "roster": ["dev.iron.a" + W],
         "reports": {"dev.iron.a" + W: [{"good": "17", "color": "Red", "size": "s"},
                                         {"good": "19", "color": "Red", "size": "m"}]}},
        {"stage": "packing", "roster": ["dev.fin.a" + W],
         "reports": {"dev.fin.a" + W: [{"good": "17", "color": "Red", "size": "s"},
                                        {"good": "19", "color": "Red", "size": "m"}]}},
        {"stage": "dispatch", "advance_only": True},
    ],
    golden="344.25",
    tag="LOW",
)
LOWER["rolls"]["rolls"] = [{"color": "Red", "qty": 1}]

# ── T-SHIRT — ADST-0005 · ₹801.00 (FOM §10) ─────────────────────────────────
TSHIRT = _j(
    "regression-tshirt",
    {"code": "T-SHIRT", "name": "T-Shirt"},
    sizes=["s", "m", "l", "xl", "xxl"],
    patterns=["Front Panel", "Back Panel", "Left Sleeve", "Right Sleeve",
              "Neck Rib", "Pocket", "Brand Label", "Care Label"],
    flow={
        "codes": ["cutting_pattern", "cutting", "barcode_generation",
                   "shoulder_join", "neck_join", "sleeve_fold", "sleeve_join",
                   "side_seam_close", "bottom_fold", "label_attach", "thread_cutting",
                   "checking", "iron_press", "packing", "dispatch"],
        "costs": [
            {"stage": "layering", "method": "per_layer", "rate": "10", "credits": False},
            {"stage": "cutting_pattern", "method": "fixed_cost", "rate": "500", "credits": False},  # W2-F5 replay-only
            {"stage": "cutting", "method": "per_piece", "rate": "2", "credits": False},  # W2-F5 replay-only
            {"stage": "shoulder_join", "method": "per_piece", "rate": "1.50", "credits": True},
            {"stage": "neck_join", "method": "per_piece", "rate": "2", "credits": True},
            {"stage": "sleeve_fold", "method": "per_piece", "rate": "1", "credits": True},
            {"stage": "sleeve_join", "method": "per_piece", "rate": "2", "credits": True},
            {"stage": "side_seam_close", "method": "per_piece", "rate": "2.50", "credits": True},
            {"stage": "bottom_fold", "method": "per_piece", "rate": "1", "credits": True},
            {"stage": "label_attach", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "thread_cutting", "method": "per_piece", "rate": "0.50", "credits": True},
            {"stage": "checking", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "iron_press", "method": "per_piece", "rate": "1", "credits": True},
            {"stage": "packing", "method": "per_piece", "rate": "0.50", "credits": True},
        ],
    },
    layering={"mode": "advance"},        # certified truth: completed empty, no roll
    cutting_breakup=[("m", "Blue", 0, 20), ("m", "Red", 0, 20),
                     ("l", "Blue", 0, 10), ("l", "Red", 0, 10)],
    stages=[
        {"stage": "shoulder_join", "roster": ["dev.ow.a" + W, "dev.ow.b" + W],
         "reports": {"dev.ow.a" + W: [{"good": "20", "color": "Red", "size": "m"},
                                       {"good": "10", "color": "Red", "size": "l"}],
                     "dev.ow.b" + W: [{"good": "20", "color": "Blue", "size": "m"},
                                       {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "neck_join", "roster": ["dev.ow.b" + W],
         "reports": {"dev.ow.b" + W: [{"good": "20", "color": "Red", "size": "m"},
                                       {"good": "10", "color": "Red", "size": "l"},
                                       {"good": "20", "color": "Blue", "size": "m"},
                                       {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "sleeve_fold", "roster": ["dev.flat.a" + W],
         "reports": {"dev.flat.a" + W: [{"good": "20", "color": "Red", "size": "m"},
                                         {"good": "10", "color": "Red", "size": "l"},
                                         {"good": "20", "color": "Blue", "size": "m"},
                                         {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "sleeve_join", "roster": ["dev.sw.b" + W],
         "reports": {"dev.sw.b" + W: [{"good": "20", "color": "Red", "size": "m"},
                                       {"good": "10", "color": "Red", "size": "l"},
                                       {"good": "20", "color": "Blue", "size": "m"},
                                       {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "side_seam_close", "roster": ["dev.ow.b" + W],
         "reports": {"dev.ow.b" + W: [{"good": "20", "color": "Red", "size": "m"},
                                       {"good": "10", "color": "Red", "size": "l"},
                                       {"good": "20", "color": "Blue", "size": "m"},
                                       {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "bottom_fold", "roster": ["dev.flat.a" + W],
         "reports": {"dev.flat.a" + W: [{"good": "20", "color": "Red", "size": "m"},
                                         {"good": "10", "color": "Red", "size": "l"},
                                         {"good": "20", "color": "Blue", "size": "m"},
                                         {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "label_attach", "roster": ["dev.sn.a" + W],
         "reports": {"dev.sn.a" + W: [{"good": "20", "color": "Red", "size": "m"},
                                       {"good": "10", "color": "Red", "size": "l"},
                                       {"good": "20", "color": "Blue", "size": "m"},
                                       {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "thread_cutting", "roster": ["dev.fin.a" + W],
         "reports": {"dev.fin.a" + W: [{"good": "20", "color": "Red", "size": "m"},
                                        {"good": "10", "color": "Red", "size": "l"},
                                        {"good": "20", "color": "Blue", "size": "m"},
                                        {"good": "10", "color": "Blue", "size": "l"}]}},
        {"stage": "checking", "roster": ["dev.chk.a" + W],
         "reports": {"dev.chk.a" + W: [{"good": "18", "color": "Red", "size": "m", "alter": "2"},
                                        {"good": "10", "color": "Red", "size": "l"},
                                        {"good": "20", "color": "Blue", "size": "m"},
                                        {"good": "9", "color": "Blue", "size": "l"}]},
         "verify": [{"worker": "dev.chk.a" + W, "color": "Red", "size": "m", "quantity": "17"}]},
        {"stage": "iron_press", "roster": ["dev.iron.a" + W],
         "reports": {"dev.iron.a" + W: [{"good": "17", "color": "Red", "size": "m"},
                                         {"good": "10", "color": "Red", "size": "l"},
                                         {"good": "20", "color": "Blue", "size": "m"},
                                         {"good": "9", "color": "Blue", "size": "l"}]}},
        {"stage": "packing", "roster": ["dev.fin.a" + W],
         "reports": {"dev.fin.a" + W: [{"good": "17", "color": "Red", "size": "m"},
                                        {"good": "10", "color": "Red", "size": "l"},
                                        {"good": "20", "color": "Blue", "size": "m"},
                                        {"good": "9", "color": "Blue", "size": "l"}]}},
        {"stage": "dispatch", "advance_only": True},
    ],
    golden="801.00",
    roll=False,
    tag="TSH",
)

# ── 3-PATTI — ADST-0006 · ₹633.00 (FOM §12) ─────────────────────────────────
PATTI = _j(
    "regression-3patti",
    {"code": "3-PATTI", "name": "3 Patti"},
    sizes=["free", "1", "2"],
    patterns=["Patti Panel", "Patti Back Panel"],
    flow={
        "codes": ["cutting_pattern", "cutting", "barcode_generation",
                   "overlock", "leg_binding", "elastic_attach", "label_attach",
                   "thread_cutting", "checking", "packing", "dispatch"],
        "costs": [
            {"stage": "layering", "method": "per_layer", "rate": "10", "credits": False},
            {"stage": "cutting_pattern", "method": "fixed_cost", "rate": "500", "credits": False},  # W2-F5 replay-only
            {"stage": "cutting", "method": "per_piece", "rate": "100", "credits": False},  # W2-F5 replay-only
            {"stage": "overlock", "method": "per_piece", "rate": "5", "credits": True},
            {"stage": "leg_binding", "method": "per_piece", "rate": "1.50", "credits": True},
            {"stage": "elastic_attach", "method": "per_piece", "rate": "2", "credits": True},
            {"stage": "label_attach", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "thread_cutting", "method": "per_piece", "rate": "0.50", "credits": True},
            {"stage": "checking", "method": "per_piece", "rate": "0.75", "credits": True},
            {"stage": "packing", "method": "per_piece", "rate": "0.50", "credits": True},
        ],
    },
    layering={"mode": "full", "roster": ["dev.monthly" + W],
              "roll_colors": ["Red", "Blue"],  # W2-F4: GAP-2 law (postdates journey)
              "width_inch": 36, "weight_kg": "25.00", "layers": 15,
              "leftover_kg": "2.50", "duration_minutes": 45, "layer_length_m": "1.50"},
    cutting_breakup=[("1", "Blue", 0, 18), ("1", "Red", 0, 24), ("2", "Red", 0, 18)],
    stages=[
        {"stage": "overlock", "roster": ["dev.ow.a" + W, "dev.ow.b" + W],
         "reports": {"dev.ow.a" + W: [{"good": "23", "color": "Red", "size": "1", "alter": "1"},
                                       {"good": "18", "color": "Red", "size": "2"}],
                     "dev.ow.b" + W: [{"good": "17", "color": "Blue", "size": "1"}]}},
        {"stage": "leg_binding", "roster": ["dev.flat.a" + W],
         "reports": {"dev.flat.a" + W: [{"good": "23", "color": "Red", "size": "1"},
                                         {"good": "18", "color": "Red", "size": "2"},
                                         {"good": "17", "color": "Blue", "size": "1"}]}},
        {"stage": "elastic_attach", "roster": ["dev.el.a" + W],
         "reports": {"dev.el.a" + W: [{"good": "23", "color": "Red", "size": "1"},
                                       {"good": "18", "color": "Red", "size": "2"},
                                       {"good": "17", "color": "Blue", "size": "1"}]}},
        {"stage": "label_attach", "roster": ["dev.sn.a" + W],
         "reports": {"dev.sn.a" + W: [{"good": "23", "color": "Red", "size": "1"},
                                       {"good": "18", "color": "Red", "size": "2"},
                                       {"good": "17", "color": "Blue", "size": "1"}]}},
        {"stage": "thread_cutting", "roster": ["dev.fin.a" + W],
         "reports": {"dev.fin.a" + W: [{"good": "23", "color": "Red", "size": "1"},
                                        {"good": "18", "color": "Red", "size": "2"},
                                        {"good": "17", "color": "Blue", "size": "1"}]}},
        {"stage": "checking", "roster": ["dev.chk.a" + W],
         "reports": {"dev.chk.a" + W: [{"good": "21", "color": "Red", "size": "1", "alter": "1"},
                                        {"good": "18", "color": "Red", "size": "2"},
                                        {"good": "16", "color": "Blue", "size": "1", "missing": "1"}]},
         "verify": [{"worker": "dev.chk.a" + W, "color": "Red", "size": "1", "quantity": "20"}]},
        {"stage": "packing", "roster": ["dev.fin.b" + W],
         "reports": {"dev.fin.b" + W: [{"good": "20", "color": "Red", "size": "1"},
                                        {"good": "18", "color": "Red", "size": "2"},
                                        {"good": "16", "color": "Blue", "size": "1"}]}},
        {"stage": "dispatch", "advance_only": True},
    ],
    golden="633.00",
    tag="PAT",
)
PATTI["rolls"]["rolls"] = [{"color": "Red", "qty": 1}, {"color": "Blue", "qty": 1}]

RECIPES = {r["slug"]: r for r in (LOWER, TSHIRT, PATTI)}

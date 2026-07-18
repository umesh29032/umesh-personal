"""3-PATTI-016 yield-board data walk (P0) — READ-ONLY against the real DB.

Runs under the DJANGO venv (not the poc venv):
  cd config && ../env/bin/python manage.py shell < ../poc/patterns_ai/yield_walk.py

Proves the P1 yield-board math end-to-end on the settled ₹633.00 journey:
fabric-in (layering) → garments (APSCPB / packed) → meters-per-garment →
estimated utilization using the harness patti piece areas. Writes NOTHING.
"""
import json

from production.models import Adda, AddaStageRecord, LayeringRecord
from production.models import AddaProductSizeColorPieceBreakdown as APSCPB
from production.models.worker_task import WorkerStageContribution as WSC

a = Adda.objects.get(code='3-PATTI-016')
lay = LayeringRecord.objects.get(stage_record__adda=a)
roll = lay.rolls_used.first()

plies = lay.lay_count
lay_len_m = float(lay.layer_length_meters)
width_in = roll.width_inch
width_m_tubeflat = width_in * 0.0254

cut = sum(APSCPB.objects.filter(adda=a).values_list('verified_piece_count', flat=True))
packed_rows = WSC.objects.filter(task__stage_record__adda=a,
                                 task__stage_record__workflow_stage__stage__code='packing')
packed = sum(float(w.verified_quantity if w.verified_quantity is not None else w.good_quantity)
             for w in packed_rows)

fabric_in_m = plies * lay_len_m                       # linear meters laid
fabric_in_m2 = fabric_in_m * width_m_tubeflat         # tube-flat area basis

# harness patti piece area: 0.806 m^2 per 5-garment repeat (make_pieces.py)
GARMENT_AREA_M2 = 0.806 / 5

walk = {
    "adda": a.code,
    "roll": roll.roll_id, "roll_width_inch": width_in,
    "plies": plies, "lay_length_m": lay_len_m,
    "fabric_in_linear_m": round(fabric_in_m, 2),
    "fabric_in_area_m2_tubeflat": round(fabric_in_m2, 3),
    "garments_cut_apscpb": cut,
    "garments_packed": packed,
    "meters_per_garment_cut": round(fabric_in_m / cut, 4),
    "meters_per_100_garments": round(fabric_in_m / cut * 100, 1),
    "est_garment_area_m2_harness": GARMENT_AREA_M2,
    "est_utilization_pct": round(cut * GARMENT_AREA_M2 / fabric_in_m2 * 100, 1),
    "honest_notes": [
        "utilization is an ESTIMATE: garment area from the P0 harness geometry, not captured patterns",
        "manual chalk marker (no digital marker existed) — exactly what P1 manual-markers will record",
        "leftover-roll and end-allowance not modelled here; P1 outcome facts add them",
    ],
}
print(json.dumps(walk, indent=1))
with open('../poc/patterns_ai/results/yield_walk.json', 'w') as f:
    json.dump(walk, f, indent=1)

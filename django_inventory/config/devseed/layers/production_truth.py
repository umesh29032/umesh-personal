"""Layer 7 — production truth (writer-map rows: adda_service · layering
stage service · worker_task_service — the certified chokepoints ONLY; every
WST/WSC row below is a SERVICE OUTCOME, never a direct write).

Journey shape (minimal worlds): create_adda → layering (start → attach roll →
breakup → complete, TRUE skilled-worker + completer actors) → each generic
stage (set_stage_workers → report_contributions(good) → complete_worker_task →
advance) → Adda COMPLETED.

Convergence: an Adda handle that already exists COMPLETED = skip (idempotent);
existing but PARTIAL = DivergenceError (drift evidence — report, never pave).
"""

from decimal import Decimal

from django.apps import apps

from production.services import adda_service, worker_task_service
from production.stages.layering import service as layering_service

from devseed.layers import DivergenceError


def seed_adda_journey(journey, *, actors, roll, product):
    """Run one Adda journey per the declarative `journey` spec. Returns dict."""
    Adda = apps.get_model("production", "Adda")
    code = journey["adda_code"]

    expect_completed = journey.get("expect_completed", True)
    existing = Adda.objects.filter(code=code).first()
    if existing is not None:
        if existing.status == Adda.Status.COMPLETED or not expect_completed:
            # partial worlds (expect_completed False) converge on existence
            return {"created": 0, "skipped": 1, "adda": existing}
        raise DivergenceError(
            f"adda {code}: exists in status '{existing.status}' (partial journey) — "
            f"drift evidence, not auto-resumed"
        )

    mgr = actors[journey["manager"]]
    completer = actors[journey["layering"]["completer"]]
    worker = actors[journey["worker"]]

    # create_adda mints the code via its own sequence — the scenario handle is
    # enforced post-create (rename is not a service op; the service-issued code
    # is the OUTPUT handle, journey['adda_code'] maps to it in the manifest).
    adda = adda_service.create_adda(mgr, product=product)

    lay = journey["layering"]
    sr = layering_service.start_layering(adda=adda, worker_ids=[worker.pk], user=mgr)
    entry = layering_service.attach_roll_to_layering(
        stage_record=sr, roll=roll,
        width_verified_inch=lay["width_inch"],
        weight_verified_kg=Decimal(lay["weight_kg"]),
        user=worker,
    )
    layering_service.save_layering_breakup(
        entry=entry,
        layers_on_roll=lay["layers"],
        leftover_weight_kg=Decimal(lay["leftover_kg"]),
        user=worker,
    )
    layering_service.complete_layering(
        adda=adda,
        duration_minutes=lay["duration_minutes"],
        layer_length_meters=Decimal(lay["layer_length_m"]),
        per_entry_layers={entry.pk: lay["layers"]},
        notes="devseed journey",
        user=completer,
    )
    adda.refresh_from_db()

    # Cutting (trio member — the join gate): legacy single-shot completion
    # (pieces_cut given ⇒ MANAGEMENT gate; materializes the piece breakdown).
    if "cutting" in journey:
        from production.stages.cutting import service as cutting_service
        cutting_service.complete_cutting(
            adda=adda,
            pieces_cut=journey["cutting"]["pieces"],
            worker_ids=[worker.pk],
            notes="devseed journey",
            user=mgr,
        )
        adda.refresh_from_db()

    # Generic stages: worker reports GOOD quantity, completes, manager advances.
    for step in journey["stages"]:
        sr = adda_service.lane_stage_record(adda, adda.current_stage, None, create=True)
        # Contract 2 (S2): every stage-record creation site snapshots role
        # rates — same call the certified creation sites make (adda_service
        # :247, layering :293, cutting_pattern :177).
        from production.services.stage_rate_service import ensure_stage_role_rates
        ensure_stage_role_rates(sr)
        tasks = worker_task_service.set_stage_workers(sr, [worker.pk])
        task = [t for t in tasks if t.worker_id == worker.pk][0] if isinstance(tasks, list) else \
            sr.worker_tasks.get(worker=worker)
        worker_task_service.report_contributions(
            task, [{"reported_quantity": step["good"]}], actor=worker)
        worker_task_service.complete_worker_task(task, actor=worker)
        adda = adda_service.advance_to_next_stage(adda, mgr)

    adda.refresh_from_db()
    if expect_completed and adda.status != Adda.Status.COMPLETED:
        raise DivergenceError(
            f"adda {adda.code}: journey ended in status '{adda.status}', expected COMPLETED")
    return {"created": 1, "skipped": 0, "adda": adda}

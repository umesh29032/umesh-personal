"""SEED-C Wave-2 — the golden-journey REPLAY engine. Recipe-driven, certified
services ONLY; the settlement totals EMERGE from rates × good quantities —
never hardcoded (the recipe's `golden` is the assertion target).

Completion modes transcribe the extracted production truth:
  layering 'full'    → start/attach/breakup(/worker report)/complete
  layering 'advance' → finalize-empty via advance (the certified T-SHIRT path)
  cutting            → workspace path: upsert_breakup_row per (size,color,pattern)
                       → complete_cutting_from_bundles (helper-skill/SA gate)
  cutting_pattern / barcode_generation / dispatch → advance (blind-advance of a
                       never-opened trio stage / empty finalize — adda_service law)
  generic stages     → set_stage_workers → report_contributions(good+alter+
                       missing, color/size dims) → complete_worker_task
                       → optional set_verified_quantity → advance
"""

from decimal import Decimal

from django.apps import apps

from production.services import adda_service, worker_task_service
from production.services.stage_rate_service import ensure_stage_role_rates
from production.stages.cutting import service as cutting_service
from production.stages.layering import service as layering_service

from devseed.layers import DivergenceError


def _dims(product):
    ProductSize = apps.get_model("production", "ProductSize")
    ClothColor = apps.get_model("raw_materials", "ClothColor")
    sizes = {s.code: s.pk for s in ProductSize.objects.filter(product=product)}
    colors = {c.name: c.pk for c in ClothColor.objects.all()}
    return sizes, colors


def replay_journey(recipe, *, actors, product, rolls=()):
    Adda = apps.get_model("production", "Adda")
    j = recipe["journey"]
    mgr = actors[recipe["manager_handle"]]
    sa = actors[recipe["sa_handle"]]

    existing = Adda.objects.filter(product=product).order_by("pk").first()
    if existing is not None:
        if existing.status == Adda.Status.COMPLETED:
            return {"created": 0, "skipped": 1, "adda": existing}
        raise DivergenceError(
            f"adda {existing.code}: exists in status '{existing.status}' — drift, not resumed")

    adda = adda_service.create_adda(mgr, product=product)
    sizes, colors = _dims(product)

    # ── layering ──
    lay = j["layering"]
    if lay["mode"] == "full":
        worker = actors[lay["roster"][0]]
        sr = layering_service.start_layering(adda=adda, worker_ids=[worker.pk], user=mgr)
        # W2-F4: roll_colors selects one seeded roll per reported dim color
        # (GAP-2 breakup-color law postdates the extracted journeys).
        if lay.get("roll_colors"):
            attach = [next(r for r in rolls if r.cloth_color.name == cn)
                      for cn in lay["roll_colors"]]
        else:
            attach = [rolls[0]]
        per_entry = {}
        for r in attach:
            entry = layering_service.attach_roll_to_layering(
                stage_record=sr, roll=r,
                width_verified_inch=lay["width_inch"],
                weight_verified_kg=Decimal(lay["weight_kg"]), user=worker)
            layering_service.save_layering_breakup(
                entry=entry, layers_on_roll=lay["layers"],
                leftover_weight_kg=Decimal(lay["leftover_kg"]), user=worker)
            per_entry[entry.pk] = lay["layers"]
        if lay.get("report"):
            task = sr.worker_tasks.get(worker=worker)
            worker_task_service.report_contributions(
                task, [{"reported_quantity": lay["report"]["good"]}], actor=worker)
            worker_task_service.complete_worker_task(task, actor=worker)
        layering_service.complete_layering(
            adda=adda, duration_minutes=lay["duration_minutes"],
            layer_length_meters=Decimal(lay["layer_length_m"]),
            per_entry_layers=per_entry,
            notes="devseed replay", user=sa)
    else:  # 'advance' — the certified empty-finalize path
        adda_service.advance_to_next_stage(adda, sa, enforce_worker_credit=False)
    adda.refresh_from_db()

    # ── cutting_pattern: blind advance (never-opened trio stage) ──
    if adda.current_stage.stage.code == "cutting_pattern":
        adda_service.advance_to_next_stage(adda, sa, enforce_worker_credit=False)
        adda.refresh_from_db()

    # ── cutting: workspace breakup path ──
    if adda.current_stage.stage.code == "cutting":
        worker = actors[recipe["manager_handle"]]  # breakup entry = cutting-skilled; mgr has '*'
        pattern_ids = _pattern_ids(product)
        for (size_code, color_name, pat_idx, count) in j["cutting_breakup"]:
            cutting_service.upsert_breakup_row(
                adda=adda, size_id=sizes[size_code], color_id=colors[color_name],
                pattern_id=pattern_ids[pat_idx], count=count, user=worker)
        cutting_service.complete_cutting_from_bundles(adda=adda, user=sa)
        adda.refresh_from_db()

    # ── barcode_generation: empty finalize via advance ──
    if adda.current_stage.stage.code == "barcode_generation":
        adda_service.advance_to_next_stage(adda, sa, enforce_worker_credit=False)
        adda.refresh_from_db()

    # ── generic payable stages ──
    for step in j["stages"]:
        cur = adda.current_stage
        if cur.stage.code != step["stage"]:
            raise DivergenceError(
                f"pointer at '{cur.stage.code}', recipe expects '{step['stage']}'")
        if step.get("advance_only"):
            adda = adda_service.advance_to_next_stage(adda, mgr, enforce_worker_credit=False)
            adda.refresh_from_db() if hasattr(adda, "refresh_from_db") else None
            continue
        sr = adda_service.lane_stage_record(adda, cur, None, create=True)
        ensure_stage_role_rates(sr)  # contract-2 parity (certified creation sites)
        roster = [actors[h] for h in step["roster"]]
        worker_task_service.set_stage_workers(sr, [w.pk for w in roster])
        for handle, lines in step["reports"].items():
            w = actors[handle]
            task = sr.worker_tasks.get(worker=w)
            payload = []
            for ln in lines:
                row = {"reported_quantity": ln["good"]}
                if ln.get("color"):
                    row["color_id"] = colors[ln["color"]]
                if ln.get("size"):
                    row["size_id"] = sizes[ln["size"]]
                if ln.get("alter"):
                    row["alter_quantity"] = ln["alter"]
                if ln.get("missing"):
                    row["missing_quantity"] = ln["missing"]
                payload.append(row)
            worker_task_service.report_contributions(task, payload, actor=w)
            worker_task_service.complete_worker_task(task, actor=w)
        for v in step.get("verify", ()):
            WSC = apps.get_model("production", "WorkerStageContribution")
            c = WSC.objects.get(
                task__stage_record=sr, task__worker=actors[v["worker"]],
                color_id=colors[v["color"]], size_id=sizes[v["size"]])
            worker_task_service.set_verified_quantity(c, Decimal(v["quantity"]), actor=mgr)
        adda = adda_service.advance_to_next_stage(adda, mgr)
        adda.refresh_from_db()

    if adda.status != Adda.Status.COMPLETED:
        raise DivergenceError(
            f"journey ended in status '{adda.status}', expected COMPLETED")
    return {"created": 1, "skipped": 0, "adda": adda}


def _pattern_ids(product):
    PPA = apps.get_model("production", "ProductPatternAssignment")
    return list(PPA.objects.filter(product=product)
                .order_by("pk").values_list("pattern_id", flat=True))

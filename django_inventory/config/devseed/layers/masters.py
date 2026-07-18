"""Layer 3 — core master data (writer-map rows: cloth masters + stage library
have NO service owner — the spec §3 plain-ORM exception; converge by unique
natural name/slug)."""

from django.apps import apps

from devseed.layers import DivergenceError


def _get_or_create(model, key_field, key_value, defaults):
    obj = model.objects.filter(**{key_field: key_value}).first()
    if obj is None:
        return model.objects.create(**{key_field: key_value}, **defaults), 1, 0
    return obj, 0, 1


def seed_masters(spec, actor=None):
    ClothType = apps.get_model("raw_materials", "ClothType")
    ClothColor = apps.get_model("raw_materials", "ClothColor")
    Storage = apps.get_model("raw_materials", "StorageLocation")
    StageCategory = apps.get_model("production", "StageCategory")
    Stage = apps.get_model("production", "Stage")
    MachineType = apps.get_model("production", "MachineType")

    created = skipped = 0
    out = {}
    for model, field, value, defaults in [
        (ClothType, "name", spec["cloth_type"], {}),
        (ClothColor, "name", spec["cloth_color"], {}),
        # code = unique NOT-NULL slug (PG unique constraint) — name doubles as
        # the deterministic code; a second world's '' default would collide.
        (Storage, "name", spec["storage"], {"code": spec["storage"][:20]}),
    ]:
        obj, c, s = _get_or_create(model, field, value, defaults)
        created += c
        skipped += s
        out[value] = obj

    # Dim colors journeys report against (certified-dim reconstruction —
    # WSC.color FK targets ClothColor; names transcribe the extracted truth).
    for cname in spec.get("extra_colors", ()):
        obj, c, s = _get_or_create(ClothColor, "name", cname, {})
        created += c
        skipped += s
        out[cname] = obj

    cat_spec = spec["stage_category"]
    category, c, s = _get_or_create(StageCategory, "code", cat_spec["code"], {"name": cat_spec["name"]})
    created += c
    skipped += s

    for st in spec["stages"]:
        stage = Stage.objects.filter(code=st["code"]).first()
        if stage is None:
            Stage.objects.create(code=st["code"], name=st["name"], category=category)
            created += 1
        else:
            if stage.category_id != category.pk:
                raise DivergenceError(
                    f"stage {st['code']}: category '{stage.category.code}' != scenario '{category.code}'"
                )
            skipped += 1

    # Machine types (certified writer: machine_service.create_machine_type —
    # idempotent get_or_create by slugged code).
    for mt_name in spec.get("machine_types", ()):
        from machines.services import machine_service
        before = MachineType.objects.count()
        machine_service.create_machine_type(name=mt_name, user=actor)
        created += 1 if MachineType.objects.count() > before else 0
        skipped += 0 if MachineType.objects.count() > before else 1

    # Library stages (layer-3 masters, plain-ORM exception): the UI-created
    # stage-library rows the journeys run on — extracted configs, converge by code.
    for row in spec.get("library_stages", ()):
        stage = Stage.objects.filter(code=row["code"]).first()
        if stage is not None:
            skipped += 1
            continue
        cat = StageCategory.objects.get(code=row["category"])
        mt = MachineType.objects.get(code=row["machine_type"]) if row.get("machine_type") else None
        Stage.objects.create(
            code=row["code"], name=row["name"], category=cat,
            work_type=row.get("work_type", "manual"), machine_type=mt)
        created += 1
    return {"created": created, "skipped": skipped, "objects": out}

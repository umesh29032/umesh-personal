"""Layer 6 — raw materials (writer-map row: raw_materials.roll_service
`bulk_create_rolls` — the certified intake path incl. ClothRollHistory CREATED
rows via history_service and the FINANCIAL_ROLES gate; the seeder never writes
a ClothRoll directly).

Convergence note (recorded in the spec's spirit, §4): `roll_id` is
SEQUENCE-ASSIGNED by the service (CR-NNNNNN) — an OUTPUT handle reported in
the manifest, not an input key. Roll convergence is therefore attribute-keyed:
the scenario expects an exact roll population per (cloth_type, color, storage);
a matching population = skip."""

import datetime

from django.apps import apps

from raw_materials.services import roll_service

# Deterministic fixed date (spec §1: no wall-clock in seeded content).
SEED_PURCHASE_DATE = datetime.date(2026, 1, 1)


def seed_rolls(spec, masters, *, actor):
    ClothRoll = apps.get_model("raw_materials", "ClothRoll")
    cloth_type = masters[spec["cloth_type"]]
    storage = masters[spec["storage"]]

    created = skipped = 0
    out_handles = []
    for row in spec["rolls"]:
        color = masters[row["color"]]
        existing = ClothRoll.objects.filter(
            cloth_type=cloth_type, cloth_color=color, storage_location=storage,
        )
        want = int(row["qty"])
        have = existing.count()
        if have >= want:
            skipped += want
            out_handles += list(existing.values_list("roll_id", flat=True)[:want])
            continue
        rolls = roll_service.bulk_create_rolls(
            actor,
            cloth_type=cloth_type,
            storage_location=storage,
            purchased_date=SEED_PURCHASE_DATE,
            breakup=[{"color": color, "qty": want - have}],
            # No financial fields here: the scenario's manager actor is not
            # FINANCIAL_ROLES — supplier/cost stay honest-NULL (spec layer 6).
        )
        created += len(rolls)
        skipped += have
        out_handles += [r.roll_id for r in rolls]
    return {"created": created, "skipped": skipped, "roll_ids": out_handles}

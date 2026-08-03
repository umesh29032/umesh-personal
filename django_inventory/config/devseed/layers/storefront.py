"""Layer 9 — storefront (spec §2). Category/FeaturedProduct have NO service
owner (writer map: "listing UI + image_service"; image processing is the only
service and applies to uploads, which the seeder does not fabricate) — the
spec §3 plain-ORM exception applies, AUDITED here exactly like masters.py
(the purity test allowlists ONLY these two models in THIS module)."""

from django.apps import apps


def seed_storefront(spec):
    Category = apps.get_model("storefront", "Category")
    FeaturedProduct = apps.get_model("storefront", "FeaturedProduct")
    created = skipped = 0
    cat = Category.objects.filter(name=spec["category"]).first()
    if cat is None:
        cat = Category.objects.create(name=spec["category"])
        created += 1
    else:
        skipped += 1
    fp_spec = spec["product"]
    fp = FeaturedProduct.objects.filter(name=fp_spec["name"]).first()
    if fp is None:
        FeaturedProduct.objects.create(name=fp_spec["name"], category=cat,
                                       price=fp_spec.get("price", 0))
        created += 1
    else:
        skipped += 1
    return {"created": created, "skipped": skipped}

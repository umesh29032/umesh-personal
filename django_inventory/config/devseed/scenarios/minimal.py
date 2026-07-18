"""Scenario content — `minimal` (spec §7: 1 product + 1 flow + minimal cast +
1 roll + 1 Adda). Declarative data only; executors do the work. The Adda
(layer 7) is SEED-C territory — this module carries the full declaration; the
orchestrator seeds only layers whose executors exist (wave gates elsewhere).

DEV-marking: every minted handle carries the `dev.min.` / `DEV-MIN` / `dev-min`
namespace (spec §4 invariant) and collides with NO reserved-registry handle
(spec §11 law)."""

MINIMAL = {
    "dev_prefixes": ("dev.min.", "DEV-MIN", "dev-min"),
    "cast": [
        {"handle": "dev.min.sa@test.local", "role": "super_admin",
         "first_name": "DevMin", "last_name": "Admin"},
        {"handle": "dev.min.mgr@test.local", "role": "manager",
         "first_name": "DevMin", "last_name": "Manager"},
        {"handle": "dev.min.worker@test.local", "role": "worker",
         "first_name": "DevMin", "last_name": "Worker"},
    ],
    # Actor split mirrors production reality: product CRUD = super_admin-only
    # (product_service gate); flows/machines/rolls = manager (production roles).
    "sa_handle": "dev.min.sa@test.local",
    "manager_handle": "dev.min.mgr@test.local",
    "masters": {
        "cloth_type": "DEV-MIN-COTTON",
        "cloth_color": "DEV-MIN-RED",
        "storage": "DEV-MIN-RACK",
        "stage_category": {"code": "dev-min", "name": "DEV-MIN"},
        "stages": [
            {"code": "dev-min-stitching", "name": "DEV-MIN Stitching"},
        ],
    },
    "product": {"code": "DEV-MIN-TEE", "name": "DEV-MIN Tee"},
    # Production law (trio/join): cutting must follow layering — the REAL
    # library `cutting` stage (legacy single-shot completion), then one
    # DEV-MIN generic stage. Flow = auto-layering + these two.
    "flow": ["cutting", "dev-min-stitching"],
    "rolls": {
        "cloth_type": "DEV-MIN-COTTON",
        "storage": "DEV-MIN-RACK",
        "rolls": [{"color": "DEV-MIN-RED", "qty": 1}],
    },
    # layer 7 declaration (SEED-C executes it): 1 Adda on the product flow
    "adda": {"code": "DEV-MIN-A1"},
}

"""SEED-C purity test — the PERMANENT U8 compliance pin (contract §3.4):
the devseed package contains ZERO direct ORM writes to guarded tables. Every
guarded row is a service outcome. Static source scan (the patterns_ai
test_purity precedent applied to writes): any `.objects.create/bulk_create/
update/get_or_create(` or `.save(`/`.delete(` in devseed source that touches a
guarded model name = red battery, forever.

Allowed exceptions (spec §3 writer map): `layers/masters.py` may plain-ORM the
FIVE service-less masters (ClothType · ClothColor · StorageLocation ·
StageCategory · Stage); `layers/storefront.py` may plain-ORM the TWO
service-less storefront masters (Category · FeaturedProduct — writer map says
"listing UI"; the only storefront service is image processing, N/A to
seeding) — and NOTHING else.
"""

import os
import re

from django.test import SimpleTestCase

import devseed

DEVSEED_DIR = os.path.dirname(devseed.__file__)

GUARDED_NAMES = [
    "WorkerLedgerEntry", "AddaSettlement", "AddaSettlementItem",
    "StageWorkAssignment", "WorkerStageTask", "WorkerStageContribution",
    "WorkerStageAllocation", "StagePoolSnapshot", "FactoryExpense",
    "WorkerAdvance", "ClothRollHistory", "AddaHistory", "ProductHistory",
    "LayeringRecord", "LayeringRollEntry", "AddaStageRecord", "Adda",
    "ClothRoll", "Machine", "MachineAssignment", "Product", "WorkflowStage",
    "User",
]

WRITE_CALL = re.compile(
    r"\.objects\.(create|bulk_create|update|get_or_create|update_or_create)\s*\("
)

MASTERS_ALLOWED = {"ClothType", "ClothColor", "StorageLocation", "StageCategory", "Stage"}
STOREFRONT_ALLOWED = {"Category", "FeaturedProduct"}  # SEED-D audited exception


def _source_files():
    for root, _dirs, files in os.walk(DEVSEED_DIR):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


class DevseedPurityTests(SimpleTestCase):
    def test_no_direct_orm_writes_outside_the_masters_exception(self):
        offenders = []
        for path in _source_files():
            rel = os.path.relpath(path, DEVSEED_DIR)
            src = open(path, encoding="utf-8").read()
            for m in WRITE_CALL.finditer(src):
                # The receiver identifier immediately before `.objects.`
                head = src[: m.start()]
                recv = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", head)
                name = recv.group(1) if recv else "?"
                if rel == os.path.join("layers", "masters.py") and name in (MASTERS_ALLOWED | {"model"}):
                    # the spec §3 plain-ORM masters exception; `model` = the audited
                    # _get_or_create helper receiver, whose reachable models are
                    # pinned by test_masters_module_only_touches_the_five_masters
                    continue
                if rel == os.path.join("layers", "storefront.py") and name in STOREFRONT_ALLOWED:
                    # SEED-D storefront exception, pinned by
                    # test_storefront_module_only_touches_the_two_storefront_masters
                    continue
                offenders.append(f"{rel}: {name}.objects.{m.group(1)}(")
        self.assertEqual(offenders, [], "direct ORM writes found in devseed:\n" + "\n".join(offenders))

    def test_no_model_save_or_delete_calls(self):
        # devseed never mutates fetched model instances directly. `.save(` /
        # `.delete(` anywhere in devseed source = a violation (services own
        # every mutation; the seeder is an orchestrator).
        offenders = []
        for path in _source_files():
            rel = os.path.relpath(path, DEVSEED_DIR)
            if rel.startswith("tests"):
                continue  # tests may arrange fixtures (e.g. divergence setups)
            src = open(path, encoding="utf-8").read()
            for pat in (r"\.save\s*\(", r"\.delete\s*\("):
                for m in re.finditer(pat, src):
                    offenders.append(f"{rel}:{src[:m.start()].count(chr(10)) + 1}")
        self.assertEqual(offenders, [], "instance mutations found in devseed:\n" + "\n".join(offenders))

    def test_masters_module_only_touches_the_five_masters(self):
        src = open(os.path.join(DEVSEED_DIR, "layers", "masters.py"), encoding="utf-8").read()
        models_used = set(re.findall(r'get_model\("(?:[a-z_]+)",\s*"([A-Za-z]+)"\)', src))
        # MachineType: READ-ONLY FK resolution (Stage.machine_type); its writes
        # go through machine_service (the write-scan test above enforces that —
        # a MachineType.objects.create in masters.py stays battery-red).
        allowed = MASTERS_ALLOWED | {"MachineType"}
        self.assertTrue(models_used <= allowed,
                        f"masters.py touches non-master models: {models_used - allowed}")

    def test_storefront_module_only_touches_the_two_storefront_masters(self):
        src = open(os.path.join(DEVSEED_DIR, "layers", "storefront.py"), encoding="utf-8").read()
        models_used = set(re.findall(r'get_model\("(?:[a-z_]+)",\s*"([A-Za-z]+)"\)', src))
        self.assertTrue(models_used <= STOREFRONT_ALLOWED,
                        f"storefront.py touches non-storefront models: {models_used - STOREFRONT_ALLOWED}")

    def test_guarded_names_never_written_anywhere_in_devseed(self):
        # Belt over braces: no guarded model name appears as a write receiver
        # ANYWHERE in devseed (masters exception can't reach these names).
        offenders = []
        for path in _source_files():
            rel = os.path.relpath(path, DEVSEED_DIR)
            if rel.startswith("tests"):
                continue
            src = open(path, encoding="utf-8").read()
            for name in set(GUARDED_NAMES) - MASTERS_ALLOWED:
                # lookbehind: 'Product' must not match inside 'FeaturedProduct'
                if re.search(r"(?<![A-Za-z0-9_])" + name
                             + r"\.objects\.(create|bulk_create|update|get_or_create|update_or_create)\s*\(", src):
                    offenders.append(f"{rel}: {name}")
        self.assertEqual(offenders, [], "guarded-model writes in devseed:\n" + "\n".join(offenders))

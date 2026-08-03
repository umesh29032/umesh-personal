"""VER-A — THE PERMANENT READ-ONLY PIN (contract §3.2, the phase's cardinal
property, landed BEFORE any check logic exists).

The verification ENGINE holds no code path that writes to any database, ever:
no ORM write methods, no instance save/delete, no write-verb raw SQL, no
transactions (a read-only engine needs none). Static source scan — the devseed
purity-test precedent applied to the stricter read-only law (devseed may write
THROUGH services; this engine may not write AT ALL). Battery-red forever on
violation. Tests are exempt from the scan (they may arrange fixtures in their
own test DBs — the ENGINE writes nothing)."""

import os
import re

from django.test import SimpleTestCase

import verification

VERIFICATION_DIR = os.path.dirname(verification.__file__)

ORM_WRITE = re.compile(
    r"\.objects\.(create|bulk_create|update|delete|get_or_create|update_or_create|bulk_update)\s*\("
)
QS_WRITE = re.compile(r"\.(update|delete)\s*\(")   # queryset-level writes
INSTANCE_WRITE = re.compile(r"\.(save|delete)\s*\(")
RAW_WRITE_SQL = re.compile(
    r"execute\s*\(\s*[\"'][^\"']*\b(INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|TRUNCATE)\b",
    re.IGNORECASE,
)
TRANSACTION_USE = re.compile(r"\btransaction\.(atomic|on_commit|set_autocommit)\b")


def _engine_sources():
    for root, _dirs, files in os.walk(VERIFICATION_DIR):
        if "__pycache__" in root or os.sep + "tests" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


class ReadOnlyPurityTests(SimpleTestCase):
    def scan(self, pattern):
        offenders = []
        for path in _engine_sources():
            rel = os.path.relpath(path, VERIFICATION_DIR)
            src = open(path, encoding="utf-8").read()
            for m in pattern.finditer(src):
                offenders.append(f"{rel}:{src[:m.start()].count(chr(10)) + 1}: {m.group(0)}")
        return offenders

    def test_no_orm_write_methods(self):
        self.assertEqual(self.scan(ORM_WRITE), [],
                         "ORM write calls in the read-only engine")

    def test_no_queryset_or_instance_writes(self):
        offenders = self.scan(QS_WRITE) + self.scan(INSTANCE_WRITE)
        self.assertEqual(offenders, [],
                         "queryset/instance mutations in the read-only engine")

    def test_no_write_verb_raw_sql(self):
        self.assertEqual(self.scan(RAW_WRITE_SQL), [],
                         "write-verb raw SQL in the read-only engine")

    def test_no_transaction_management(self):
        # A read-only engine needs no transaction control; its presence is a
        # write-path smell (checks read committed state as-is).
        self.assertEqual(self.scan(TRANSACTION_USE), [],
                         "transaction management in the read-only engine")

    def test_structurally_write_free_shape(self):
        # No models, no migrations, no URLs, no templates — read-only by
        # architecture (VER-D1), not by discipline.
        for forbidden in ("models.py", "migrations", "urls.py", "templates", "forms.py"):
            self.assertFalse(
                os.path.exists(os.path.join(VERIFICATION_DIR, forbidden)),
                f"verification/{forbidden} exists — the engine must stay modelless/write-free")

    def test_registered_in_base_settings(self):
        # Production-present is the POINT (VER-D1): verify_production must
        # exist under production settings, unlike devseed.
        from django.conf import settings
        self.assertIn("verification", settings.INSTALLED_APPS)

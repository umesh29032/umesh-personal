"""Postgres SEQUENCE create karta hai — Roll ID allocation ke liye.

YEH FILE KYU HAI?
─────────────────
roll_service._next_roll_id() Postgres `nextval('cloth_roll_seq')` use karta hai.
Wo sequence object yahi migration banata hai.

Postgres-only kyun?
──────────────────
Sequences atomic counters hote hain — race-safe by design (DB-level lock built-in).
Django MAX(roll_id)+1 pattern race-prone hota — 2 concurrent inserts same ID le sakte.
SQLite mein nextval nahi hota — isliye CI ko Postgres pe chalana zaruri hai.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('raw_materials', '0003_clothroll')]

    operations = [
        # RunSQL = raw SQL execute. Django ORM ke through nahi ho sakta (sequence Django ke bahar).
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS cloth_roll_seq START 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS cloth_roll_seq;",
        ),
    ]

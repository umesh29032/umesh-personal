"""generate_monthly_expenses — the MEE-D4 command: a THIN wrapper around THE
same service function the UI uses (one implementation path; the command
writes nothing itself — purity-pinned). Intended for an operator shell or an
EXTERNAL cron post-deploy (no in-repo scheduler, by owner ruling); the actor
must be a management user — the service enforces every gate."""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = ("Preview (default) or --confirm one month's recurring factory "
            "expenses via expense_service.generate_monthly_expenses.")

    def add_arguments(self, parser):
        parser.add_argument("month", help="Period as YYYY-MM (e.g. 2026-07).")
        parser.add_argument("--actor", required=True,
                            help="Email of the MANAGEMENT user acting.")
        parser.add_argument("--confirm", action="store_true",
                            help="Actually create rows (default: preview only).")

    def handle(self, *args, **options):
        from accounts.models import User
        from expense.services.expense_service import generate_monthly_expenses

        raw = options["month"]
        try:
            year, month = int(raw[:4]), int(raw[5:7])
            if raw[4] != '-':
                raise ValueError
        except (ValueError, IndexError):
            raise CommandError(f"Invalid month '{raw}' — expected YYYY-MM.")
        try:
            actor = User.objects.get(email=options["actor"], is_active=True)
        except User.DoesNotExist:
            raise CommandError(f"No active user '{options['actor']}'.")

        receipt = generate_monthly_expenses(
            year, month, actor=actor, confirm=options["confirm"])
        mode = "CONFIRMED" if options["confirm"] else "PREVIEW (nothing written)"
        self.stdout.write(f"{mode} — period {receipt['period_key']}")
        for row in receipt["to_create"]:
            self.stdout.write(f"  create: {row['template'].label} "
                              f"₹{row['amount']} on {row['expense_date']}")
        for rec in receipt["created"]:
            self.stdout.write(f"  CREATED: {rec.template.label} → FE#{rec.expense_id}")
        for t, why in receipt["skipped"]:
            self.stdout.write(f"  skip: {t.label} — {why}")
        self.stdout.write(f"created={len(receipt['created'])} "
                          f"skipped={len(receipt['skipped'])}")

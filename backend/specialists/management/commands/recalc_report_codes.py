from django.core.management.base import BaseCommand

from specialists.models import ScientificWork
from specialists.report_codes import compute_report_code


class Command(BaseCommand):
    help = "Recompute report_code for every ScientificWork row (backfill after taxonomy changes)."

    def handle(self, *args, **options):
        updated = 0
        for work in ScientificWork.objects.all():
            new_code = compute_report_code(work)
            if new_code != work.report_code:
                ScientificWork.objects.filter(pk=work.pk).update(report_code=new_code)
                updated += 1

        total = ScientificWork.objects.count()
        unclassified = ScientificWork.objects.filter(report_code="").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Recomputed report_code for {updated} row(s) out of {total} total "
                f"({unclassified} unclassified)."
            )
        )

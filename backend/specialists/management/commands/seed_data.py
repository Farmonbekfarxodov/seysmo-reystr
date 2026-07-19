from django.core.management.base import BaseCommand

from specialists.models import Department

DEPARTMENTS = [
    "Seysmogen jarayonlar laboratoriyasi",
    "Gruntlar seysmodinamikasi laboratoriyasi",
    "Geoinformatika va sun'iy intellekt laboratoriyasi",
    "Instrumental seysmologiya va seysmometriya laboratoriyasi",
    "Muhandislik seysmologiyasi laboratoriyasi",
    "Seysmik xavf laboratoriyasi",
    "Zamonaviy geodinamika laboratoriyasi",
]


class Command(BaseCommand):
    help = "Seed the institute's departments (laboratories). No demo employees."

    def handle(self, *args, **options):
        created_count = 0
        for name in DEPARTMENTS:
            department, created = Department.objects.get_or_create(name=name)
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} new department(s) "
                f"(skipped {len(DEPARTMENTS) - created_count} already present)."
            )
        )

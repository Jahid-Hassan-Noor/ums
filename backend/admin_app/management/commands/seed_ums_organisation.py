from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Compatibility alias for neutral demo organisation data. This is not "
        "required for a generic installation."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-bootstrap",
            action="store_true",
            help="Forwarded to the neutral demo seed.",
        )
        parser.add_argument(
            "--skip-public-content",
            action="store_true",
            help="Accepted for compatibility; neutral public content may still be seeded.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "seed_ums_organisation is a legacy alias. Use "
                "seed_neutral_demo_data for neutral demo data, or "
                "bootstrap_university for generic setup."
            )
        )
        call_command(
            "seed_neutral_demo_data",
            skip_bootstrap=options.get("skip_bootstrap", False),
            skip_users=True,
            verbosity=options.get("verbosity", 1),
        )

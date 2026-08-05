from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Seed a neutral local-development demo pack. This command is retained "
        "as a generic compatibility entry point and does not load an "
        "institution-specific demo profile."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-bootstrap",
            action="store_true",
            help="Do not create or refresh generic bootstrap settings first.",
        )
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Seed academic/public demo data without demo user accounts.",
        )
        parser.add_argument(
            "--password",
            default="",
            help="Optional password forwarded to neutral demo user creation.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "seed_all_data now loads the neutral demo pack. Use an explicit "
                "institution demo seed command when you need branded sample data."
            )
        )
        call_command(
            "seed_neutral_demo_data",
            skip_bootstrap=options.get("skip_bootstrap", False),
            skip_users=options.get("skip_users", False),
            password=options.get("password") or "",
            verbosity=options.get("verbosity", 1),
        )

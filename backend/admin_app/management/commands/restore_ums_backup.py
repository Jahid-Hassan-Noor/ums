from pathlib import Path

from django.core.management import BaseCommand, CommandError

from admin_app.services.backups import restore_database_backup_file


class Command(BaseCommand):
    help = "Restore a UMS backup zip or generated SQL file into the current database and media root."

    def add_arguments(self, parser):
        parser.add_argument("backup", help="Path to a UMS backup .zip archive or generated .sql file.")
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required. Confirms that the current database can be replaced.",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Restore database data only and leave MEDIA_ROOT unchanged.",
        )
        parser.add_argument(
            "--no-flush",
            action="store_true",
            help="Load fixture without flushing first. Use only for advanced recovery work.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Refusing to restore without --confirm because this can replace production data.")

        backup_path = Path(options["backup"])
        try:
            restore_database_backup_file(
                backup_path,
                original_name=backup_path.name,
                skip_media=options["skip_media"],
                no_flush=options["no_flush"],
                verbosity=options.get("verbosity", 1),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("UMS backup restored successfully."))

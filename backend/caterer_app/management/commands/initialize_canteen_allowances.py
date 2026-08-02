from django.core.management.base import BaseCommand

from caterer_app.tasks import initialize_canteen_allowances_task


class Command(BaseCommand):
    help = "Initialize or synchronize canteen allowances for the current allowance month."

    def handle(self, *args, **options):
        result = initialize_canteen_allowances_task.enqueue()
        self.stdout.write(
            self.style.SUCCESS(
                f"Queued canteen allowance initialization as task {result.id}."
            )
        )

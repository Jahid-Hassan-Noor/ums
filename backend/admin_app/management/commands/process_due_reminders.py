from django.core.management.base import BaseCommand

from notifications_package.tasks import process_due_reminders_task


class Command(BaseCommand):
    help = "Create two-hour reminders for active library loans and unsubmitted assignments."

    def handle(self, *args, **options):
        result = process_due_reminders_task.enqueue()
        self.stdout.write(
            self.style.SUCCESS(
                f"Queued due-reminder processing as task {result.id}."
            )
        )

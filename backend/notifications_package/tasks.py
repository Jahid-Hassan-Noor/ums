from django.tasks import task

from notifications_package.reminders import process_due_reminders


@task
def process_due_reminders_task():
    return process_due_reminders(force=True)

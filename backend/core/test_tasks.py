from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase
from django.tasks.base import TaskResultStatus

from core.task_backend import CeleryTaskBackend
from notifications_package.tasks import process_due_reminders_task


class CeleryTaskBackendTests(SimpleTestCase):
    @patch("core.task_backend.celery_app.send_task")
    def test_enqueue_sends_django_task_to_celery(self, send_task):
        backend = CeleryTaskBackend(
            "test",
            {
                "QUEUES": ["default"],
                "OPTIONS": {},
            },
        )

        result = backend.enqueue(process_due_reminders_task, (), {})

        self.assertEqual(result.status, TaskResultStatus.READY)
        send_task.assert_called_once()
        call = send_task.call_args
        self.assertEqual(call.args[0], "core.execute_django_task")
        self.assertEqual(
            call.kwargs["kwargs"]["task_path"],
            "notifications_package.tasks.process_due_reminders_task",
        )
        self.assertEqual(call.kwargs["task_id"], result.id)
        self.assertEqual(call.kwargs["queue"], "default")


class PeriodicTaskScheduleTests(SimpleTestCase):
    def test_due_reminders_run_every_minute(self):
        entry = settings.CELERY_BEAT_SCHEDULE["process-due-reminders-every-minute"]
        schedule = entry["schedule"]

        self.assertEqual(
            entry["args"],
            ("notifications_package.tasks.process_due_reminders_task",),
        )
        self.assertEqual(schedule.minute, set(range(60)))

    def test_overdue_fines_run_hourly(self):
        entry = settings.CELERY_BEAT_SCHEDULE["mark-overdue-fines-hourly"]
        schedule = entry["schedule"]

        self.assertEqual(entry["task"], "core.enqueue_django_task")
        self.assertEqual(
            entry["args"],
            ("accountant_app.tasks.mark_overdue_fines_task",),
        )
        self.assertEqual(schedule.minute, {0})
        self.assertEqual(schedule.hour, set(range(24)))

    def test_allowances_run_first_day_at_8am_configured_timezone(self):
        schedule = settings.CELERY_BEAT_SCHEDULE[
            "initialize-canteen-allowances-monthly"
        ]["schedule"]

        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)
        self.assertEqual(schedule.minute, {0})
        self.assertEqual(schedule.hour, {8})
        self.assertEqual(schedule.day_of_month, {1})

    def test_database_backup_email_runs_first_day_at_8am_configured_timezone(self):
        entry = settings.CELERY_BEAT_SCHEDULE[
            "send-monthly-database-backup-email"
        ]
        schedule = entry["schedule"]

        self.assertEqual(entry["task"], "core.enqueue_django_task")
        self.assertEqual(
            entry["args"],
            ("admin_app.tasks.send_monthly_database_backup_email_task",),
        )
        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)
        self.assertEqual(schedule.minute, {0})
        self.assertEqual(schedule.hour, {8})
        self.assertEqual(schedule.day_of_month, {1})

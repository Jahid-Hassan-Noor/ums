from unittest.mock import patch

from django.test import SimpleTestCase

from notifications_package.tasks import process_due_reminders_task


class DueReminderTaskTests(SimpleTestCase):
    @patch("notifications_package.tasks.process_due_reminders")
    def test_task_processes_all_due_reminders(self, process_due_reminders):
        process_due_reminders.return_value = {
            "library": 2,
            "assignments": 3,
            "throttled": False,
        }

        result = process_due_reminders_task.call()

        process_due_reminders.assert_called_once_with(force=True)
        self.assertEqual(result["library"], 2)
        self.assertEqual(result["assignments"], 3)

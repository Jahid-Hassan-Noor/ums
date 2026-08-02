from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from caterer_app.tasks import initialize_canteen_allowances_task


class CanteenAllowanceTaskTests(SimpleTestCase):
    @patch("caterer_app.tasks.initialize_accounts")
    def test_task_initializes_allowances_with_json_safe_result(
        self,
        initialize_accounts,
    ):
        initialize_accounts.return_value = {
            "month": date(2026, 7, 1),
            "created": 12,
            "updated": 4,
        }

        result = initialize_canteen_allowances_task.call()

        initialize_accounts.assert_called_once_with()
        self.assertEqual(
            result,
            {
                "month": "2026-07-01",
                "created": 12,
                "updated": 4,
            },
        )

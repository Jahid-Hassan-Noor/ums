from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import Profile
from hr_app.models import (
    Employee,
    EmploymentRecord,
    OnboardingCard,
    OnboardingColumn,
    OnboardingEmployeeLink,
    OnboardingStageChange,
)


User = get_user_model()


class HrOnboardingBoardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.hr_user = User.objects.create_user(username="board-hr", password="StrongPass123!")
        self.hr_user.profile.role = Profile.ROLE_HR
        self.hr_user.profile.save(update_fields=["role"])
        self.other_user = User.objects.create_user(username="board-teacher", password="StrongPass123!")
        self.other_user.profile.role = Profile.ROLE_TEACHER
        self.other_user.profile.save(update_fields=["role"])
        self.applicant_column = OnboardingColumn.objects.get(phase="applicant", position=0)
        self.onboarding_column = OnboardingColumn.objects.get(phase="onboarding", position=0)

    def authenticate_hr(self):
        self.client.force_authenticate(user=self.hr_user)

    def create_card(self, **overrides):
        payload = {
            "name": "Candidate One",
            "email": "candidate@example.test",
            "column_id": self.applicant_column.id,
            **overrides,
        }
        response = self.client.post("/hr/onboarding-board/cards", payload, format="json")
        self.assertEqual(response.status_code, 201, response.json())
        return response.json()["card"]

    def test_board_is_hr_only_and_starts_with_ordered_columns(self):
        self.client.force_authenticate(user=self.other_user)
        self.assertEqual(self.client.get("/hr/onboarding-board").status_code, 403)
        self.assertEqual(
            self.client.post("/hr/onboarding-board/cards", {"name": "Blocked"}, format="json").status_code,
            403,
        )
        self.authenticate_hr()
        response = self.client.get("/hr/onboarding-board")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()["can_manage"])
        self.assertEqual([column["phase"] for column in response.json()["columns"]], [
            "applicant", "applicant", "onboarding", "onboarding", "onboarding",
        ])
        self.assertEqual(response.json()["cards"], [])

    def test_move_is_atomic_stale_guarded_and_audited(self):
        self.authenticate_hr()
        card = self.create_card()
        event = OnboardingStageChange.objects.get(card_id=card["id"])
        self.assertIsNone(event.from_column_id)
        self.assertEqual(event.to_label, self.applicant_column.label)
        self.assertEqual(event.actor_id, self.hr_user.profile.id)

        response = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {
                "column_id": self.onboarding_column.id,
                "expected_column_id": self.applicant_column.id,
                "reason": "Ready for the joining process",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["card"]["kind"], "onboarding")
        self.assertEqual(OnboardingCard.objects.get(pk=card["id"]).column_id, self.onboarding_column.id)
        self.assertEqual(OnboardingStageChange.objects.filter(card_id=card["id"]).count(), 2)
        move_event = OnboardingStageChange.objects.filter(card_id=card["id"]).first()
        self.assertEqual(move_event.from_label, self.applicant_column.label)
        self.assertEqual(move_event.to_label, self.onboarding_column.label)
        self.assertEqual(move_event.reason, "Ready for the joining process")

        stale = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.applicant_column.id, "expected_column_id": self.applicant_column.id},
            format="json",
        )
        self.assertEqual(stale.status_code, 409, stale.json())
        no_op = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.onboarding_column.id, "expected_column_id": self.onboarding_column.id},
            format="json",
        )
        self.assertEqual(no_op.status_code, 400, no_op.json())
        self.assertEqual(OnboardingStageChange.objects.filter(card_id=card["id"]).count(), 2)

        self.client.force_authenticate(user=self.other_user)
        forbidden = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.applicant_column.id, "expected_column_id": self.onboarding_column.id},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(OnboardingCard.objects.get(pk=card["id"]).column_id, self.onboarding_column.id)

    def test_column_configuration_and_history_keep_stage_snapshots(self):
        self.authenticate_hr()
        created = self.client.post(
            "/hr/onboarding-board/columns",
            {"label": "References", "phase": "applicant", "position": 1},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.json())
        new_column_id = created.json()["column"]["id"]
        card = self.create_card()
        moved = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": new_column_id, "expected_column_id": self.applicant_column.id},
            format="json",
        )
        self.assertEqual(moved.status_code, 200, moved.json())

        occupied = self.client.patch(
            f"/hr/onboarding-board/columns/{new_column_id}",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(occupied.status_code, 400, occupied.json())
        renamed = self.client.patch(
            f"/hr/onboarding-board/columns/{new_column_id}",
            {"label": "Reference checks", "position": 0},
            format="json",
        )
        self.assertEqual(renamed.status_code, 200, renamed.json())
        self.assertEqual(renamed.json()["column"]["position"], 0)
        history = self.client.get(f"/hr/onboarding-board/cards/{card['id']}/history")
        self.assertEqual(history.status_code, 200, history.json())
        self.assertEqual(history.json()["changes"][0]["to_label"], "References")

        invalid = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": 999999, "expected_column_id": new_column_id},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400, invalid.json())
        self.assertEqual(OnboardingStageChange.objects.filter(card_id=card["id"]).count(), 2)

        empty = self.client.post(
            "/hr/onboarding-board/columns",
            {"label": "Orientation", "phase": "onboarding"},
            format="json",
        )
        self.assertEqual(empty.status_code, 201, empty.json())
        empty_id = empty.json()["column"]["id"]
        archived = self.client.patch(
            f"/hr/onboarding-board/columns/{empty_id}",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(archived.status_code, 200, archived.json())
        self.assertIn(empty_id, [column["id"] for column in self.client.get("/hr/onboarding-board").json()["archived_columns"]])
        restored = self.client.patch(
            f"/hr/onboarding-board/columns/{empty_id}",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(restored.status_code, 200, restored.json())
        self.assertIn(empty_id, [column["id"] for column in self.client.get("/hr/onboarding-board").json()["columns"]])

    def test_linked_employee_moves_do_not_change_employment_status(self):
        self.authenticate_hr()
        employee_user = User.objects.create_user(username="board-employee", password="StrongPass123!")
        employee_user.profile.role = Profile.ROLE_TEACHER
        employee_user.profile.save(update_fields=["role"])
        employee = Employee.objects.create(
            profile=employee_user.profile,
            employee_no="BOARD-001",
            employment_status=Employee.STATUS_DRAFT,
        )
        card = self.create_card(
            name="",
            email="",
            employee_id=employee.id,
            column_id=self.onboarding_column.id,
        )
        self.assertEqual(OnboardingEmployeeLink.objects.get(card_id=card["id"]).actor_id, self.hr_user.profile.id)
        destination = OnboardingColumn.objects.get(phase="onboarding", position=1)
        moved = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": destination.id, "expected_column_id": self.onboarding_column.id},
            format="json",
        )
        self.assertEqual(moved.status_code, 200, moved.json())
        employee.refresh_from_db()
        self.assertEqual(employee.employment_status, Employee.STATUS_DRAFT)
        self.assertEqual(EmploymentRecord.objects.filter(employee=employee).count(), 0)
        backward = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.applicant_column.id, "expected_column_id": destination.id},
            format="json",
        )
        self.assertEqual(backward.status_code, 400, backward.json())

    def test_candidate_handoff_links_existing_employee_once_with_audit_snapshot(self):
        self.authenticate_hr()
        card = self.create_card()
        moved = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.onboarding_column.id, "expected_column_id": self.applicant_column.id},
            format="json",
        )
        self.assertEqual(moved.status_code, 200, moved.json())
        employee_user = User.objects.create_user(
            username="handoff-employee",
            email="employee@example.test",
            password="StrongPass123!",
            first_name="Employee",
            last_name="One",
        )
        employee_user.profile.role = Profile.ROLE_TEACHER
        employee_user.profile.save(update_fields=["role"])
        created_employee = self.client.post(
            "/hr/employees",
            {
                "profile_id": employee_user.profile.id,
                "employee_no": "HANDOFF-001",
                "employment_status": Employee.STATUS_DRAFT,
            },
            format="json",
        )
        self.assertEqual(created_employee.status_code, 201, created_employee.json())
        employee = Employee.objects.get(employee_no="HANDOFF-001")
        records_before_link = EmploymentRecord.objects.filter(employee=employee).count()

        url = f"/hr/onboarding-board/cards/{card['id']}/employee-link"
        self.client.force_authenticate(user=self.other_user)
        forbidden = self.client.post(url, {
            "employee_id": employee.id,
            "expected_column_id": self.onboarding_column.id,
        }, format="json")
        self.assertEqual(forbidden.status_code, 403)

        self.authenticate_hr()
        linked = self.client.post(url, {
            "employee_id": employee.id,
            "expected_column_id": self.onboarding_column.id,
        }, format="json")
        self.assertEqual(linked.status_code, 200, linked.json())
        self.assertEqual(linked.json()["card"]["employee_id"], employee.id)
        self.assertTrue(linked.json()["card"]["has_employee_link"])
        audit = OnboardingEmployeeLink.objects.get(card_id=card["id"])
        self.assertEqual(audit.employee_no, "HANDOFF-001")
        self.assertEqual(audit.employee_name, "Employee One")
        self.assertEqual(audit.actor_id, self.hr_user.profile.id)
        self.assertEqual(audit.actor_name, "board-hr")
        history = self.client.get(f"/hr/onboarding-board/cards/{card['id']}/history")
        self.assertEqual(history.status_code, 200, history.json())
        self.assertEqual(history.json()["employee_link"]["employee_no"], "HANDOFF-001")
        self.assertEqual(len(history.json()["changes"]), 2)
        employee.refresh_from_db()
        self.assertEqual(employee.employment_status, Employee.STATUS_DRAFT)
        self.assertEqual(EmploymentRecord.objects.filter(employee=employee).count(), records_before_link)

        duplicate_card = self.client.post(url, {
            "employee_id": employee.id,
            "expected_column_id": self.onboarding_column.id,
        }, format="json")
        self.assertEqual(duplicate_card.status_code, 409, duplicate_card.json())
        second = self.create_card(name="Another Candidate", column_id=self.onboarding_column.id)
        duplicate_employee = self.client.post(
            f"/hr/onboarding-board/cards/{second['id']}/employee-link",
            {"employee_id": employee.id, "expected_column_id": self.onboarding_column.id},
            format="json",
        )
        self.assertEqual(duplicate_employee.status_code, 409, duplicate_employee.json())
        self.assertEqual(OnboardingEmployeeLink.objects.count(), 1)

        employee.delete()
        board_card = next(row for row in self.client.get("/hr/onboarding-board").json()["cards"] if row["id"] == card["id"])
        self.assertIsNone(board_card["employee_id"])
        self.assertTrue(board_card["has_employee_link"])
        self.assertEqual(
            self.client.get(f"/hr/onboarding-board/cards/{card['id']}/history").json()["employee_link"]["employee_no"],
            "HANDOFF-001",
        )
        applicant_move = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.applicant_column.id, "expected_column_id": self.onboarding_column.id},
            format="json",
        )
        self.assertEqual(applicant_move.status_code, 400, applicant_move.json())

    def test_candidate_handoff_rejects_applicant_stale_and_unknown_employee(self):
        self.authenticate_hr()
        card = self.create_card()
        url = f"/hr/onboarding-board/cards/{card['id']}/employee-link"
        applicant = self.client.post(url, {
            "employee_id": 12345,
            "expected_column_id": self.applicant_column.id,
        }, format="json")
        self.assertEqual(applicant.status_code, 400, applicant.json())
        moved = self.client.post(
            f"/hr/onboarding-board/cards/{card['id']}/move",
            {"column_id": self.onboarding_column.id, "expected_column_id": self.applicant_column.id},
            format="json",
        )
        self.assertEqual(moved.status_code, 200, moved.json())
        stale = self.client.post(url, {
            "employee_id": 12345,
            "expected_column_id": self.applicant_column.id,
        }, format="json")
        self.assertEqual(stale.status_code, 409, stale.json())
        unknown = self.client.post(url, {
            "employee_id": 12345,
            "expected_column_id": self.onboarding_column.id,
        }, format="json")
        self.assertEqual(unknown.status_code, 400, unknown.json())
        self.assertIsNone(OnboardingCard.objects.get(pk=card["id"]).employee_id)
        self.assertFalse(OnboardingEmployeeLink.objects.filter(card_id=card["id"]).exists())

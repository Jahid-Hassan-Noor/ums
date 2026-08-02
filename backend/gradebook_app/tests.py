from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Course, CourseOffering, Profile, School, Semester
from executive_app.models import ResultBatch, ResultRecord
from executive_app.results_service import grade_for_score
from gradebook_app.models import GradebookGrade, GradebookItem
from gradebook_app.services import sync_quiz_grade
from quiz_app.models import Quiz, QuizGrade
from student_app.models import Enrollment
from teacher_app.models import Assignment, AssignmentSubmission


User = get_user_model()


class GradebookWorkflowTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SGB", name="School of Gradebook")
        self.semester = Semester.objects.create(
            name="Semester 1 2026/2027",
            academic_session="2026/2027",
            start_date="2026-09-01",
            end_date="2027-01-15",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="GBK1013",
            title="Flexible Gradebook",
            credits=3,
            school=self.school,
        )
        self.admin = self._profile("gradebook_admin", Profile.ROLE_ADMIN)
        self.teacher = self._profile("gradebook_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("gradebook_student", Profile.ROLE_STUDENT, student_id="GBK260001")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A",
            capacity=30,
        )
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.admin)
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin.user)
        self.teacher_client = APIClient()
        self.teacher_client.force_authenticate(self.teacher.user)
        self.student_client = APIClient()
        self.student_client.force_authenticate(self.student.user)

    def _profile(self, username, role, student_id=""):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.student_id = student_id
        profile.staff_id = "" if role == Profile.ROLE_STUDENT else username.upper()
        profile.save(update_fields=["role", "school", "student_id", "staff_id", "updated_at"])
        return profile

    def test_admin_scale_updates_official_grade_lookup(self):
        response = self.admin_client.post(
            "/gradebook/admin",
            {
                "action": "save_scale",
                "name": "UMS Custom Scale",
                "description": "Senate-approved custom criteria",
                "is_active": True,
                "is_default": True,
                "ranges": [
                    {
                        "letter": "HD",
                        "min_score": "85",
                        "max_score": "100",
                        "grade_points": "4.00",
                        "outcome": "High Distinction",
                        "is_passing": True,
                    },
                    {
                        "letter": "P",
                        "min_score": "50",
                        "max_score": "84.99",
                        "grade_points": "2.00",
                        "outcome": "Pass",
                        "is_passing": True,
                    },
                    {
                        "letter": "F",
                        "min_score": "0",
                        "max_score": "49.99",
                        "grade_points": "0.00",
                        "outcome": "Fail",
                        "is_passing": False,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["scales"][0]["name"], "UMS Custom Scale")
        self.assertEqual(grade_for_score(Decimal("86.00")), ("HD", Decimal("4.00")))

    def test_assignment_grading_syncs_released_student_gradebook(self):
        assignment = Assignment.objects.create(
            offering=self.offering,
            title="Reflection",
            max_score=Decimal("50.00"),
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.student,
            content="Submitted work",
            status=AssignmentSubmission.STATUS_SUBMITTED,
        )

        response = self.teacher_client.post(
            f"/teacher/assignments/{assignment.id}",
            {
                "action": "grade_submission",
                "submission_id": submission.id,
                "grade": "42",
                "feedback": "Clear and complete.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        item = GradebookItem.objects.get(source_app="teacher_app", source_model="Assignment", source_id=assignment.id)
        grade = GradebookGrade.objects.get(item=item, student=self.student)
        self.assertEqual(grade.status, GradebookGrade.STATUS_RELEASED)
        self.assertEqual(grade.raw_score, Decimal("42.00"))

        student_response = self.student_client.get("/gradebook/student")
        self.assertEqual(student_response.status_code, 200)
        course = student_response.json()["courses"][0]
        self.assertEqual(course["items"][0]["title"], "Reflection")
        self.assertEqual(course["grades"][0]["raw_score"], "42.00")

    def test_teacher_can_copy_gradebook_totals_to_result_draft(self):
        item_response = self.teacher_client.post(
            "/gradebook/teacher",
            {
                "action": "save_item",
                "offering_id": self.offering.id,
                "title": "Portfolio",
                "item_type": "manual",
                "max_score": "100",
                "weight": "100",
                "release_to_students": True,
                "is_extra_credit": False,
                "is_active": True,
                "sort_order": 1,
            },
            format="json",
        )
        self.assertEqual(item_response.status_code, 200, item_response.content)
        item_id = item_response.json()["selected"]["items"][0]["id"]

        grade_response = self.teacher_client.post(
            "/gradebook/teacher",
            {
                "action": "update_grade",
                "offering_id": self.offering.id,
                "item_id": item_id,
                "student_id": self.student.id,
                "raw_score": "88",
                "status": "released",
            },
            format="json",
        )
        self.assertEqual(grade_response.status_code, 200, grade_response.content)

        draft_response = self.teacher_client.post(
            "/gradebook/teacher",
            {
                "action": "send_to_result_draft",
                "offering_id": self.offering.id,
            },
            format="json",
        )
        self.assertEqual(draft_response.status_code, 200, draft_response.content)
        batch = ResultBatch.objects.get(offering=self.offering)
        record = ResultRecord.objects.get(batch=batch, student=self.student)
        self.assertEqual(batch.status, "draft")
        self.assertEqual(record.score, Decimal("88.00"))

    def test_quiz_grade_syncs_to_gradebook_item(self):
        quiz = Quiz.objects.create(
            offering=self.offering,
            title="Quiz One",
            status=Quiz.STATUS_PUBLISHED,
            total_marks=Decimal("10.00"),
            review_show_marks=True,
            created_by=self.teacher,
            closes_at=timezone.now(),
        )
        quiz_grade = QuizGrade.objects.create(
            quiz=quiz,
            student=self.student,
            grade=Decimal("8.00"),
            attempts_count=1,
            needs_manual_grading=False,
        )

        sync_quiz_grade(quiz_grade, actor=self.teacher)

        item = GradebookItem.objects.get(source_app="quiz_app", source_model="Quiz", source_id=quiz.id)
        grade = GradebookGrade.objects.get(item=item, student=self.student)
        self.assertEqual(item.title, "Quiz One")
        self.assertEqual(grade.status, GradebookGrade.STATUS_RELEASED)
        self.assertEqual(grade.raw_score, Decimal("8.00"))

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Course, CourseOffering, Profile, School, Semester
from student_app.models import Enrollment
from teacher_app.models import Assignment, AssignmentSubmission


User = get_user_model()


class StudentAssignmentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        self.semester = Semester.objects.create(
            name="Semester 1, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CCS2223",
            title="Systems Development",
            credits=3,
            school=self.school,
        )
        self.teacher = self._profile("assignment_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("assignment_student", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="C1",
            capacity=30,
        )
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.teacher)

        now = timezone.now()
        self.upcoming = self._assignment("Portfolio Draft", now + timezone.timedelta(days=3))
        self.overdue = self._assignment("Missed Reflection", now - timezone.timedelta(days=2))
        self.submitted = self._assignment("Research Notes", now + timezone.timedelta(days=1))
        AssignmentSubmission.objects.create(
            assignment=self.submitted,
            student=self.student,
            content="Submitted notes.",
            attempt_count=1,
            status=AssignmentSubmission.STATUS_SUBMITTED,
        )
        self.graded = self._assignment("Final Report", now - timezone.timedelta(days=1))
        AssignmentSubmission.objects.create(
            assignment=self.graded,
            student=self.student,
            content="Final report content.",
            attempt_count=1,
            status=AssignmentSubmission.STATUS_GRADED,
            grade=88,
            feedback="Strong work.",
            graded_by=self.teacher,
            graded_at=now,
        )
        self.client.force_authenticate(user=self.student.user)

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def _assignment(self, title, due_date):
        return Assignment.objects.create(
            offering=self.offering,
            title=title,
            description=f"{title} description",
            instructions=f"{title} instructions",
            due_date=due_date,
            accepted_file_type=Assignment.FILE_PDF,
            max_files=1,
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )

    def test_student_assignment_status_endpoints_return_bucketed_rows(self):
        cases = [
            ("/student/assignments/upcoming", "Portfolio Draft", "upcoming"),
            ("/student/assignments/overdue", "Missed Reflection", "overdue"),
            ("/student/assignments/submitted", "Research Notes", "submitted"),
            ("/student/assignments/graded", "Final Report", "graded"),
        ]

        for url, title, bucket in cases:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, response.json())
            payload = response.json()
            self.assertEqual(payload["counts"]["all"], 4)
            self.assertEqual(payload["counts"][bucket], 1)
            self.assertEqual([row["title"] for row in payload["assignments"]], [title])
            self.assertEqual(payload["assignments"][0]["student_status"], bucket)

    def test_student_assignment_detail_includes_submission_status_and_feedback(self):
        response = self.client.get(f"/student/assignments/{self.graded.id}")

        self.assertEqual(response.status_code, 200, response.json())
        payload = response.json()
        self.assertEqual(payload["assignment"]["student_status"], "graded")
        self.assertEqual(payload["submission"]["grade"], "88.00")
        self.assertEqual(payload["submission"]["feedback"], "Strong work.")
        self.assertEqual(payload["submission"]["attachments"], [])

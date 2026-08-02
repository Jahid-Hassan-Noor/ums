from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Building, Course, CourseOffering, Profile, Program, School, Semester, Venue
from student_app.models import Enrollment, Exam, ExamVenueAllocation, TranscriptRecord
from teacher_app.models import ResultSubmission


User = get_user_model()


class StudentResultsPortalTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCS", name="School of Computing and Informatics")
        self.program = Program.objects.create(
            code="N/481/6/0827",
            name="Bachelor in Computer Science (Honours)",
            school=self.school,
        )
        today = timezone.localdate()
        self.previous_semester = Semester.objects.create(
            name="Semester 1 (2025/2026-UGP)",
            academic_session="2025/2026",
            start_date=today - timedelta(days=210),
            end_date=today - timedelta(days=90),
        )
        self.current_semester = Semester.objects.create(
            name="Semester 2 (2025/2026-UGP)",
            academic_session="2025/2026",
            start_date=today - timedelta(days=20),
            end_date=today + timedelta(days=90),
            examination_starts_on=today + timedelta(days=30),
            examination_ends_on=today + timedelta(days=40),
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CCC2113",
            title="Data Structures and Algorithm Analysis",
            credits=3,
            school=self.school,
            program=self.program,
        )
        self.previous_offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.previous_semester,
            section="A",
        )
        self.current_offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.current_semester,
            section="A",
        )
        self.teacher = self._profile("teacher_results", Profile.ROLE_TEACHER)
        self.current_offering.instructor = self.teacher
        self.current_offering.save(update_fields=["instructor", "updated_at"])
        self.student = self._profile("student_results", Profile.ROLE_STUDENT)
        Enrollment.objects.create(student=self.student, offering=self.current_offering, created_by=self.teacher)
        TranscriptRecord.objects.create(
            student=self.student,
            semester=self.previous_semester,
            offering=self.previous_offering,
            course_code=self.course.code,
            course_title=self.course.title,
            credit_hours=3,
            score="25.00",
            grade="F",
            grade_points="0.00",
            gpa="0.00",
            cgpa="0.00",
            published_at=timezone.now() - timedelta(days=30),
        )
        TranscriptRecord.objects.create(
            student=self.student,
            semester=self.current_semester,
            offering=self.current_offering,
            course_code=self.course.code,
            course_title=self.course.title,
            credit_hours=3,
            score="45.00",
            grade="C-",
            grade_points="1.67",
            gpa="1.67",
            cgpa="0.84",
            published_at=timezone.now(),
        )
        ResultSubmission.objects.create(
            offering=self.current_offering,
            student=self.student,
            score="54.00",
            grade="C",
            submitted_by=self.teacher,
        )
        building = Building.objects.create(code="B11", name="B11")
        venue = Venue.objects.create(building=building, code="HALL6", name="Level 3 Exam Hall 6", capacity=40)
        exam = Exam.objects.create(
            semester=self.current_semester,
            offering=self.current_offering,
            title="CCC2113 Final Examination",
            exam_type=Exam.TYPE_FINAL,
            starts_at=timezone.now() + timedelta(days=30),
            ends_at=timezone.now() + timedelta(days=30, hours=2),
            is_published=True,
        )
        ExamVenueAllocation.objects.create(exam=exam, venue=venue, seats=40)
        self.client = APIClient()
        self.client.force_authenticate(self.student.user)

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.program = self.program if role == Profile.ROLE_STUDENT else None
        if role == Profile.ROLE_STUDENT:
            profile.student_id = "AIU24102058"
        else:
            profile.staff_id = username.upper()
        profile.save(update_fields=["role", "school", "program", "student_id", "staff_id", "updated_at"])
        return profile

    def test_semester_results_include_all_filter_and_retake_failed_note(self):
        response = self.client.get("/student/results/semester", {"semester": "all"})

        self.assertEqual(response.status_code, 200, response.json())
        self.assertFalse(response.data["summary"]["include_gpa"])
        self.assertEqual(response.data["semesters"][0]["id"], "all")
        self.assertEqual(response.data["records"][0]["note"], "Failed")
        self.assertEqual(response.data["records"][1]["note"], "Retake & Failed")

    def test_specific_semester_includes_gpa_and_pdf_report(self):
        response = self.client.get(
            "/student/results/semester",
            {"semester": str(self.current_semester.id)},
        )
        pdf = self.client.get(
            "/student/results/semester/pdf",
            {"semester": str(self.current_semester.id)},
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.data["summary"]["include_gpa"])
        self.assertEqual(response.data["summary"]["gpa"], "1.67")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_courseworks_show_current_semester_default_ratio(self):
        response = self.client.get("/student/results/course-works")

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.data["default_coursework_weight"], "60.00")
        self.assertEqual(response.data["courseworks"][0]["status"], "Published")
        self.assertEqual(response.data["courseworks"][0]["coursework_mark"], "54.00")

    def test_courseworks_use_coursework_only_assessment_plan(self):
        self.current_offering.has_final_exam = False
        self.current_offering.coursework_percentage = "100.00"
        self.current_offering.final_exam_percentage = "0.00"
        self.current_offering.save(
            update_fields=[
                "has_final_exam",
                "coursework_percentage",
                "final_exam_percentage",
                "updated_at",
            ]
        )

        response = self.client.get("/student/results/course-works")

        self.assertEqual(response.status_code, 200, response.json())
        row = response.data["courseworks"][0]
        self.assertFalse(row["has_final_exam"])
        self.assertEqual(row["coursework_weight"], "100.00")
        self.assertEqual(row["final_exam_weight"], "0.00")
        self.assertIsNone(row["final_exam_starts_at"])

    def test_exam_slip_uses_published_final_exam_schedule_and_downloads_pdf(self):
        response = self.client.get("/student/results/exam-slip")
        pdf = self.client.get("/student/results/exam-slip/pdf")

        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.data["can_download"])
        self.assertEqual(response.data["exams"][0]["course_code"], "CCC2113")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

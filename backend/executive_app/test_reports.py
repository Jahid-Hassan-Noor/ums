import io
import tempfile
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import (
    AuditLog,
    Course,
    CourseOffering,
    Profile,
    Program,
    ReportExport,
    School,
    Semester,
)
from applicant_app.models import AdmissionApplication, Applicant, ApplicationIntake
from student_app.models import TranscriptRecord
from teacher_app.models import Teacher


User = get_user_model()


class ExecutiveReportTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()

        self.school = School.objects.create(code="SCI", name="School of Computing")
        self.other_school = School.objects.create(code="SBSS", name="School of Business")
        self.program = Program.objects.create(
            code="SCI-BCS",
            name="Computer Science",
            school=self.school,
        )
        self.other_program = Program.objects.create(
            code="SBSS-BBA",
            name="Business Administration",
            school=self.other_school,
        )
        self.intake = ApplicationIntake.objects.create(
            code="OCT-2025",
            title="October 2025",
            academic_year="2025/2026",
        )
        self.semester = Semester.objects.create(
            name="Semester 1 2025/2026",
            academic_session="2025/2026",
        )
        self.course = Course.objects.create(
            code="CSC101",
            title="Programming",
            credits=3,
            school=self.school,
            program=self.program,
        )
        self.other_course = Course.objects.create(
            code="BUS101",
            title="Business",
            credits=3,
            school=self.other_school,
            program=self.other_program,
        )
        self.offering = CourseOffering.objects.create(course=self.course, semester=self.semester)
        self.other_offering = CourseOffering.objects.create(
            course=self.other_course,
            semester=self.semester,
        )

        self.executive_user = User.objects.create_user(username="scope_exec", password="pass")
        self.executive = self.executive_user.profile
        self.executive.role = Profile.ROLE_EXECUTIVE
        self.executive.school = self.school
        self.executive.save(update_fields=["role", "school", "updated_at"])

        self.student = self._student("scoped_student", self.school, self.program, "SCI-001", "3.50")
        self.low_cgpa_student = self._student(
            "low_cgpa_student",
            self.school,
            self.program,
            "SCI-002",
            "2.40",
        )
        self.other_student = self._student(
            "other_student",
            self.other_school,
            self.other_program,
            "SBSS-001",
            "4.00",
            offering=self.other_offering,
        )
        self.teacher = self._teacher("scoped_teacher", self.school, "Senior Lecturer")
        self._teacher("other_teacher", self.other_school, "Professor")

        self.client = APIClient()
        self.client.force_authenticate(self.executive_user)

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    def _student(self, username, school, program, student_id, cgpa, offering=None):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.school = school
        profile.program = program
        profile.student_id = student_id
        profile.save(update_fields=["school", "program", "student_id", "updated_at"])
        detail = profile.student_detail
        detail.school = school
        detail.program = program
        detail.student_id = student_id
        detail.current_year = 2
        detail.enrollment_status = "active"
        detail.save()
        applicant, _created = Applicant.objects.update_or_create(profile=profile)
        AdmissionApplication.objects.create(applicant=applicant, intake=self.intake)
        selected_offering = offering or self.offering
        TranscriptRecord.objects.create(
            student=profile,
            semester=self.semester,
            offering=selected_offering,
            course_code=selected_offering.course.code,
            course_title=selected_offering.course.title,
            credit_hours=selected_offering.course.credits,
            score="80.00",
            grade="A",
            grade_points="4.00",
            gpa=cgpa,
            cgpa=cgpa,
            published_at=timezone.now(),
        )
        return profile

    def _teacher(self, username, school, designation):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = Profile.ROLE_TEACHER
        profile.school = school
        profile.designation = designation
        profile.staff_id = username.upper()
        profile.save(
            update_fields=["role", "school", "designation", "staff_id", "updated_at"]
        )
        detail, _created = Teacher.objects.update_or_create(
            profile=profile,
            defaults={
                "school": school,
                "designation": designation,
                "academic_rank": designation,
            },
        )
        return detail

    def _sheet(self, response):
        with ZipFile(io.BytesIO(response.content)) as workbook:
            return workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")

    def test_report_overview_is_limited_to_executive_scope(self):
        response = self.client.get("/executive/reports")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"]["id"], self.school.id)
        self.assertEqual(response.data["students"]["count"], 2)
        self.assertEqual(response.data["teachers"]["count"], 1)
        self.assertEqual(response.data["results"]["count"], 2)

    def test_student_export_excludes_other_school_and_records_scope(self):
        response = self.client.get("/executive/reports/students/export")

        self.assertEqual(response.status_code, 200)
        sheet = self._sheet(response)
        self.assertIn("scoped_student", sheet)
        self.assertNotIn("other_student", sheet)

        report = ReportExport.objects.get(export_type="executive-students")
        self.assertEqual(report.filters["scope"]["id"], self.school.id)
        audit = AuditLog.objects.get(action="report.export.completed", object_id=str(report.id))
        self.assertEqual(audit.details["scope"]["id"], self.school.id)

    def test_final_results_export_filters_minimum_cgpa_and_cohort(self):
        response = self.client.get(
            "/executive/reports/final-results/export",
            {"minimum_cgpa": "3.00", "cohort": "2025/2026"},
        )

        self.assertEqual(response.status_code, 200)
        sheet = self._sheet(response)
        self.assertIn("scoped_student", sheet)
        self.assertNotIn("low_cgpa_student", sheet)
        self.assertNotIn("other_student", sheet)

        report = ReportExport.objects.get(export_type="executive-final-results")
        self.assertEqual(report.filters["minimum_cgpa"], "3.00")
        self.assertEqual(report.filters["cohort"], "2025/2026")
        self.assertEqual(report.filters["row_count"], 1)

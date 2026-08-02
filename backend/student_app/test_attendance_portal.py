from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import ClassMeeting, Course, CourseOffering, Profile, School, Semester, TimetableSlot
from student_app.models import AttendanceRecord, Enrollment
from teacher_app.attendance_service import start_attendance_session


User = get_user_model()


class StudentAttendancePortalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="ATT-S", name="Attendance Student School")
        self.running_semester = Semester.objects.create(
            name="Attendance Running Semester",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            is_active=True,
        )
        self.completed_semester = Semester.objects.create(
            name="Attendance Completed Semester",
            academic_session="2025/2026",
            start_date="2026-03-23",
            end_date="2026-07-17",
            is_active=False,
        )
        self.teacher = self.profile("student_attendance_teacher", Profile.ROLE_TEACHER, "T-ATT-002")
        self.student = self.profile("student_attendance_user", Profile.ROLE_STUDENT, "S-ATT-002")
        self.running_course = Course.objects.create(
            code="ATT2001",
            title="Running Attendance",
            credits=3,
            school=self.school,
        )
        self.completed_course = Course.objects.create(
            code="ATT1001",
            title="Completed Attendance",
            credits=3,
            school=self.school,
        )
        self.running_offering = self.offering(
            self.running_course,
            self.running_semester,
        )
        self.completed_offering = self.offering(
            self.completed_course,
            self.completed_semester,
        )
        self.running_meeting = self.meeting(self.running_offering)
        self.completed_meeting = self.meeting(self.completed_offering)
        Enrollment.objects.create(
            student=self.student,
            offering=self.running_offering,
            created_by=self.teacher,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.completed_offering,
            completed_at=timezone.now(),
            created_by=self.teacher,
        )
        self.client.force_authenticate(user=self.student.user)

    def profile(self, username, role, identifier):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        if role == Profile.ROLE_STUDENT:
            profile.student_id = identifier
        else:
            profile.staff_id = identifier
        profile.save(
            update_fields=["role", "school", "student_id", "staff_id", "updated_at"]
        )
        return profile

    def offering(self, course, semester):
        return CourseOffering.objects.create(
            course=course,
            semester=semester,
            instructor=self.teacher,
            section="A",
            capacity=30,
        )

    def meeting(self, offering):
        return ClassMeeting.objects.create(
            offering=offering,
            semester=offering.semester,
            day_of_week=TimetableSlot.MONDAY,
            start_time="09:00",
            end_time="10:00",
            lecturer=self.teacher,
            class_type=ClassMeeting.CLASS_TYPE_LECTURE,
            status=ClassMeeting.STATUS_SCHEDULED,
        )

    def test_scanned_link_resolves_and_submits_using_code_only(self):
        session = start_attendance_session(
            self.teacher,
            self.running_meeting,
            session_date=timezone.localdate(),
        )

        lookup = self.client.get("/student/attendance/qr", {"code": session.qr_token})
        self.assertEqual(lookup.status_code, 200)
        self.assertTrue(lookup.json()["is_valid"])
        self.assertEqual(lookup.json()["session"]["course_code"], self.running_course.code)

        submitted = self.client.post(
            "/student/attendance/code",
            {"code": session.qr_token},
            format="json",
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["submission"]["status"], "accepted")
        self.assertTrue(
            AttendanceRecord.objects.filter(
                attendance_session=session,
                student=self.student,
                present=True,
            ).exists()
        )

    def test_report_lists_running_and_completed_semesters_with_course_details(self):
        completed_session = start_attendance_session(
            self.teacher,
            self.completed_meeting,
            session_date=date(2026, 7, 17),
        )
        AttendanceRecord.objects.create(
            student=self.student,
            offering=self.completed_offering,
            attendance_session=completed_session,
            class_date=completed_session.session_date,
            present=True,
            attendance_status=AttendanceRecord.STATUS_ATTEND,
            source=AttendanceRecord.SOURCE_MANUAL,
            marked_by=self.teacher,
            marked_at=timezone.now(),
        )

        response = self.client.get(
            "/student/attendance/report",
            {"semester_id": self.completed_semester.id},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            {semester["id"] for semester in data["semesters"]},
            {self.running_semester.id, self.completed_semester.id},
        )
        self.assertEqual(data["semester"]["id"], self.completed_semester.id)
        self.assertEqual(data["courses"][0]["course_code"], self.completed_course.code)
        self.assertEqual(data["courses"][0]["attendance_percentage"], 100)
        self.assertEqual(data["courses"][0]["records"][0]["status"], "attend")

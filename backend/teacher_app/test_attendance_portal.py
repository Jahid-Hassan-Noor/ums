from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import ClassMeeting, Course, CourseOffering, Profile, School, Semester, TimetableSlot
from student_app.models import AttendanceRecord, Enrollment
from teacher_app.attendance_service import start_attendance_session


User = get_user_model()


class TeacherAttendancePortalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="ATT-T", name="Attendance Teacher School")
        self.semester = Semester.objects.create(
            name="Attendance Teacher Semester",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            is_active=True,
        )
        self.teacher = self.profile("attendance_teacher", Profile.ROLE_TEACHER, "T-ATT-001")
        self.student = self.profile("attendance_student", Profile.ROLE_STUDENT, "S-ATT-001")
        self.course = Course.objects.create(
            code="ATT1001",
            title="Attendance Systems",
            credits=3,
            school=self.school,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A",
            capacity=30,
        )
        self.meeting = ClassMeeting.objects.create(
            offering=self.offering,
            semester=self.semester,
            day_of_week=TimetableSlot.MONDAY,
            start_time="09:00",
            end_time="10:00",
            lecturer=self.teacher,
            class_type=ClassMeeting.CLASS_TYPE_LECTURE,
            status=ClassMeeting.STATUS_SCHEDULED,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            created_by=self.teacher,
        )
        self.client.force_authenticate(user=self.teacher.user)

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

    def test_open_session_uses_six_character_sixty_second_code(self):
        before = timezone.now()
        session = start_attendance_session(
            self.teacher,
            self.meeting,
            session_date=timezone.localdate(),
        )

        self.assertEqual(len(session.qr_token), 6)
        self.assertTrue(session.qr_token.isalnum())
        self.assertGreaterEqual((session.qr_expires_at - before).total_seconds(), 59)
        self.assertLessEqual((session.qr_expires_at - before).total_seconds(), 61)

    def test_teacher_can_regenerate_open_qr_and_load_it_from_sessions(self):
        session = start_attendance_session(
            self.teacher,
            self.meeting,
            session_date=timezone.localdate(),
        )
        original_code = session.qr_token

        listing = self.client.get("/teacher/attendance/sessions")
        self.assertEqual(listing.status_code, 200)
        listed_session = listing.json()["sessions"][0]
        self.assertEqual(listed_session["qr_token"], original_code)
        self.assertEqual(listed_session["qr_ttl_seconds"], 60)
        self.assertEqual(
            listed_session["attendance_url_path"],
            f"/class-attendance?code={original_code}",
        )

        regenerated = self.client.post(
            "/teacher/attendance/sessions",
            {"session_id": session.id, "action": "regenerate_qr"},
            format="json",
        )
        self.assertEqual(regenerated.status_code, 200)
        self.assertNotEqual(regenerated.json()["session"]["qr_token"], original_code)

    def test_corrections_endpoint_loads_roster_and_updates_record(self):
        session = start_attendance_session(
            self.teacher,
            self.meeting,
            session_date=timezone.localdate(),
        )

        roster = self.client.get(
            "/teacher/attendance/corrections",
            {"session_id": session.id},
        )
        self.assertEqual(roster.status_code, 200)
        self.assertEqual(roster.json()["students"][0]["student_id"], self.student.id)
        self.assertEqual(roster.json()["students"][0]["record"]["status"], "pending")

        correction = self.client.post(
            "/teacher/attendance/corrections",
            {
                "session_id": session.id,
                "student_id": self.student.id,
                "attendance_status": AttendanceRecord.STATUS_LATE,
                "reason": "Arrived after the first scan.",
            },
            format="json",
        )
        self.assertEqual(correction.status_code, 200)
        record = AttendanceRecord.objects.get(
            attendance_session=session,
            student=self.student,
        )
        self.assertEqual(record.attendance_status, AttendanceRecord.STATUS_LATE)
        self.assertTrue(record.present)


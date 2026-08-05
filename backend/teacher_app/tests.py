import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from admin_app.models import ClassMeeting, Course, CourseOffering, Profile, School, Semester, SystemSetting, TimetableSlot
from admin_app.settings_registry import invalidate_settings_cache
from student_app.models import AttendanceRecord, Enrollment
from teacher_app.attendance_service import (
    attendance_summary_for_offering,
    manual_mark_attendance,
    qr_ttl_seconds,
    reschedule_or_cancel_class,
    send_low_attendance_warnings,
    start_attendance_session,
    submit_qr_attendance,
)
from teacher_app.assignment_service import (
    can_submit_assignment,
    notify_assignment_students,
    upsert_submission,
    validate_submission_files,
)
from teacher_app.course_content_service import (
    create_course_announcement,
    validate_resource_file,
)
from teacher_app.models import Assignment, AssignmentSubmission


User = get_user_model()


class AssignmentRuleTests(TestCase):
    def setUp(self):
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
        self.teacher = self._profile("teacher_one", Profile.ROLE_TEACHER)
        self.student = self._profile("student_one", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="C1",
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            created_by=self.teacher,
        )
        self.assignment = Assignment.objects.create(
            offering=self.offering,
            title="Design Report",
            description="Submit the design report.",
            instructions="Upload one PDF file.",
            due_date=timezone.now() + timezone.timedelta(days=3),
            accepted_file_type=Assignment.FILE_PDF,
            max_files=1,
            allow_multiple_submissions=False,
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def image_upload(self):
        image = Image.new("RGB", (20, 20), color="navy")
        content = io.BytesIO()
        image.save(content, format="PNG")
        content.seek(0)
        return SimpleUploadedFile(
            "diagram.png",
            content.read(),
            content_type="image/png",
        )

    def test_file_type_and_file_count_are_validated(self):
        pdf = SimpleUploadedFile("report.pdf", b"content", content_type="application/pdf")
        doc = SimpleUploadedFile(
            "report.docx",
            b"content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertIsNone(validate_submission_files(self.assignment, [pdf]))
        self.assertIn("not allowed", validate_submission_files(self.assignment, [doc]))
        self.assertIn("up to 1 file", validate_submission_files(self.assignment, [pdf, pdf]))

    def test_image_assignment_validates_uploaded_image_content(self):
        self.assignment.accepted_file_type = Assignment.FILE_IMAGE
        self.assignment.save(update_fields=["accepted_file_type", "updated_at"])

        invalid_image = SimpleUploadedFile(
            "diagram.jpg",
            b"not really an image",
            content_type="image/jpeg",
        )

        self.assertIsNone(validate_submission_files(self.assignment, [self.image_upload()]))
        self.assertIn("valid image", validate_submission_files(self.assignment, [invalid_image]))

    def test_single_submission_assignment_blocks_second_attempt(self):
        submission = AssignmentSubmission.objects.create(
            assignment=self.assignment,
            student=self.student,
            attempt_count=1,
            status=AssignmentSubmission.STATUS_SUBMITTED,
        )

        error = can_submit_assignment(self.assignment, existing_submission=submission)

        self.assertIn("only one submission", error)

    def test_published_assignment_notifies_enrolled_students(self):
        notify_assignment_students(self.assignment)

        self.assertTrue(
            self.student.notifications.filter(
                verb=f"New assignment posted: {self.assignment.title}",
                data__assignment_id=self.assignment.id,
            ).exists()
        )

    def test_assignment_submission_notifies_teacher(self):
        submission = upsert_submission(
            self.assignment,
            self.student,
            content="Completed report.",
        )

        self.assertTrue(
            self.teacher.notifications.filter(
                data__event_type="assignments.submitted",
                data__submission_id=submission.id,
                data__url=f"/teacher/assignments/{self.assignment.id}/submissions",
            ).exists()
        )


class CourseContentAndAttendanceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        self.semester = Semester.objects.create(
            name="Semester 2, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2027-03-22",
            end_date="2027-07-16",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CCS3333",
            title="Advanced Systems",
            credits=3,
            school=self.school,
            has_lab=True,
        )
        self.teacher = self._profile("teacher_content", Profile.ROLE_TEACHER)
        self.student = self._profile("student_content", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="C1",
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
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.teacher)

    def tearDown(self):
        invalidate_settings_cache()

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.designation = "Lecturer"
        profile.save(update_fields=["role", "school", "designation", "updated_at"])
        return profile

    def test_course_announcement_notifies_enrolled_students(self):
        announcement = create_course_announcement(
            self.offering,
            self.teacher,
            {
                "title": "Quiz 1",
                "body": "Quiz next week.",
                "announcement_type": "quiz",
            },
        )

        self.assertEqual(announcement.announcement_type, "quiz")
        self.assertTrue(
            self.student.notifications.filter(
                data__announcement_id=announcement.id,
                data__course_code=self.course.code,
            ).exists()
        )

    def test_attendance_qr_ttl_uses_academic_policy_setting(self):
        SystemSetting.objects.create(
            key="ums.academic",
            value={"attendance_code_expiry_minutes": 5},
        )
        invalidate_settings_cache()

        self.assertEqual(qr_ttl_seconds(), 300)

    def test_resource_upload_validation_allows_pdf_and_ppt_only(self):
        pdf = SimpleUploadedFile("outline.pdf", b"content", content_type="application/pdf")
        ppt = SimpleUploadedFile("slides.pptx", b"content", content_type="application/vnd.ms-powerpoint")
        zip_file = SimpleUploadedFile("bundle.zip", b"content", content_type="application/zip")

        self.assertIsNone(validate_resource_file(pdf))
        self.assertIsNone(validate_resource_file(ppt))
        self.assertIn("PDF, PPT, or PPTX", validate_resource_file(zip_file))

    def test_qr_attendance_and_manual_late_status(self):
        session = start_attendance_session(self.teacher, self.meeting, session_date=timezone.localdate())
        accepted = submit_qr_attendance(self.student, session=session, token=session.qr_token)

        self.assertEqual(accepted.status, "accepted")
        self.assertTrue(
            AttendanceRecord.objects.filter(
                student=self.student,
                attendance_session=session,
                attendance_status=AttendanceRecord.STATUS_ATTEND,
                present=True,
            ).exists()
        )

        record, error = manual_mark_attendance(
            session,
            self.student,
            self.teacher,
            attendance_status=AttendanceRecord.STATUS_LATE,
            reason="Arrived after QR closed.",
        )

        self.assertIsNone(error)
        self.assertEqual(record.attendance_status, AttendanceRecord.STATUS_LATE)
        self.assertTrue(record.present)

    def test_manual_attendance_rejects_invalid_image_certificate(self):
        session = start_attendance_session(self.teacher, self.meeting, session_date=timezone.localdate())
        record, error = manual_mark_attendance(
            session,
            self.student,
            self.teacher,
            attendance_status=AttendanceRecord.STATUS_ABSENT_MC,
            reason="Medical certificate supplied.",
            medical_certificate=SimpleUploadedFile(
                "certificate.jpg",
                b"not really an image",
                content_type="image/jpeg",
            ),
        )

        self.assertIsNone(record)
        self.assertIn("valid image", error)

    def test_schedule_change_notifies_students(self):
        updated = reschedule_or_cancel_class(
            self.teacher,
            self.meeting,
            {
                "start_time": "10:00",
                "end_time": "11:00",
                "reason": "Room preparation delay.",
            },
        )

        self.assertEqual(updated.start_time.strftime("%H:%M"), "10:00")
        self.assertTrue(
            self.student.notifications.filter(
                data__class_meeting_id=updated.id,
                data__reason="Room preparation delay.",
            ).exists()
        )

    def test_low_attendance_warning_after_five_classes(self):
        for offset in range(5):
            session = start_attendance_session(
                self.teacher,
                self.meeting,
                session_date=timezone.localdate() + timezone.timedelta(days=offset),
            )
            if offset == 0:
                manual_mark_attendance(
                    session,
                    self.student,
                    self.teacher,
                    attendance_status=AttendanceRecord.STATUS_ATTEND,
                )

        summary = attendance_summary_for_offering(self.offering)[0]
        warned = send_low_attendance_warnings(self.offering, self.teacher)

        self.assertEqual(summary["total_classes"], 5)
        self.assertEqual(summary["attendance_percentage"], 20)
        self.assertEqual(len(warned), 1)
        self.assertTrue(
            self.student.notifications.filter(
                verb=f"Attendance warning for {self.course.code}",
            ).exists()
        )

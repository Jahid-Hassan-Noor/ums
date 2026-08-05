from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import (
    Course,
    CourseOffering,
    Profile,
    School,
    Semester,
    SystemSetting,
)
from admin_app.settings_registry import invalidate_settings_cache
from executive_app.models import CourseEvaluationResponse, CourseEvaluationSurvey
from librarian_app.models import Book, BookCopy, Laptop, LibraryRoom, Loan
from notifications_package.models import Notification
from notifications_package.reminders import process_due_reminders
from notifications_package.service import notify_profile, notify_roles
from student_app.models import Enrollment
from teacher_app.models import Assignment, AssignmentSubmission


User = get_user_model()


class NotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="notification_user",
            first_name="Notification",
            last_name="User",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="other_notification_user",
            password="StrongPass123!",
        )
        self.actor_user = User.objects.create_user(
            username="notification_actor",
            first_name="Portal",
            last_name="Admin",
            password="StrongPass123!",
        )
        self.actor_user.profile.role = Profile.ROLE_ADMIN
        self.actor_user.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(self.user)

    def test_list_returns_only_current_users_notifications(self):
        own = Notification.objects.create(
            recipient=self.user.profile,
            actor=self.actor_user.profile,
            verb="Your request was approved.",
            data={"url": "/student/registration/requests"},
        )
        Notification.objects.create(
            recipient=self.other_user.profile,
            verb="Other user's notification.",
        )

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(response.data["notifications"][0]["id"], own.id)
        self.assertEqual(response.data["notifications"][0]["actor"]["name"], "Portal Admin")

    def test_list_without_trailing_slash_returns_shared_notifications(self):
        own = Notification.objects.create(
            recipient=self.user.profile,
            verb="Frontend normalized notification.",
        )

        response = self.client.get("/notifications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(response.data["notifications"][0]["id"], own.id)

    def test_mark_read_only_updates_current_users_notification(self):
        own = Notification.objects.create(
            recipient=self.user.profile,
            verb="Own notification.",
        )
        other = Notification.objects.create(
            recipient=self.other_user.profile,
            verb="Other notification.",
        )

        response = self.client.post(f"/notifications/{own.id}/read/")
        forbidden = self.client.post(f"/notifications/{other.id}/read/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["notification"]["unread"])
        self.assertEqual(forbidden.status_code, 404)
        own.refresh_from_db()
        other.refresh_from_db()
        self.assertFalse(own.unread)
        self.assertTrue(other.unread)

    def test_mark_all_read_only_updates_current_users_notifications(self):
        Notification.objects.create(recipient=self.user.profile, verb="First.")
        Notification.objects.create(recipient=self.user.profile, verb="Second.")
        other = Notification.objects.create(
            recipient=self.other_user.profile,
            verb="Other.",
        )

        response = self.client.post("/notifications/read-all/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated_count"], 2)
        self.assertFalse(
            Notification.objects.filter(recipient=self.user.profile, unread=True).exists()
        )
        other.refresh_from_db()
        self.assertTrue(other.unread)

    def test_delete_only_removes_current_users_notification(self):
        own = Notification.objects.create(
            recipient=self.user.profile,
            verb="Own notification.",
        )
        other = Notification.objects.create(
            recipient=self.other_user.profile,
            verb="Other notification.",
        )

        response = self.client.delete(f"/notifications/{own.id}/")
        forbidden = self.client.delete(f"/notifications/{other.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted_count"], 1)
        self.assertEqual(response.data["total_count"], 0)
        self.assertEqual(response.data["unread_count"], 0)
        self.assertEqual(forbidden.status_code, 404)
        self.assertFalse(Notification.objects.filter(id=own.id).exists())
        self.assertTrue(Notification.objects.filter(id=other.id).exists())

    def test_delete_read_only_removes_current_users_read_notifications(self):
        read = Notification.objects.create(
            recipient=self.user.profile,
            verb="Read notification.",
            unread=False,
        )
        unread = Notification.objects.create(
            recipient=self.user.profile,
            verb="Unread notification.",
        )
        other_read = Notification.objects.create(
            recipient=self.other_user.profile,
            verb="Other read notification.",
            unread=False,
        )

        response = self.client.delete("/notifications/read/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted_count"], 1)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertFalse(Notification.objects.filter(id=read.id).exists())
        self.assertTrue(Notification.objects.filter(id=unread.id).exists())
        self.assertTrue(Notification.objects.filter(id=other_read.id).exists())


class NotificationServiceTests(TestCase):
    def create_profile(self, username, role, *, active=True):
        user = User.objects.create_user(username=username, password="pass", is_active=active)
        profile = user.profile
        profile.role = role
        profile.is_active = active
        profile.save(update_fields=["role", "is_active", "updated_at"])
        return profile

    def test_notify_profile_adds_event_type_and_deep_link(self):
        student = self.create_profile("service_student", Profile.ROLE_STUDENT)
        actor = self.create_profile("service_admin", Profile.ROLE_ADMIN)

        notify_profile(
            student,
            actor=actor,
            event_type="student.test_event",
            verb="A test event is ready.",
            data={"object_id": 42},
            url="/student/dashboard",
        )

        notification = student.notifications.get()
        self.assertEqual(notification.actor, actor)
        self.assertEqual(notification.data["event_type"], "student.test_event")
        self.assertEqual(notification.data["object_id"], 42)
        self.assertEqual(notification.data["url"], "/student/dashboard")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://portal.test",
        DEFAULT_FROM_EMAIL="University Portal <portal@example.com>",
    )
    def test_notify_profile_can_send_email_when_requested(self):
        student = self.create_profile("email_service_student", Profile.ROLE_STUDENT)
        student.user.email = "email-service-student@example.com"
        student.user.save(update_fields=["email"])

        notify_profile(
            student,
            event_type="student.email_test",
            verb="A test event also sent email.",
            data={"object_id": 43},
            url="/student/dashboard",
            email_subject="University Portal notification",
            email_message="A test notification is ready.",
        )

        self.assertEqual(student.notifications.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "University Portal notification")
        self.assertIn("A test notification is ready.", mail.outbox[0].body)
        self.assertIn("Open in University Portal:", mail.outbox[0].body)
        self.assertIn("http://portal.test/student/dashboard", mail.outbox[0].body)

    def test_notify_roles_excludes_inactive_profiles(self):
        active = self.create_profile("active_librarian", Profile.ROLE_LIBRARIAN)
        inactive = self.create_profile(
            "inactive_librarian",
            Profile.ROLE_LIBRARIAN,
            active=False,
        )

        notify_roles(
            [Profile.ROLE_LIBRARIAN],
            event_type="library.requested",
            verb="A borrowing request is ready.",
        )

        self.assertEqual(active.notifications.count(), 1)
        self.assertEqual(inactive.notifications.count(), 0)


class DueReminderTests(TestCase):
    def setUp(self):
        invalidate_settings_cache()
        self.client = APIClient()
        self.school = School.objects.create(code="REM", name="Reminder School")
        self.semester = Semester.objects.create(
            name="Reminder Semester 2026",
            academic_session="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
            is_active=True,
        )
        self.teacher = self._profile("reminder_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("reminder_student", Profile.ROLE_STUDENT)
        self.course = Course.objects.create(
            code="REM101",
            title="Reminder Testing",
            credits=3,
            school=self.school,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="R1",
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            created_by=self.teacher,
        )
        self.now = timezone.now()

    def tearDown(self):
        invalidate_settings_cache()

    def _profile(self, username, role):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def _set_notification_setting(self, name, value):
        SystemSetting.objects.update_or_create(
            key="portal.notifications",
            defaults={
                "value": {name: value},
                "updated_by": self.teacher,
            },
        )
        invalidate_settings_cache()

    def _assignment(self, title, due_date):
        return Assignment.objects.create(
            offering=self.offering,
            title=title,
            due_date=due_date,
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )

    def _evaluation_offering(self, code, title):
        course = Course.objects.create(
            code=code,
            title=title,
            credits=3,
            school=self.school,
        )
        offering = CourseOffering.objects.create(
            course=course,
            semester=self.semester,
            instructor=self.teacher,
            section=code[-1],
        )
        Enrollment.objects.create(
            student=self.student,
            offering=offering,
            created_by=self.teacher,
        )
        return offering

    def _evaluation_survey(self, offering, *, opens_at, closes_at):
        return CourseEvaluationSurvey.objects.create(
            offering=offering,
            title=f"SEC-SET {offering.course.code}",
            instructions="Complete the required SEC-SET evaluation.",
            questions=[
                {
                    "id": "q1",
                    "section": "General",
                    "text": "The course was effective.",
                    "type": "likert",
                    "required": True,
                }
            ],
            opens_at=opens_at,
            closes_at=closes_at,
            is_published=True,
            is_required=True,
            created_by=self.teacher,
        )

    def test_two_hour_reminders_are_created_once_for_unreturned_and_unsubmitted_items(self):
        book = Book.objects.create(title="Reminder Book", author="Library Author")
        copy = BookCopy.objects.create(book=book, accession_number="REM-BK-1")
        due_loan = Loan.objects.create(
            student=self.student,
            book_copy=copy,
            assigned_by=self.teacher,
            due_at=self.now + timezone.timedelta(minutes=90),
        )
        returned_laptop = Laptop.objects.create(
            asset_tag="REM-LT-1",
            brand="Dell",
            model="Latitude",
            status=Laptop.STATUS_AVAILABLE,
        )
        Loan.objects.create(
            student=self.student,
            laptop=returned_laptop,
            assigned_by=self.teacher,
            due_at=self.now + timezone.timedelta(minutes=60),
            status=Loan.STATUS_RETURNED,
            returned_at=self.now,
        )
        due_room = LibraryRoom.objects.create(
            code="REM-ROOM-1",
            name="Reminder Discussion Room",
            location="Library Level 2",
            status=LibraryRoom.STATUS_IN_USE,
        )
        due_room_loan = Loan.objects.create(
            student=self.student,
            room=due_room,
            assigned_by=self.teacher,
            due_at=self.now + timezone.timedelta(minutes=45),
        )

        due_project = self._assignment(
            "Capstone Project",
            self.now + timezone.timedelta(minutes=100),
        )
        submitted_assignment = self._assignment(
            "Submitted Exercise",
            self.now + timezone.timedelta(minutes=80),
        )
        AssignmentSubmission.objects.create(
            assignment=submitted_assignment,
            student=self.student,
            attempt_count=1,
            status=AssignmentSubmission.STATUS_SUBMITTED,
        )
        self._assignment(
            "Later Assignment",
            self.now + timezone.timedelta(hours=4),
        )

        first = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )
        second = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )

        self.assertEqual(first["library"], 2)
        self.assertEqual(first["assignments"], 1)
        self.assertEqual(second["library"], 0)
        self.assertEqual(second["assignments"], 0)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="library.loan_due_soon",
                data__loan_id=due_loan.id,
            ).count(),
            1,
        )
        room_reminder = Notification.objects.get(
            recipient=self.student,
            data__event_type="library.loan_due_soon",
            data__loan_id=due_room_loan.id,
        )
        self.assertEqual(room_reminder.data["asset_type"], "room")
        self.assertEqual(room_reminder.data["url"], "/student/library/rooms")
        self.assertIn("Return the key", room_reminder.verb)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="assignments.due_soon",
                data__assignment_id=due_project.id,
            ).count(),
            1,
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__assignment_id=submitted_assignment.id,
            ).exists()
        )

    def test_library_due_reminders_respect_notification_setting(self):
        book = Book.objects.create(
            title="Disabled Reminder Book",
            author="Library Author",
        )
        copy = BookCopy.objects.create(book=book, accession_number="REM-BK-DISABLED")
        Loan.objects.create(
            student=self.student,
            book_copy=copy,
            assigned_by=self.teacher,
            due_at=self.now + timezone.timedelta(minutes=90),
        )
        self._set_notification_setting("notify_library_due_reminders", False)

        result = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )

        self.assertEqual(result["library"], 0)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="library.loan_due_soon",
            ).exists()
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_BASE_URL="http://portal.test",
        DEFAULT_FROM_EMAIL="University Portal <portal@example.com>",
    )
    def test_required_sec_set_reminders_are_created_once_for_open_and_closing_surveys(self):
        opened_survey = self._evaluation_survey(
            self.offering,
            opens_at=self.now - timezone.timedelta(minutes=30),
            closes_at=self.now + timezone.timedelta(days=7),
        )
        closing_offering = self._evaluation_offering("REM102", "Closing Evaluation")
        closing_survey = self._evaluation_survey(
            closing_offering,
            opens_at=self.now - timezone.timedelta(days=7),
            closes_at=self.now + timezone.timedelta(minutes=90),
        )
        submitted_offering = self._evaluation_offering("REM103", "Submitted Evaluation")
        submitted_survey = self._evaluation_survey(
            submitted_offering,
            opens_at=self.now - timezone.timedelta(minutes=30),
            closes_at=self.now + timezone.timedelta(days=7),
        )
        CourseEvaluationResponse.objects.create(
            survey=submitted_survey,
            student=self.student,
            answers={"q1": "agree"},
        )

        first = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )
        second = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )

        self.assertEqual(first["evaluations"], 2)
        self.assertEqual(second["evaluations"], 0)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="evaluations.opened",
                data__survey_id=opened_survey.id,
            ).count(),
            1,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="evaluations.closing_soon",
                data__survey_id=closing_survey.id,
            ).count(),
            1,
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__survey_id=submitted_survey.id,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 2)
        subjects = {message.subject for message in mail.outbox}
        self.assertIn("SEC-SET evaluation is open: REM101", subjects)
        self.assertIn("SEC-SET evaluation closes soon: REM102", subjects)
        self.assertTrue(
            any(
                f"http://portal.test/student/evaluations/{opened_survey.id}" in message.body
                for message in mail.outbox
            )
        )

    def test_sec_set_reminders_respect_notification_setting(self):
        survey = self._evaluation_survey(
            self.offering,
            opens_at=self.now - timezone.timedelta(minutes=30),
            closes_at=self.now + timezone.timedelta(days=7),
        )
        self._set_notification_setting("notify_sec_set_reminders", False)

        result = process_due_reminders(
            profile=self.student,
            now=self.now,
            force=True,
        )

        self.assertEqual(result["evaluations"], 0)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__survey_id=survey.id,
            ).exists()
        )

    def test_notification_summary_does_not_process_due_reminders_inline(self):
        assignment = self._assignment(
            "Two Hour Assignment",
            self.now + timezone.timedelta(minutes=110),
        )
        self.client.force_authenticate(user=self.student.user)

        response = self.client.get("/notifications/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unread_count"], 0)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.student,
                data__event_type="assignments.due_soon",
                data__assignment_id=assignment.id,
            ).exists()
        )

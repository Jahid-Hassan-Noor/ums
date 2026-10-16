from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.schedule import reference_semester_for_date
from admin_app.models import Course, CourseOffering, Profile, School, Semester
from student_app.models import Enrollment, Exam
from teacher_app.models import (
    Assignment,
    CourseActivity,
    CourseAnnouncement,
    CourseAnnouncementSlot,
)


User = get_user_model()


class AcademicCalendarApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="CAL", name="Calendar School")
        self.semester = Semester.objects.create(
            name="Calendar Semester",
            academic_session="2026/2027",
            start_date="2026-06-01",
            end_date="2026-12-20",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CAL101",
            title="Calendar Systems",
            credits=3,
            school=self.school,
            has_lab=True,
        )
        self.teacher = self._profile("calendar_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("calendar_student", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A",
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            created_by=self.teacher,
        )
        due_at = timezone.now() + timezone.timedelta(days=3)
        self.assignment = Assignment.objects.create(
            offering=self.offering,
            title="Design report",
            due_date=due_at,
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )
        self.lab = Assignment.objects.create(
            offering=self.offering,
            title="Network lab",
            activity_kind=Assignment.ACTIVITY_LAB,
            due_date=due_at + timezone.timedelta(days=1),
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )
        CourseActivity.objects.create(
            offering=self.offering,
            title="In-class midterm",
            activity_type=CourseActivity.TYPE_EXAM,
            due_at=due_at + timezone.timedelta(days=2),
        )
        announcement = CourseAnnouncement.objects.create(
            offering=self.offering,
            title="Project presentation",
            announcement_type=CourseAnnouncement.TYPE_PRESENTATION,
            is_published=True,
            created_by=self.teacher,
        )
        CourseAnnouncementSlot.objects.create(
            announcement=announcement,
            label="Presentation room 1",
            starts_at=due_at + timezone.timedelta(days=3),
            ends_at=due_at + timezone.timedelta(days=3, hours=1),
        )
        Exam.objects.create(
            semester=self.semester,
            offering=self.offering,
            title="CAL101 Final Examination",
            starts_at=due_at + timezone.timedelta(days=10),
            ends_at=due_at + timezone.timedelta(days=10, hours=2),
            is_published=True,
        )

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def test_teacher_calendar_contains_scoped_clickable_course_events(self):
        self.client.force_authenticate(user=self.teacher.user)

        response = self.client.get("/teacher/calendar")

        self.assertEqual(response.status_code, 200, response.json())
        events = response.json()["schedule"]["events"]
        event_types = {event["event_type"] for event in events}
        self.assertTrue({"assignment", "lab_work", "exam", "presentation"} <= event_types)
        assignment_event = next(
            event for event in events if event["id"] == f"assignment-{self.assignment.id}"
        )
        self.assertEqual(
            assignment_event["href"],
            f"/teacher/assignments/{self.assignment.id}",
        )
        self.assertEqual(assignment_event["course_code"], "CAL101")
        self.assertEqual(
            response.json()["schedule"]["semester"],
            {
                "id": self.semester.id,
                "name": "Calendar Semester",
                "start_date": "2026-06-01",
                "end_date": "2026-12-20",
                "starting_week": 1,
            },
        )

    def test_student_calendar_contains_only_published_enrolled_events(self):
        other_course = Course.objects.create(
            code="OUT101",
            title="Outside Course",
            credits=3,
            school=self.school,
        )
        other_offering = CourseOffering.objects.create(
            course=other_course,
            semester=self.semester,
            instructor=self.teacher,
            section="B",
            capacity=30,
        )
        Assignment.objects.create(
            offering=other_offering,
            title="Outside assignment",
            due_date=timezone.now() + timezone.timedelta(days=2),
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )
        Assignment.objects.create(
            offering=self.offering,
            title="Draft assignment",
            due_date=timezone.now() + timezone.timedelta(days=2),
            status=Assignment.STATUS_DRAFT,
            created_by=self.teacher,
        )
        self.client.force_authenticate(user=self.student.user)

        response = self.client.get("/student/calendar")

        self.assertEqual(response.status_code, 200, response.json())
        events = response.json()["schedule"]["events"]
        titles = {event["title"] for event in events}
        self.assertNotIn("Outside assignment", titles)
        self.assertNotIn("Draft assignment", titles)
        self.assertIn("Design report", titles)
        assignment_event = next(
            event for event in events if event["id"] == f"assignment-{self.assignment.id}"
        )
        self.assertEqual(
            assignment_event["href"],
            f"/student/assignments/{self.assignment.id}",
        )
        self.assertEqual(
            response.json()["schedule"]["semester"]["id"],
            self.semester.id,
        )

    def test_timetables_include_official_semester_week_context(self):
        for profile, endpoint in (
            (self.teacher, "/teacher/timetable"),
            (self.student, "/student/timetable"),
        ):
            with self.subTest(endpoint=endpoint):
                self.client.force_authenticate(user=profile.user)
                response = self.client.get(endpoint)

                self.assertEqual(response.status_code, 200, response.json())
                semester = response.json()["schedule"]["semester"]
                self.assertEqual(semester["id"], self.semester.id)
                self.assertEqual(semester["start_date"], "2026-06-01")
                self.assertEqual(semester["starting_week"], 1)

    def test_reference_calendar_does_not_fabricate_unsaved_semester(self):
        reference = reference_semester_for_date(
            Semester.CALENDAR_UNDERGRADUATE,
            date(2026, 4, 27),
        )

        self.assertIsNone(reference)

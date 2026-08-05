from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import (
    ClassMeeting,
    Course,
    CourseOffering,
    Profile,
    School,
    Semester,
    TimetableSlot,
)
from admin_app.xlsx import build_xlsx
from executive_app.evaluation_service import (
    default_questions,
    ensure_starter_template,
    export_rows,
)
from executive_app.models import CourseEvaluationSurvey
from executive_app.notifications import notify_meeting_change, notify_offering_teachers
from student_app.models import Enrollment, RegistrationPeriod
from student_app.registration_service import register_student


User = get_user_model()


class ExecutiveCoursePrerequisiteTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        user = User.objects.create_user(username="course_exec", password="pass")
        self.executive = user.profile
        self.executive.role = Profile.ROLE_EXECUTIVE
        self.executive.school = self.school
        self.executive.staff_id = "EXEC-COURSES"
        self.executive.save(update_fields=["role", "school", "staff_id", "updated_at"])
        self.client = APIClient()
        self.client.force_authenticate(user=user)
        self.prerequisite = Course.objects.create(
            code="CCS1001",
            title="Programming Fundamentals",
            credits=3,
            school=self.school,
        )

    def test_executive_can_add_and_later_edit_course_prerequisites(self):
        response = self.client.post(
            "/executive/courses/add",
            {
                "code": "CCS2001",
                "title": "Data Structures",
                "credits": 3,
                "prerequisites": [self.prerequisite.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        course = Course.objects.get(code="CCS2001")
        self.assertEqual(list(course.prerequisites.values_list("id", flat=True)), [self.prerequisite.id])

        response = self.client.patch(
            f"/executive/courses/all?course_id={course.id}",
            {"prerequisites": []},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(course.prerequisites.exists())


class ExecutiveNotificationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="NOTIFY", name="Notification School")
        self.semester = Semester.objects.create(
            name="Notification Semester",
            start_date="2026-10-01",
            end_date="2027-02-01",
        )
        self.course = Course.objects.create(
            code="NOT1001",
            title="Notification Workflows",
            credits=3,
            school=self.school,
        )
        self.executive = self.profile("notify_exec", Profile.ROLE_EXECUTIVE)
        self.teacher = self.profile("notify_teacher", Profile.ROLE_TEACHER)
        self.student = self.profile("notify_student", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A",
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            created_by=self.executive,
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

    def profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def test_course_assignment_and_schedule_changes_notify_affected_users(self):
        notify_offering_teachers(
            self.offering,
            self.executive,
            event_type="courses.assigned",
            verb="You were assigned to a course.",
        )
        notify_meeting_change(
            self.meeting,
            self.executive,
            event_type="schedule.changed",
            verb="A schedule changed.",
        )

        self.assertTrue(
            self.teacher.notifications.filter(data__event_type="courses.assigned").exists()
        )
        self.assertTrue(
            self.teacher.notifications.filter(data__event_type="schedule.changed").exists()
        )
        self.assertTrue(
            self.student.notifications.filter(data__event_type="schedule.changed").exists()
        )


class CourseEvaluationWorkflowTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SECSET", name="SEC-SET School")
        self.current_semester = Semester.objects.create(
            name="SEC-SET Current Semester",
            academic_session="2026/2027",
            start_date="2026-01-05",
            end_date="2026-06-30",
        )
        self.next_semester = Semester.objects.create(
            name="SEC-SET Next Semester",
            academic_session="2026/2027",
            start_date="2026-08-03",
            end_date="2026-12-18",
            max_credit_hours=21,
        )
        RegistrationPeriod.objects.create(
            semester=self.next_semester,
            title="Next Semester Registration",
            phase=RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            opens_at=timezone.now() - timezone.timedelta(days=1),
            closes_at=timezone.now() + timezone.timedelta(days=7),
        )
        current_course = Course.objects.create(
            code="SET1001",
            title="Evaluated Course",
            credits=3,
            school=self.school,
        )
        next_course = Course.objects.create(
            code="SET2001",
            title="Next Course",
            credits=3,
            school=self.school,
        )
        self.current_offering = CourseOffering.objects.create(
            course=current_course,
            semester=self.current_semester,
            section="A",
            capacity=40,
        )
        self.next_offering = CourseOffering.objects.create(
            course=next_course,
            semester=self.next_semester,
            section="A",
            capacity=40,
        )

        self.executive_user = User.objects.create_user(username="secset_exec", password="pass")
        self.executive = self.executive_user.profile
        self.executive.role = Profile.ROLE_EXECUTIVE
        self.executive.school = self.school
        self.executive.staff_id = "EXEC-SECSET"
        self.executive.save(update_fields=["role", "school", "staff_id", "updated_at"])

        self.student_user = User.objects.create_user(username="secset_student", password="pass")
        self.student = self.student_user.profile
        self.student.role = Profile.ROLE_STUDENT
        self.student.school = self.school
        self.student.student_id = "STU-SECSET"
        self.student.save(update_fields=["role", "school", "student_id", "updated_at"])
        Enrollment.objects.create(
            student=self.student,
            offering=self.current_offering,
            created_by=self.executive,
        )
        self.template = ensure_starter_template(self.executive)

    def complete_answers(self, questions):
        return {
            question["id"]: "agree" if question["type"] == "likert" else "Constructive feedback."
            for question in questions
        }

    def create_open_survey(self):
        return CourseEvaluationSurvey.objects.create(
            offering=self.current_offering,
            template=self.template,
            title="SEC-SET Evaluated Course",
            instructions="Complete all questions.",
            questions=default_questions(),
            opens_at=timezone.now() - timezone.timedelta(hours=1),
            closes_at=timezone.now() + timezone.timedelta(days=7),
            is_published=True,
            is_required=True,
            created_by=self.executive,
        )

    def test_required_evaluation_blocks_registration_until_submission(self):
        survey = self.create_open_survey()

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.next_offering,
            actor=self.student,
        )

        self.assertEqual(response_status, 403)
        self.assertIn("course evaluation", error.lower())
        self.assertIn(self.current_offering.course.code, error)

        client = APIClient()
        client.force_authenticate(user=self.student_user)
        response = client.post(
            f"/student/evaluations/{survey.id}",
            {"answers": self.complete_answers(survey.questions)},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        registration, error, response_status = register_student(
            student=self.student,
            offering=self.next_offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.offering, self.next_offering)

    def test_required_evaluation_still_blocks_registration_after_close(self):
        CourseEvaluationSurvey.objects.create(
            offering=self.current_offering,
            template=self.template,
            title="Closed SEC-SET Evaluated Course",
            instructions="Complete all questions.",
            questions=default_questions(),
            opens_at=timezone.now() - timezone.timedelta(days=7),
            closes_at=timezone.now() - timezone.timedelta(hours=1),
            is_published=True,
            is_required=True,
            created_by=self.executive,
        )

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.next_offering,
            actor=self.student,
        )

        self.assertEqual(response_status, 403)
        self.assertIn("course evaluation", error.lower())
        self.assertIn(self.current_offering.course.code, error)

    def test_executive_launch_and_analytics_track_completion(self):
        client = APIClient()
        client.force_authenticate(user=self.executive_user)
        response = client.post(
            "/executive/evaluations/surveys",
            {
                "offering_id": self.current_offering.id,
                "template_id": self.template.id,
                "title": "Course and Teaching Evaluation",
                "opens_at": (timezone.now() - timezone.timedelta(hours=1)).isoformat(),
                "closes_at": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
                "is_published": True,
                "is_required": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        survey = CourseEvaluationSurvey.objects.get(offering=self.current_offering)

        detail = client.get(f"/executive/evaluations/surveys/{survey.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["eligible_count"], 1)
        self.assertEqual(detail.data["pending_count"], 1)

        student_client = APIClient()
        student_client.force_authenticate(user=self.student_user)
        submitted = student_client.post(
            f"/student/evaluations/{survey.id}",
            {"answers": self.complete_answers(survey.questions)},
            format="json",
        )
        self.assertEqual(submitted.status_code, 201)

        detail = client.get(f"/executive/evaluations/surveys/{survey.id}")
        self.assertEqual(detail.data["response_count"], 1)
        self.assertEqual(detail.data["pending_count"], 0)
        first_likert = next(
            item for item in detail.data["analytics"] if item["type"] == "likert"
        )
        self.assertEqual(first_likert["answered"], 1)
        self.assertEqual(first_likert["average"], 3.0)

        workbook = build_xlsx(export_rows(survey), sheet_name="SEC-SET")
        self.assertTrue(workbook.startswith(b"PK"))

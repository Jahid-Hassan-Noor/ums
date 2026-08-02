from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Course, CourseOffering, Profile, School, Semester
from executive_app.models import ResultApproval, ResultBatch, ResultPublication, ResultReviewNote
from student_app.models import Enrollment, TranscriptRecord


User = get_user_model()


class ResultWorkflowTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.school = School.objects.create(code="SRE", name="School of Results")
        self.semester = Semester.objects.create(
            name="Semester 2 2025/2026",
            academic_session="2025/2026",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=60),
            is_active=True,
        )
        self.course = Course.objects.create(
            code="RES2103",
            title="Result Workflow Design",
            credits=3,
            school=self.school,
        )
        self.teacher = self._profile("results_teacher", Profile.ROLE_TEACHER)
        self.executive = self._profile("results_executive", Profile.ROLE_EXECUTIVE)
        self.student_one = self._profile(
            "results_student_one",
            Profile.ROLE_STUDENT,
            student_id="AIU250001",
        )
        self.student_two = self._profile(
            "results_student_two",
            Profile.ROLE_STUDENT,
            student_id="AIU250002",
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A",
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student_one,
            offering=self.offering,
            created_by=self.executive,
        )
        Enrollment.objects.create(
            student=self.student_two,
            offering=self.offering,
            created_by=self.executive,
        )
        self.teacher_client = APIClient()
        self.teacher_client.force_authenticate(self.teacher.user)
        self.executive_client = APIClient()
        self.executive_client.force_authenticate(self.executive.user)

    def _profile(self, username, role, student_id=""):
        user = User.objects.create_user(
            username=username,
            password="pass",
            first_name=username.replace("_", " ").title(),
        )
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.student_id = student_id
        profile.staff_id = "" if role == Profile.ROLE_STUDENT else username.upper()
        profile.save(
            update_fields=[
                "role",
                "school",
                "student_id",
                "staff_id",
                "updated_at",
            ]
        )
        return profile

    def _records(self):
        return [
            {
                "student_id": self.student_one.id,
                "score": "84",
                "remarks": "Strong performance",
            },
            {
                "student_id": self.student_two.id,
                "score": "68",
                "remarks": "",
            },
        ]

    def test_teacher_can_save_draft_and_submit_complete_roster(self):
        draft = self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "save",
                "records": [
                    {
                        "student_id": self.student_one.id,
                        "score": "84",
                        "remarks": "",
                    }
                ],
            },
            format="json",
        )
        incomplete_submit = self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "submit",
                "records": [
                    {
                        "student_id": self.student_one.id,
                        "score": "84",
                        "remarks": "",
                    }
                ],
            },
            format="json",
        )
        submitted = self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "submit",
                "records": self._records(),
            },
            format="json",
        )

        self.assertEqual(draft.status_code, 200, draft.json())
        self.assertEqual(draft.data["batch"]["status"], "draft")
        self.assertEqual(incomplete_submit.status_code, 400, incomplete_submit.json())
        self.assertEqual(submitted.status_code, 200, submitted.json())
        self.assertEqual(submitted.data["batch"]["status"], "review")
        self.assertEqual(submitted.data["batch"]["records"][0]["grade"], "A")

    def test_executive_can_return_results_with_a_note_and_teacher_can_resubmit(self):
        self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "submit",
                "records": self._records(),
            },
            format="json",
        )
        batch = ResultBatch.objects.get(offering=self.offering)
        returned = self.executive_client.post(
            "/executive/results/review",
            {
                "batch_id": batch.id,
                "action": "return",
                "note": "Please verify the second score.",
            },
            format="json",
        )
        resubmitted = self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "submit",
                "records": self._records(),
            },
            format="json",
        )

        self.assertEqual(returned.status_code, 200, returned.json())
        self.assertEqual(returned.data["batch"]["status"], "draft")
        self.assertTrue(
            ResultReviewNote.objects.filter(
                batch=batch,
                note="Please verify the second score.",
            ).exists()
        )
        self.assertEqual(resubmitted.status_code, 200, resubmitted.json())
        self.assertEqual(resubmitted.data["batch"]["status"], "review")

    def test_approval_and_publication_create_student_transcript_records(self):
        self.teacher_client.post(
            "/teacher/results/submit",
            {
                "offering_id": self.offering.id,
                "action": "submit",
                "records": self._records(),
            },
            format="json",
        )
        batch = ResultBatch.objects.get(offering=self.offering)
        review_list = self.executive_client.get("/executive/results/review")
        approved = self.executive_client.post(
            "/executive/results/review",
            {
                "batch_id": batch.id,
                "action": "approve",
                "note": "Verified against the mark sheet.",
            },
            format="json",
        )
        publication_list = self.executive_client.get(
            "/executive/results/publication"
        )
        published = self.executive_client.post(
            "/executive/results/publication",
            {
                "batch_id": batch.id,
                "note": "Semester board release.",
            },
            format="json",
        )

        self.assertEqual(review_list.status_code, 200, review_list.json())
        self.assertEqual(len(review_list.data["batches"]), 1)
        self.assertEqual(approved.status_code, 200, approved.json())
        self.assertTrue(ResultApproval.objects.filter(batch=batch).exists())
        self.assertEqual(publication_list.status_code, 200, publication_list.json())
        self.assertEqual(len(publication_list.data["batches"]), 1)
        self.assertEqual(published.status_code, 200, published.json())
        self.assertEqual(published.data["batch"]["status"], "published")
        self.assertTrue(ResultPublication.objects.filter(offering=self.offering).exists())

        transcript = TranscriptRecord.objects.get(
            student=self.student_one,
            offering=self.offering,
        )
        self.assertEqual(str(transcript.score), "84.00")
        self.assertEqual(transcript.grade, "A")
        self.assertEqual(str(transcript.gpa), "4.00")
        self.assertEqual(str(transcript.cgpa), "4.00")

        student_client = APIClient()
        student_client.force_authenticate(self.student_one.user)
        student_results = student_client.get("/student/results/semester")
        self.assertEqual(student_results.status_code, 200, student_results.json())
        self.assertEqual(student_results.data["records"][0]["course_code"], "RES2103")

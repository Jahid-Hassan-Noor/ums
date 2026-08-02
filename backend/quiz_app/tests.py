from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Course, CourseOffering, Profile, School, Semester
from quiz_app.models import QuizAttempt, QuizGrade
from quiz_app.services import create_or_update_question, default_bank_for_offering
from student_app.models import Enrollment


User = get_user_model()


class QuizEngineApiTests(TestCase):
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
            code="CCS4413",
            title="Secure Learning Systems",
            credits=3,
            school=self.school,
        )
        self.teacher = self._profile("quiz_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("quiz_student", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="Q1",
            capacity=30,
        )
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.teacher)

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def _create_quiz(self, **overrides):
        self.client.force_authenticate(self.teacher.user)
        payload = {
            "offering_id": self.offering.id,
            "title": "Quiz 1",
            "description": "Foundations quiz",
            "instructions": "Answer all questions.",
            "status": "published",
            "opens_at": (timezone.now() - timezone.timedelta(minutes=5)).isoformat(),
            "closes_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "time_limit_minutes": 30,
            "max_attempts": 1,
            "grade_method": "highest",
            "pass_mark": "5",
            "review_show_marks": True,
            "review_show_feedback": True,
            "questions": [
                {
                    "title": "HTTP method",
                    "question_type": "multiple_choice",
                    "question_text": "Which HTTP method usually creates a resource?",
                    "default_mark": "2",
                    "max_mark": "2",
                    "choices": [
                        {"label": "A", "text": "GET", "is_correct": False},
                        {"label": "B", "text": "POST", "is_correct": True},
                    ],
                },
                {
                    "title": "Explain autosave",
                    "question_type": "essay",
                    "question_text": "Explain why autosave matters in online quizzes.",
                    "default_mark": "5",
                    "max_mark": "5",
                },
            ],
        }
        payload.update(overrides)
        response = self.client.post("/quiz/teacher/quizzes", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()["quiz"]

    def test_quiz_attempt_auto_and_manual_grading_flow(self):
        quiz = self._create_quiz()

        self.client.force_authenticate(self.student.user)
        list_response = self.client.get("/quiz/student/quizzes")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["quizzes"]), 1)

        start_response = self.client.post(f"/quiz/student/quizzes/{quiz['id']}/start", {}, format="json")
        self.assertEqual(start_response.status_code, 201, start_response.content)
        attempt = start_response.json()["attempt"]
        questions = attempt["questions"]
        self.assertEqual(len(questions), 2)

        mcq = next(question for question in questions if question["question"]["question_type"] == "multiple_choice")
        essay = next(question for question in questions if question["question"]["question_type"] == "essay")
        correct_choice = next(choice for choice in mcq["question"]["choices"] if choice["label"] == "B")

        answer_response = self.client.post(
            f"/quiz/student/attempts/{attempt['id']}/answer",
            {
                "question_attempt_id": mcq["id"],
                "response": {"choice_ids": [correct_choice["id"]]},
            },
            format="json",
        )
        self.assertEqual(answer_response.status_code, 200, answer_response.content)
        answer_response = self.client.post(
            f"/quiz/student/attempts/{attempt['id']}/answer",
            {
                "question_attempt_id": essay["id"],
                "response": {"answer": "Autosave protects work if the browser closes."},
            },
            format="json",
        )
        self.assertEqual(answer_response.status_code, 200, answer_response.content)

        submit_response = self.client.post(f"/quiz/student/attempts/{attempt['id']}/submit", {}, format="json")
        self.assertEqual(submit_response.status_code, 200, submit_response.content)
        submitted = submit_response.json()["attempt"]
        self.assertEqual(submitted["score"], "2.00")
        self.assertTrue(submitted["needs_manual_grading"])

        grade = QuizGrade.objects.get(quiz_id=quiz["id"], student=self.student)
        self.assertEqual(str(grade.grade), "2.00")
        self.assertTrue(grade.needs_manual_grading)

        self.client.force_authenticate(self.teacher.user)
        grade_response = self.client.post(
            f"/quiz/teacher/quizzes/{quiz['id']}/attempts/{attempt['id']}/grade",
            {
                "question_attempt_id": essay["id"],
                "awarded_mark": "4",
                "feedback": "Good explanation.",
            },
            format="json",
        )
        self.assertEqual(grade_response.status_code, 200, grade_response.content)
        graded_attempt = grade_response.json()["attempt"]
        self.assertEqual(graded_attempt["score"], "6.00")
        self.assertFalse(graded_attempt["needs_manual_grading"])

        grade.refresh_from_db()
        self.assertEqual(str(grade.grade), "6.00")
        self.assertFalse(grade.needs_manual_grading)

        detail_response = self.client.get(f"/quiz/teacher/quizzes/{quiz['id']}")
        self.assertEqual(detail_response.status_code, 200)
        statistics = detail_response.json()["quiz"]["statistics"]
        self.assertEqual(statistics["attempts_submitted"], 1)
        self.assertEqual(statistics["average_score"], "6.00")
        self.assertEqual(statistics["manual_pending"], 0)

    def test_random_question_rule_adds_questions_to_attempts(self):
        quiz = self._create_quiz()
        bank = default_bank_for_offering(self.offering, self.teacher)
        create_or_update_question(
            bank,
            self.teacher,
            {
                "title": "Safe browser",
                "question_type": "true_false",
                "question_text": "Safe Exam Browser can be required for a quiz.",
                "correct_answer": "true",
                "default_mark": "1",
            },
        )

        self.client.force_authenticate(self.teacher.user)
        rule_response = self.client.post(
            f"/quiz/teacher/quizzes/{quiz['id']}/random-rules",
            {"question_type": "true_false", "count": 1, "max_mark": "1"},
            format="json",
        )
        self.assertEqual(rule_response.status_code, 201, rule_response.content)
        updated_quiz = rule_response.json()["quiz"]
        self.assertEqual(len(updated_quiz["random_rules"]), 1)
        self.assertEqual(updated_quiz["total_marks"], "8.00")

        self.client.force_authenticate(self.student.user)
        start_response = self.client.post(f"/quiz/student/quizzes/{quiz['id']}/start", {}, format="json")
        self.assertEqual(start_response.status_code, 201, start_response.content)
        question_types = [question["question"]["question_type"] for question in start_response.json()["attempt"]["questions"]]
        self.assertIn("true_false", question_types)
        self.assertEqual(len(question_types), 3)

    def test_question_bank_category_version_and_existing_question_reuse(self):
        self.client.force_authenticate(self.teacher.user)
        bank_response = self.client.get("/quiz/teacher/question-bank")
        self.assertEqual(bank_response.status_code, 200)
        bank = bank_response.json()["banks"][0]

        category_response = self.client.post(
            "/quiz/teacher/question-bank/categories",
            {"bank_id": bank["id"], "title": "Security"},
            format="json",
        )
        self.assertEqual(category_response.status_code, 201, category_response.content)
        category_id = category_response.json()["category"]["id"]

        question_response = self.client.post(
            "/quiz/teacher/question-bank/questions",
            {
                "bank_id": bank["id"],
                "category_id": category_id,
                "title": "Risk score",
                "question_type": "numerical",
                "question_text": "What is the risk score?",
                "correct_answer": "42",
                "default_mark": "3",
                "tolerance": "0.50",
            },
            format="json",
        )
        self.assertEqual(question_response.status_code, 201, question_response.content)
        question = question_response.json()["question"]
        self.assertEqual(question["version_count"], 1)

        version_response = self.client.post(
            f"/quiz/teacher/question-bank/questions/{question['id']}/versions",
            {
                "title": "Risk score updated",
                "question_text": "What is the updated risk score?",
                "correct_answer": "43",
                "default_mark": "3",
                "tolerance": "0.50",
            },
            format="json",
        )
        self.assertEqual(version_response.status_code, 201, version_response.content)

        quiz = self._create_quiz(questions=[], pass_mark="0")
        add_response = self.client.post(
            f"/quiz/teacher/quizzes/{quiz['id']}/questions",
            {"question_id": question["id"], "max_mark": "3"},
            format="json",
        )
        self.assertEqual(add_response.status_code, 201, add_response.content)
        self.assertEqual(add_response.json()["quiz"]["total_marks"], "3.00")

        self.client.force_authenticate(self.student.user)
        start_response = self.client.post(f"/quiz/student/quizzes/{quiz['id']}/start", {}, format="json")
        self.assertEqual(start_response.status_code, 201, start_response.content)
        attempt = start_response.json()["attempt"]
        numerical = attempt["questions"][0]
        self.assertEqual(numerical["question"]["question_type"], "numerical")

        submit_response = self.client.post(
            f"/quiz/student/attempts/{attempt['id']}/submit",
            {"responses": {str(numerical["id"]): {"answer": "43.25"}}},
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200, submit_response.content)
        self.assertEqual(submit_response.json()["attempt"]["score"], "3.00")
        self.assertFalse(submit_response.json()["attempt"]["needs_manual_grading"])

    def test_matching_and_ordering_questions_auto_grade(self):
        self.client.force_authenticate(self.teacher.user)
        quiz = self._create_quiz(
            pass_mark="0",
            questions=[
                {
                    "title": "Match controls",
                    "question_type": "matching",
                    "question_text": "Match each control to the outcome.",
                    "default_mark": "2",
                    "max_mark": "2",
                    "matching_pairs": [
                        {"prompt": "MFA", "answer": "Identity"},
                        {"prompt": "Backup", "answer": "Recovery"},
                    ],
                },
                {
                    "title": "Order response",
                    "question_type": "ordering",
                    "question_text": "Order the incident response stages.",
                    "default_mark": "2",
                    "max_mark": "2",
                    "ordering_items": ["Identify", "Contain", "Recover"],
                },
            ],
        )

        self.client.force_authenticate(self.student.user)
        start_response = self.client.post(f"/quiz/student/quizzes/{quiz['id']}/start", {}, format="json")
        self.assertEqual(start_response.status_code, 201, start_response.content)
        attempt = start_response.json()["attempt"]
        matching = next(question for question in attempt["questions"] if question["question"]["question_type"] == "matching")
        ordering = next(question for question in attempt["questions"] if question["question"]["question_type"] == "ordering")

        submit_response = self.client.post(
            f"/quiz/student/attempts/{attempt['id']}/submit",
            {
                "responses": {
                    str(matching["id"]): {"matching": {"MFA": "Identity", "Backup": "Recovery"}},
                    str(ordering["id"]): {"order": ["Identify", "Contain", "Recover"]},
                }
            },
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200, submit_response.content)
        self.assertEqual(submit_response.json()["attempt"]["score"], "4.00")
        self.assertFalse(submit_response.json()["attempt"]["needs_manual_grading"])

    def test_quiz_access_rules_enforce_password_ip_and_max_attempts(self):
        quiz = self._create_quiz(
            password="secret",
            ip_allowlist="10.0.0.0/24",
            require_safe_exam_browser=True,
            safe_exam_browser_config_key="seb-key",
        )

        self.client.force_authenticate(self.student.user)
        bad_password = self.client.post(
            f"/quiz/student/quizzes/{quiz['id']}/start",
            {"password": "wrong"},
            REMOTE_ADDR="10.0.0.5",
            format="json",
        )
        self.assertEqual(bad_password.status_code, 403)

        bad_ip = self.client.post(
            f"/quiz/student/quizzes/{quiz['id']}/start",
            {"password": "secret"},
            REMOTE_ADDR="192.168.1.10",
            format="json",
        )
        self.assertEqual(bad_ip.status_code, 403)

        missing_seb = self.client.post(
            f"/quiz/student/quizzes/{quiz['id']}/start",
            {"password": "secret"},
            REMOTE_ADDR="10.0.0.5",
            format="json",
        )
        self.assertEqual(missing_seb.status_code, 403)

        started = self.client.post(
            f"/quiz/student/quizzes/{quiz['id']}/start",
            {"password": "secret"},
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_SAFE_EXAM_BROWSER_CONFIG_KEY_HASH="seb-key",
            format="json",
        )
        self.assertEqual(started.status_code, 201, started.content)
        attempt_id = started.json()["attempt"]["id"]
        QuizAttempt.objects.filter(pk=attempt_id).update(state=QuizAttempt.STATE_SUBMITTED, score=0)

        blocked = self.client.post(
            f"/quiz/student/quizzes/{quiz['id']}/start",
            {"password": "secret"},
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_SAFE_EXAM_BROWSER_CONFIG_KEY_HASH="seb-key",
            format="json",
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Maximum attempts", blocked.json()["detail"])

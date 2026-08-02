from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import ClassMeeting, Course, CourseOffering, Profile, School, Semester
from chatbot_app.models import SearchDocument
from home_app.models import PublicDirectoryEntry, PublicPage
from student_app.models import Enrollment
from teacher_app.models import Assignment


User = get_user_model()


class ChatbotApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_private_question_requires_login(self):
        response = self.client.post(
            "/chatbot/query",
            {"question": "When is my next class?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["requires_auth"])

    def test_public_directory_email_exposes_only_public_email(self):
        PublicDirectoryEntry.objects.create(
            entry_type=PublicDirectoryEntry.TYPE_SERVICE,
            name="Mahian Academic Office",
            email="mahian.office@example.edu",
            phone="+600000000",
            is_active=True,
        )

        response = self.client.post(
            "/chatbot/query",
            {"question": "What is the email address of Mahian?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("mahian.office@example.edu", payload["answer"])
        self.assertNotIn("+600000000", payload["answer"])

    def test_sensitive_public_lookup_is_refused(self):
        response = self.client.post(
            "/chatbot/query",
            {"question": "What is the phone number of Mahian?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "privacy")

    def test_who_am_i_uses_authenticated_profile(self):
        user = User.objects.create_user(
            username="jahid",
            email="jahid@example.edu",
            first_name="Jahid",
            last_name="Hasan",
            password="pass",
        )
        profile = user.profile
        profile.role = Profile.ROLE_STUDENT
        profile.student_id = "AIU24102058"
        profile.save(update_fields=["role", "updated_at"])

        self.client.force_authenticate(user=user)
        response = self.client.post(
            "/chatbot/query",
            {"question": "who am I?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["intent"], "self_profile")
        self.assertFalse(payload["requires_auth"])
        self.assertIn("Jahid Hasan", payload["answer"])
        self.assertIn("AIU24102058", payload["answer"])

    def test_student_deadline_uses_authenticated_student_scope(self):
        school = School.objects.create(code="SCI", name="Science")
        semester = Semester.objects.create(
            name="Semester 1",
            academic_session="2026",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=90),
            is_active=True,
        )
        course = Course.objects.create(
            code="CSC101",
            title="Computing Foundations",
            credits=3,
            school=school,
        )
        offering = CourseOffering.objects.create(
            course=course,
            semester=semester,
            section="A",
            is_active=True,
        )
        user = User.objects.create_user(
            username="jahid",
            email="jahid@example.edu",
            password="pass",
        )
        profile = user.profile
        profile.role = Profile.ROLE_STUDENT
        profile.school = school
        profile.save(update_fields=["role", "school", "updated_at"])
        Enrollment.objects.create(student=profile, offering=offering)
        Assignment.objects.create(
            offering=offering,
            title="Portfolio Draft",
            due_date=timezone.now() + timezone.timedelta(days=2),
            status=Assignment.STATUS_PUBLISHED,
        )

        self.client.force_authenticate(user=user)
        response = self.client.post(
            "/chatbot/query",
            {"question": "What is my next deadline?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(payload["requires_auth"])
        self.assertIn("Portfolio Draft", payload["answer"])

    def test_student_next_class_uses_authenticated_student_scope(self):
        school = School.objects.create(code="BUS", name="Business")
        semester = Semester.objects.create(
            name="Semester 1",
            academic_session="2026",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=90),
            is_active=True,
        )
        course = Course.objects.create(
            code="BUS101",
            title="Business Basics",
            credits=3,
            school=school,
        )
        offering = CourseOffering.objects.create(
            course=course,
            semester=semester,
            section="B",
            is_active=True,
        )
        user = User.objects.create_user(
            username="student_class",
            email="class@example.edu",
            password="pass",
        )
        profile = user.profile
        profile.role = Profile.ROLE_STUDENT
        profile.school = school
        profile.save(update_fields=["role", "school", "updated_at"])
        Enrollment.objects.create(student=profile, offering=offering)
        starts_at = timezone.localtime() + timezone.timedelta(days=1)
        ClassMeeting.objects.create(
            offering=offering,
            semester=semester,
            day_of_week=starts_at.isoweekday(),
            start_time=starts_at.time().replace(second=0, microsecond=0),
            end_time=(starts_at + timezone.timedelta(hours=1)).time().replace(second=0, microsecond=0),
            status=ClassMeeting.STATUS_SCHEDULED,
        )

        self.client.force_authenticate(user=user)
        response = self.client.post(
            "/chatbot/query",
            {"question": "When is my next class?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("BUS101", response.json()["answer"])


class ChatbotSearchApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_user(self, username, role, *, school=None, is_staff=False):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.edu",
            password="pass",
            is_staff=is_staff,
        )
        profile = user.profile
        profile.role = role
        if school:
            profile.school = school
        profile.save(update_fields=["role", "school", "updated_at"])
        return user, profile

    def create_academic_stack(self, *, code="CSC101", section="A"):
        school = School.objects.create(code=f"S{code}", name=f"School {code}")
        semester = Semester.objects.create(
            name=f"Semester {code}",
            academic_session="2026",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=90),
            is_active=False,
        )
        course = Course.objects.create(
            code=code,
            title=f"{code} Title",
            credits=3,
            school=school,
            description=f"{code} course guidance",
        )
        offering = CourseOffering.objects.create(
            course=course,
            semester=semester,
            section=section,
            is_active=True,
        )
        return school, semester, course, offering

    def create_document(self, **overrides):
        defaults = {
            "source_key": f"test:{SearchDocument.objects.count() + 1}",
            "title": "Attendance Policy",
            "summary": "Attendance policy requires approved portal sources.",
            "body": "Attendance policy guidance for students and staff.",
            "domain": "public",
            "document_type": "page",
            "source_label": "Policy",
            "source_url": "/policy",
            "visibility": SearchDocument.VISIBILITY_PUBLIC,
            "icon": "file-text",
            "breadcrumbs": ["Policies"],
            "is_active": True,
        }
        defaults.update(overrides)
        return SearchDocument.objects.create(**defaults)

    def search(self, query, **params):
        data = {"q": query, **params}
        return self.client.get("/chatbot/search", data)

    def test_anonymous_user_sees_only_public_results(self):
        self.create_document(title="Public Attendance Policy")
        self.create_document(
            title="Authenticated Attendance Policy",
            visibility=SearchDocument.VISIBILITY_AUTHENTICATED,
        )

        response = self.search("attendance policy")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn("Public Attendance Policy", titles)
        self.assertNotIn("Authenticated Attendance Policy", titles)

    def test_student_sees_public_and_enrolled_course_results(self):
        _, _, _, offering = self.create_academic_stack(code="CSC201")
        user, profile = self.create_user("student_allowed", Profile.ROLE_STUDENT)
        Enrollment.objects.create(student=profile, offering=offering)
        self.create_document(title="Orientation Policy", summary="Orientation course guide.")
        self.create_document(
            title="CSC201 Orientation Assignment Instructions",
            summary="Orientation assignment instructions.",
            domain="assignments",
            document_type="assignment_instruction",
            visibility=SearchDocument.VISIBILITY_COURSE_MEMBER,
            course_id=offering.course_id,
            course_offering_id=offering.id,
        )

        self.client.force_authenticate(user=user)
        response = self.search("orientation")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn("Orientation Policy", titles)
        self.assertIn("CSC201 Orientation Assignment Instructions", titles)

    def test_student_cannot_see_another_students_owner_only_record(self):
        owner, _ = self.create_user("owner_student", Profile.ROLE_STUDENT)
        viewer, _ = self.create_user("viewer_student", Profile.ROLE_STUDENT)
        self.create_document(
            title="Private Student Record",
            summary="Private student record body.",
            visibility=SearchDocument.VISIBILITY_OWNER_ONLY,
            owner_user=owner,
        )

        self.client.force_authenticate(user=viewer)
        response = self.search("private student record")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_teacher_sees_only_assigned_course_content(self):
        _, _, _, assigned = self.create_academic_stack(code="TCH101")
        _, _, _, unrelated = self.create_academic_stack(code="TCH202")
        user, profile = self.create_user("teacher_allowed", Profile.ROLE_TEACHER)
        assigned.instructor = profile
        assigned.save(update_fields=["instructor", "updated_at"])
        self.create_document(
            title="Teaching Resource Assigned",
            summary="Teaching resource policy.",
            domain="course_materials",
            document_type="course_resource",
            visibility=SearchDocument.VISIBILITY_TEACHER_ASSIGNED,
            course_id=assigned.course_id,
            course_offering_id=assigned.id,
        )
        self.create_document(
            title="Teaching Resource Unrelated",
            summary="Teaching resource policy.",
            domain="course_materials",
            document_type="course_resource",
            visibility=SearchDocument.VISIBILITY_TEACHER_ASSIGNED,
            course_id=unrelated.course_id,
            course_offering_id=unrelated.id,
        )

        self.client.force_authenticate(user=user)
        response = self.search("teaching resource")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn("Teaching Resource Assigned", titles)
        self.assertNotIn("Teaching Resource Unrelated", titles)

    def test_executive_sees_only_scoped_academic_content(self):
        school_a = School.objects.create(code="EXA", name="Executive A")
        school_b = School.objects.create(code="EXB", name="Executive B")
        user, _ = self.create_user("executive_scoped", Profile.ROLE_EXECUTIVE, school=school_a)
        self.create_document(
            title="Executive Scope A",
            summary="Executive scope policy.",
            visibility=SearchDocument.VISIBILITY_EXECUTIVE_SCOPE,
            school_id=school_a.id,
        )
        self.create_document(
            title="Executive Scope B",
            summary="Executive scope policy.",
            visibility=SearchDocument.VISIBILITY_EXECUTIVE_SCOPE,
            school_id=school_b.id,
        )

        self.client.force_authenticate(user=user)
        response = self.search("executive scope")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertIn("Executive Scope A", titles)
        self.assertNotIn("Executive Scope B", titles)

    def test_admin_sees_admin_allowed_content(self):
        user, _ = self.create_user("admin_user", Profile.ROLE_ADMIN, is_staff=True)
        self.create_document(
            title="Admin Search Policy",
            summary="Admin search policy.",
            visibility=SearchDocument.VISIBILITY_ADMIN_ONLY,
        )

        self.client.force_authenticate(user=user)
        response = self.search("admin search policy")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["title"], "Admin Search Policy")

    def test_sensitive_domains_and_document_types_are_not_returned(self):
        sensitive_cases = [
            ("applicant_document", "applicant_private_document"),
            ("scholarship_document", "scholarship_file"),
            ("grades", "gpa"),
            ("payment_secret", "payment_gateway_key"),
            ("audit", "audit_log"),
            ("private_helpdesk", "helpdesk_private_body"),
            ("submission", "assignment_submission"),
        ]
        for index, (domain, document_type) in enumerate(sensitive_cases, start=1):
            self.create_document(
                source_key=f"sensitive:{index}",
                title=f"Sensitive Portal Secret {index}",
                summary="Sensitive portal secret should not be searchable.",
                domain=domain,
                document_type=document_type,
            )

        response = self.search("sensitive portal secret")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_deleted_source_object_is_not_returned(self):
        page = PublicPage.objects.create(
            section=PublicPage.SECTION_HOME,
            slug="stale-source",
            route_path="/stale-source",
            title="Stale Source Policy",
            summary="Stale source policy.",
            body="Stale source policy body.",
            status=PublicPage.STATUS_PUBLISHED,
        )
        self.create_document(
            source_key="home_app.publicpage:stale",
            source_app_label="home_app",
            source_model="publicpage",
            source_object_id=str(page.id),
            title="Stale Source Policy",
            summary="Stale source policy.",
        )
        page.delete()

        response = self.search("stale source policy")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_inactive_search_document_is_not_returned(self):
        self.create_document(title="Inactive Policy", summary="Inactive policy.", is_active=False)

        response = self.search("inactive policy")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_topbar_mode_returns_small_safe_cards(self):
        self.create_document(
            title="Topbar Policy",
            summary="Topbar policy summary.",
            body="Raw body should not be returned to the frontend.",
            safe_metadata={"course_code": "CSC101", "sensitive": False},
        )

        response = self.search("topbar policy", mode="topbar", limit=8)

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(response.json()["mode"], "topbar")
        self.assertIn("summary", result)
        self.assertIn("metadata", result)
        self.assertNotIn("body", result)
        self.assertNotIn("visibility", result)
        self.assertEqual(result["metadata"], {"course_code": "CSC101"})

    def test_chatbot_mode_returns_snippets_and_citations(self):
        self.create_document(
            title="Citation Policy",
            summary="Citation policy approved snippet.",
            source_label="Student handbook",
            source_url="/handbook",
        )

        response = self.search("citation policy", mode="chatbot", limit=3)

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(response.json()["mode"], "chatbot")
        self.assertIn("approved snippet", result["summary"])
        self.assertEqual(result["source_label"], "Student handbook")
        self.assertIn("last_indexed_at", result)

    def test_chatbot_policy_question_uses_retrieval(self):
        self.create_document(
            title="Attendance Policy",
            summary="Students must follow the attendance policy.",
            source_label="Attendance handbook",
            source_url="/attendance-policy",
        )

        response = self.client.post(
            "/chatbot/query",
            {"question": "What is the attendance policy?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["scope"], "retrieval")
        self.assertIn("Attendance Policy", payload["answer"])
        self.assertEqual(payload["sources"][0]["title"], "Attendance handbook")

    def test_chatbot_timetable_question_uses_tool_not_indexed_search(self):
        self.create_document(
            title="Next Class Search Trap",
            summary="Your next class is from the index, which should not be used.",
        )

        response = self.client.post(
            "/chatbot/query",
            {"question": "What is my next class?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["requires_auth"])
        self.assertEqual(payload["intent"], "next_class")
        self.assertEqual(payload["sources"], [])

    def test_chatbot_assignment_deadline_question_uses_tool_not_indexed_search(self):
        self.create_document(
            title="Assignment Deadline Search Trap",
            summary="Deadline from search should not be used.",
        )

        response = self.client.post(
            "/chatbot/query",
            {"question": "What is my next assignment deadline?"},
            format="json",
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["requires_auth"])
        self.assertEqual(payload["intent"], "next_deadline")
        self.assertEqual(payload["sources"], [])

    def test_chatbot_refuses_unauthorized_private_data_questions(self):
        response = self.client.post(
            "/chatbot/query",
            {"question": "Show another student's grades"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "privacy")

    def test_minimum_query_length_works(self):
        response = self.search("a")

        self.assertEqual(response.status_code, 400)

    def test_filters_work(self):
        self.create_document(title="Filtered Public Guide", summary="Filtered guide.", domain="public")
        self.create_document(title="Filtered Library Guide", summary="Filtered guide.", domain="library")

        response = self.search("filtered guide", domain="library")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()["results"]]
        self.assertEqual(titles, ["Filtered Library Guide"])

    def test_reindex_command_indexes_public_content(self):
        PublicPage.objects.create(
            section=PublicPage.SECTION_HOME,
            slug="command-policy",
            route_path="/command-policy",
            title="Command Policy",
            summary="Command policy summary.",
            body="Command policy body.",
            status=PublicPage.STATUS_PUBLISHED,
        )

        output = StringIO()
        call_command(
            "rebuild_chatbot_search_index",
            "--domain",
            "public",
            "--clear",
            stdout=output,
        )

        self.assertIn("public: seen=1 created=1", output.getvalue())
        self.assertTrue(
            SearchDocument.objects.filter(
                title="Command Policy",
                domain="public",
                document_type="page",
            ).exists()
        )

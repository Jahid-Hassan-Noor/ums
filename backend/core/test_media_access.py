import tempfile
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from admin_app.models import Course, CourseOffering, School, Semester
from applicant_app.models import Applicant, AdmissionApplication, ApplicationDocument
from applicant_app.serializers import ApplicationDocumentSerializer
from auth_app.models import Profile
from core.media_access import public_profile_picture_url
from home_app.models import PublicNews
from student_app.models import Enrollment
from teacher_app.models import CourseResource


User = get_user_model()


class ProtectedMediaAccessTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.client = APIClient()

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    def profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.save(update_fields=["role", "updated_at"])
        return profile

    def assert_accel_response(self, response, media_path):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Accel-Redirect"], f"/_protected_media/{quote(media_path, safe='/')}")

    def test_applicant_document_requires_owner_or_staff_role(self):
        owner = self.profile("applicant_owner", Profile.ROLE_APPLICANT)
        other = self.profile("applicant_other", Profile.ROLE_APPLICANT)
        executive = self.profile("applicant_exec", Profile.ROLE_EXECUTIVE)
        applicant, _created = Applicant.objects.get_or_create(profile=owner)
        application = AdmissionApplication.objects.create(applicant=applicant)
        document = ApplicationDocument.objects.create(
            application=application,
            document_type=ApplicationDocument.TYPE_PASSPORT,
            file=SimpleUploadedFile("passport.pdf", b"%PDF-1.4 applicant passport", content_type="application/pdf"),
        )
        payload = ApplicationDocumentSerializer(document).data
        self.assertNotIn("file", payload)
        self.assertTrue(payload["file_url"].startswith("/ums-auth/backend/media/applications/"))

        response = self.client.get(f"/media/{document.file.name}")
        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(user=other.user)
        response = self.client.get(f"/media/{document.file.name}")
        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(user=owner.user)
        response = self.client.get(f"/media/{document.file.name}")
        self.assert_accel_response(response, document.file.name)

        self.client.force_authenticate(user=executive.user)
        response = self.client.get(f"/media/{document.file.name}")
        self.assert_accel_response(response, document.file.name)

    def test_course_resource_requires_enrollment_or_instructor(self):
        school = School.objects.create(code="SCS", name="School of Computer Science")
        semester = Semester.objects.create(
            name="Semester 1",
            academic_session="2026/2027",
            start_date="2026-10-01",
            end_date="2027-02-01",
            is_active=True,
        )
        course = Course.objects.create(code="SEC101", title="Security", credits=3, school=school)
        teacher = self.profile("resource_teacher", Profile.ROLE_TEACHER)
        student = self.profile("resource_student", Profile.ROLE_STUDENT)
        stranger = self.profile("resource_stranger", Profile.ROLE_STUDENT)
        offering = CourseOffering.objects.create(
            course=course,
            semester=semester,
            instructor=teacher,
            section="A",
            capacity=30,
        )
        Enrollment.objects.create(student=student, offering=offering, created_by=teacher)
        resource = CourseResource.objects.create(
            offering=offering,
            title="Week 1 notes",
            file=SimpleUploadedFile("week-1.pdf", b"%PDF-1.4 notes", content_type="application/pdf"),
            is_published=True,
        )

        response = self.client.get(f"/media/{resource.file.name}")
        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(user=stranger.user)
        response = self.client.get(f"/media/{resource.file.name}")
        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(user=student.user)
        response = self.client.get(f"/media/{resource.file.name}")
        self.assert_accel_response(response, resource.file.name)

        self.client.force_authenticate(user=teacher.user)
        response = self.client.get(f"/media/{resource.file.name}")
        self.assert_accel_response(response, resource.file.name)

    def test_public_news_media_requires_published_content_for_anonymous_users(self):
        published = PublicNews.objects.create(
            title="Published",
            slug="published",
            status=PublicNews.STATUS_PUBLISHED,
            image=SimpleUploadedFile("published.jpg", b"published image", content_type="image/jpeg"),
        )
        draft = PublicNews.objects.create(
            title="Draft",
            slug="draft",
            status=PublicNews.STATUS_DRAFT,
            image=SimpleUploadedFile("draft.jpg", b"draft image", content_type="image/jpeg"),
        )

        response = self.client.get(f"/media/{published.image.name}")
        self.assert_accel_response(response, published.image.name)

        response = self.client.get(f"/media/{draft.image.name}")
        self.assertEqual(response.status_code, 404)

    def test_profile_picture_uses_public_opaque_url_only(self):
        profile = self.profile("picture_owner", Profile.ROLE_TEACHER)
        profile.profile_picture.save(
            "avatar.png",
            SimpleUploadedFile("avatar.png", b"fake profile image", content_type="image/png"),
            save=True,
        )

        public_url = public_profile_picture_url(profile)
        self.assertTrue(public_url.startswith("/media/profile-pictures/"))
        self.assertNotIn("profiles/pictures", public_url)

        response = self.client.get(f"/media/{profile.profile_picture.name}")
        self.assertEqual(response.status_code, 404)

        response = self.client.get(public_url)
        self.assert_accel_response(response, profile.profile_picture.name)

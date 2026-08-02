import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from admin_app.models import Profile, ensure_role_detail, prune_role_details
from applicant_app import models
from applicant_app.serializers import ApplicationDocumentSerializer
from notifications_package.models import Notification


User = get_user_model()
NO_THROTTLE_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


def remote_addr_for_test(name):
    last_octet = (sum(ord(char) for char in name) % 200) + 10
    return f"10.241.0.{last_octet}"


@override_settings(REST_FRAMEWORK=NO_THROTTLE_REST_FRAMEWORK)
class ApplicantAppApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.defaults["REMOTE_ADDR"] = remote_addr_for_test(
            self._testMethodName
        )

    def applicant_payload(self, **overrides):
        payload = {
            "username": "applytest",
            "first_name": "Test",
            "last_name": "Applicant",
            "email": "apply-test@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "phone": "+60123456789",
            "nationality": "Malaysia",
            "country_of_residence": "Malaysia",
            "passport_or_identity_no": "990101011234",
        }
        payload.update(overrides)
        return payload

    def image_upload(self, *, image_format="PNG"):
        image = Image.new("RGB", (20, 20), color="teal")
        content = io.BytesIO()
        image.save(content, format=image_format)
        content.seek(0)
        return SimpleUploadedFile(
            f"identity.{image_format.lower()}",
            content.read(),
            content_type=f"image/{image_format.lower()}",
        )

    def register(self):
        response = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
        return response.json()

    def test_options_are_seeded(self):
        response = self.client.get("/applicant/options")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()["programmes"]), 4)
        country_values = {country["value"] for country in response.json()["countries"]}
        self.assertIn("Malaysia", country_values)

    def test_register_requires_username_and_identity_details(self):
        response = self.client.post(
            "/applicant/auth/register",
            {
                "first_name": "Test",
                "last_name": "Applicant",
                "email": "missing-fields@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())
        self.assertIn("confirm_password", response.json())
        self.assertIn("phone", response.json())
        self.assertIn("nationality", response.json())
        self.assertIn("country_of_residence", response.json())
        self.assertIn("passport_or_identity_no", response.json())

    def test_register_requires_matching_password_confirmation(self):
        response = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(confirm_password="DifferentPass123!"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json())

    def test_register_rejects_passwords_longer_than_twenty_characters(self):
        response = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(
                password="ApplicantStrongPass123!",
                confirm_password="ApplicantStrongPass123!",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("20 characters or fewer", str(response.json()))

    def test_identity_document_upload_requires_valid_image_file(self):
        pdf_serializer = ApplicationDocumentSerializer(
            data={
                "document_type": models.ApplicationDocument.TYPE_PASSPORT,
                "file": SimpleUploadedFile(
                    "identity.pdf",
                    b"%PDF-1.4",
                    content_type="application/pdf",
                ),
            }
        )
        self.assertFalse(pdf_serializer.is_valid())
        self.assertIn("image", str(pdf_serializer.errors["file"]).lower())

        invalid_image_serializer = ApplicationDocumentSerializer(
            data={
                "document_type": models.ApplicationDocument.TYPE_PHOTO,
                "file": SimpleUploadedFile(
                    "photo.jpg",
                    b"not really an image",
                    content_type="image/jpeg",
                ),
            }
        )
        self.assertFalse(invalid_image_serializer.is_valid())
        self.assertIn("valid image", str(invalid_image_serializer.errors["file"]).lower())

        valid_serializer = ApplicationDocumentSerializer(
            data={
                "document_type": models.ApplicationDocument.TYPE_PASSPORT,
                "file": self.image_upload(),
            }
        )
        self.assertTrue(valid_serializer.is_valid(), valid_serializer.errors)

    def test_register_rejects_duplicate_account_details(self):
        self.register()
        self.client.credentials()

        duplicate_username = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(
                email="second@example.com",
                passport_or_identity_no="P987654321",
            ),
            format="json",
        )
        self.assertEqual(duplicate_username.status_code, 400)
        self.assertIn("username", duplicate_username.json())

        duplicate_email = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(
                username="secondapply",
                passport_or_identity_no="P987654321",
            ),
            format="json",
        )
        self.assertEqual(duplicate_email.status_code, 400)
        self.assertIn("email", duplicate_email.json())

        duplicate_identity = self.client.post(
            "/applicant/auth/register",
            self.applicant_payload(
                username="thirdapply",
                email="third@example.com",
            ),
            format="json",
        )
        self.assertEqual(duplicate_identity.status_code, 400)
        self.assertIn("passport_or_identity_no", duplicate_identity.json())

    def test_applicant_uses_shared_username_login(self):
        self.register()
        self.client.credentials()

        response = self.client.post(
            "/auth/login",
            {"username": "applytest", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "applicant")

    def test_applicant_can_update_profile_but_not_username_or_email(self):
        self.register()

        response = self.client.patch(
            "/applicant/me",
            {"email": "changed@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

        response = self.client.patch(
            "/applicant/me",
            {
                "first_name": "Updated",
                "last_name": "Applicant",
                "phone": "+60111111111",
                "nationality": "Indonesia",
                "country_of_residence": "Malaysia",
                "passport_or_identity_no": "A12345678",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        applicant = response.json()["applicant"]
        self.assertEqual(applicant["username"], "applytest")
        self.assertEqual(applicant["email"], "apply-test@example.com")
        self.assertEqual(applicant["first_name"], "Updated")
        self.assertEqual(applicant["nationality"], "Indonesia")

    def test_applicant_can_create_and_submit_application(self):
        admin_user = User.objects.create_superuser(
            username="application_admin",
            email="application-admin@example.com",
            password="pass",
        )
        executive_user = User.objects.create_user(username="application_executive", password="pass")
        executive_user.profile.role = Profile.ROLE_EXECUTIVE
        executive_user.profile.save(update_fields=["role", "updated_at"])
        self.register()
        response = self.client.post(
            "/applicant/applications",
            {
                "application_type": "undergraduate",
                "programme_preferences": [
                    "Bachelor in Data Science (Honours)",
                    "Bachelor in Computer Science (Honours)",
                    "Bachelor in Information Technology (Cybersecurity) (Honours)",
                    "Bachelor of Media and Communication (Honours)",
                ],
                "personal_information": {
                    "first_name": "Test",
                    "last_name": "Applicant",
                    "email": "apply-test@example.com",
                    "phone": "+60123456789",
                    "identity_number": "P1234567",
                    "country": "Malaysia",
                    "nationality": "Malaysia",
                },
                "academic_information": {
                    "highest_qualification": "High School",
                    "institution_name": "Test School",
                },
                "statement_accepted": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        application_id = response.json()["id"]

        response = self.client.post(
            f"/applicant/applications/{application_id}/submit",
            {"confirm": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "submitted")
        self.assertTrue(
            Notification.objects.filter(
                recipient__user__username="applytest",
                data__event_type="applications.submitted",
            ).exists()
        )
        self.assertTrue(
            admin_user.profile.notifications.filter(
                data__event_type="applications.review_requested",
            ).exists()
        )
        self.assertTrue(
            executive_user.profile.notifications.filter(
                data__event_type="applications.review_requested",
            ).exists()
        )

        self.client.force_authenticate(user=admin_user)
        review_response = self.client.patch(
            f"/applicant/staff/applications/{application_id}/status",
            {"status": "screening", "review_notes": "Initial screening started."},
            format="json",
        )
        self.assertEqual(review_response.status_code, 200, review_response.json())
        self.assertTrue(
            Notification.objects.filter(
                recipient__user__username="applytest",
                data__event_type="applications.status_changed",
                data__status="screening",
            ).exists()
        )

    def test_admin_can_configure_admission_requirements(self):
        admin_user = User.objects.create_superuser(
            username="setup_admin",
            email="setup-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.patch(
            "/admin/manage/applicants/setup",
            {
                "required_documents": [models.ApplicationDocument.TYPE_PASSPORT],
                "required_detail_fields": ["personal.first_name"],
                "custom_questions": [
                    {
                        "label": "Future goals",
                        "help_text": "Share your goals after graduation.",
                        "required": True,
                    }
                ],
                "scholarship_enabled": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        setup = response.json()["settings"]
        self.assertEqual(setup["required_documents"], [models.ApplicationDocument.TYPE_PASSPORT])
        self.assertFalse(setup["scholarship_enabled"])

        options_response = self.client.get("/applicant/options")
        self.assertEqual(options_response.status_code, 200)
        self.assertFalse(options_response.json()["admissions_setup"]["scholarship_enabled"])

        self.client.force_authenticate(user=None)
        self.register()
        application_response = self.client.post(
            "/applicant/applications",
            {
                "application_type": "undergraduate",
                "programme_preferences": [
                    "Bachelor in Data Science (Honours)",
                    "Bachelor in Computer Science (Honours)",
                    "Bachelor in Information Technology (Cybersecurity) (Honours)",
                    "Bachelor of Media and Communication (Honours)",
                ],
                "personal_information": {
                    "first_name": "Test",
                },
                "academic_information": {},
                "statement_accepted": True,
            },
            format="json",
        )
        self.assertEqual(application_response.status_code, 201, application_response.json())
        submit_response = self.client.post(
            f"/applicant/applications/{application_response.json()['id']}/submit",
            {"confirm": True},
            format="json",
        )
        self.assertEqual(submit_response.status_code, 400)
        self.assertIn("Future goals is required.", submit_response.json()["missing"])
        self.assertIn(
            "Passport or Identity Document must be uploaded.",
            submit_response.json()["missing"],
        )

    def test_admin_applicant_management_uses_applicant_record_ids(self):
        admin_user = User.objects.create_superuser(
            username="manage_admin",
            email="manage-admin@example.com",
            password="pass",
        )
        self.register()
        applicant = models.Applicant.objects.get(profile__user__username="applytest")

        self.client.force_authenticate(user=admin_user)
        response = self.client.get("/admin/manage/applicants")
        self.assertEqual(response.status_code, 200, response.json())
        row = next(item for item in response.json()["applicants"] if item["username"] == "applytest")
        self.assertEqual(row["id"], applicant.id)

        detail_response = self.client.get(f"/admin/manage/applicants/{applicant.id}")
        self.assertEqual(detail_response.status_code, 200, detail_response.json())
        self.assertEqual(detail_response.json()["applicant"]["id"], applicant.id)

    def test_staff_can_schedule_interview_and_review_document(self):
        admin_user = User.objects.create_superuser(
            username="review_admin",
            email="review-admin@example.com",
            password="pass",
        )
        self.register()
        application_response = self.client.post(
            "/applicant/applications",
            {
                "application_type": "undergraduate",
                "programme_preferences": [
                    "Bachelor in Data Science (Honours)",
                    "Bachelor in Computer Science (Honours)",
                    "Bachelor in Information Technology (Cybersecurity) (Honours)",
                    "Bachelor of Media and Communication (Honours)",
                ],
                "personal_information": {
                    "first_name": "Test",
                    "last_name": "Applicant",
                    "email": "apply-test@example.com",
                    "phone": "+60123456789",
                    "identity_number": "P1234567",
                    "country": "Malaysia",
                    "nationality": "Malaysia",
                },
                "academic_information": {
                    "highest_qualification": "High School",
                    "institution_name": "Test School",
                },
                "statement_accepted": True,
            },
            format="json",
        )
        self.assertEqual(application_response.status_code, 201, application_response.json())
        application_id = application_response.json()["id"]

        upload_response = self.client.post(
            f"/applicant/applications/{application_id}/documents",
            {
                "document_type": models.ApplicationDocument.TYPE_PASSPORT,
                "file": self.image_upload(),
            },
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 201, upload_response.json())
        document_id = upload_response.json()["id"]

        self.client.force_authenticate(user=admin_user)
        status_response = self.client.patch(
            f"/applicant/staff/applications/{application_id}/status",
            {
                "status": models.AdmissionApplication.STATUS_INTERVIEW,
                "note": "Shortlisted for panel interview.",
                "interview_at": "2026-07-10T09:00:00+08:00",
                "interview_location": "Admissions Office",
                "interview_details": "Bring original certificates.",
            },
            format="json",
        )
        self.assertEqual(status_response.status_code, 200, status_response.json())
        self.assertEqual(status_response.json()["status"], models.AdmissionApplication.STATUS_INTERVIEW)
        latest_event = models.ApplicationStatusEvent.objects.filter(
            application_id=application_id,
            to_status=models.AdmissionApplication.STATUS_INTERVIEW,
        ).first()
        self.assertIsNotNone(latest_event)
        self.assertIn("Interview schedule:", latest_event.note)
        self.assertIn("Admissions Office", latest_event.note)

        document_response = self.client.patch(
            f"/applicant/staff/documents/{document_id}",
            {
                "status": models.ApplicationDocument.STATUS_ACCEPTED,
                "notes": "Identity verified.",
            },
            format="json",
        )
        self.assertEqual(document_response.status_code, 200, document_response.json())
        self.assertEqual(document_response.json()["status"], models.ApplicationDocument.STATUS_ACCEPTED)
        self.assertEqual(document_response.json()["notes"], "Identity verified.")


class PortalRoleAccessTests(TestCase):
    protected_paths = {
        "applicant": "/applicant/applications",
        "student": "/student/dashboard",
        "teacher": "/teacher/dashboard",
        "executive": "/executive/dashboard",
        "librarian": "/librarian/dashboard",
        "admin": "/admin/dashboard",
    }

    def setUp(self):
        self.client = APIClient()
        self.users = {
            role: self.create_role_user(role)
            for role in self.protected_paths
        }

    def create_role_user(self, role):
        user = User.objects.create_user(
            username=f"{role}user",
            email=f"{role}@example.com",
            password="StrongPass123!",
            first_name=role.title(),
            last_name="User",
        )
        profile = user.profile
        profile.role = role
        profile.is_active = True
        profile.phone = "+60000000000"
        profile.save()
        prune_role_details(profile)
        detail = ensure_role_detail(profile)
        if role == Profile.ROLE_APPLICANT:
            detail.phone = "+60000000000"
            detail.nationality = "Malaysia"
            detail.country_of_residence = "Malaysia"
            detail.passport_or_identity_no = "990101011234"
            detail.save()
        return user

    def test_role_dashboards_reject_other_roles(self):
        for user_role, user in self.users.items():
            self.client.force_authenticate(user=user)
            for path_role, path in self.protected_paths.items():
                response = self.client.get(path)
                if user_role == path_role:
                    self.assertEqual(response.status_code, 200, f"{user_role} should access {path}")
                else:
                    self.assertEqual(
                        response.status_code,
                        403,
                        f"{user_role} should not access {path_role} path {path}",
                    )

    def test_only_admin_and_executive_can_access_applicant_staff_reviews(self):
        for role, user in self.users.items():
            self.client.force_authenticate(user=user)
            response = self.client.get("/applicant/staff/applications")
            if role in {Profile.ROLE_ADMIN, Profile.ROLE_EXECUTIVE}:
                self.assertEqual(response.status_code, 200, f"{role} should access staff review")
            else:
                self.assertEqual(response.status_code, 403, f"{role} should not access staff review")

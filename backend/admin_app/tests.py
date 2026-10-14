import io
import re
import tempfile
import zipfile
from datetime import timedelta
from unittest.mock import patch
from xml.sax.saxutils import escape

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from admin_app.models import (
    Admin,
    AcademicSession,
    Center,
    Hostel,
    HostelRoom,
    IELTSSession,
    School,
    Semester,
    SemesterConfiguration,
    SemesterHoliday,
    Profile,
    Unit,
)
from auth_app.serializers import RegisterSerializer
from executive_app.views.executive_courses_offer import (
    calendar_group_for_scope,
    semester_accepts_course_offers,
    semesters_accepting_course_offers,
)
from executive_app.course_schedule import scope_supports_academic_workflows, teachers_for_scope
from student_app.models import RegistrationPeriod
from student_app.models import Student
from teacher_app.models import Teacher, TeacherScopeAssignment


User = get_user_model()
NO_THROTTLE_REST_FRAMEWORK = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


def remote_addr_for_test(name):
    last_octet = (sum(ord(char) for char in name) % 200) + 10
    return f"10.240.0.{last_octet}"


def xlsx_upload(rows, name="accounts.xlsx"):
    def column_name(index):
        letters = ""
        index += 1
        while index:
            index, remainder = divmod(index - 1, 26)
            letters = chr(ord("A") + remainder) + letters
        return letters

    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            cell_ref = f"{column_name(column_index)}{row_index}"
            cells.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    workbook = io.BytesIO()
    with zipfile.ZipFile(workbook, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr(
            "xl/workbook.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Accounts" sheetId="1" r:id="rId1"/></sheets>'
                "</workbook>"
            ),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(row_xml)}</sheetData>'
                "</worksheet>"
            ),
        )
    workbook.seek(0)
    return SimpleUploadedFile(
        name,
        workbook.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class ProfileLifecycleTests(TestCase):
    def test_regular_user_gets_student_profile_and_detail(self):
        user = User.objects.create_user(username="student_noor", password="pass")

        profile = user.profile

        self.assertEqual(profile.role, Profile.ROLE_STUDENT)
        self.assertTrue(Student.objects.filter(profile=profile).exists())

    def test_superuser_gets_admin_profile_and_detail(self):
        user = User.objects.create_superuser(
            username="admin_noor",
            email="admin@example.com",
            password="pass",
        )

        profile = user.profile

        self.assertEqual(profile.role, Profile.ROLE_ADMIN)
        self.assertTrue(Admin.objects.filter(profile=profile).exists())

    def test_register_serializer_uses_explicit_role(self):
        school = School.objects.create(code="SCS", name="School of Computer Science")
        serializer = RegisterSerializer(
            data={
                "username": "teacher_noor",
                "email": "teacher@example.com",
                "first_name": "Teacher",
                "last_name": "Noor",
                "password": "StrongPass123!",
                "role": Profile.ROLE_TEACHER,
                "ums_id": "T-100",
                "phone_number": "+60123456789",
                "designation": "Part-time Teacher",
                "teacher_assignments": [{"school_id": school.id}],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        profile = user.profile

        self.assertEqual(profile.role, Profile.ROLE_TEACHER)
        self.assertFalse(Student.objects.filter(profile=profile).exists())
        self.assertTrue(
            Teacher.objects.filter(profile=profile, teacher_id="T-100").exists()
        )
        self.assertEqual(profile.designation, "Part-time Teacher")
        self.assertTrue(
            TeacherScopeAssignment.objects.filter(
                teacher=profile,
                school=school,
                is_primary=True,
            ).exists()
        )

    def test_student_account_requires_exactly_one_school_or_center(self):
        serializer = RegisterSerializer(
            data={
                "username": "student_unassigned",
                "email": "student-unassigned@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_STUDENT,
                "ums_id": "S-100",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("school_id", serializer.errors)

        school = School.objects.create(code="SCI", name="School of Science")
        serializer = RegisterSerializer(
            data={
                "username": "student_assigned",
                "email": "student-assigned@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_STUDENT,
                "ums_id": "S-101",
                "school_id": school.id,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_executive_account_requires_one_specific_unit(self):
        school = School.objects.create(code="SBS", name="School of Business")
        unit = Unit.objects.create(code="SBS-ADMIN", name="Business Administration", school=school)

        missing_unit = RegisterSerializer(
            data={
                "username": "executive_without_unit",
                "email": "executive-without-unit@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_EXECUTIVE,
                "ums_id": "E-100",
                "school_id": school.id,
            }
        )
        self.assertFalse(missing_unit.is_valid())
        self.assertIn("unit_id", missing_unit.errors)

        serializer = RegisterSerializer(
            data={
                "username": "executive_with_unit",
                "email": "executive-with-unit@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_EXECUTIVE,
                "ums_id": "E-101",
                "unit_id": unit.id,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.unit_id, unit.id)
        self.assertEqual(user.profile.school_id, school.id)

    def test_teacher_account_requires_scope_and_supports_multiple_scopes(self):
        school = School.objects.create(code="SSE", name="School of Social Sciences")
        center = Center.objects.create(code="CFGS", name="Foundation Centre")

        missing_scope = RegisterSerializer(
            data={
                "username": "teacher_without_scope",
                "email": "teacher-without-scope@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_TEACHER,
                "ums_id": "T-200",
            }
        )
        self.assertFalse(missing_scope.is_valid())
        self.assertIn("teacher_assignments", missing_scope.errors)

        serializer = RegisterSerializer(
            data={
                "username": "teacher_multiple_scopes",
                "email": "teacher-multiple-scopes@example.com",
                "password": "StrongPass123!",
                "role": Profile.ROLE_TEACHER,
                "ums_id": "T-201",
                "designation": "Part-time Teacher",
                "teacher_assignments": [
                    {"school_id": school.id},
                    {"center_id": center.id},
                ],
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        assignments = user.profile.teacher_scope_assignments.filter(is_active=True)
        self.assertEqual(assignments.count(), 2)
        self.assertEqual(assignments.filter(is_primary=True).count(), 1)
        self.assertEqual(user.profile.designation, "Part-time Teacher")
        self.assertTrue(
            teachers_for_scope({"kind": "school", "unit": school})
            .filter(pk=user.profile.pk)
            .exists()
        )
        self.assertTrue(
            teachers_for_scope({"kind": "center", "unit": center})
            .filter(pk=user.profile.pk)
            .exists()
        )

    def test_register_serializer_rejects_admin_and_applicant_roles(self):
        for role in (Profile.ROLE_ADMIN, Profile.ROLE_APPLICANT):
            serializer = RegisterSerializer(
                data={
                    "username": f"{role}_noor",
                    "email": f"{role}@example.com",
                    "first_name": role.title(),
                    "last_name": "Noor",
                    "password": "StrongPass123!",
                    "role": role,
                }
            )

            self.assertFalse(serializer.is_valid())
            self.assertIn("role", serializer.errors)

    def test_deleting_user_deletes_profile_and_role_detail(self):
        user = User.objects.create_user(username="delete_me", password="pass")
        profile_id = user.profile.id
        student_id = user.profile.student_detail.id

        user.delete()

        self.assertFalse(Profile.objects.filter(id=profile_id).exists())
        self.assertFalse(Student.objects.filter(id=student_id).exists())


class AccountProfilePictureTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.user = User.objects.create_user(username="picture_user", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    def image_upload(self, *, width=20, height=20, image_format="PNG"):
        image = Image.new("RGB", (width, height), color="navy")
        content = io.BytesIO()
        image.save(content, format=image_format)
        content.seek(0)
        return SimpleUploadedFile(
            f"profile.{image_format.lower()}",
            content.read(),
            content_type=f"image/{image_format.lower()}",
        )

    def test_user_can_upload_profile_picture(self):
        response = self.client.patch(
            "/auth/me",
            {"profile_picture": self.image_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture.name.startswith("profiles/pictures/"))
        self.assertTrue(response.json()["user"]["profile_picture"].startswith("/media/profile-pictures/"))
        self.assertNotIn("profiles/pictures", response.json()["user"]["profile_picture"])

    def test_profile_picture_rejects_images_larger_than_five_mb(self):
        response = self.client.patch(
            "/auth/me",
            {"profile_picture": self.image_upload(width=1600, height=1200, image_format="BMP")},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("5 MB or smaller", str(response.json()["profile_picture"]))

    def test_profile_picture_rejects_non_image_files(self):
        response = self.client.patch(
            "/auth/me",
            {
                "profile_picture": SimpleUploadedFile(
                    "not-an-image.txt",
                    b"not an image",
                    content_type="text/plain",
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("allowed image types", str(response.json()["profile_picture"]).lower())

    def test_profile_picture_rejects_image_extension_with_invalid_content(self):
        response = self.client.patch(
            "/auth/me",
            {
                "profile_picture": SimpleUploadedFile(
                    "payload.jpg",
                    b"<?php echo 'not an image'; ?>",
                    content_type="image/jpeg",
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("valid image", str(response.json()["profile_picture"]).lower())


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://localhost:3000",
    DEBUG=True,
    REST_FRAMEWORK=NO_THROTTLE_REST_FRAMEWORK,
)
class AccountRecoveryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.defaults["REMOTE_ADDR"] = remote_addr_for_test(
            self._testMethodName
        )
        self.user = User.objects.create_user(
            username="recover_noor",
            email="recover@example.com",
            password="OldStrongPass123!",
        )

    def request_reset(self, user=None):
        user = user or self.user
        response = self.client.post(
            "/auth/forgot-password",
            {"email": user.email},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mail.outbox)
        match = re.search(
            r"/reset-password\?token=([^\s]+)",
            mail.outbox[-1].body,
        )
        self.assertIsNotNone(match)
        return match.group(1)

    def test_public_register_endpoint_is_not_self_service(self):
        response = self.client.post(
            "/auth/register",
            {
                "username": "public_student",
                "email": "public-student@example.com",
                "first_name": "Public",
                "last_name": "Student",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_recovery_email_sends_link_and_reset_requires_confirmation(self):
        token = self.request_reset()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset-password?token=", mail.outbox[0].body)
        self.assertIn("expires in 60 minutes", mail.outbox[0].body)

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.password_reset_token)
        self.assertNotEqual(self.user.profile.password_reset_token, token)
        self.assertTrue(self.user.profile.password_reset_requested_at)

        mismatch = self.client.post(
            "/auth/reset-password",
            {
                "token": token,
                "password": "NewStrongPass123!",
                "confirm_password": "DifferentPass123!",
            },
            format="json",
        )
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn("confirm_password", mismatch.json())

        success = self.client.post(
            "/auth/reset-password",
            {
                "token": token,
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            format="json",
        )
        self.assertEqual(success.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))
        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.password_reset_token)
        self.assertIsNone(self.user.profile.password_reset_requested_at)

        reused = self.client.post(
            "/auth/reset-password",
            {
                "token": token,
                "password": "AnotherStrongPass123!",
                "confirm_password": "AnotherStrongPass123!",
            },
            format="json",
        )
        self.assertEqual(reused.status_code, 400)

    @override_settings(FRONTEND_BASE_URL="", CORS_ALLOWED_ORIGINS=["https://portal.example.edu"])
    def test_recovery_email_uses_allowed_origin_when_base_url_is_unset(self):
        response = self.client.post(
            "/auth/forgot-password",
            {"email": self.user.email},
            format="json",
            HTTP_ORIGIN="https://portal.example.edu",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://portal.example.edu/reset-password?token=", mail.outbox[-1].body)
        self.assertNotIn("localhost", mail.outbox[-1].body)

    def test_reset_password_rejects_passwords_longer_than_twenty_characters(self):
        token = self.request_reset()
        response = self.client.post(
            "/auth/reset-password",
            {
                "token": token,
                "password": "NewStrongPassword12345!",
                "confirm_password": "NewStrongPassword12345!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("20 characters or fewer", str(response.json()))

    def test_expired_reset_token_is_rejected_and_cleared(self):
        token = self.request_reset()
        self.user.profile.password_reset_requested_at = timezone.now() - timedelta(
            minutes=61
        )
        self.user.profile.save(update_fields=["password_reset_requested_at", "updated_at"])

        response = self.client.post(
            "/auth/reset-password",
            {
                "token": token,
                "password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.password_reset_token)
        self.assertIsNone(self.user.profile.password_reset_requested_at)

    def test_recovery_email_is_available_to_all_eight_roles(self):
        for index, (role, _label) in enumerate(Profile.ROLE_CHOICES):
            user = User.objects.create_user(
                username=f"recover_{role}",
                email=f"recover-{role}@example.com",
                password="OldStrongPass123!",
            )
            user.profile.role = role
            user.profile.save(update_fields=["role", "updated_at"])

            response = self.client.post(
                "/auth/forgot-password",
                {"email": user.email},
                format="json",
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), index + 1)
            self.assertEqual(mail.outbox[-1].to, [user.email])

    def test_unknown_email_does_not_reveal_account_existence(self):
        response = self.client.post(
            "/auth/forgot-password",
            {"email": "missing@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertNotIn("missing", response.json()["detail"].lower())

    def test_shared_email_receives_a_labeled_reset_link_for_each_account(self):
        other_user = User.objects.create_user(
            username="recover_second",
            email=self.user.email,
            password="OtherStrongPass123!",
        )
        other_user.profile.role = Profile.ROLE_LIBRARIAN
        other_user.profile.save(update_fields=["role", "updated_at"])

        response = self.client.post(
            "/auth/forgot-password",
            {"email": self.user.email},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        bodies = "\n".join(message.body for message in mail.outbox)
        self.assertIn("Username: recover_noor", bodies)
        self.assertIn("Username: recover_second", bodies)
        self.user.profile.refresh_from_db()
        other_user.profile.refresh_from_db()
        self.assertNotEqual(
            self.user.profile.password_reset_token,
            other_user.profile.password_reset_token,
        )

    def test_authenticated_user_can_change_password_with_current_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/auth/change-password",
            {
                "old_password": "OldStrongPass123!",
                "new_password": "ChangedPass456!",
                "confirm_password": "ChangedPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ChangedPass456!"))

    def test_change_password_rejects_wrong_current_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/auth/change-password",
            {
                "old_password": "WrongPassword123!",
                "new_password": "ChangedPass456!",
                "confirm_password": "ChangedPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.json())

    def test_change_password_rejects_passwords_longer_than_twenty_characters(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/auth/change-password",
            {
                "old_password": "OldStrongPass123!",
                "new_password": "ChangedStrongPass4567!",
                "confirm_password": "ChangedStrongPass4567!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("20 characters or fewer", str(response.json()))

    def test_change_password_requires_authentication(self):
        response = self.client.post(
            "/auth/change-password",
            {
                "old_password": "OldStrongPass123!",
                "new_password": "ChangedStrongPass456!",
                "confirm_password": "ChangedStrongPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="University Portal <portal@example.com>",
    FRONTEND_BASE_URL="http://localhost:3000",
)
class AdminCreateAccountEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="account_admin",
            email="account-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=self.admin_user)
        self.school = School.objects.create(
            code="SAS",
            name="School of Account Setup",
        )

    def student_payload(self, **overrides):
        payload = {
            "username": "new_student",
            "email": "new-student@example.com",
            "first_name": "New",
            "last_name": "Student",
            "ums_id": "S-EMAIL-100",
            "school_id": self.school.id,
        }
        payload.update(overrides)
        return payload

    def test_admin_supplied_temporary_password_is_set_and_emailed(self):
        response = self.client.post(
            "/admin/create-account/student",
            self.student_payload(password="Abcdefg1"),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertTrue(response.json()["email_sent"])
        user = User.objects.get(username="new_student")
        self.assertTrue(user.check_password("Abcdefg1"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new-student@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Your University Portal account credentials")
        self.assertIn("A University Portal student account has been created", mail.outbox[0].body)
        self.assertIn("Full name: New Student", mail.outbox[0].body)
        self.assertIn("Username: new_student", mail.outbox[0].body)
        self.assertIn("Email: new-student@example.com", mail.outbox[0].body)
        self.assertIn("Temporary password: Abcdefg1", mail.outbox[0].body)

    def test_admin_supplied_temporary_password_rejects_more_than_twenty_characters(self):
        response = self.client.post(
            "/admin/create-account/student",
            self.student_payload(password="TemporaryStrongPass123!"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("20 characters or fewer", str(response.json()))
        self.assertFalse(User.objects.filter(username="new_student").exists())

    def test_full_hostel_room_rejects_new_student_and_capacity_reduction(self):
        hostel = Hostel.objects.create(
            code="QA-HOSTEL",
            name="QA Hostel",
            hostel_type=Hostel.TYPE_MALE,
        )
        room = HostelRoom.objects.create(hostel=hostel, floor=1, number="01", capacity=2)

        first = self.client.post(
            "/admin/create-account/student",
            self.student_payload(password="Abcdefg1", room=room.code),
            format="json",
        )
        second = self.client.post(
            "/admin/create-account/student",
            self.student_payload(
                username="second_student",
                email="second-student@example.com",
                ums_id="S-EMAIL-101",
                password="Abcdefg1",
                room=f"{room.code}-A",
            ),
            format="json",
        )
        self.assertEqual(first.status_code, 201, first.json())
        self.assertEqual(second.status_code, 201, second.json())

        over_capacity = self.client.post(
            "/admin/create-account/student",
            self.student_payload(
                username="third_student",
                email="third-student@example.com",
                ums_id="S-EMAIL-102",
                password="Abcdefg1",
                room=f"{room.code}-B",
            ),
            format="json",
        )
        self.assertEqual(over_capacity.status_code, 400, over_capacity.json())
        self.assertIn("full", str(over_capacity.json()).lower())
        self.assertFalse(User.objects.filter(username="third_student").exists())
        self.assertEqual(len(mail.outbox), 2)

        reduced_capacity = self.client.put(
            f"/admin/hostels/rooms/{room.id}",
            {"capacity": 1},
            format="json",
        )
        self.assertEqual(reduced_capacity.status_code, 400, reduced_capacity.json())
        room.refresh_from_db()
        self.assertEqual(room.capacity, 2)

    @patch(
        "admin_app.views.admin_create_account._generate_temporary_password",
        return_value="Abc123xy",
    )
    def test_blank_temporary_password_is_generated_and_emailed(self, generate_password):
        response = self.client.post(
            "/admin/create-account/student",
            self.student_payload(password=""),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        generate_password.assert_called_once_with()
        user = User.objects.get(username="new_student")
        self.assertTrue(user.check_password("Abc123xy"))
        self.assertIn("Temporary password: Abc123xy", mail.outbox[0].body)
        self.assertNotIn("temporary_password", response.json())

    @patch(
        "admin_app.views.admin_create_account._generate_temporary_password",
        return_value="Abc123xy",
    )
    def test_csv_import_creates_student_accounts(self, generate_password):
        upload = SimpleUploadedFile(
            "students.csv",
            (
                "username,email,first_name,last_name,student_id,school_code,password\n"
                "bulk_student,bulk-student@example.com,Bulk,Student,S-BULK-1,SAS,\n"
                "bulk_student_two,bulk-student-two@example.com,Bulk,Two,S-BULK-2,SAS,Abcdefg1\n"
            ).encode(),
            content_type="text/csv",
        )

        response = self.client.post(
            "/admin/create-account/student/import",
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["created_count"], 2)
        self.assertEqual(response.json()["failed_count"], 0)
        generate_password.assert_called_once_with()
        first_user = User.objects.get(username="bulk_student")
        second_user = User.objects.get(username="bulk_student_two")
        self.assertTrue(first_user.check_password("Abc123xy"))
        self.assertTrue(second_user.check_password("Abcdefg1"))
        self.assertEqual(first_user.profile.school, self.school)
        self.assertEqual(len(mail.outbox), 2)

    def test_xlsx_import_creates_teacher_with_assignment(self):
        upload = xlsx_upload(
            [
                [
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "staff_id",
                    "teacher_assignments",
                    "designation",
                    "password",
                ],
                [
                    "bulk_teacher",
                    "bulk-teacher@example.com",
                    "Bulk",
                    "Teacher",
                    "T-BULK-1",
                    "school:SAS",
                    "Lecturer",
                    "Abcdefg1",
                ],
            ]
        )

        response = self.client.post(
            "/admin/create-account/teacher/import",
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["created_count"], 1)
        user = User.objects.get(username="bulk_teacher")
        profile = user.profile
        self.assertEqual(profile.role, Profile.ROLE_TEACHER)
        self.assertEqual(profile.staff_id, "T-BULK-1")
        self.assertEqual(profile.designation, "Lecturer")
        self.assertTrue(
            TeacherScopeAssignment.objects.filter(
                teacher=profile,
                school=self.school,
                is_primary=True,
            ).exists()
        )
        self.assertIn("Temporary password: Abcdefg1", mail.outbox[0].body)

    @patch(
        "admin_app.views.admin_create_account.send_mail",
        side_effect=RuntimeError("SMTP unavailable"),
    )
    def test_account_not_created_when_credentials_email_fails(self, send_email):
        response = self.client.post(
            "/admin/create-account/student",
            self.student_payload(password="Abcdefg1"),
            format="json",
        )

        self.assertEqual(response.status_code, 502, response.json())
        self.assertFalse(User.objects.filter(username="new_student").exists())
        send_email.assert_called_once()


class AdminSemesterEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="semester_admin",
            email="semester-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=self.admin_user)

    def notification_recipients(self, prefix):
        recipients = {}
        for role in (Profile.ROLE_STUDENT, Profile.ROLE_TEACHER, Profile.ROLE_EXECUTIVE):
            user = User.objects.create_user(username=f"{prefix}_{role}", password="pass")
            user.profile.role = role
            user.profile.save(update_fields=["role", "updated_at"])
            recipients[role] = user.profile
        return recipients

    def test_admin_can_configure_semesters_per_academic_year(self):
        response = self.client.post(
            "/admin/semesters",
            {
                "action": "update_semester_configuration",
                "calendar_group": Semester.CALENDAR_UNDERGRADUATE,
                "semesters_per_year": 2,
                "semester_lengths": [
                    {
                        "name": "Autumn Term",
                        "weeks": 14,
                        "semester_type": Semester.TYPE_LONG,
                        "default_classes_per_week": 1,
                    },
                    {
                        "name": "Spring Term",
                        "weeks": 16,
                        "semester_type": Semester.TYPE_LONG,
                        "default_classes_per_week": 1,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        config = SemesterConfiguration.objects.get(calendar_group=Semester.CALENDAR_UNDERGRADUATE)
        self.assertEqual(config.semesters_per_year, 2)
        self.assertEqual([item["weeks"] for item in config.semester_lengths], [14, 16])
        self.assertEqual(response.json()["semester_configuration"]["semester_lengths"][1]["name"], "Spring Term")

    def test_admin_can_configure_custom_center_calendar_group(self):
        center = Center.objects.create(
            code="HON",
            name="Honours Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_SEMESTER,
            semester_calendar_group="center:honours",
        )

        list_response = self.client.get("/admin/semesters")
        self.assertEqual(list_response.status_code, 200, list_response.json())
        self.assertIn(
            "center:honours",
            {choice["value"] for choice in list_response.json()["calendar_groups"]},
        )

        response = self.client.post(
            "/admin/semesters",
            {
                "action": "update_semester_configuration",
                "calendar_group": center.semester_calendar_group,
                "semesters_per_year": 1,
                "semester_lengths": [
                    {
                        "name": "Honours Year",
                        "weeks": 40,
                        "semester_type": Semester.TYPE_LONG,
                        "default_classes_per_week": 1,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(
            SemesterConfiguration.objects.filter(calendar_group="center:honours").exists()
        )

    def test_semester_plan_uses_configured_length_for_selected_semester(self):
        SemesterConfiguration.objects.create(
            calendar_group=Semester.CALENDAR_UNDERGRADUATE,
            semesters_per_year=4,
            semester_lengths=[
                {
                    "number": 1,
                    "name": "Term 1",
                    "weeks": 10,
                    "semester_type": Semester.TYPE_LONG,
                    "default_classes_per_week": 1,
                },
                {
                    "number": 2,
                    "name": "Term 2",
                    "weeks": 10,
                    "semester_type": Semester.TYPE_LONG,
                    "default_classes_per_week": 1,
                },
                {
                    "number": 3,
                    "name": "Term 3",
                    "weeks": 8,
                    "semester_type": Semester.TYPE_SHORT,
                    "default_classes_per_week": 2,
                },
                {
                    "number": 4,
                    "name": "Term 4",
                    "weeks": 6,
                    "semester_type": Semester.TYPE_SHORT,
                    "default_classes_per_week": 3,
                },
            ],
        )

        response = self.client.post(
            "/admin/semesters",
            {
                "action": "create_semester",
                "name": "Term 4, Session 2028",
                "academic_session": "2028",
                "calendar_group": Semester.CALENDAR_UNDERGRADUATE,
                "semester_number": 4,
                "start_date": "2028-10-01",
                "end_date": "2028-11-15",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        semester = Semester.objects.get(name="Term 4, Session 2028")
        self.assertEqual(semester.semester_number, 4)
        self.assertEqual(semester.planned_weeks, 6)
        self.assertEqual(semester.semester_type, Semester.TYPE_SHORT)
        self.assertEqual(semester.default_classes_per_week, 3)
        self.assertEqual(response.json()["semester"]["expected_weeks"], 6)

    def test_admin_can_start_semester_with_default_registration_phases(self):
        recipients = self.notification_recipients("semester")
        response = self.client.post(
            "/admin/semesters",
            {
                "name": "Semester 2, Session 2026/2027",
                "academic_session": "2026/2027",
                "semester_type": Semester.TYPE_LONG,
                "start_date": "2027-03-22",
                "end_date": "2027-07-16",
                "max_credit_hours": 21,
                "holidays": [
                    {
                        "name": "Labour Day",
                        "starts_on": "2027-05-01",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        semester = Semester.objects.get(name="Semester 2, Session 2026/2027")
        self.assertEqual(semester.max_credit_hours, 21)
        self.assertTrue(semester.is_active)
        self.assertTrue(SemesterHoliday.objects.filter(semester=semester, name="Labour Day").exists())
        self.assertEqual(RegistrationPeriod.objects.filter(semester=semester).count(), 3)
        self.assertTrue(
            RegistrationPeriod.objects.filter(
                semester=semester,
                phase=RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            ).exists()
        )
        for profile in recipients.values():
            self.assertTrue(
                profile.notifications.filter(
                    data__event_type="semesters.started",
                    data__semester_id=semester.id,
                ).exists()
            )

    def test_admin_can_list_plan_but_cannot_start_it_while_same_calendar_is_running(self):
        Semester.objects.create(
            name="Running schools semester",
            calendar_group=Semester.CALENDAR_UNDERGRADUATE,
            semester_type=Semester.TYPE_LONG,
            start_date="2026-03-23",
            end_date="2026-07-17",
            is_active=True,
        )
        create_response = self.client.post(
            "/admin/semesters",
            {
                "action": "create_semester",
                "name": "Planned schools semester",
                "academic_session": "2026/2027",
                "calendar_group": Semester.CALENDAR_UNDERGRADUATE,
                "semester_type": Semester.TYPE_SHORT,
                "start_date": "2026-08-03",
                "end_date": "2026-10-02",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201, create_response.json())
        planned = Semester.objects.get(name="Planned schools semester")
        self.assertFalse(planned.is_active)

        start_response = self.client.post(
            "/admin/semesters",
            {"action": "start_semester", "semester_id": planned.id},
            format="json",
        )

        self.assertEqual(start_response.status_code, 400, start_response.json())
        planned.refresh_from_db()
        self.assertFalse(planned.is_active)

    def test_admin_can_start_existing_semester_plan_and_notify_roles(self):
        recipients = self.notification_recipients("planned_semester")
        planned = Semester.objects.create(
            name="Ready Semester Plan",
            academic_session="2027/2028",
            calendar_group=Semester.CALENDAR_UNDERGRADUATE,
            semester_type=Semester.TYPE_LONG,
            start_date="2027-10-25",
            end_date="2028-02-25",
            is_active=False,
        )

        response = self.client.post(
            "/admin/semesters",
            {"action": "start_semester", "semester_id": planned.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.json())
        planned.refresh_from_db()
        self.assertTrue(planned.is_active)
        for profile in recipients.values():
            self.assertTrue(
                profile.notifications.filter(
                    data__event_type="semesters.started",
                    data__semester_id=planned.id,
                ).exists()
            )

    def test_cfgs_semester_can_run_alongside_schools_semester(self):
        Semester.objects.create(
            name="Running schools semester",
            calendar_group=Semester.CALENDAR_UNDERGRADUATE,
            semester_type=Semester.TYPE_LONG,
            start_date="2026-03-23",
            end_date="2026-07-17",
            is_active=True,
        )

        response = self.client.post(
            "/admin/semesters",
            {
                "action": "start_semester",
                "name": "Foundation Semester 1, 2027/2028",
                "academic_session": "2027/2028",
                "calendar_group": Semester.CALENDAR_FOUNDATION,
                "semester_type": Semester.TYPE_LONG,
                "start_date": "2027-04-06",
                "end_date": "2027-08-02",
                "revision_starts_on": "2027-07-20",
                "revision_ends_on": "2027-07-26",
                "examination_starts_on": "2027-07-27",
                "examination_ends_on": "2027-08-02",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(Semester.objects.filter(is_active=True).count(), 2)

    def test_admin_can_update_a_listed_semester_plan(self):
        recipients = self.notification_recipients("updated_semester")
        create_response = self.client.post(
            "/admin/semesters",
            {
                "action": "create_semester",
                "name": "Editable Semester Plan",
                "academic_session": "2027/2028",
                "start_date": "2027-10-25",
                "end_date": "2028-02-25",
            },
            format="json",
        )
        semester_id = create_response.json()["semester"]["id"]

        update_response = self.client.post(
            "/admin/semesters",
            {
                "action": "update_semester",
                "semester_id": semester_id,
                "name": "Editable Semester Plan",
                "academic_session": "2027/2028",
                "start_date": "2027-10-25",
                "end_date": "2028-02-25",
                "max_credit_hours": 18,
                "holidays": [{"name": "Planning Holiday", "starts_on": "2027-12-25"}],
            },
            format="json",
        )

        self.assertEqual(update_response.status_code, 200, update_response.json())
        semester = Semester.objects.get(pk=semester_id)
        self.assertEqual(semester.max_credit_hours, 18)
        self.assertTrue(semester.holidays.filter(name="Planning Holiday").exists())
        for profile in recipients.values():
            self.assertTrue(
                profile.notifications.filter(
                    data__event_type="semesters.updated",
                    data__semester_id=semester.id,
                ).exists()
            )
            self.assertFalse(
                profile.notifications.filter(
                    data__event_type="semesters.started",
                    data__semester_id=semester.id,
                ).exists()
            )

    def test_whole_year_center_is_limited_by_configured_sessions_per_academic_year(self):
        center = Center.objects.create(
            code="LANG",
            name="Language Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_WHOLE_YEAR,
            annual_session_limit=2,
        )
        payload = {
            "action": "create_ielts_session",
            "academic_session": "2026/2027",
            "center": center.id,
            "capacity": 40,
            "registration_opens_at": "2026-08-01T00:00:00Z",
            "registration_closes_at": "2026-08-31T23:59:59Z",
        }
        for number, exam_date in [(1, "2026-09-12"), (2, "2027-03-13")]:
            response = self.client.post(
                "/admin/semesters",
                {**payload, "title": f"IELTS Session {number}", "exam_date": exam_date},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.json())

        response = self.client.post(
            "/admin/semesters",
            {**payload, "title": "IELTS Session 3", "exam_date": "2027-06-12"},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(IELTSSession.objects.filter(academic_session="2026/2027").count(), 2)

    def test_academic_session_model_keeps_legacy_ielts_alias(self):
        center = Center.objects.create(
            code="CPD",
            name="Professional Development Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_WHOLE_YEAR,
        )
        session = AcademicSession.objects.create(
            academic_session="2026/2027",
            title="Placement Session",
            center=center,
            exam_date="2026-11-20",
            capacity=25,
        )

        self.assertIs(IELTSSession, AcademicSession)
        self.assertEqual(AcademicSession._meta.db_table, "admin_app_ieltssession")
        self.assertEqual(IELTSSession.objects.get(pk=session.pk).title, "Placement Session")

    def test_admin_can_create_academic_session_with_neutral_action(self):
        center = Center.objects.create(
            code="EXT",
            name="Extension Learning Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_WHOLE_YEAR,
            annual_session_limit=1,
        )

        response = self.client.post(
            "/admin/semesters",
            {
                "action": "create_academic_session",
                "academic_session": "2026/2027",
                "center": center.id,
                "capacity": 30,
                "registration_opens_at": "2026-09-01T00:00:00Z",
                "registration_closes_at": "2026-09-30T23:59:59Z",
                "title": "Professional Entry Session",
                "exam_date": "2026-10-15",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        payload = response.json()
        self.assertEqual(payload["message"], "Academic session created successfully.")
        self.assertEqual(payload["academic_session"]["title"], "Professional Entry Session")
        self.assertEqual(payload["ielts_session"]["id"], payload["academic_session"]["id"])
        self.assertEqual(AcademicSession.objects.count(), 1)

    def test_planned_semester_is_available_during_course_offering_window(self):
        now = timezone.now()
        semester = Semester.objects.create(
            name="Planned course-offering semester",
            calendar_group=Semester.CALENDAR_UNDERGRADUATE,
            semester_type=Semester.TYPE_LONG,
            start_date=timezone.localdate() + timezone.timedelta(days=30),
            end_date=timezone.localdate() + timezone.timedelta(days=150),
            course_offering_opens_at=now - timezone.timedelta(days=1),
            course_offering_closes_at=now + timezone.timedelta(days=1),
            is_active=False,
        )

        self.assertTrue(semester_accepts_course_offers(semester, now=now))
        self.assertTrue(semesters_accepting_course_offers(now=now).filter(pk=semester.pk).exists())

    def test_executive_center_scope_uses_configured_calendar_mode(self):
        foundation_center = Center.objects.create(
            code="FOUND",
            name="Foundation Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_SEMESTER,
            semester_calendar_group=Semester.CALENDAR_FOUNDATION,
        )
        custom_center = Center.objects.create(
            code="HON",
            name="Honours Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_SEMESTER,
            semester_calendar_group="center:honours",
        )
        year_round_center = Center.objects.create(
            code="LANG",
            name="Language Centre",
            center_type=Center.CENTER_ACADEMIC,
            academic_calendar_mode=Center.CALENDAR_WHOLE_YEAR,
        )
        support_center = Center.objects.create(
            code="ICT",
            name="ICT Centre",
            center_type=Center.CENTER_NON_ACADEMIC,
        )

        self.assertEqual(
            calendar_group_for_scope({"kind": "center", "unit": foundation_center}),
            Semester.CALENDAR_FOUNDATION,
        )
        self.assertEqual(
            calendar_group_for_scope({"kind": "center", "unit": custom_center}),
            "center:honours",
        )
        self.assertIsNone(calendar_group_for_scope({"kind": "center", "unit": year_round_center}))
        self.assertFalse(scope_supports_academic_workflows({"kind": "center", "unit": support_center}))

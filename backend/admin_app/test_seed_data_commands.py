from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from admin_app.models import Admin, Center, Course, Program, Profile, School, SystemSetting
from admin_app.settings_registry import SETTINGS_SECTIONS, setting_key
from executive_app.models import Executive
from home_app.models import PublicPage
from student_app.models import Student
from teacher_app.models import Teacher


class BootstrapUniversityCommandTests(TestCase):
    def test_bootstrap_creates_settings_without_institution_records(self):
        call_command("bootstrap_university")
        call_command("bootstrap_university")

        expected_keys = {
            setting_key(section)
            for section in SETTINGS_SECTIONS
        } | {setting_key("ui_customization")}
        self.assertTrue(
            expected_keys.issubset(
                set(SystemSetting.objects.values_list("key", flat=True))
            )
        )
        self.assertEqual(School.objects.count(), 0)
        self.assertEqual(Center.objects.count(), 0)
        self.assertEqual(Program.objects.count(), 0)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(
            SystemSetting.objects.get(key=setting_key("general")).value["ums_name"],
            "University Portal",
        )
        self.assertIn(
            "enable_library",
            SystemSetting.objects.get(key=setting_key("dashboard")).value,
        )

    def test_bootstrap_syncs_existing_superusers_as_admin_profiles(self):
        user = get_user_model().objects.create_superuser(
            username="root",
            email="root@example.edu",
            password="secret",
        )

        call_command("bootstrap_university")

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, Profile.ROLE_ADMIN)
        self.assertTrue(Admin.objects.filter(profile=profile).exists())


class NeutralDemoDataCommandTests(TestCase):
    def test_neutral_demo_pack_is_idempotent_and_non_aiu(self):
        call_command("seed_neutral_demo_data")
        call_command("seed_neutral_demo_data")

        self.assertTrue(School.objects.filter(code="DEMO-SCI").exists())
        self.assertTrue(Center.objects.filter(code="DEMO-FND").exists())
        self.assertTrue(Program.objects.filter(code="DEMO-BCOMP").exists())
        self.assertEqual(Course.objects.filter(code__startswith="DEMO").count(), 3)
        self.assertEqual(
            Teacher.objects.filter(profile__user__email="teacher@demo-university.example").count(),
            1,
        )
        self.assertEqual(
            Executive.objects.filter(profile__user__email="executive@demo-university.example").count(),
            1,
        )
        self.assertEqual(
            Student.objects.filter(profile__user__email="student@demo-university.example").count(),
            1,
        )
        self.assertTrue(
            PublicPage.objects.filter(
                slug="demo-home",
                metadata__demo_pack="neutral",
            ).exists()
        )

        self.assertFalse(School.objects.filter(code__in=["SBSS", "SEHS", "SCI"]).exists())
        self.assertFalse(Center.objects.filter(code="ACE-SEDI").exists())
        self.assertFalse(
            get_user_model().objects.filter(email__iendswith="@aiu.edu.my").exists()
        )

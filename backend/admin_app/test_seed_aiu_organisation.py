from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from admin_app.models import Center, Department, Program, School, Unit
from executive_app.models import Executive
from teacher_app.models import Teacher


class SeedAIUOrganisationTests(TestCase):
    def test_seed_creates_full_structure_with_people(self):
        user_count_before = get_user_model().objects.count()
        Program.objects.create(code="CGS-RS", name="Legacy graduate support record")

        call_command("seed_aiu_organisation")
        call_command("seed_aiu_organisation")

        self.assertEqual(School.objects.count(), 3)
        self.assertEqual(Center.objects.count(), 12)
        self.assertEqual(Department.objects.count(), 7)
        self.assertGreater(Unit.objects.count(), 14)
        self.assertEqual(Program.objects.count(), 37)
        self.assertEqual(Teacher.objects.count(), 73)
        self.assertEqual(Executive.objects.count(), 90)
        self.assertFalse(Program.objects.filter(code="CGS-RS").exists())

        user_count_after = get_user_model().objects.count()
        self.assertGreater(
            user_count_after, user_count_before,
            "Teacher, executive, and admin accounts should be created",
        )

        for code in ("CSAA", "ICT", "CPC", "COR", "CQAA", "ACE-SEDI", "CRIM", "CCIE"):
            self.assertTrue(Center.objects.filter(code=code).exists())
            self.assertFalse(Department.objects.filter(code=code).exists())

        self.assertTrue(
            Unit.objects.filter(
                code="CTN-ADMIN",
                name="Canteen Admin",
                center__code="CSAA",
            ).exists()
        )

        for school in School.objects.all():
            self.assertEqual(
                Unit.objects.filter(
                    school=school,
                    unit_type=Unit.UNIT_ADMINISTRATIVE,
                ).count(),
                1,
            )

        for center_code in ("CDAE", "CFGS", "CGS", "LC"):
            self.assertEqual(
                Unit.objects.filter(
                    center__code=center_code,
                    unit_type=Unit.UNIT_ADMINISTRATIVE,
                ).count(),
                1,
            )

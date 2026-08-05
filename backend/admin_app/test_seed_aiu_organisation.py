from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from admin_app.management.commands.seed_aiu_demo_data import (
    CENTERS,
    DEPARTMENTS,
    SCHOOL_PROGRAMMES,
    CENTER_PROGRAMMES,
    SCHOOLS,
    UNITS,
)
from admin_app.models import Center, Department, Program, School, Unit
from executive_app.models import Executive
from home_app.models import PublicPage
from teacher_app.models import Teacher


class SeedAIUOrganisationTests(TestCase):
    def test_seed_creates_full_structure_with_people(self):
        user_count_before = get_user_model().objects.count()
        Program.objects.create(code="CGS-RS", name="Legacy graduate support record")
        center_only_codes = ("CSAA", "ICT", "CPC", "COR", "CQAA", "ACE-SEDI", "CRIM", "CCIE")
        Department.objects.filter(code__in=center_only_codes).delete()

        call_command("seed_aiu_demo_data")
        call_command("seed_aiu_demo_data")

        school_codes = {item["code"] for item in SCHOOLS}
        center_codes = {item["code"] for item in CENTERS}
        department_codes = {item["code"] for item in DEPARTMENTS}
        unit_codes = {item["code"] for item in UNITS}
        programme_codes = {
            row[0]
            for programmes in SCHOOL_PROGRAMMES.values()
            for row in programmes
        } | {
            row[0]
            for programmes in CENTER_PROGRAMMES.values()
            for row in programmes
        }

        self.assertEqual(School.objects.filter(code__in=school_codes).count(), 3)
        self.assertEqual(Center.objects.filter(code__in=center_codes).count(), 12)
        self.assertEqual(Department.objects.filter(code__in=department_codes).count(), 7)
        self.assertGreater(Unit.objects.filter(code__in=unit_codes).count(), 14)
        self.assertEqual(Program.objects.filter(code__in=programme_codes).count(), 37)
        self.assertEqual(
            Teacher.objects.filter(profile__user__email__iendswith="@aiu.edu.my").count(),
            73,
        )
        self.assertEqual(
            Executive.objects.filter(profile__user__email__iendswith="@aiu.edu.my").count(),
            90,
        )
        self.assertFalse(Program.objects.filter(code="CGS-RS").exists())
        self.assertTrue(
            PublicPage.objects.filter(
                slug="about-aiu",
                metadata__demo_pack="aiu",
            ).exists()
        )

        user_count_after = get_user_model().objects.count()
        self.assertGreater(
            user_count_after, user_count_before,
            "Teacher, executive, and admin accounts should be created",
        )

        for code in center_only_codes:
            self.assertTrue(Center.objects.filter(code=code).exists())
            self.assertFalse(Department.objects.filter(code=code).exists())

        self.assertTrue(
            Unit.objects.filter(
                code="CTN-ADMIN",
                name="Canteen Admin",
                center__code="CSAA",
            ).exists()
        )

        for school in School.objects.filter(code__in=school_codes):
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

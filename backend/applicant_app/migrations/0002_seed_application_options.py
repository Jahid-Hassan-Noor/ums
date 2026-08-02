from django.db import migrations


PROGRAMMES = [
    ("BDS", "Bachelor in Data Science (Honours)", "undergraduate", "School of Computing and Informatics"),
    ("BBA-HRM", "Bachelor of Business Administration (Honours) (Human Resource Management)", "undergraduate", "School of Business and Social Sciences"),
    ("BBA-MKT", "Bachelor of Business Administration (Honours) (Marketing)", "undergraduate", "School of Business and Social Sciences"),
    ("BBA", "Bachelor of Business Administration (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("FIC", "Foundation in Computing", "foundation", "Centre for Foundation and General Studies"),
    ("BECE", "Bachelor in Early Childhood Education (Honours)", "undergraduate", "School of Education and Human Sciences"),
    ("BEE", "Bachelor of Elementary Education (Honours)", "undergraduate", "School of Education and Human Sciences"),
    ("BFIN-IF", "Bachelor of Finance (Islamic Finance) (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("BECON", "Bachelor of Economics (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("BSD", "Bachelor of Social Development (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("BCS", "Bachelor in Computer Science (Honours)", "undergraduate", "School of Computing and Informatics"),
    ("BMC", "Bachelor of Media and Communication (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("BPIR", "Bachelor of Politics and International Relations (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("FIA", "Foundation in Arts", "foundation", "Centre for Foundation and General Studies"),
    ("BBA-CS", "Bachelor of Business Administration with Computer Science (Honours)", "undergraduate", "School of Business and Social Sciences"),
    ("BIT-CYB", "Bachelor in Information Technology (Cybersecurity) (Honours)", "undergraduate", "School of Computing and Informatics"),
]


def seed_options(apps, schema_editor):
    ApplicationIntake = apps.get_model("applicant_app", "ApplicationIntake")
    ApplicationProgramme = apps.get_model("applicant_app", "ApplicationProgramme")

    ApplicationIntake.objects.update_or_create(
        code="UG-2026-2027",
        defaults={
            "title": "2026/2027 Undergraduate Intake",
            "application_type": "undergraduate",
            "academic_year": "2026/2027",
            "is_active": True,
        },
    )

    for sort_order, (code, name, level, school) in enumerate(PROGRAMMES, start=1):
        ApplicationProgramme.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "level": level,
                "school": school,
                "is_active": True,
                "sort_order": sort_order,
            },
        )


def unseed_options(apps, schema_editor):
    ApplicationIntake = apps.get_model("applicant_app", "ApplicationIntake")
    ApplicationProgramme = apps.get_model("applicant_app", "ApplicationProgramme")
    ApplicationIntake.objects.filter(code="UG-2026-2027").delete()
    ApplicationProgramme.objects.filter(code__in=[program[0] for program in PROGRAMMES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("applicant_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_options, unseed_options),
    ]

from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from admin_app import models
from auth_app.models import prune_role_details
from executive_app.models import Executive, TimetableSlot
from home_app import models as home_models
from student_app.models import Student
from teacher_app.models import Teacher


def username_from_email(email):
    return email.split("@", 1)[0].replace(".", "_").replace("+", "_").lower()


def split_name(full_name):
    parts = str(full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


class Command(BaseCommand):
    help = (
        "Seed an opt-in neutral university demo pack using example.edu data. "
        "This is safe for universal CI and does not create AIU records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-bootstrap",
            action="store_true",
            help="Do not run the generic bootstrap_university command first.",
        )
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Seed academic/public demo data without demo user accounts.",
        )
        parser.add_argument(
            "--password",
            default="",
            help=(
                "Optional password for demo users. If omitted, newly created "
                "demo users receive unusable passwords."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options.get("skip_bootstrap"):
            call_command(
                "bootstrap_university",
                skip_admin_sync=True,
                verbosity=options.get("verbosity", 1),
            )

        school, center, department, units = self.seed_organization()
        program, courses, semester = self.seed_academics(school, center)
        self.seed_facilities()
        if not options.get("skip_users"):
            self.seed_people(
                school=school,
                center=center,
                department=department,
                units=units,
                program=program,
                password=options.get("password") or "",
            )
        self.seed_public_content()

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded neutral demo data: "
                f"{school.code} school, {center.code} center, "
                f"{len(units)} units, {len(courses)} courses, "
                f"{'active ' if semester.is_active else ''}{semester.name}."
            )
        )

    def seed_organization(self):
        school, _ = models.School.objects.update_or_create(
            code="DEMO-SCI",
            defaults={
                "slug": "demo-school-of-science",
                "name": "Demo School of Science",
                "description": "Neutral demo school for universal portal testing.",
                "about": "A generic academic school used only by the neutral demo pack.",
                "vision": "Make universal portal testing predictable.",
                "mission": ["Provide neutral demo academic data."],
                "programmes": ["Bachelor of Computing"],
                "is_active": True,
            },
        )
        center, _ = models.Center.objects.update_or_create(
            code="DEMO-FND",
            defaults={
                "slug": "demo-foundation-center",
                "name": "Demo Foundation Center",
                "center_type": models.Center.CENTER_ACADEMIC,
                "academic_calendar_mode": models.Center.CALENDAR_SEMESTER,
                "semester_calendar_group": models.Semester.CALENDAR_FOUNDATION,
                "description": "Neutral demo foundation center.",
                "about": "A generic center used only by the neutral demo pack.",
                "offerings": ["Foundation pathways"],
                "is_active": True,
            },
        )
        department, _ = models.Department.objects.update_or_create(
            code="DEMO-REG",
            defaults={
                "name": "Demo Registry Department",
                "description": "Neutral demo registry department.",
                "is_active": True,
            },
        )
        unit_specs = [
            ("DEMO-SCI-ADMIN", "Demo Science Admin Unit", models.Unit.UNIT_ADMINISTRATIVE, school, None, None),
            ("DEMO-FND-ADMIN", "Demo Foundation Admin Unit", models.Unit.UNIT_ADMINISTRATIVE, None, center, None),
            ("DEMO-REG-ADMIN", "Demo Registry Admin Unit", models.Unit.UNIT_ADMINISTRATIVE, None, None, department),
        ]
        units = {}
        for code, name, unit_type, unit_school, unit_center, unit_department in unit_specs:
            unit, _ = models.Unit.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "unit_type": unit_type,
                    "school": unit_school,
                    "center": unit_center,
                    "department": unit_department,
                    "description": "Neutral demo unit.",
                    "is_active": True,
                },
            )
            units[code] = unit
        return school, center, department, units

    def seed_academics(self, school, center):
        program, _ = models.Program.objects.update_or_create(
            code="DEMO-BCOMP",
            defaults={
                "name": "Bachelor of Computing",
                "school": school,
                "program_type": models.Program.PROGRAM_ACADEMIC,
                "level": "Bachelor",
                "duration_years": 3,
                "description": "Neutral demo academic programme.",
                "is_active": True,
            },
        )
        course_specs = [
            ("DEMO101", "Introduction to University Studies", 3, school, None, False),
            ("DEMO-CS101", "Introduction to Computing", 4, school, None, True),
            ("DEMO-FND101", "Foundation Seminar", 2, None, center, False),
        ]
        courses = {}
        for code, title, credits, course_school, course_center, has_lab in course_specs:
            course, _ = models.Course.objects.update_or_create(
                code=code,
                defaults={
                    "title": title,
                    "credits": credits,
                    "school": course_school,
                    "center": course_center,
                    "program": program if course_school else None,
                    "has_lab": has_lab,
                    "description": "Neutral demo course.",
                    "is_active": True,
                },
            )
            courses[code] = course

        today = timezone.localdate()
        year = today.year
        active_exists = models.Semester.objects.filter(
            calendar_group=models.Semester.CALENDAR_UNDERGRADUATE,
            is_active=True,
        ).exclude(name="Demo Semester").exists()
        semester, _ = models.Semester.objects.update_or_create(
            name="Demo Semester",
            defaults={
                "academic_session": f"{year}/{year + 1}",
                "semester_type": models.Semester.TYPE_LONG,
                "calendar_group": models.Semester.CALENDAR_UNDERGRADUATE,
                "semester_number": 1,
                "planned_weeks": 14,
                "start_date": date(year, 9, 1),
                "end_date": date(year + 1, 1, 31),
                "course_offering_opens_at": datetime(year, 7, 1, 9, 0, tzinfo=timezone.get_current_timezone()),
                "course_offering_closes_at": datetime(year, 8, 15, 17, 0, tzinfo=timezone.get_current_timezone()),
                "course_selection_closes_at": datetime(year, 9, 15, 17, 0, tzinfo=timezone.get_current_timezone()),
                "max_credit_hours": 18,
                "is_active": not active_exists,
            },
        )
        for index, course in enumerate(courses.values(), start=1):
            models.CourseOffering.objects.update_or_create(
                course=course,
                semester=semester,
                section="A",
                defaults={
                    "capacity": 40 + (index * 5),
                    "is_active": True,
                },
            )
        return program, courses, semester

    def seed_facilities(self):
        building, _ = models.Building.objects.update_or_create(
            code="DEMO-MAIN",
            defaults={
                "name": "Demo Main Building",
                "address": "100 Example Avenue",
                "description": "Neutral demo building.",
                "is_active": True,
            },
        )
        models.Venue.objects.update_or_create(
            code="DEMO-LH1",
            defaults={
                "building": building,
                "name": "Demo Lecture Hall 1",
                "floor": "1",
                "capacity": 80,
                "is_active": True,
            },
        )
        models.Room.objects.update_or_create(
            code="DEMO-R101",
            defaults={
                "name": "Demo Room 101",
                "campus": "Demo Campus",
                "building": building.name,
                "floor": "1",
                "capacity": 35,
                "is_active": True,
            },
        )
        for day in (TimetableSlot.MONDAY, TimetableSlot.WEDNESDAY):
            TimetableSlot.objects.update_or_create(
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(10, 30),
                defaults={"label": "Demo morning class"},
            )

    def seed_people(self, school, center, department, units, program, password):
        people = [
            {
                "email": "admin@demo-university.example",
                "name": "Demo Admin",
                "role": models.Profile.ROLE_ADMIN,
                "designation": "Portal Administrator",
                "unit": units["DEMO-REG-ADMIN"],
                "detail_model": models.Admin,
                "identifier": "DEMO-ADMIN-001",
                "identifier_field": "admin_id",
                "is_superuser": True,
            },
            {
                "email": "executive@demo-university.example",
                "name": "Demo Executive",
                "role": models.Profile.ROLE_EXECUTIVE,
                "designation": "Academic Executive",
                "school": school,
                "unit": units["DEMO-SCI-ADMIN"],
                "detail_model": Executive,
                "identifier": "DEMO-EXEC-001",
                "identifier_field": "executive_id",
            },
            {
                "email": "teacher@demo-university.example",
                "name": "Demo Teacher",
                "role": models.Profile.ROLE_TEACHER,
                "designation": "Lecturer",
                "school": school,
                "unit": units["DEMO-SCI-ADMIN"],
                "detail_model": Teacher,
                "identifier": "DEMO-TEACH-001",
                "identifier_field": "teacher_id",
            },
            {
                "email": "student@demo-university.example",
                "name": "Demo Student",
                "role": models.Profile.ROLE_STUDENT,
                "designation": "Student",
                "school": school,
                "program": program,
                "detail_model": Student,
                "identifier": "DEMO-STU-001",
                "identifier_field": "student_id",
            },
        ]
        for person in people:
            user = self.ensure_user(person, password)
            profile_defaults = {
                "role": person["role"],
                "designation": person["designation"],
                "school": person.get("school"),
                "center": person.get("center"),
                "department": person.get("department") or department if person["role"] == models.Profile.ROLE_ADMIN else person.get("department"),
                "unit": person.get("unit"),
                "is_active": True,
            }
            profile, _ = models.Profile.objects.update_or_create(
                user=user,
                defaults=profile_defaults,
            )
            prune_role_details(profile)
            detail_defaults = {
                person["identifier_field"]: person["identifier"],
                "is_active": True,
            }
            if person["role"] == models.Profile.ROLE_STUDENT:
                detail_defaults.update(
                    {
                        "school": school,
                        "program": program,
                        "current_year": 1,
                        "enrollment_status": "active",
                    }
                )
            else:
                detail_defaults.update(
                    {
                        "designation": person["designation"],
                        "school": person.get("school"),
                        "center": person.get("center"),
                        "department": person.get("department") or department if person["role"] == models.Profile.ROLE_ADMIN else person.get("department"),
                        "unit": person.get("unit"),
                    }
                )
            person["detail_model"].objects.update_or_create(
                profile=profile,
                defaults=detail_defaults,
            )

    def ensure_user(self, person, password):
        User = get_user_model()
        first_name, last_name = split_name(person["name"])
        user, created = User.objects.get_or_create(
            username=username_from_email(person["email"]),
            defaults={
                "email": person["email"],
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": person["role"] == models.Profile.ROLE_ADMIN,
                "is_superuser": person.get("is_superuser", False),
            },
        )
        user.email = person["email"]
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        if person["role"] == models.Profile.ROLE_ADMIN:
            user.is_staff = True
            user.is_superuser = True
        if password:
            user.set_password(password)
        elif created:
            user.set_unusable_password()
        user.save()
        return user

    def seed_public_content(self):
        pages = [
            ("demo-home", "/", home_models.PublicPage.SECTION_HOME, "Demo University", "Neutral demo homepage.", 0),
            ("demo-about", "/about", home_models.PublicPage.SECTION_ABOUT, "About Demo University", "Neutral demo about page.", 10),
            ("demo-programmes", "/programmes", home_models.PublicPage.SECTION_ACADEMICS, "Demo Programmes", "Neutral demo programmes page.", 30),
        ]
        for slug, route_path, section, title, summary, sort_order in pages:
            home_models.PublicPage.objects.update_or_create(
                slug=slug,
                defaults={
                    "route_path": route_path,
                    "section": section,
                    "title": title,
                    "summary": summary,
                    "body": f"{summary} Replace this content for a real institution.",
                    "metadata": {
                        "demo_pack": "neutral",
                        "navigation": {
                            "show": True,
                            "label": title,
                            "order": sort_order,
                        },
                    },
                    "status": home_models.PublicPage.STATUS_PUBLISHED,
                    "sort_order": sort_order,
                    "published_at": timezone.now(),
                },
            )
        home_models.PublicNews.objects.update_or_create(
            slug="neutral-demo-welcome",
            defaults={
                "title": "Welcome to Demo University",
                "summary": "Neutral demo news record.",
                "body": "This record belongs to the neutral demo pack.",
                "status": home_models.PublicNews.STATUS_PUBLISHED,
                "published_at": timezone.now(),
            },
        )
        home_models.OfficialLink.objects.update_or_create(
            title="Demo Student Portal",
            defaults={
                "url": "https://example.edu/student",
                "audience": home_models.OfficialLink.AUDIENCE_STUDENT,
                "category": "Academic",
                "description": "Neutral demo student link.",
                "sort_order": 10,
                "is_active": True,
            },
        )

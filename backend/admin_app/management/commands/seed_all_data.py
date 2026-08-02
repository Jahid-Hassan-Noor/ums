import random
import string
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from admin_app import models as admin_models
from applicant_app import models as applicant_models
from caterer_app import models as caterer_models
from executive_app import models as executive_models
from home_app import models as home_models
from librarian_app import models as librarian_models
from notifications_package.models import Notification
from student_app import models as student_models
from teacher_app import models as teacher_models
from technician_app import models as technician_models
from accountant_app import models as accountant_models

LOCAL_TZ = ZoneInfo("Asia/Kuala_Lumpur")

PASSWORDS = {}


def random_password(length=10):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def make_username(email):
    return email.split("@")[0].replace(".", "_").lower()


def get_or_create_user(email, first_name, last_name=""):
    username = make_username(email)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        },
    )
    if created:
        pw = random_password()
        user.set_password(pw)
        user.save()
        PASSWORDS[email] = pw
    return user


def get_or_create_profile(user, role, school=None, center=None, department=None, unit=None, designation=""):
    profile, _ = admin_models.Profile.objects.update_or_create(
        user=user,
        defaults={
            "role": role,
            "school": school,
            "center": center,
            "department": department,
            "unit": unit,
            "designation": designation,
            "is_active": True,
        },
    )
    return profile


def today_local():
    return timezone.localdate()


class Command(BaseCommand):
    help = "Seed comprehensive dummy data for all application tables."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding all data...")

        self.seed_buildings_venues_rooms_hostels()
        profiles = self.seed_students()
        self.seed_librarians()
        self.seed_technicians()
        self.seed_caterers()
        self.seed_accountants()
        self.seed_applicants()
        courses = self.seed_courses()
        semester = self.seed_semesters()
        self.seed_timetable_slots()
        offerings = self.seed_course_offerings(courses, semester)
        self.seed_tutorial_lab_groups(offerings)
        self.seed_class_groups(semester)
        self.seed_registration_periods(semester)
        self.seed_academic_events(semester)
        self.seed_elections()
        self.seed_library_data()
        self.seed_canteen_data(profiles)
        self.seed_ict_helpdesk(profiles)
        self.seed_venue_bookings(profiles)
        self.seed_leave_requests(profiles)
        self.seed_public_content()
        self.seed_system_settings()
        self.seed_notifications(profiles)
        self.seed_assignments(offerings, profiles)
        self.seed_course_sections_resources(offerings)

        self.stdout.write(self.style.SUCCESS(f"\n\n=== SEEDING COMPLETE ==="))
        self.stdout.write(self.style.SUCCESS(f"\nAccounts created with passwords:"))
        for email, pw in sorted(PASSWORDS.items()):
            self.stdout.write(f"  {email:50s}  password: {pw}")

    def seed_buildings_venues_rooms_hostels(self):
        buildings_data = [
            {"code": "MAIN", "name": "Main Academic Building", "address": "Main Campus"},
            {"code": "LIB", "name": "Library Building", "address": "Main Campus"},
            {"code": "SCI", "name": "Science and Computing Block", "address": "Main Campus"},
            {"code": "ADMIN", "name": "Administration Building", "address": "Main Campus"},
            {"code": "HALL", "name": "Student Centre / Hall", "address": "Main Campus"},
            {"code": "BSNSS", "name": "Business School Block", "address": "Main Campus"},
        ]
        buildings = {}
        for b in buildings_data:
            obj, _ = admin_models.Building.objects.update_or_create(
                code=b["code"], defaults={"name": b["name"], "address": b["address"], "is_active": True}
            )
            buildings[obj.code] = obj

        venues_data = [
            {"building": "MAIN", "code": "LH-A", "name": "Lecture Hall A", "floor": "G", "capacity": 200},
            {"building": "MAIN", "code": "LH-B", "name": "Lecture Hall B", "floor": "G", "capacity": 150},
            {"building": "SCI", "code": "CL-1", "name": "Computing Lab 1", "floor": "1", "capacity": 40},
            {"building": "SCI", "code": "CL-2", "name": "Computing Lab 2", "floor": "1", "capacity": 35},
            {"building": "SCI", "code": "CL-3", "name": "Computing Lab 3", "floor": "2", "capacity": 30},
            {"building": "BSNSS", "code": "SR-1", "name": "Seminar Room 1", "floor": "1", "capacity": 60},
            {"building": "BSNSS", "code": "SR-2", "name": "Seminar Room 2", "floor": "2", "capacity": 50},
            {"building": "HALL", "code": "MPH", "name": "Multi-Purpose Hall", "floor": "G", "capacity": 500},
            {"building": "LIB", "code": "DR-1", "name": "Discussion Room 1", "floor": "1", "capacity": 10},
            {"building": "LIB", "code": "DR-2", "name": "Discussion Room 2", "floor": "1", "capacity": 8},
        ]
        for v in venues_data:
            admin_models.Venue.objects.update_or_create(
                code=v["code"],
                defaults={
                    "building": buildings[v["building"]],
                    "name": v["name"],
                    "floor": v["floor"],
                    "capacity": v["capacity"],
                    "is_active": True,
                },
            )

        rooms_data = [
            {"code": "R-101", "name": "Room 101", "building": "MAIN", "floor": "1", "capacity": 40},
            {"code": "R-102", "name": "Room 102", "building": "MAIN", "floor": "1", "capacity": 35},
            {"code": "R-201", "name": "Room 201", "building": "MAIN", "floor": "2", "capacity": 30},
            {"code": "R-202", "name": "Room 202", "building": "MAIN", "floor": "2", "capacity": 25},
            {"code": "SCI-LAB1", "name": "Science Lab 1", "building": "SCI", "floor": "1", "capacity": 30},
        ]
        for r in rooms_data:
            admin_models.Room.objects.update_or_create(
                code=r["code"],
                defaults={
                    "name": r["name"],
                    "campus": "Main Campus",
                    "building": r["building"],
                    "floor": r["floor"],
                    "capacity": r["capacity"],
                    "is_active": True,
                },
            )

        hostels_data = [
            {"code": "M-H1", "name": "Men's Hostel 1", "hostel_type": "male"},
            {"code": "M-H2", "name": "Men's Hostel 2", "hostel_type": "male"},
            {"code": "F-H1", "name": "Women's Hostel 1", "hostel_type": "female"},
            {"code": "F-H2", "name": "Women's Hostel 2", "hostel_type": "female"},
        ]
        for h in hostels_data:
            hostel, _ = admin_models.Hostel.objects.update_or_create(
                code=h["code"],
                defaults={"name": h["name"], "hostel_type": h["hostel_type"], "is_active": True},
            )
            for floor_num in range(1, 4):
                for room_num in range(1, 11):
                    number = f"{floor_num:02d}-{room_num:02d}"
                    admin_models.HostelRoom.objects.update_or_create(
                        hostel=hostel, floor=floor_num, number=number,
                        defaults={"capacity": 4, "is_active": True},
                    )

        self.stdout.write("  Buildings, venues, rooms, hostels seeded")

    def seed_students(self):
        student_data = [
            ("student1@aiu.edu.my", "Ahmad", "Bin Ibrahim", "SBSS", "SBSS-BBA", 2),
            ("student2@aiu.edu.my", "Siti", "Binti Abdullah", "SBSS", "SBSS-BBA", 2),
            ("student3@aiu.edu.my", "Muhammad", "Bin Ali", "SCI", "SCI-BCS", 2),
            ("student4@aiu.edu.my", "Nurul", "Ain Binti Hassan", "SCI", "SCI-BCS", 1),
            ("student5@aiu.edu.my", "Fatima", "Al-Zahra", "SEHS", "SEHS-BEE", 1),
            ("student6@aiu.edu.my", "Ali", "Bin Abu Bakar", "SBSS", "SBSS-BBAM", 3),
            ("student7@aiu.edu.my", "Zainab", "Binti Omar", "SBSS", "SBSS-BBAHRM", 3),
            ("student8@aiu.edu.my", "Hassan", "Bin Ismail", "SCI", "SCI-BDS", 1),
            ("student9@aiu.edu.my", "Aisha", "Binti Khalid", "SEHS", "SEHS-BECE", 2),
            ("student10@aiu.edu.my", "Ibrahim", "Bin Yusof", "SBSS", "SBSS-BFIN", 1),
            ("student11@aiu.edu.my", "Mariam", "Binti Saleh", "SCI", "SCI-BITC", 2),
            ("student12@aiu.edu.my", "Yusuf", "Bin Hassan", "SBSS", "SBSS-BSD", 1),
            ("student13@aiu.edu.my", "Khadijah", "Binti Rashid", "SEHS", "SEHS-BMC", 2),
            ("student14@aiu.edu.my", "Umar", "Bin Abdul Aziz", "SBSS", "SBSS-BECO", 3),
            ("student15@aiu.edu.my", "Sarah", "Binti Mahmud", "SCI", "SCI-BCS", 1),
        ]
        schools = {s.code: s for s in admin_models.School.objects.all()}
        programs = {p.code: p for p in admin_models.Program.objects.all()}
        profiles = []

        for email, first, last, school_code, prog_code, year in student_data:
            user = get_or_create_user(email, first, last)
            school = schools.get(school_code)
            program = programs.get(prog_code)
            profile = get_or_create_profile(user, "student", school=school, designation="Student")
            student_models.Student.objects.update_or_create(
                profile=profile,
                defaults={
                    "student_id": f"STU{user.pk:05d}",
                    "school": school,
                    "program": program,
                    "current_year": year,
                    "enrollment_status": "active",
                    "is_active": True,
                },
            )
            profiles.append(profile)

        self.stdout.write(f"  {len(student_data)} students seeded")
        return profiles

    def seed_librarians(self):
        data = [
            ("librarian1@aiu.edu.my", "Syuhada", "Binti Ali", "COR", "COR-ADMIN", "Chief Librarian"),
            ("librarian2@aiu.edu.my", "Nurul Izzati", "Binti Sabri", "COR", "COR-ADMIN", "Librarian"),
        ]
        centers = {c.code: c for c in admin_models.Center.objects.all()}
        units = {u.code: u for u in admin_models.Unit.objects.all()}
        for email, first, last, center_code, unit_code, designation in data:
            user = get_or_create_user(email, first, last)
            profile = get_or_create_profile(
                user, "librarian",
                center=centers.get(center_code),
                unit=units.get(unit_code),
                designation=designation,
            )
            librarian_models.Librarian.objects.update_or_create(
                profile=profile,
                defaults={
                    "librarian_id": f"LIB{user.pk:05d}",
                    "designation": designation,
                    "center": centers.get(center_code),
                    "unit": units.get(unit_code),
                    "is_active": True,
                },
            )
        self.stdout.write(f"  {len(data)} librarians seeded")

    def seed_technicians(self):
        data = [
            ("technician1@aiu.edu.my", "Ammar", "Ihsan", "ICT", "ICT-ADMIN", "Technology Operations Lead"),
            ("technician2@aiu.edu.my", "Anwar", "Feisal", "ICT", "ICT-ADMIN", "IT Technical Project Coordinator"),
        ]
        centers = {c.code: c for c in admin_models.Center.objects.all()}
        units = {u.code: u for u in admin_models.Unit.objects.all()}
        for email, first, last, center_code, unit_code, designation in data:
            user = get_or_create_user(email, first, last)
            profile = get_or_create_profile(
                user, "technician",
                center=centers.get(center_code),
                unit=units.get(unit_code),
                designation=designation,
            )
            technician_models.Technician.objects.update_or_create(
                profile=profile,
                defaults={
                    "technician_id": f"TEC{user.pk:05d}",
                    "designation": designation,
                    "center": centers.get(center_code),
                    "unit": units.get(unit_code),
                    "is_active": True,
                },
            )
        self.stdout.write(f"  {len(data)} technicians seeded")

    def seed_caterers(self):
        data = [
            ("caterer1@aiu.edu.my", "Razuan", "Bin Mahmud", "CSAA", "CTN-ADMIN", "Canteen Operator"),
            ("caterer2@aiu.edu.my", "Muhammad", "Faiz", "CSAA", "CTN-ADMIN", "Canteen Staff"),
        ]
        centers = {c.code: c for c in admin_models.Center.objects.all()}
        units = {u.code: u for u in admin_models.Unit.objects.all()}
        for email, first, last, center_code, unit_code, designation in data:
            user = get_or_create_user(email, first, last)
            profile = get_or_create_profile(
                user, "caterer",
                center=centers.get(center_code),
                unit=units.get(unit_code),
                designation=designation,
            )
            caterer_models.Caterer.objects.update_or_create(
                profile=profile,
                defaults={
                    "caterer_id": f"CAT{user.pk:05d}",
                    "designation": designation,
                    "center": centers.get(center_code),
                    "unit": units.get(unit_code),
                    "is_active": True,
                },
            )
        self.stdout.write(f"  {len(data)} caterers seeded")

    def seed_accountants(self):
        data = [
            ("accountant1@aiu.edu.my", "Chong", "Chew Lee", "FIN", "FIN-ADMIN", "Chief Financial Officer"),
        ]
        departments = {d.code: d for d in admin_models.Department.objects.all()}
        units = {u.code: u for u in admin_models.Unit.objects.all()}
        for email, first, last, dept_code, unit_code, designation in data:
            user = get_or_create_user(email, first, last)
            profile = get_or_create_profile(
                user, "accountant",
                department=departments.get(dept_code),
                unit=units.get(unit_code),
                designation=designation,
            )
            accountant_models.Accountant.objects.update_or_create(
                profile=profile,
                defaults={
                    "accountant_id": f"ACC{user.pk:05d}",
                    "designation": designation,
                    "department": departments.get(dept_code),
                    "unit": units.get(unit_code),
                    "is_active": True,
                },
            )
        self.stdout.write(f"  {len(data)} accountants seeded")

    def seed_applicants(self):
        data = [
            ("applicant1@gmail.com", "Amirul", "Syafiq"),
            ("applicant2@gmail.com", "Nur", "Aisyah"),
            ("applicant3@yahoo.com", "Muhammad", "Faris"),
        ]
        for email, first, last in data:
            user = get_or_create_user(email, first, last)
            profile = get_or_create_profile(user, "applicant", designation="Applicant")
            applicant_models.Applicant.objects.update_or_create(
                profile=profile,
                defaults={
                    "applicant_id": f"APP{user.pk:05d}",
                    "phone": f"012{random.randint(3000000, 9999999)}",
                    "nationality": "Malaysian",
                    "is_active": True,
                },
            )
        self.stdout.write(f"  {len(data)} applicants seeded")

    def seed_courses(self):
        courses_data = [
            ("CSC101", "Introduction to Programming", 4, "SCI", None, True),
            ("CSC102", "Data Structures", 4, "SCI", None, True),
            ("CSC201", "Web Systems", 3, "SCI", None, False),
            ("CSC202", "Database Systems", 3, "SCI", None, False),
            ("CSC301", "Software Engineering", 3, "SCI", None, False),
            ("MAT101", "Calculus I", 3, "SCI", None, False),
            ("MAT102", "Linear Algebra", 3, "SCI", None, False),
            ("ENG101", "Academic English", 3, "SEHS", None, False),
            ("ENG201", "Academic Writing", 2, "SEHS", None, False),
            ("BUS101", "Principles of Management", 3, "SBSS", None, False),
            ("BUS102", "Principles of Marketing", 3, "SBSS", None, False),
            ("BUS201", "Business Accounting", 3, "SBSS", None, False),
            ("BUS202", "Organizational Behaviour", 3, "SBSS", None, False),
            ("BUS301", "Strategic Management", 3, "SBSS", None, False),
            ("ECO101", "Microeconomics", 3, "SBSS", None, False),
            ("ECO102", "Macroeconomics", 3, "SBSS", None, False),
            ("EDU101", "Foundations of Education", 3, "SEHS", None, False),
            ("EDU201", "Educational Psychology", 3, "SEHS", None, False),
            ("FND001", "Foundation Mathematics", 3, None, "CFGS", False),
            ("FND002", "Foundation English", 3, None, "CFGS", False),
            ("FND003", "Introduction to Computing", 3, None, "CFGS", False),
        ]
        schools = {s.code: s for s in admin_models.School.objects.all()}
        centers = {c.code: c for c in admin_models.Center.objects.all()}
        courses = {}
        for code, title, credits, school_code, center_code, has_lab in courses_data:
            course, _ = admin_models.Course.objects.update_or_create(
                code=code,
                defaults={
                    "title": title,
                    "credits": credits,
                    "school": schools.get(school_code) if school_code else None,
                    "center": centers.get(center_code) if center_code else None,
                    "has_lab": has_lab,
                    "is_active": True,
                },
            )
            courses[code] = course

        courses["CSC102"].prerequisites.add(courses["CSC101"])
        courses["CSC201"].prerequisites.add(courses["CSC101"])
        courses["CSC202"].prerequisites.add(courses["CSC102"])
        courses["CSC301"].prerequisites.add(courses["CSC201"])
        courses["MAT102"].prerequisites.add(courses["MAT101"])
        courses["BUS201"].prerequisites.add(courses["BUS101"])
        courses["BUS202"].prerequisites.add(courses["BUS101"])
        courses["BUS301"].prerequisites.add(courses["BUS202"])
        courses["ENG201"].prerequisites.add(courses["ENG101"])
        courses["EDU201"].prerequisites.add(courses["EDU101"])

        self.stdout.write(f"  {len(courses_data)} courses seeded with prerequisites")
        return courses

    def seed_semesters(self):
        today = today_local()
        year = today.year
        semester_name = f"Semester 1 {year}/{year+1}"
        semester, _ = admin_models.Semester.objects.update_or_create(
            name=semester_name,
            defaults={
                "academic_session": f"{year}/{year+1}",
                "semester_type": "long",
                "calendar_group": "undergraduate",
                "start_date": date(year, 9, 1),
                "end_date": date(year + 1, 1, 31),
                "course_offering_opens_at": datetime(year, 7, 1, tzinfo=LOCAL_TZ),
                "course_offering_closes_at": datetime(year, 8, 15, tzinfo=LOCAL_TZ),
                "course_selection_closes_at": datetime(year, 9, 15, tzinfo=LOCAL_TZ),
                "mid_semester_break_starts_on": date(year, 10, 23),
                "mid_semester_break_ends_on": date(year, 10, 29),
                "revision_starts_on": date(year + 1, 1, 1),
                "revision_ends_on": date(year + 1, 1, 7),
                "examination_starts_on": date(year + 1, 1, 8),
                "examination_ends_on": date(year + 1, 1, 21),
                "max_credit_hours": 21,
                "is_active": True,
            },
        )

        holidays = [
            ("National Day", date(year, 8, 31), date(year, 8, 31)),
            ("Malaysia Day", date(year, 9, 16), date(year, 9, 16)),
            ("Deepavali", date(year, 10, 1), date(year, 10, 1)),
            ("Christmas", date(year, 12, 25), date(year, 12, 25)),
            ("New Year", date(year + 1, 1, 1), date(year + 1, 1, 1)),
        ]
        for name, start, end in holidays:
            admin_models.SemesterHoliday.objects.update_or_create(
                semester=semester, name=name, starts_on=start,
                defaults={"ends_on": end, "is_active": True},
            )

        self.stdout.write(f"  Semester '{semester_name}' seeded with holidays")
        return semester

    def seed_timetable_slots(self):
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        slots_data = []
        for day_idx, day_name in enumerate(day_names, 1):
            for hour in range(8, 17):
                start = time(hour, 0)
                end = time(hour + 1, 30) if hour < 16 else time(17, 0)
                slots_data.append((day_idx, start, end, f"{day_name.capitalize()} {hour}:00-{end.strftime('%H:%M')}"))

        for day, start, end, label in slots_data:
            executive_models.TimetableSlot.objects.update_or_create(
                day_of_week=day, start_time=start, end_time=end,
                defaults={"label": label},
            )
        self.stdout.write(f"  {len(slots_data)} timetable slots seeded")

    def seed_course_offerings(self, courses, semester):
        teachers = admin_models.Profile.objects.filter(role="teacher", is_active=True)
        venues = {v.code: v for v in admin_models.Venue.objects.all()}
        offerings = {}

        offering_data = [
            ("CSC101", "A", 60, teachers[0] if teachers else None),
            ("CSC102", "A", 50, teachers[1] if len(teachers) > 1 else None),
            ("CSC201", "A", 45, teachers[2] if len(teachers) > 2 else None),
            ("MAT101", "A", 60, teachers[3] if len(teachers) > 3 else None),
            ("ENG101", "A", 80, teachers[4] if len(teachers) > 4 else None),
            ("BUS101", "A", 60, teachers[5] if len(teachers) > 5 else None),
            ("BUS102", "A", 55, teachers[6] if len(teachers) > 6 else None),
            ("ECO101", "A", 50, teachers[7] if len(teachers) > 7 else None),
            ("EDU101", "A", 40, teachers[8] if len(teachers) > 8 else None),
            ("FND001", "A", 80, teachers[9] if len(teachers) > 9 else None),
        ]

        for course_code, section, capacity, instructor in offering_data:
            course = courses.get(course_code)
            if not course:
                continue
            offering, _ = admin_models.CourseOffering.objects.update_or_create(
                course=course, semester=semester, section=section,
                defaults={
                    "instructor": instructor,
                    "capacity": capacity,
                    "is_active": True,
                },
            )
            offerings[course_code] = offering

        self.stdout.write(f"  {len(offering_data)} course offerings seeded")
        return offerings

    def seed_tutorial_lab_groups(self, offerings):
        for code, offering in offerings.items():
            tg, _ = admin_models.CourseTutorialGroup.objects.update_or_create(
                offering=offering, code=f"{code}-T01",
                defaults={"capacity": 30, "is_active": True},
            )
            if offering.course.has_lab:
                admin_models.CourseLabGroup.objects.update_or_create(
                    tutorial_group=tg, code=f"{code}-L01",
                    defaults={"capacity": 20, "is_active": True},
                )
        self.stdout.write("  Tutorial/lab groups seeded")

    def seed_class_groups(self, semester):
        programs = admin_models.Program.objects.filter(is_active=True)[:3]
        for program in programs:
            admin_models.ClassGroup.objects.update_or_create(
                program=program, semester=semester, year=2025, cohort="A",
                defaults={"code": f"{program.code}-2025-A", "name": f"{program.name} Cohort A", "is_active": True},
            )
        self.stdout.write("  Class groups seeded")

    def seed_registration_periods(self, semester):
        now = timezone.now()
        periods_data = [
            ("Course Registration", "course_registration", now - timedelta(days=30), now + timedelta(days=7)),
            ("Add/Drop", "add_drop", now + timedelta(days=8), now + timedelta(days=21)),
        ]
        admin_profile = admin_models.Profile.objects.filter(role="admin").first()
        for title, phase, opens, closes in periods_data:
            student_models.RegistrationPeriod.objects.update_or_create(
                semester=semester, phase=phase,
                defaults={
                    "title": title,
                    "opens_at": opens,
                    "closes_at": closes,
                    "is_active": True,
                    "created_by": admin_profile,
                },
            )
        self.stdout.write("  Registration periods seeded")

    def seed_academic_events(self, semester):
        admin_profile = admin_models.Profile.objects.filter(role="admin").first()
        now = timezone.now()
        events_data = [
            ("Semester Opening Ceremony", "public", now - timedelta(days=14), now - timedelta(days=14, hours=-2)),
            ("Course Registration Opens", "registration", now - timedelta(days=30), now - timedelta(days=30)),
            ("Mid-Semester Break", "public", now + timedelta(days=30), now + timedelta(days=36)),
            ("Final Exam Period", "exam", now + timedelta(days=60), now + timedelta(days=73)),
        ]
        for title, etype, start, end in events_data:
            admin_models.AcademicEvent.objects.update_or_create(
                title=title, starts_at=start,
                defaults={
                    "event_type": etype,
                    "ends_at": end,
                    "semester": semester,
                    "created_by": admin_profile,
                },
            )
        self.stdout.write("  Academic events seeded")

    def seed_elections(self):
        schools = {s.code: s for s in admin_models.School.objects.all()}
        admin_profile = admin_models.Profile.objects.filter(role="admin").first()
        students = admin_models.Profile.objects.filter(role="student", is_active=True)

        src_election, _ = technician_models.Election.objects.update_or_create(
            title="SRC Election 2026",
            defaults={
                "description": "Student Representative Council Election",
                "election_type": "src",
                "general_selection_count": 5,
                "status": "draft",
                "is_active": False,
                "created_by": admin_profile,
            },
        )
        technician_models.ElectionCandidate.objects.update_or_create(
            election=src_election,
            student=students[0] if students else None,
            category="general",
            defaults={
                "display_name": students[0].user.get_full_name() if students else "Candidate 1",
                "status": "approved",
                "sort_order": 1,
            },
        )

        if schools.get("SBSS"):
            school_election, _ = technician_models.Election.objects.update_or_create(
                title="SBSS Committee Election 2026",
                defaults={
                    "description": "School of Business Committee Election",
                    "election_type": "school_committee",
                    "school": schools["SBSS"],
                    "school_selection_count": 3,
                    "status": "draft",
                    "is_active": False,
                    "created_by": admin_profile,
                },
            )
            technician_models.SchoolElectionSeat.objects.update_or_create(
                election=school_election, school=schools["SBSS"],
                defaults={"seat_count": 3},
            )
        self.stdout.write("  Elections seeded")

    def seed_library_data(self):
        shelves_data = [
            ("SH-A", "Shelf A - General", "Library Ground Floor"),
            ("SH-B", "Shelf B - Science", "Library Ground Floor"),
            ("SH-C", "Shelf C - Social Sciences", "Library First Floor"),
            ("SH-D", "Shelf D - Reference", "Library First Floor"),
            ("SH-E", "Shelf E - Fiction", "Library Second Floor"),
        ]
        shelves = {}
        for code, name, location in shelves_data:
            shelf, _ = librarian_models.Shelf.objects.update_or_create(
                code=code, defaults={"name": name, "location": location, "is_active": True},
            )
            shelves[code] = shelf

        books_data = [
            ("9780131103627", "The C Programming Language", "Kernighan & Ritchie", "Prentice Hall", "2nd", "Computer Science"),
            ("9780262033848", "Introduction to Algorithms", "Cormen et al.", "MIT Press", "3rd", "Computer Science"),
            ("9780135957059", "Database Systems: The Complete Book", "Ullman, Widom", "Pearson", "2nd", "Computer Science"),
            ("9781119366447", "Principles of Management", "Flaherty", "Wiley", "1st", "Business"),
            ("9780134630843", "Marketing Management", "Kotler & Keller", "Pearson", "15th", "Business"),
            ("9780078110913", "Economics", "McConnell & Brue", "McGraw-Hill", "20th", "Economics"),
            ("9780133573220", "Educational Psychology", "Woolfolk", "Pearson", "13th", "Education"),
            ("9780135160428", "Academic Writing for Success", "Oshima & Hogue", "Pearson", "4th", "English"),
            ("9780199264797", "Foundations of Education", "Ormrod", "Oxford", "1st", "Education"),
            ("9780262510875", "Structure and Interpretation of Computer Programs", "Sussman & Abelson", "MIT Press", "2nd", "Computer Science"),
        ]
        admin_profile = admin_models.Profile.objects.filter(role="admin").first()
        for isbn, title, author, publisher, edition, category in books_data:
            book, _ = librarian_models.Book.objects.update_or_create(
                isbn=isbn, title=title,
                defaults={
                    "author": author,
                    "publisher": publisher,
                    "edition": edition,
                    "category": category,
                    "is_active": True,
                    "created_by": admin_profile,
                },
            )
            for i in range(1, random.randint(2, 4)):
                acc_num = f"ACC-{book.pk:04d}-{i:02d}"
                shelf_key = random.choice(list(shelves.keys()))
                librarian_models.BookCopy.objects.update_or_create(
                    accession_number=acc_num,
                    defaults={
                        "book": book,
                        "shelf": shelves[shelf_key],
                        "status": "available",
                    },
                )

        laptops_data = [
            ("LAP001", "Dell", "Latitude 5420", "i5, 16GB RAM, 256GB SSD"),
            ("LAP002", "Dell", "Latitude 5420", "i5, 16GB RAM, 256GB SSD"),
            ("LAP003", "HP", "ProBook 450", "i5, 8GB RAM, 512GB SSD"),
            ("LAP004", "HP", "ProBook 450", "i5, 8GB RAM, 512GB SSD"),
            ("LAP005", "Lenovo", "ThinkPad X1", "i7, 16GB RAM, 512GB SSD"),
        ]
        for asset_tag, brand, model, specs in laptops_data:
            librarian_models.Laptop.objects.update_or_create(
                asset_tag=asset_tag,
                defaults={
                    "brand": brand, "model": model,
                    "specifications": specs,
                    "status": "available",
                    "storage_location": "Library IT Cabinet",
                },
            )

        room_data = [
            ("LR-DR1", "Discussion Room 1", "Library 1F", 6, 120),
            ("LR-DR2", "Discussion Room 2", "Library 1F", 8, 120),
            ("LR-SR", "Study Room", "Library 2F", 4, 180),
        ]
        for code, name, location, capacity, duration in room_data:
            librarian_models.LibraryRoom.objects.update_or_create(
                code=code,
                defaults={
                    "name": name, "location": location,
                    "capacity": capacity, "default_duration_minutes": duration,
                    "status": "available",
                },
            )

        self.stdout.write("  Library data seeded (books, shelves, laptops, rooms)")

    def seed_canteen_data(self, student_profiles):
        caterer_models.CanteenSetting.objects.update_or_create(
            pk=1,
            defaults={"monthly_allowance": Decimal("150.00")},
        )

        first_of_month = today_local().replace(day=1)
        for student in student_profiles:
            caterer_models.StudentCanteenAccount.objects.update_or_create(
                student=student, month=first_of_month,
                defaults={
                    "allowance_amount": Decimal("150.00"),
                    "spent_amount": Decimal("0.00"),
                },
            )

        self.stdout.write("  Canteen data seeded")

    def seed_ict_helpdesk(self, student_profiles):
        technicians = admin_models.Profile.objects.filter(role="technician", is_active=True)
        categories = ["hotspot_account", "email_password", "id_card", "printing_code", "moodle", "wifi"]

        for i, student in enumerate(student_profiles[:5]):
            cat = categories[i % len(categories)]
            ticket = technician_models.HelpdeskTicket.objects.create(
                student=student,
                assigned_to=technicians[i % len(technicians)] if technicians else None,
                category=cat,
                subject=f"Help with {cat.replace('_', ' ')} issue",
                description=f"Student reports an issue with {cat.replace('_', ' ')}. Needs technical assistance.",
                status="submitted",
                location=f"Hostel {random.choice(['A', 'B', 'C'])}",
            )
            if technicians:
                technician_models.HelpdeskTicketUpdate.objects.create(
                    ticket=ticket,
                    author=technicians[i % len(technicians)],
                    status="addressed",
                    note="Ticket acknowledged. Technician will follow up.",
                )

        self.stdout.write("  ICT helpdesk tickets seeded")

    def seed_venue_bookings(self, student_profiles):
        venues = admin_models.Venue.objects.all()[:5]
        statuses = ["pending", "approved", "rejected"]
        purposes = [
            "Student club meeting",
            "Study group session",
            "Event rehearsal",
            "Guest lecture preparation",
            "Class project presentation",
        ]

        for i, student in enumerate(student_profiles[:5]):
            venue = venues[i % len(venues)]
            admin_models.VenueBookingRequest.objects.create(
                requester=student,
                venue=venue,
                booking_type="event" if i % 2 == 0 else "personal",
                purpose=purposes[i % len(purposes)],
                explanation=f"Need the venue for {purposes[i % len(purposes)].lower()} on campus.",
                booking_date=today_local() + timedelta(days=random.randint(7, 30)),
                start_time=time(9, 0),
                end_time=time(11, 0),
                status=statuses[i % len(statuses)],
            )
        self.stdout.write("  Venue bookings seeded")

    def seed_leave_requests(self, student_profiles):
        teachers = admin_models.Profile.objects.filter(role="teacher", is_active=True)
        statuses = ["pending", "approved", "rejected"]
        reasons = [
            "Family emergency requiring immediate travel.",
            "Medical appointment and recovery.",
            "Personal leave for important family matter.",
            "Participating in university competition.",
            "Attending a conference.",
        ]

        for i, student in enumerate(student_profiles[:5]):
            lr = student_models.LeaveRequest.objects.create(
                student=student,
                start_date=today_local() + timedelta(days=random.randint(10, 20)),
                end_date=today_local() + timedelta(days=random.randint(21, 30)),
                reason=reasons[i % len(reasons)],
                status=statuses[i % len(statuses)],
                reviewed_by=teachers[i % len(teachers)] if teachers else None,
            )
            if teachers:
                student_models.LeaveApproval.objects.create(
                    leave_request=lr,
                    approver=teachers[i % len(teachers)],
                    approval_role="teacher",
                    status=statuses[i % len(statuses)],
                    note="Leave request reviewed.",
                )
        self.stdout.write("  Leave requests seeded")

    def seed_public_content(self):
        home_models.PublicPage.objects.update_or_create(
            slug="home",
            defaults={
                "section": "home",
                "title": "Welcome to AIU",
                "summary": "Albukhary International University",
                "body": "Welcome to AIU Unified Portal. This is the official portal for students, staff, and applicants.",
                "status": "published",
                "sort_order": 1,
            },
        )
        home_models.PublicPage.objects.update_or_create(
            slug="about-aiu",
            defaults={
                "section": "about",
                "title": "About AIU",
                "summary": "About Albukhary International University",
                "body": "AIU is a private international university in Malaysia founded on social business principles.",
                "status": "published",
                "sort_order": 1,
            },
        )

        home_models.PublicNews.objects.update_or_create(
            slug="welcome-new-students",
            defaults={
                "title": "Welcome New Students 2026!",
                "summary": "Orientation week begins in September",
                "body": "We welcome all new students to the 2026/2027 academic year.",
                "status": "published",
            },
        )

        home_models.PublicEvent.objects.update_or_create(
            slug="orientation-week-2026",
            defaults={
                "title": "Orientation Week 2026",
                "description": "Welcome event for new students",
                "starts_at": datetime(today_local().year, 9, 1, 8, 0, tzinfo=LOCAL_TZ),
                "ends_at": datetime(today_local().year, 9, 5, 17, 0, tzinfo=LOCAL_TZ),
                "status": "published",
            },
        )

        home_models.PublicAnnouncement.objects.update_or_create(
            title="System Maintenance Notice",
            defaults={
                "body": "The portal will undergo scheduled maintenance on Sunday.",
                "audience": "public",
                "is_published": True,
            },
        )

        links_data = [
            ("Student Portal", "https://portal.aiu.edu.my", "student", "Academic"),
            ("Library Portal", "https://library.aiu.edu.my", "student", "Academic"),
            ("Staff Email", "https://mail.aiu.edu.my", "teacher", "Communication"),
        ]
        for title, url, audience, category in links_data:
            home_models.OfficialLink.objects.update_or_create(
                title=title, defaults={"url": url, "audience": audience, "category": category, "is_active": True},
            )

        home_models.PublicDirectoryEntry.objects.update_or_create(
            entry_type="school", code="SBSS",
            defaults={"name": "School of Business and Social Sciences", "is_active": True},
        )

        self.stdout.write("  Public content seeded")

    def seed_system_settings(self):
        settings_data = [
            ("ums.site_name", "AIU Unified Portal", "Site display name", True),
            ("ums.site_description", "Albukhary International University Portal", "Site description", True),
            ("ums.enable_venue_booking", True, "Enable venue booking feature", False),
            ("ums.enable_canteen", True, "Enable canteen feature", False),
            ("ums.enable_library", True, "Enable library feature", False),
            ("ums.enable_ict_helpdesk", True, "Enable ICT helpdesk feature", False),
            ("ums.enable_hostel", True, "Enable hostel feature", False),
            ("ums.enable_elections", True, "Enable elections feature", False),
        ]
        for key, value, description, is_public in settings_data:
            admin_models.SystemSetting.objects.update_or_create(
                key=key,
                defaults={"value": value, "description": description, "is_public": is_public},
            )
        self.stdout.write("  System settings seeded")

    def seed_notifications(self, student_profiles):
        admin_profile = admin_models.Profile.objects.filter(role="admin").first()
        for student in student_profiles[:5]:
            Notification.objects.create(
                recipient=student,
                actor=admin_profile,
                verb="Welcome to the AIU Portal! Please complete your profile.",
                data={"type": "welcome"},
            )
        self.stdout.write("  Notifications seeded")

    def seed_assignments(self, offerings, student_profiles):
        teachers = admin_models.Profile.objects.filter(role="teacher", is_active=True)
        now = timezone.now()
        assignment_titles = [
            "Individual Assignment 1: Research Paper",
            "Lab Report: Practical Exercise",
            "Group Project: Case Study Analysis",
            "Quiz 1: Topic Review",
            "Final Project: Implementation & Report",
        ]

        for offering_code, offering in list(offerings.items())[:5]:
            teacher = offering.instructor or (teachers[0] if teachers else None)
            title = assignment_titles[list(offerings.keys()).index(offering_code) % len(assignment_titles)]
            assignment = teacher_models.Assignment.objects.create(
                offering=offering,
                activity_kind="assignment",
                collaboration_mode="individual",
                title=f"{offering.course.code} - {title}",
                description=f"Complete this assignment for {offering.course.title}",
                instructions="Follow the instructions carefully and submit before the deadline.",
                opens_at=now - timedelta(days=14),
                due_date=now + timedelta(days=7),
                max_score=100,
                submission_type="file",
                max_files=1,
                max_file_size_mb=10,
                status="published",
                created_by=teacher,
            )

            teacher_models.AssignmentRubric.objects.create(
                assignment=assignment,
                title="Standard Rubric",
                criteria=[
                    {"criterion": "Content Quality", "max_score": 40, "weight": 40},
                    {"criterion": "Organization", "max_score": 20, "weight": 20},
                    {"criterion": "References", "max_score": 20, "weight": 20},
                    {"criterion": "Presentation", "max_score": 20, "weight": 20},
                ],
                max_score=100,
                is_active=True,
                created_by=teacher,
            )

            for student in student_profiles[:3]:
                teacher_models.AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=student,
                    content=f"Submission by {student.user.get_full_name()}",
                    status="submitted",
                )

        self.stdout.write("  Assignments, rubrics, and submissions seeded")

    def seed_course_sections_resources(self, offerings):
        for offering_code, offering in list(offerings.items())[:5]:
            for week in range(1, 8):
                section = teacher_models.CourseSection.objects.create(
                    offering=offering,
                    title=f"Week {week}: {offering.course.title} - Topic {week}",
                    summary=f"Materials for week {week}",
                    section_type="topic" if week % 2 == 0 else "outline",
                    week_number=week,
                    sort_order=week,
                    is_published=True,
                )
                teacher_models.CourseResource.objects.create(
                    offering=offering,
                    section=section,
                    resource_type="file",
                    title=f"Lecture Notes Week {week}",
                    description=f"Slides and notes for week {week}",
                    visible_from=timezone.now() - timedelta(days=30),
                    sort_order=1,
                    is_published=True,
                    created_by=offering.instructor,
                )
        self.stdout.write("  Course sections and resources seeded")

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from admin_app.models import AcademicEvent, Profile


LOCAL_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def week_start(today):
    return today - timedelta(days=today.weekday())


def event_datetime(day, clock):
    hour, minute = [int(part) for part in clock.split(":")]
    local_value = datetime.combine(day, time(hour, minute), tzinfo=LOCAL_TZ)
    return local_value.astimezone(timezone.get_current_timezone())


def profile_for_role(role):
    return Profile.objects.filter(role=role, is_active=True).first()


class Command(BaseCommand):
    help = "Seed sample schedule events for teacher and student dashboards."

    def handle(self, *args, **options):
        today = timezone.localdate()
        monday = week_start(today)
        created_by = {
            "student": profile_for_role(Profile.ROLE_STUDENT),
            "teacher": profile_for_role(Profile.ROLE_TEACHER),
        }

        samples = [
            {
                "slug": "teacher-weekly-planning-sync",
                "role": "teacher",
                "title": "Weekly Planning Sync",
                "description": "Early planning block used to verify the weekly scheduler grid",
                "location": "Academic Office",
                "category": "meeting",
                "variant": "warning",
                "day_offset": 0,
                "start": "03:15",
                "end": "04:00",
            },
            {
                "slug": "teacher-web-systems",
                "role": "teacher",
                "title": "Teach Web Systems",
                "description": "CSC 201 lecture block",
                "location": "Lecture Hall B",
                "category": "class",
                "variant": "primary",
                "day_offset": 0,
                "start": "09:00",
                "end": "10:30",
            },
            {
                "slug": "teacher-consultation",
                "role": "teacher",
                "title": "Student Consultations",
                "description": "Open office hour for project teams",
                "location": "Faculty Office 4.08",
                "category": "office-hours",
                "variant": "success",
                "day_offset": 1,
                "start": "11:00",
                "end": "12:00",
            },
            {
                "slug": "teacher-lab-supervision",
                "role": "teacher",
                "title": "Supervise App Lab",
                "description": "CSC 302 practical supervision",
                "location": "Computing Lab 1",
                "category": "lab",
                "variant": "default",
                "day_offset": 2,
                "start": "14:00",
                "end": "16:00",
            },
            {
                "slug": "teacher-curriculum-planning",
                "role": "teacher",
                "title": "Curriculum Planning",
                "description": "Review next week's teaching plan",
                "location": "Academic Office",
                "category": "meeting",
                "variant": "warning",
                "day_offset": 3,
                "start": "09:30",
                "end": "10:30",
            },
            {
                "slug": "teacher-results-review",
                "role": "teacher",
                "title": "Results Review",
                "description": "Draft marks moderation",
                "location": "Academic Office",
                "category": "meeting",
                "variant": "warning",
                "day_offset": 3,
                "start": "13:30",
                "end": "14:30",
            },
            {
                "slug": "teacher-feedback-due",
                "role": "teacher",
                "title": "Assignment Feedback Due",
                "description": "Return CSC 201 feedback",
                "location": "Learning portal",
                "category": "assessment",
                "variant": "danger",
                "day_offset": 4,
                "start": "16:00",
                "end": "16:30",
            },
            {
                "slug": "student-weekly-study-briefing",
                "role": "student",
                "title": "Weekly Study Briefing",
                "description": "Early study block used to verify the weekly scheduler grid",
                "location": "Learning Commons",
                "category": "meeting",
                "variant": "warning",
                "day_offset": 1,
                "start": "03:30",
                "end": "04:15",
            },
            {
                "slug": "student-web-systems",
                "role": "student",
                "title": "Web Systems Lecture",
                "description": "CSC 201 with Dr. Farah",
                "location": "Lecture Hall B",
                "category": "class",
                "variant": "primary",
                "day_offset": 0,
                "start": "09:00",
                "end": "10:30",
            },
            {
                "slug": "student-quant-methods",
                "role": "student",
                "title": "Quantitative Methods Lab",
                "description": "MAT 120 applied lab",
                "location": "Computing Lab 3",
                "category": "lab",
                "variant": "success",
                "day_offset": 1,
                "start": "14:00",
                "end": "16:00",
            },
            {
                "slug": "student-writing",
                "role": "student",
                "title": "Academic Writing Tutorial",
                "description": "ENG 210 small group session",
                "location": "Room 2.15",
                "category": "class",
                "variant": "default",
                "day_offset": 2,
                "start": "11:00",
                "end": "12:30",
            },
            {
                "slug": "student-advisor",
                "role": "student",
                "title": "Advisor Check-in",
                "description": "Semester progress review",
                "location": "Student Affairs Office",
                "category": "meeting",
                "variant": "warning",
                "day_offset": 3,
                "start": "10:00",
                "end": "10:45",
            },
            {
                "slug": "student-database-lab",
                "role": "student",
                "title": "Database Systems Lab",
                "description": "SQL schema design workshop",
                "location": "Computing Lab 2",
                "category": "lab",
                "variant": "success",
                "day_offset": 3,
                "start": "13:00",
                "end": "15:00",
            },
            {
                "slug": "student-project-brief",
                "role": "student",
                "title": "Project Brief Due",
                "description": "Submit CSC 201 proposal",
                "location": "Learning portal",
                "category": "assessment",
                "variant": "danger",
                "day_offset": 4,
                "start": "15:00",
                "end": "15:30",
            },
        ]

        created = 0
        updated = 0

        for week_offset, sample_group in ((0, "current"), (1, "weekly")):
            week_monday = monday + timedelta(days=week_offset * 7)

            for sample in samples:
                sample_key = (
                    sample["slug"]
                    if week_offset == 0
                    else f"{sample['slug']}-weekly-view"
                )
                event_day = week_monday + timedelta(days=sample["day_offset"])
                starts_at = event_datetime(event_day, sample["start"])
                ends_at = event_datetime(event_day, sample["end"])
                metadata = {
                    "sample_key": sample_key,
                    "schedule_sample": True,
                    "schedule_sample_group": sample_group,
                    "schedule_audiences": [sample["role"]],
                    "location": sample["location"],
                    "category": sample["category"],
                    "variant": sample["variant"],
                }

                _event, was_created = AcademicEvent.objects.update_or_create(
                    metadata__sample_key=sample_key,
                    defaults={
                        "title": sample["title"],
                        "description": sample["description"],
                        "event_type": AcademicEvent.TYPE_CLASS
                        if sample["category"] in {"class", "lab", "office-hours"}
                        else AcademicEvent.TYPE_PUBLIC,
                        "starts_at": starts_at,
                        "ends_at": ends_at,
                        "all_day": False,
                        "metadata": metadata,
                        "created_by": created_by.get(sample["role"]),
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded schedule samples from {monday.isoformat()} "
                f"through {(monday + timedelta(days=11)).isoformat()}: "
                f"{created} created, {updated} updated."
            )
        )

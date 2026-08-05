from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from home_app import models as home_models


LOCAL_TZ = ZoneInfo("Asia/Kuala_Lumpur")


class Command(BaseCommand):
    help = "Seed opt-in AIU demo public website content."

    @transaction.atomic
    def handle(self, *args, **options):
        pages = [
            {
                "slug": "home",
                "route_path": "/",
                "section": home_models.PublicPage.SECTION_HOME,
                "title": "Welcome to AIU",
                "summary": "Albukhary International University",
                "body": (
                    "Welcome to the AIU Unified Portal demo. Replace this demo "
                    "homepage with your institution's public content before use."
                ),
                "sort_order": 0,
            },
            {
                "slug": "about-aiu",
                "route_path": "/about",
                "section": home_models.PublicPage.SECTION_ABOUT,
                "title": "About AIU",
                "summary": "About Albukhary International University",
                "body": (
                    "AIU is represented here as an opt-in demo content pack for "
                    "testing the public CMS and portal workflows."
                ),
                "sort_order": 10,
            },
            {
                "slug": "aiu-programmes",
                "route_path": "/programmes",
                "section": home_models.PublicPage.SECTION_ACADEMICS,
                "title": "AIU Programmes",
                "summary": "Demo academic programme overview.",
                "body": "Demo overview for schools, centres, and programmes.",
                "sort_order": 30,
            },
            {
                "slug": "aiu-student-life",
                "route_path": "/student-life",
                "section": home_models.PublicPage.SECTION_STUDENT_LIFE,
                "title": "Student Life at AIU",
                "summary": "Demo student life page.",
                "body": "Demo student life content for local testing.",
                "sort_order": 70,
            },
        ]
        for page in pages:
            metadata = {
                "demo_pack": "aiu",
                "navigation": {
                    "show": True,
                    "label": page["title"],
                    "order": page["sort_order"],
                },
            }
            home_models.PublicPage.objects.update_or_create(
                slug=page["slug"],
                defaults={
                    **page,
                    "metadata": metadata,
                    "status": home_models.PublicPage.STATUS_PUBLISHED,
                    "published_at": timezone.now(),
                },
            )

        home_models.PublicNews.objects.update_or_create(
            slug="aiu-demo-welcome",
            defaults={
                "title": "Welcome New Students",
                "summary": "Demo orientation news for the AIU content pack.",
                "body": "This is opt-in AIU demo news content for local testing.",
                "status": home_models.PublicNews.STATUS_PUBLISHED,
                "published_at": timezone.now(),
            },
        )
        home_models.PublicEvent.objects.update_or_create(
            slug="aiu-demo-orientation-week",
            defaults={
                "title": "Orientation Week",
                "description": "Demo orientation event for the AIU content pack.",
                "starts_at": datetime(timezone.localdate().year, 9, 1, 8, 0, tzinfo=LOCAL_TZ),
                "ends_at": datetime(timezone.localdate().year, 9, 5, 17, 0, tzinfo=LOCAL_TZ),
                "location": "AIU Main Campus",
                "status": home_models.PublicEvent.STATUS_PUBLISHED,
            },
        )
        home_models.PublicAnnouncement.objects.update_or_create(
            title="AIU Demo Maintenance Notice",
            defaults={
                "body": "This is an opt-in AIU demo announcement.",
                "audience": home_models.PublicAnnouncement.AUDIENCE_PUBLIC,
                "is_published": True,
            },
        )

        links = [
            ("AIU Student Portal", "https://portal.aiu.edu.my", "student", "Academic"),
            ("AIU Library Portal", "https://library.aiu.edu.my", "student", "Academic"),
            ("AIU Staff Email", "https://mail.aiu.edu.my", "teacher", "Communication"),
        ]
        for sort_order, (title, url, audience, category) in enumerate(links, start=10):
            home_models.OfficialLink.objects.update_or_create(
                title=title,
                defaults={
                    "url": url,
                    "audience": audience,
                    "category": category,
                    "description": "AIU demo link. Replace before production use.",
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Seeded AIU demo public content."))

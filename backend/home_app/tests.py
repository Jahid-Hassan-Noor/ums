from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from home_app import models
from home_app.serializers import PublicNewsSerializer


class PublicContentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            username="content_admin",
            email="content-admin@example.com",
            password="password",
        )

    def authenticate_admin(self):
        self.client.force_authenticate(user=self.admin)

    def test_admin_page_publication_controls_public_page_endpoint(self):
        self.authenticate_admin()
        response = self.client.post(
            "/admin/public-content",
            {
                "title": "About From Database",
                "slug": "about-from-database",
                "route_path": "/about",
                "section": models.PublicPage.SECTION_ABOUT,
                "summary": "Admin-managed about summary.",
                "body": "Admin-managed body.",
                "metadata": {"eyebrow": "Managed"},
                "status": models.PublicPage.STATUS_PUBLISHED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        public_response = self.client.get("/about")

        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(public_response.data["page"]["title"], "About From Database")
        self.assertEqual(public_response.data["page"]["route_path"], "/about")

    def test_public_page_navigation_lists_only_current_published_pages(self):
        visible = models.PublicPage.objects.create(
            title="Visible About",
            slug="visible-about",
            route_path="/about",
            section=models.PublicPage.SECTION_ABOUT,
            metadata={"navigation": {"label": "About", "show": True}},
            status=models.PublicPage.STATUS_PUBLISHED,
            sort_order=2,
            published_at=timezone.now(),
        )
        models.PublicPage.objects.create(
            title="Draft Admissions",
            slug="draft-admissions",
            route_path="/admissions",
            section=models.PublicPage.SECTION_ADMISSIONS,
            status=models.PublicPage.STATUS_DRAFT,
            sort_order=1,
        )
        models.PublicPage.objects.create(
            title="Future News",
            slug="future-news",
            route_path="/news",
            section=models.PublicPage.SECTION_HOME,
            status=models.PublicPage.STATUS_PUBLISHED,
            published_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get("/pages/navigation")

        self.assertEqual(response.status_code, 200)
        titles = [page["title"] for page in response.data["pages"]]
        self.assertEqual(titles, [visible.title])
        self.assertEqual(response.data["pages"][0]["metadata"]["navigation"]["label"], "About")

    def test_public_news_only_returns_published_records_and_detail(self):
        draft = models.PublicNews.objects.create(
            title="Draft News",
            slug="draft-news",
            status=models.PublicNews.STATUS_DRAFT,
        )
        published = models.PublicNews.objects.create(
            title="Published News",
            slug="published-news",
            summary="Visible summary.",
            body="Visible body.",
            status=models.PublicNews.STATUS_PUBLISHED,
            published_at=timezone.now(),
        )

        list_response = self.client.get("/news")

        self.assertEqual(list_response.status_code, 200)
        titles = [item["title"] for item in list_response.data["news"]]
        self.assertIn(published.title, titles)
        self.assertNotIn(draft.title, titles)

        detail_response = self.client.get("/news/published-news")

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["news"]["body"], "Visible body.")

    def test_public_news_image_rejects_unsupported_or_invalid_images(self):
        serializer = PublicNewsSerializer(
            data={
                "title": "Unsafe Image",
                "slug": "unsafe-image",
                "status": models.PublicNews.STATUS_DRAFT,
                "image": SimpleUploadedFile(
                    "unsafe.svg",
                    b"<svg><script>alert(1)</script></svg>",
                    content_type="image/svg+xml",
                ),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("Allowed image types", str(serializer.errors["image"]))

    def test_public_official_links_are_admin_controlled_and_filtered(self):
        models.OfficialLink.objects.create(
            title="Public Link",
            url="https://example.com/public",
            audience=models.OfficialLink.AUDIENCE_PUBLIC,
            is_active=True,
        )
        models.OfficialLink.objects.create(
            title="Student Link",
            url="https://example.com/student",
            audience=models.OfficialLink.AUDIENCE_STUDENT,
            is_active=True,
        )
        models.OfficialLink.objects.create(
            title="Inactive Link",
            url="https://example.com/inactive",
            audience=models.OfficialLink.AUDIENCE_PUBLIC,
            is_active=False,
        )

        response = self.client.get("/official-links")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data["official_links"]]
        self.assertEqual(titles, ["Public Link"])

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import models
from django.utils import timezone


class SearchDocument(models.Model):
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_AUTHENTICATED = "authenticated"
    VISIBILITY_ROLE_BASED = "role-based"
    VISIBILITY_OWNER_ONLY = "owner-only"
    VISIBILITY_COURSE_MEMBER = "course-member"
    VISIBILITY_TEACHER_ASSIGNED = "teacher-assigned"
    VISIBILITY_EXECUTIVE_SCOPE = "executive-scope"
    VISIBILITY_STAFF_SCOPE = "staff-scope"
    VISIBILITY_ADMIN_ONLY = "admin-only"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_AUTHENTICATED, "Authenticated"),
        (VISIBILITY_ROLE_BASED, "Role based"),
        (VISIBILITY_OWNER_ONLY, "Owner only"),
        (VISIBILITY_COURSE_MEMBER, "Course member"),
        (VISIBILITY_TEACHER_ASSIGNED, "Teacher assigned"),
        (VISIBILITY_EXECUTIVE_SCOPE, "Executive scope"),
        (VISIBILITY_STAFF_SCOPE, "Staff scope"),
        (VISIBILITY_ADMIN_ONLY, "Admin only"),
    ]

    source_key = models.CharField(max_length=255, unique=True)
    source_app_label = models.CharField(max_length=80, blank=True)
    source_model = models.CharField(max_length=80, blank=True)
    source_object_id = models.CharField(max_length=80, blank=True)

    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    source_label = models.CharField(max_length=255, blank=True)
    source_url = models.CharField(max_length=500, blank=True)
    domain = models.CharField(max_length=80, db_index=True)
    document_type = models.CharField(max_length=80, db_index=True)
    icon = models.CharField(max_length=80, blank=True)
    breadcrumbs = models.JSONField(default=list, blank=True)

    visibility = models.CharField(
        max_length=30,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        db_index=True,
    )
    allowed_roles = models.JSONField(default=list, blank=True)
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="owned_search_documents",
    )
    course_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    course_offering_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    semester_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    school_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    center_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    department_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    unit_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    program_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    scope_metadata = models.JSONField(default=dict, blank=True)
    safe_metadata = models.JSONField(default=dict, blank=True)

    content_hash = models.CharField(max_length=64, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    last_indexed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain", "document_type", "title")
        indexes = [
            models.Index(fields=("is_active", "visibility")),
            models.Index(fields=("domain", "document_type", "is_active")),
            models.Index(fields=("source_app_label", "source_model", "source_object_id")),
            models.Index(fields=("owner_user", "is_active")),
            models.Index(fields=("course_id", "is_active")),
            models.Index(fields=("course_offering_id", "is_active")),
            models.Index(fields=("semester_id", "is_active")),
            models.Index(fields=("school_id", "is_active")),
            models.Index(fields=("center_id", "is_active")),
            models.Index(fields=("department_id", "is_active")),
            models.Index(fields=("unit_id", "is_active")),
            models.Index(fields=("program_id", "is_active")),
            models.Index(fields=("title",)),
            models.Index(fields=("-last_indexed_at",)),
            GinIndex(
                SearchVector("title", "summary", "keywords", "body", config="english"),
                name="chatbot_search_fts_gin",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.domain}/{self.document_type})"

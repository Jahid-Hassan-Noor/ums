from django.db import models


class PublicPage(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    SECTION_HOME = "home"
    SECTION_ABOUT = "about"
    SECTION_ADMISSIONS = "admissions"
    SECTION_ACADEMICS = "academics"
    SECTION_SERVICES = "services"
    SECTION_STUDENT_LIFE = "student_life"
    SECTION_UMS = "portal"
    SECTION_CHOICES = [
        (SECTION_HOME, "Home"),
        (SECTION_ABOUT, "About"),
        (SECTION_ADMISSIONS, "Admissions"),
        (SECTION_ACADEMICS, "Academics"),
        (SECTION_SERVICES, "Services"),
        (SECTION_STUDENT_LIFE, "Student Life"),
        (SECTION_UMS, "Portal"),
    ]

    section = models.CharField(max_length=40, choices=SECTION_CHOICES, default=SECTION_HOME)
    slug = models.SlugField(max_length=120, unique=True)
    route_path = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    metadata = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    sort_order = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("section", "sort_order", "title")

    def __str__(self):
        return self.title


class PublicAnnouncement(models.Model):
    AUDIENCE_PUBLIC = "public"
    AUDIENCE_AUTHENTICATED = "authenticated"
    AUDIENCE_STUDENTS = "students"
    AUDIENCE_TEACHERS = "teachers"
    AUDIENCE_EXECUTIVES = "executives"
    AUDIENCE_ADMINS = "admins"
    AUDIENCE_CHOICES = [
        (AUDIENCE_PUBLIC, "Public"),
        (AUDIENCE_AUTHENTICATED, "Authenticated"),
        (AUDIENCE_STUDENTS, "Students"),
        (AUDIENCE_TEACHERS, "Teachers"),
        (AUDIENCE_EXECUTIVES, "Executives"),
        (AUDIENCE_ADMINS, "Admins"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default=AUDIENCE_PUBLIC)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_pinned", "-starts_at", "-created_at")

    def __str__(self):
        return self.title


class PublicNews(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=140, unique=True)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    image = models.FileField(upload_to="public/news/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    author = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self):
        return self.title


class PublicEvent(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("starts_at",)

    def __str__(self):
        return self.title


class OfficialLink(models.Model):
    AUDIENCE_PUBLIC = "public"
    AUDIENCE_STUDENT = "student"
    AUDIENCE_TEACHER = "teacher"
    AUDIENCE_EXECUTIVE = "executive"
    AUDIENCE_ADMIN = "admin"
    AUDIENCE_CHOICES = [
        (AUDIENCE_PUBLIC, "Public"),
        (AUDIENCE_STUDENT, "Student"),
        (AUDIENCE_TEACHER, "Teacher"),
        (AUDIENCE_EXECUTIVE, "Executive"),
        (AUDIENCE_ADMIN, "Admin"),
    ]

    title = models.CharField(max_length=255)
    url = models.URLField()
    category = models.CharField(max_length=100, blank=True)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_PUBLIC)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("category", "sort_order", "title")

    def __str__(self):
        return self.title


class PublicDirectoryEntry(models.Model):
    TYPE_SCHOOL = "school"
    TYPE_CENTER = "center"
    TYPE_DEPARTMENT = "department"
    TYPE_UNIT = "unit"
    TYPE_PROGRAM = "program"
    TYPE_SERVICE = "service"
    TYPE_CHOICES = [
        (TYPE_SCHOOL, "School"),
        (TYPE_CENTER, "Center"),
        (TYPE_DEPARTMENT, "Department"),
        (TYPE_UNIT, "Unit"),
        (TYPE_PROGRAM, "Program"),
        (TYPE_SERVICE, "Service"),
    ]

    entry_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    code = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("entry_type", "sort_order", "name")

    def __str__(self):
        return self.name


class PublicInquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    assigned_to = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.subject

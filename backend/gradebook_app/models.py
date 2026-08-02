from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class GradebookScale(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gradebook_scales",
    )
    updated_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_gradebook_scales",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_default", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("is_default",),
                condition=Q(is_default=True),
                name="one_default_gradebook_scale",
            )
        ]

    def __str__(self):
        return self.name


class GradebookScaleRange(models.Model):
    scale = models.ForeignKey(GradebookScale, on_delete=models.CASCADE, related_name="ranges")
    letter = models.CharField(max_length=20)
    min_score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    grade_points = models.DecimalField(max_digits=5, decimal_places=2)
    outcome = models.CharField(max_length=120, blank=True)
    is_passing = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("scale", "-min_score", "sort_order")
        unique_together = ("scale", "letter")

    def clean(self):
        if self.min_score < 0 or self.max_score > 100:
            raise ValidationError("Grade scale ranges must stay between 0 and 100.")
        if self.min_score > self.max_score:
            raise ValidationError("Minimum score must be less than or equal to maximum score.")

    def __str__(self):
        return f"{self.scale}: {self.letter}"


class GradebookCategory(models.Model):
    offering = models.ForeignKey(
        "admin_app.CourseOffering",
        on_delete=models.CASCADE,
        related_name="gradebook_categories",
    )
    title = models.CharField(max_length=120)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    drop_lowest = models.PositiveSmallIntegerField(default=0)
    release_to_students = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gradebook_categories",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "title")
        unique_together = ("offering", "title")

    def clean(self):
        if self.weight < 0 or self.weight > 100:
            raise ValidationError({"weight": "Category weight must be between 0 and 100."})

    def __str__(self):
        return f"{self.offering} - {self.title}"


class GradebookItem(models.Model):
    TYPE_ASSIGNMENT = "assignment"
    TYPE_QUIZ = "quiz"
    TYPE_ATTENDANCE = "attendance"
    TYPE_MANUAL = "manual"
    TYPE_EXTERNAL = "external"
    TYPE_CHOICES = [
        (TYPE_ASSIGNMENT, "Assignment"),
        (TYPE_QUIZ, "Quiz"),
        (TYPE_ATTENDANCE, "Attendance"),
        (TYPE_MANUAL, "Manual"),
        (TYPE_EXTERNAL, "External tool"),
    ]

    offering = models.ForeignKey(
        "admin_app.CourseOffering",
        on_delete=models.CASCADE,
        related_name="gradebook_items",
    )
    category = models.ForeignKey(
        GradebookCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    scale = models.ForeignKey(
        GradebookScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    title = models.CharField(max_length=255)
    item_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_MANUAL)
    source_app = models.CharField(max_length=80, blank=True)
    source_model = models.CharField(max_length=80, blank=True)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    due_at = models.DateTimeField(null=True, blank=True)
    release_to_students = models.BooleanField(default=False)
    is_extra_credit = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gradebook_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("category__sort_order", "sort_order", "due_at", "title")
        constraints = [
            models.UniqueConstraint(
                fields=("source_app", "source_model", "source_id"),
                condition=Q(source_id__isnull=False),
                name="unique_gradebook_source_item",
            )
        ]

    def clean(self):
        if self.max_score <= 0:
            raise ValidationError({"max_score": "Maximum score must be greater than zero."})
        if self.weight < 0 or self.weight > 100:
            raise ValidationError({"weight": "Item weight must be between 0 and 100."})
        if self.category_id and self.category.offering_id != self.offering_id:
            raise ValidationError({"category": "Category must belong to the same course offering."})

    def __str__(self):
        return f"{self.offering} - {self.title}"


class GradebookGrade(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_RELEASED = "released"
    STATUS_MISSING = "missing"
    STATUS_EXCUSED = "excused"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_RELEASED, "Released"),
        (STATUS_MISSING, "Missing"),
        (STATUS_EXCUSED, "Excused"),
    ]

    item = models.ForeignKey(GradebookItem, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="gradebook_grades",
    )
    raw_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_override = models.BooleanField(default=False)
    source_attempt = models.CharField(max_length=120, blank=True)
    graded_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_gradebook_grades",
    )
    overridden_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="overridden_gradebook_grades",
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("item", "student__student_detail__student_id", "student__user__first_name")
        unique_together = ("item", "student")

    def clean(self):
        if self.raw_score is not None and self.raw_score < 0:
            raise ValidationError({"raw_score": "Score cannot be negative."})
        if self.raw_score is not None and self.item_id and self.raw_score > self.item.max_score:
            raise ValidationError({"raw_score": "Score cannot exceed the grade item maximum."})

    def __str__(self):
        return f"{self.item_id} - {self.student_id}"


class GradebookGradeHistory(models.Model):
    grade = models.ForeignKey(GradebookGrade, on_delete=models.CASCADE, related_name="history")
    previous_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    new_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gradebook_grade_changes",
    )
    source = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Grade history {self.grade_id}"

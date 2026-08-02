from django.core.exceptions import ValidationError
from django.db import models


class Executive(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="executive_detail",
    )
    executive_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    office_location = models.CharField(max_length=255, blank=True)
    responsibility_area = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.executive_id

    @staff_id.setter
    def staff_id(self, value):
        self.executive_id = value


class ExecutiveUnitAssignment(models.Model):
    executive = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="executive_unit_assignments")
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    program = models.ForeignKey("admin_app.Program", on_delete=models.SET_NULL, null=True, blank=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Executive assignment {self.executive_id}"

    def clean(self):
        if bool(self.school_id) == bool(self.center_id):
            raise ValidationError("Assign an executive to exactly one school or centre.")

        active_assignments = ExecutiveUnitAssignment.objects.filter(
            executive=self.executive,
            is_active=True,
        )
        if self.pk:
            active_assignments = active_assignments.exclude(pk=self.pk)
        if self.is_active and active_assignments.exists():
            raise ValidationError("An executive can only have one active school or centre assignment.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CourseOfferProposal(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_OFFERED = "offered"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_OFFERED, "Offered"),
    ]

    course = models.ForeignKey("admin_app.Course", on_delete=models.CASCADE)
    semester = models.ForeignKey("admin_app.Semester", on_delete=models.CASCADE)
    section = models.CharField(max_length=30, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    proposed_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="course_offer_proposals")
    reviewed_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_course_offer_proposals")
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("course", "semester", "section")

    def __str__(self):
        return f"{self.course_id} {self.semester_id} {self.section}".strip()


class ResultPublication(models.Model):
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    published_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.offering_id}"



class ResultBatch(models.Model):
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=(("draft", "Draft"), ("review", "Under Review"), ("approved", "Approved"), ("published", "Published")),
        default="draft",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ResultBatch {self.offering_id} ({self.status})"


class ResultRecord(models.Model):
    batch = models.ForeignKey(ResultBatch, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    grade_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("batch", "student")

    def __str__(self):
        return f"Record {self.batch_id} - {self.student_id}"


class ResultApproval(models.Model):
    batch = models.ForeignKey(ResultBatch, on_delete=models.CASCADE, related_name="approvals")
    approved_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Approval {self.batch_id} by {self.approved_by_id}"


class ResultReviewNote(models.Model):
    batch = models.ForeignKey(ResultBatch, on_delete=models.CASCADE, related_name="review_notes")
    author = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, blank=True)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Review note {self.batch_id}"



class TimetableSlot(models.Model):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    DAY_CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("day_of_week", "start_time", "end_time")
        ordering = ("day_of_week", "start_time")

    def __str__(self):
        return self.label or f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class EvaluationTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    questions = models.JSONField(default=list)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluation_templates",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")

    def __str__(self):
        return self.name


class CourseEvaluationSurvey(models.Model):
    offering = models.OneToOneField(
        "admin_app.CourseOffering",
        on_delete=models.CASCADE,
        related_name="course_evaluation",
    )
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surveys",
    )
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    questions = models.JSONField(default=list)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    is_required = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_course_evaluations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if bool(self.opens_at) != bool(self.closes_at):
            raise ValidationError("An evaluation requires both an opening and closing time.")
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError("The evaluation closing time must be after its opening time.")

    def __str__(self):
        return f"{self.offering} - {self.title}"


class CourseEvaluationResponse(models.Model):
    survey = models.ForeignKey(
        CourseEvaluationSurvey,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="course_evaluation_responses",
    )
    answers = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-submitted_at",)
        unique_together = ("survey", "student")

    def __str__(self):
        return f"{self.survey_id} - {self.student_id}"

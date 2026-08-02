from django.core.exceptions import ValidationError
from django.db import models


class Teacher(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="teacher_detail",
    )
    teacher_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    academic_rank = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    office_location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.teacher_id

    @staff_id.setter
    def staff_id(self, value):
        self.teacher_id = value


class TeacherScopeAssignment(models.Model):
    teacher = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="teacher_scope_assignments",
    )
    school = models.ForeignKey(
        "admin_app.School",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    center = models.ForeignKey(
        "admin_app.Center",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_primary", "school__name", "center__name")
        constraints = [
            models.UniqueConstraint(
                fields=("teacher", "school"),
                condition=models.Q(school__isnull=False),
                name="unique_teacher_school_assignment",
            ),
            models.UniqueConstraint(
                fields=("teacher", "center"),
                condition=models.Q(center__isnull=False),
                name="unique_teacher_center_assignment",
            ),
            models.UniqueConstraint(
                fields=("teacher",),
                condition=models.Q(is_primary=True, is_active=True),
                name="one_primary_teacher_scope_assignment",
            ),
        ]

    def clean(self):
        if self.teacher_id and self.teacher.role != "teacher":
            raise ValidationError("Teacher scope assignments can only belong to teacher profiles.")
        if bool(self.school_id) == bool(self.center_id):
            raise ValidationError("Assign a teacher scope to exactly one school or centre.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        scope = self.school or self.center
        return f"{self.teacher_id} - {scope}"


class AttendanceSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    class_meeting = models.ForeignKey("admin_app.ClassMeeting", on_delete=models.SET_NULL, null=True, blank=True)
    session_date = models.DateField()
    topic = models.CharField(max_length=255, blank=True)
    attendance_code = models.CharField(max_length=20, blank=True)
    qr_token = models.CharField(max_length=255, blank=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    actual_starts_at = models.DateTimeField(null=True, blank=True)
    actual_ends_at = models.DateTimeField(null=True, blank=True)
    schedule_change_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("class_meeting", "session_date")

    def __str__(self):
        return f"{self.offering_id} - {self.session_date}"


class CourseResourceFolder(models.Model):
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="resource_folders")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class CourseSection(models.Model):
    TYPE_OUTLINE = "outline"
    TYPE_TOPIC = "topic"
    TYPE_LAB_WORK = "lab_work"
    TYPE_CHOICES = [
        (TYPE_OUTLINE, "Course outline"),
        (TYPE_TOPIC, "Topic"),
        (TYPE_LAB_WORK, "Lab work"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="course_sections")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    section_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_TOPIC)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)
    topic_label = models.CharField(max_length=100, blank=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("offering", "sort_order", "week_number")

    def __str__(self):
        return f"{self.offering_id} - {self.title}"


class CourseAnnouncement(models.Model):
    TYPE_GENERAL = "general"
    TYPE_TEST = "test"
    TYPE_QUIZ = "quiz"
    TYPE_PRESENTATION = "presentation"
    TYPE_CHOICES = [
        (TYPE_GENERAL, "General"),
        (TYPE_TEST, "Test"),
        (TYPE_QUIZ, "Quiz"),
        (TYPE_PRESENTATION, "Presentation"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="announcements")
    assignment = models.ForeignKey(
        "teacher_app.Assignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presentation_announcements",
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    announcement_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    visible_from = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class CourseAnnouncementSlot(models.Model):
    SELECTION_INDIVIDUAL = "individual"
    SELECTION_GROUP = "group"
    SELECTION_CHOICES = [
        (SELECTION_INDIVIDUAL, "Individual"),
        (SELECTION_GROUP, "Group"),
    ]

    announcement = models.ForeignKey(CourseAnnouncement, on_delete=models.CASCADE, related_name="slots")
    label = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    selection_type = models.CharField(max_length=20, choices=SELECTION_CHOICES, default=SELECTION_INDIVIDUAL)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("starts_at", "id")

    def clean(self):
        if self.capacity < 1 or self.capacity > 100:
            raise ValidationError({"capacity": "Slot capacity must be between 1 and 100."})
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Slot end time must be after its start time."})

    def __str__(self):
        return self.label or f"{self.announcement.title} - {self.starts_at}"


class CourseAnnouncementSlotSelection(models.Model):
    announcement = models.ForeignKey(
        CourseAnnouncement,
        on_delete=models.CASCADE,
        related_name="slot_selections",
    )
    slot = models.ForeignKey(
        CourseAnnouncementSlot,
        on_delete=models.CASCADE,
        related_name="selections",
    )
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="announcement_slot_selections",
    )
    assignment_group = models.ForeignKey(
        "teacher_app.AssignmentGroup",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="presentation_slot_selections",
    )
    group_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("announcement", "student"),
                name="one_slot_per_student_per_announcement",
            ),
            models.UniqueConstraint(
                fields=("announcement", "assignment_group"),
                condition=models.Q(assignment_group__isnull=False),
                name="one_slot_per_group_per_announcement",
            ),
        ]

    def clean(self):
        if self.slot_id and self.announcement_id and self.slot.announcement_id != self.announcement_id:
            raise ValidationError({"slot": "The selected slot does not belong to this announcement."})
        if self.slot_id and self.slot.selection_type == CourseAnnouncementSlot.SELECTION_GROUP and not self.group_name.strip():
            raise ValidationError({"group_name": "Enter a group name for a group presentation slot."})

    def __str__(self):
        return f"{self.student_id} - {self.slot_id}"


class CourseResource(models.Model):
    TYPE_FILE = "file"
    TYPE_LINK = "link"
    TYPE_PAGE = "page"
    TYPE_VIDEO = "video"
    TYPE_FOLDER = "folder"
    TYPE_CHOICES = [
        (TYPE_FILE, "File"),
        (TYPE_LINK, "Link"),
        (TYPE_PAGE, "Page"),
        (TYPE_VIDEO, "Video"),
        (TYPE_FOLDER, "Folder"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="course_resources")
    section = models.ForeignKey(CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="resources")
    folder = models.ForeignKey(CourseResourceFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FILE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="courses/resources/", null=True, blank=True)
    url = models.URLField(blank=True)
    content = models.TextField(blank=True)
    visible_from = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class Assignment(models.Model):
    ACTIVITY_ASSIGNMENT = "assignment"
    ACTIVITY_LAB = "lab_activity"
    ACTIVITY_CHOICES = [
        (ACTIVITY_ASSIGNMENT, "Assignment"),
        (ACTIVITY_LAB, "Lab activity"),
    ]

    COLLABORATION_INDIVIDUAL = "individual"
    COLLABORATION_GROUP = "group"
    COLLABORATION_CHOICES = [
        (COLLABORATION_INDIVIDUAL, "Individual"),
        (COLLABORATION_GROUP, "Group"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    SUBMISSION_TEXT = "text"
    SUBMISSION_FILE = "file"
    SUBMISSION_BOTH = "both"
    SUBMISSION_CHOICES = [
        (SUBMISSION_TEXT, "Text"),
        (SUBMISSION_FILE, "File"),
        (SUBMISSION_BOTH, "Text and File"),
    ]

    FILE_DOC = "doc"
    FILE_PDF = "pdf"
    FILE_ZIP = "zip"
    FILE_PRESENTATION = "presentation"
    FILE_IMAGE = "image"
    FILE_SPREADSHEET = "spreadsheet"
    FILE_CHOICES = [
        (FILE_DOC, "DOC/DOCX"),
        (FILE_PDF, "PDF"),
        (FILE_ZIP, "ZIP"),
        (FILE_PRESENTATION, "PPT/PPTX"),
        (FILE_IMAGE, "JPG/JPEG/PNG"),
        (FILE_SPREADSHEET, "XLS/XLSX/CSV"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    section = models.ForeignKey(CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    activity_kind = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default=ACTIVITY_ASSIGNMENT)
    collaboration_mode = models.CharField(
        max_length=20,
        choices=COLLABORATION_CHOICES,
        default=COLLABORATION_INDIVIDUAL,
    )
    max_group_members = models.PositiveSmallIntegerField(default=1)
    require_same_tutorial_group = models.BooleanField(default=False)
    require_same_lab_group = models.BooleanField(default=False)
    min_distinct_countries = models.PositiveSmallIntegerField(default=0)
    group_rules = models.TextField(blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    file_instructions = models.TextField(blank=True)
    opens_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    cutoff_at = models.DateTimeField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_CHOICES, default=SUBMISSION_BOTH)
    accepted_file_type = models.CharField(max_length=20, choices=FILE_CHOICES, default=FILE_PDF)
    accepted_file_types = models.JSONField(default=list, blank=True)
    max_files = models.PositiveSmallIntegerField(default=1)
    max_file_size_mb = models.PositiveSmallIntegerField(default=10)
    allow_multiple_submissions = models.BooleanField(default=False)
    allow_late_submissions = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.max_files < 1 or self.max_files > 5:
            raise ValidationError({"max_files": "Students can submit between 1 and 5 files."})
        if self.max_file_size_mb < 1 or self.max_file_size_mb > 100:
            raise ValidationError({"max_file_size_mb": "Each file must be limited to between 1 and 100 MB."})
        valid_file_types = {value for value, _label in self.FILE_CHOICES}
        invalid_file_types = set(self.accepted_file_types or []) - valid_file_types
        if invalid_file_types:
            raise ValidationError({"accepted_file_types": "Select only supported file formats."})
        if self.activity_kind == self.ACTIVITY_LAB and (
            not self.section or self.section.section_type != CourseSection.TYPE_LAB_WORK
        ):
            raise ValidationError({"section": "Lab activities must be linked to a lab-work course section."})
        if self.collaboration_mode == self.COLLABORATION_GROUP:
            if self.max_group_members < 2 or self.max_group_members > 20:
                raise ValidationError({"max_group_members": "Group assignments allow between 2 and 20 members."})
            if self.min_distinct_countries > self.max_group_members:
                raise ValidationError({
                    "min_distinct_countries": "Country diversity cannot exceed the maximum group size."
                })
        elif self.max_group_members != 1:
            raise ValidationError({"max_group_members": "Individual assignments must have a group size of 1."})
        if self.opens_at and self.due_date and self.opens_at > self.due_date:
            raise ValidationError({"due_date": "Assignment deadline must be after the opening time."})
        if self.due_date and self.cutoff_at and self.due_date > self.cutoff_at:
            raise ValidationError({"cutoff_at": "Cutoff time must be after the assignment deadline."})

    def __str__(self):
        return self.title


class AssignmentGroup(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=255)
    leader = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="led_assignment_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("assignment", "name"),
                name="unique_group_name_per_assignment",
            ),
            models.UniqueConstraint(
                fields=("assignment", "leader"),
                name="one_led_group_per_student_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.assignment.title} - {self.name}"


class AssignmentGroupMembership(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    group = models.ForeignKey(
        AssignmentGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="assignment_group_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("joined_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("assignment", "student"),
                name="one_group_per_student_assignment",
            ),
            models.UniqueConstraint(
                fields=("group", "student"),
                name="unique_student_in_assignment_group",
            ),
        ]

    def clean(self):
        if self.group_id and self.assignment_id and self.group.assignment_id != self.assignment_id:
            raise ValidationError({"group": "The group does not belong to this assignment."})

    def __str__(self):
        return f"{self.group_id} - {self.student_id}"


class AssignmentGroupInvitation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="group_invitations",
    )
    group = models.ForeignKey(
        AssignmentGroup,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="sent_assignment_group_invitations",
    )
    invitee = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="assignment_group_invitations",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("group", "invitee"),
                name="unique_group_invitation_per_student",
            ),
        ]

    def clean(self):
        if self.group_id and self.assignment_id and self.group.assignment_id != self.assignment_id:
            raise ValidationError({"group": "The group does not belong to this assignment."})

    def __str__(self):
        return f"{self.group_id} -> {self.invitee_id}"


class CourseActivity(models.Model):
    TYPE_ASSIGNMENT = "assignment"
    TYPE_RESOURCE = "resource"
    TYPE_ATTENDANCE = "attendance"
    TYPE_EXAM = "exam"
    TYPE_DISCUSSION = "discussion"
    TYPE_CHOICES = [
        (TYPE_ASSIGNMENT, "Assignment"),
        (TYPE_RESOURCE, "Resource"),
        (TYPE_ATTENDANCE, "Attendance"),
        (TYPE_EXAM, "Exam"),
        (TYPE_DISCUSSION, "Discussion"),
    ]

    COMPLETION_VIEW = "view"
    COMPLETION_SUBMIT = "submit"
    COMPLETION_GRADE = "grade"
    COMPLETION_MANUAL = "manual"
    COMPLETION_CHOICES = [
        (COMPLETION_VIEW, "View"),
        (COMPLETION_SUBMIT, "Submit"),
        (COMPLETION_GRADE, "Grade"),
        (COMPLETION_MANUAL, "Manual"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="activities")
    section = models.ForeignKey(CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    resource = models.ForeignKey(CourseResource, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    activity_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    opens_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    completion_policy = models.CharField(max_length=30, choices=COMPLETION_CHOICES, default=COMPLETION_VIEW)
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "due_at", "title")

    def __str__(self):
        return self.title


class AssignmentRubric(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="rubrics")
    title = models.CharField(max_length=255)
    criteria = models.JSONField(default=list, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ResultSubmission(models.Model):
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    remarks = models.TextField(blank=True)
    submitted_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_results")
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("offering", "student")

    def __str__(self):
        return f"{self.offering_id} - {self.student_id}"


class AssignmentSubmission(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_LATE = "late"
    STATUS_GRADED = "graded"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_LATE, "Late"),
        (STATUS_GRADED, "Graded"),
        (STATUS_RETURNED, "Returned"),
    ]

    assignment = models.ForeignKey("teacher_app.Assignment", on_delete=models.CASCADE)
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    assignment_group = models.ForeignKey(
        "teacher_app.AssignmentGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    content = models.TextField(blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    grade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="graded_submissions")
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"Submission {self.assignment_id} - {self.student_id}"


class AssignmentAttachment(models.Model):
    submission = models.ForeignKey("teacher_app.AssignmentSubmission", on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="assignments/attachments/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.submission_id}"


class AssignmentFeedback(models.Model):
    submission = models.ForeignKey("teacher_app.AssignmentSubmission", on_delete=models.CASCADE, related_name="feedback_entries")
    reviewer = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    rubric = models.ForeignKey(AssignmentRubric, on_delete=models.SET_NULL, null=True, blank=True)
    rubric_scores = models.JSONField(null=True, blank=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.submission_id} by {self.reviewer_id}"


class AssignmentComment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="comments")
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    author = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assignment_comments")
    body = models.TextField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Comment on assignment {self.assignment_id}"

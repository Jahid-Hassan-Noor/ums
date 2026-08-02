from django.core.exceptions import ValidationError
from django.db import models


class QuestionBank(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    offering = models.ForeignKey(
        "admin_app.CourseOffering",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="question_banks",
    )
    course = models.ForeignKey(
        "admin_app.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="question_banks",
    )
    owner = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_question_banks",
    )
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class QuestionCategory(models.Model):
    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name="categories")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("bank", "sort_order", "title")
        unique_together = ("bank", "parent", "title")

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE_MULTIPLE_CHOICE = "multiple_choice"
    TYPE_TRUE_FALSE = "true_false"
    TYPE_SHORT_ANSWER = "short_answer"
    TYPE_FILL_BLANK = "fill_blank"
    TYPE_NUMERICAL = "numerical"
    TYPE_MATCHING = "matching"
    TYPE_ORDERING = "ordering"
    TYPE_ESSAY = "essay"
    TYPE_CHOICES = [
        (TYPE_MULTIPLE_CHOICE, "Multiple choice"),
        (TYPE_TRUE_FALSE, "True/False"),
        (TYPE_SHORT_ANSWER, "Short answer"),
        (TYPE_FILL_BLANK, "Fill in the blank"),
        (TYPE_NUMERICAL, "Numerical"),
        (TYPE_MATCHING, "Matching"),
        (TYPE_ORDERING, "Ordering"),
        (TYPE_ESSAY, "Essay"),
    ]

    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name="questions")
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    title = models.CharField(max_length=255)
    question_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    tags = models.JSONField(default=list, blank=True)
    difficulty = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_questions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("bank", "title")

    def __str__(self):
        return self.title


class QuestionVersion(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_READY = "ready"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_READY, "Ready"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_READY)
    question_text = models.TextField()
    default_mark = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    penalty = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    general_feedback = models.TextField(blank=True)
    correct_answer = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_question_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("question", "-version")
        unique_together = ("question", "version")

    def __str__(self):
        return f"{self.question.title} v{self.version}"


class QuestionChoice(models.Model):
    question_version = models.ForeignKey(QuestionVersion, on_delete=models.CASCADE, related_name="choices")
    label = models.CharField(max_length=20, blank=True)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.label or self.text[:40]


class Quiz(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CLOSED, "Closed"),
    ]

    GRADE_HIGHEST = "highest"
    GRADE_AVERAGE = "average"
    GRADE_FIRST = "first"
    GRADE_LAST = "last"
    GRADE_CHOICES = [
        (GRADE_HIGHEST, "Highest attempt"),
        (GRADE_AVERAGE, "Average attempt"),
        (GRADE_FIRST, "First attempt"),
        (GRADE_LAST, "Last attempt"),
    ]

    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=1)
    password = models.CharField(max_length=255, blank=True)
    ip_allowlist = models.TextField(blank=True)
    require_safe_exam_browser = models.BooleanField(default=False)
    safe_exam_browser_config_key = models.CharField(max_length=255, blank=True)
    grade_method = models.CharField(max_length=20, choices=GRADE_CHOICES, default=GRADE_HIGHEST)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    pass_mark = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=False)
    review_show_attempt = models.BooleanField(default=True)
    review_show_marks = models.BooleanField(default=True)
    review_show_correctness = models.BooleanField(default=False)
    review_show_right_answer = models.BooleanField(default=False)
    review_show_feedback = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_quizzes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({"closes_at": "Quiz close time must be after open time."})

    def __str__(self):
        return self.title


class QuizSection(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    shuffle_questions = models.BooleanField(default=False)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.title or f"Section {self.sort_order}"


class QuizQuestionSlot(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="question_slots")
    section = models.ForeignKey(QuizSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="slots")
    question_version = models.ForeignKey(
        QuestionVersion,
        on_delete=models.PROTECT,
        related_name="quiz_slots",
    )
    sort_order = models.PositiveIntegerField(default=0)
    page = models.PositiveIntegerField(default=1)
    display_number = models.CharField(max_length=20, blank=True)
    max_mark = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    require_previous = models.BooleanField(default=False)

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = ("quiz", "sort_order")

    def __str__(self):
        return f"{self.quiz_id} - {self.question_version_id}"


class QuizRandomRule(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="random_rules")
    section = models.ForeignKey(QuizSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="random_rules")
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="random_quiz_rules",
    )
    question_type = models.CharField(max_length=30, choices=Question.TYPE_CHOICES, blank=True)
    count = models.PositiveSmallIntegerField(default=1)
    max_mark = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"Random {self.count} for {self.quiz_id}"


class QuizAccessOverride(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="access_overrides")
    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="quiz_access_overrides",
    )
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    max_attempts = models.PositiveSmallIntegerField(null=True, blank=True)
    password = models.CharField(max_length=255, blank=True)
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_quiz_overrides",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("quiz", "student")

    def __str__(self):
        return f"{self.quiz_id} override for {self.student_id}"


class QuizAttempt(models.Model):
    STATE_IN_PROGRESS = "in_progress"
    STATE_OVERDUE = "overdue"
    STATE_SUBMITTED = "submitted"
    STATE_ABANDONED = "abandoned"
    STATE_CHOICES = [
        (STATE_IN_PROGRESS, "In progress"),
        (STATE_OVERDUE, "Overdue"),
        (STATE_SUBMITTED, "Submitted"),
        (STATE_ABANDONED, "Abandoned"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="quiz_attempts")
    attempt_number = models.PositiveSmallIntegerField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_IN_PROGRESS)
    current_page = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_ip = models.GenericIPAddressField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    needs_manual_grading = models.BooleanField(default=False)
    graded_notifications_sent_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("quiz", "student", "attempt_number")
        unique_together = ("quiz", "student", "attempt_number")

    def __str__(self):
        return f"{self.quiz_id} - {self.student_id} attempt {self.attempt_number}"


class QuestionAttempt(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="question_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="question_attempts")
    slot = models.ForeignKey(
        QuizQuestionSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_attempts",
    )
    random_rule = models.ForeignKey(
        QuizRandomRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_attempts",
    )
    question_version = models.ForeignKey(QuestionVersion, on_delete=models.PROTECT, related_name="question_attempts")
    slot_number = models.PositiveIntegerField()
    max_mark = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    response = models.JSONField(default=dict, blank=True)
    response_summary = models.TextField(blank=True)
    right_answer_summary = models.TextField(blank=True)
    awarded_mark = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    requires_manual_grading = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    manually_graded_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manually_graded_question_attempts",
    )
    manually_graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("attempt", "slot_number")
        unique_together = ("attempt", "slot_number")

    def __str__(self):
        return f"{self.attempt_id} slot {self.slot_number}"


class QuestionAttemptStep(models.Model):
    STATE_AUTOSAVED = "autosaved"
    STATE_SUBMITTED = "submitted"
    STATE_GRADED = "graded"
    STATE_CHOICES = [
        (STATE_AUTOSAVED, "Autosaved"),
        (STATE_SUBMITTED, "Submitted"),
        (STATE_GRADED, "Graded"),
    ]

    question_attempt = models.ForeignKey(QuestionAttempt, on_delete=models.CASCADE, related_name="steps")
    sequence_number = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_AUTOSAVED)
    response = models.JSONField(default=dict, blank=True)
    fraction = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    actor = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("question_attempt", "sequence_number")
        unique_together = ("question_attempt", "sequence_number")


class QuizGrade(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="quiz_grades")
    grade = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    best_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_for_grades",
    )
    attempts_count = models.PositiveSmallIntegerField(default=0)
    needs_manual_grading = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("quiz", "student")

    def __str__(self):
        return f"{self.quiz_id} - {self.student_id}: {self.grade}"

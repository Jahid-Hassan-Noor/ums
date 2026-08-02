from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Student(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="student_detail",
    )
    student_id = models.CharField(max_length=50, blank=True, db_index=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    program = models.ForeignKey("admin_app.Program", on_delete=models.SET_NULL, null=True, blank=True)
    admission_number = models.CharField(max_length=50, blank=True)
    enrollment_status = models.CharField(max_length=50, blank=True)
    room = models.CharField(max_length=80, blank=True)
    current_year = models.PositiveSmallIntegerField(null=True, blank=True)
    expected_graduation_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    canteen_balance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)


class RegistrationPeriod(models.Model):
    PHASE_COURSE_REGISTRATION = "course_registration"
    PHASE_ADD_DROP = "add_drop"
    PHASE_DROP_ONLY = "drop_only"
    PHASE_CHOICES = [
        (PHASE_COURSE_REGISTRATION, "Course pre-registration"),
        (PHASE_ADD_DROP, "Add and drop"),
        (PHASE_DROP_ONLY, "Drop only"),
    ]

    semester = models.ForeignKey("admin_app.Semester", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    phase = models.CharField(max_length=40, choices=PHASE_CHOICES, default=PHASE_COURSE_REGISTRATION)
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-opens_at",)
        unique_together = ("semester", "phase")

    def __str__(self):
        return self.title

    def clean(self):
        if self.opens_at >= self.closes_at:
            raise ValidationError({"closes_at": "Registration period must close after it opens."})

    @property
    def allows_add(self):
        return self.phase in {self.PHASE_COURSE_REGISTRATION, self.PHASE_ADD_DROP}

    @property
    def allows_drop(self):
        return self.phase in {
            self.PHASE_COURSE_REGISTRATION,
            self.PHASE_ADD_DROP,
            self.PHASE_DROP_ONLY,
        }


class CourseRegistration(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_DROPPED = "dropped"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_DROPPED, "Dropped"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    tutorial_group = models.ForeignKey("admin_app.CourseTutorialGroup", on_delete=models.SET_NULL, null=True, blank=True)
    lab_group = models.ForeignKey("admin_app.CourseLabGroup", on_delete=models.SET_NULL, null=True, blank=True)
    period = models.ForeignKey(RegistrationPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    registered_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_registrations")
    is_manual = models.BooleanField(default=False)
    request_note = models.TextField(blank=True)
    approved_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_registrations")
    approved_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "offering")

    def __str__(self):
        return f"{self.student} - {self.offering}"


class AttendanceRecord(models.Model):
    SOURCE_CODE = "code"
    SOURCE_QR = "qr"
    SOURCE_MANUAL = "manual"
    SOURCE_IMPORT = "import"
    SOURCE_CHOICES = [
        (SOURCE_CODE, "Code"),
        (SOURCE_QR, "QR"),
        (SOURCE_MANUAL, "Manual"),
        (SOURCE_IMPORT, "Import"),
    ]

    STATUS_ATTEND = "attend"
    STATUS_LATE = "late"
    STATUS_ABSENT_REASON = "absent_reason"
    STATUS_ABSENT_MC = "absent_mc"
    ATTENDANCE_STATUS_CHOICES = [
        (STATUS_ATTEND, "Attend"),
        (STATUS_LATE, "Late"),
        (STATUS_ABSENT_REASON, "Absent with reason"),
        (STATUS_ABSENT_MC, "Absent with MC"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    attendance_session = models.ForeignKey("teacher_app.AttendanceSession", on_delete=models.SET_NULL, null=True, blank=True)
    class_date = models.DateField()
    present = models.BooleanField(default=False)
    attendance_status = models.CharField(max_length=30, choices=ATTENDANCE_STATUS_CHOICES, default=STATUS_ATTEND)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    submitted_code = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)
    medical_certificate = models.FileField(upload_to="attendance/medical-certificates/", null=True, blank=True)
    marked_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="marked_attendance")
    marked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "attendance_session")

    def __str__(self):
        return f"{self.student} - {self.offering} - {self.class_date}"


class AttendanceCodeSubmission(models.Model):
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"
    STATUS_DUPLICATE = "duplicate"
    STATUS_CHOICES = [
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_DUPLICATE, "Duplicate"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    session = models.ForeignKey("teacher_app.AttendanceSession", on_delete=models.CASCADE, related_name="code_submissions")
    code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REJECTED)
    message = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"{self.student_id} - {self.session_id} - {self.status}"


class Enrollment(models.Model):
    """Finalized enrollment record created when a registration is approved."""
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.CASCADE)
    tutorial_group = models.ForeignKey("admin_app.CourseTutorialGroup", on_delete=models.SET_NULL, null=True, blank=True)
    lab_group = models.ForeignKey("admin_app.CourseLabGroup", on_delete=models.SET_NULL, null=True, blank=True)
    registration = models.ForeignKey(CourseRegistration, on_delete=models.SET_NULL, null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_enrollments")

    class Meta:
        unique_together = ("student", "offering")

    def __str__(self):
        return f"Enrollment: {self.student} -> {self.offering}"


class Exam(models.Model):
    TYPE_FINAL = "final"
    TYPE_MIDTERM = "midterm"
    TYPE_QUIZ = "quiz"
    TYPE_PRACTICAL = "practical"
    TYPE_CHOICES = [
        (TYPE_FINAL, "Final"),
        (TYPE_MIDTERM, "Midterm"),
        (TYPE_QUIZ, "Quiz"),
        (TYPE_PRACTICAL, "Practical"),
    ]

    semester = models.ForeignKey("admin_app.Semester", on_delete=models.CASCADE)
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_FINAL)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    room = models.ForeignKey("admin_app.Room", on_delete=models.SET_NULL, null=True, blank=True)
    instructions = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("starts_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("offering",),
                condition=models.Q(exam_type="final"),
                name="one_final_exam_per_offering",
            ),
        ]

    def __str__(self):
        return self.title


class ExamVenueAllocation(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="venue_allocations")
    venue = models.ForeignKey(
        "admin_app.Venue",
        on_delete=models.PROTECT,
        related_name="exam_allocations",
    )
    seats = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("venue__building__name", "venue__name")
        unique_together = ("exam", "venue")

    def clean(self):
        if self.seats < 1:
            raise ValidationError({"seats": "An exam venue allocation must reserve at least one seat."})

    def __str__(self):
        return f"{self.exam} - {self.venue} ({self.seats})"


class ExamSlip(models.Model):
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    semester = models.ForeignKey("admin_app.Semester", on_delete=models.CASCADE)
    release_from = models.DateTimeField(null=True, blank=True)
    release_until = models.DateTimeField(null=True, blank=True)
    is_visible = models.BooleanField(default=False)
    data = models.JSONField(null=True, blank=True)
    file = models.FileField(upload_to="academic/exam-slips/", null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "semester")

    def __str__(self):
        return f"Exam slip {self.student_id} - {self.semester_id}"


class TranscriptRecord(models.Model):
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    semester = models.ForeignKey("admin_app.Semester", on_delete=models.SET_NULL, null=True, blank=True)
    offering = models.ForeignKey("admin_app.CourseOffering", on_delete=models.SET_NULL, null=True, blank=True)
    course_code = models.CharField(max_length=30, blank=True)
    course_title = models.CharField(max_length=255, blank=True)
    credit_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    grade_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "offering")

    def __str__(self):
        return f"{self.student_id} - {self.course_code or self.offering_id}"


class LeaveRequest(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    attachment = models.FileField(upload_to="leave/attachments/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_leave_requests")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Leave {self.student_id} {self.start_date} - {self.end_date}"


class LeaveApproval(models.Model):
    ROLE_TEACHER = "teacher"
    ROLE_DEAN = "dean"
    ROLE_CHOICES = [
        (ROLE_TEACHER, "Teacher"),
        (ROLE_DEAN, "Dean"),
    ]

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="leave_approvals")
    approval_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    class_meeting = models.ForeignKey("admin_app.ClassMeeting", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at",)
        unique_together = ("leave_request", "approver", "class_meeting", "approval_role")

    def __str__(self):
        return f"Leave approval {self.leave_request_id} - {self.approver_id}"


class StudentAffairsContact(models.Model):
    name = models.CharField(max_length=255)
    office = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=255, blank=True)
    visible_to_students = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class EmergencyContact(models.Model):
    CATEGORY_SECURITY = "security"
    CATEGORY_HEALTH = "health"
    CATEGORY_STUDENT_AFFAIRS = "student_affairs"
    CATEGORY_WARDEN = "warden"
    CATEGORY_OTHER = "other"
    CATEGORY_CHOICES = [
        (CATEGORY_SECURITY, "Security"),
        (CATEGORY_HEALTH, "Health"),
        (CATEGORY_STUDENT_AFFAIRS, "Student Affairs"),
        (CATEGORY_WARDEN, "Warden"),
        (CATEGORY_OTHER, "Other"),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    hours = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class WardenSchedule(models.Model):
    profile = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    warden_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("starts_at",)

    def __str__(self):
        return f"{self.warden_name} {self.starts_at}"

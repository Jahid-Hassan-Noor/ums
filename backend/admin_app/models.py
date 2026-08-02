from django.core.exceptions import ValidationError
from django.db import models
from executive_app.models import TimetableSlot
from auth_app.models import (
    Admin as AuthAdmin,
    Profile as AuthProfile,
    ROLE_DETAIL_MODELS,
    ensure_role_detail,
    prune_role_details,
    role_detail_defaults,
    role_for_user,
)


class School(models.Model):
    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    mission = models.JSONField(default=list, blank=True)
    programmes = models.JSONField(default=list, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Center(models.Model):
    CENTER_ACADEMIC = "academic"
    CENTER_ADMINISTRATIVE = "administrative"
    CENTER_TYPE_CHOICES = [
        (CENTER_ACADEMIC, "Academic"),
        (CENTER_ADMINISTRATIVE, "Administrative"),
    ]

    code = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    center_type = models.CharField(max_length=30, choices=CENTER_TYPE_CHOICES, default=CENTER_ACADEMIC)
    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    offerings = models.JSONField(default=list, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Department(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Unit(models.Model):
    UNIT_ACADEMIC = "academic"
    UNIT_ADMINISTRATIVE = "administrative"
    UNIT_STUDENT_AFFAIRS = "student_affairs"
    UNIT_SERVICE = "service"
    UNIT_CHOICES = [
        (UNIT_ACADEMIC, "Academic"),
        (UNIT_ADMINISTRATIVE, "Administrative"),
        (UNIT_STUDENT_AFFAIRS, "Student Affairs"),
        (UNIT_SERVICE, "Service"),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=30, choices=UNIT_CHOICES, default=UNIT_ADMINISTRATIVE)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Program(models.Model):
    PROGRAM_ACADEMIC = "academic"
    PROGRAM_CENTER = "center_program"
    PROGRAM_CHOICES = [
        (PROGRAM_ACADEMIC, "Academic program"),
        (PROGRAM_CENTER, "Centre program"),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    program_type = models.CharField(max_length=30, choices=PROGRAM_CHOICES, default=PROGRAM_ACADEMIC)
    level = models.CharField(max_length=100, blank=True)
    duration_years = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code



class Profile(AuthProfile):
    class Meta:
        proxy = True


class Admin(AuthAdmin):
    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admins"


AdminProfile = Admin


class Semester(models.Model):
    TYPE_LONG = "long"
    TYPE_SHORT = "short"
    TYPE_CHOICES = [
        (TYPE_LONG, "Long semester"),
        (TYPE_SHORT, "Short semester"),
    ]

    CALENDAR_UNDERGRADUATE = "undergraduate"
    CALENDAR_FOUNDATION = "foundation"
    CALENDAR_CHOICES = [
        (CALENDAR_UNDERGRADUATE, "Schools / undergraduate programmes"),
        (CALENDAR_FOUNDATION, "CFGS / foundation studies"),
    ]

    name = models.CharField(max_length=255, unique=True)
    academic_session = models.CharField(max_length=100, blank=True)
    semester_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_LONG)
    calendar_group = models.CharField(max_length=30, choices=CALENDAR_CHOICES, default=CALENDAR_UNDERGRADUATE)
    starting_week = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    teaching_periods = models.JSONField(default=list, blank=True)
    course_offering_opens_at = models.DateTimeField(null=True, blank=True)
    course_offering_closes_at = models.DateTimeField(null=True, blank=True)
    course_selection_closes_at = models.DateTimeField(null=True, blank=True)
    mid_semester_break_starts_on = models.DateField(null=True, blank=True)
    mid_semester_break_ends_on = models.DateField(null=True, blank=True)
    revision_starts_on = models.DateField(null=True, blank=True)
    revision_ends_on = models.DateField(null=True, blank=True)
    examination_starts_on = models.DateField(null=True, blank=True)
    examination_ends_on = models.DateField(null=True, blank=True)
    inter_semester_break_starts_on = models.DateField(null=True, blank=True)
    inter_semester_break_ends_on = models.DateField(null=True, blank=True)
    max_credit_hours = models.PositiveSmallIntegerField(default=21)
    default_classes_per_week = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("calendar_group",),
                condition=models.Q(is_active=True),
                name="one_active_semester_per_calendar_group",
            ),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"end_date": "Semester end date must be after the start date."})
        if (
            self.course_offering_opens_at
            and self.course_offering_closes_at
            and self.course_offering_opens_at >= self.course_offering_closes_at
        ):
            raise ValidationError(
                {"course_offering_closes_at": "Course offering must close after it opens."}
            )
        if bool(self.course_offering_opens_at) != bool(self.course_offering_closes_at):
            raise ValidationError(
                {"course_offering_closes_at": "Course offering requires both an opening and closing time."}
            )
        if self.semester_type == self.TYPE_SHORT and self.default_classes_per_week < 2:
            raise ValidationError(
                {"default_classes_per_week": "Short semesters require at least two weekly class sessions."}
            )
        if self.calendar_group == self.CALENDAR_FOUNDATION and self.semester_type != self.TYPE_LONG:
            raise ValidationError({"semester_type": "CFGS uses long semesters only."})

        date_pairs = [
            (
                "mid_semester_break_starts_on",
                "mid_semester_break_ends_on",
                "Mid-semester break",
            ),
            ("revision_starts_on", "revision_ends_on", "Revision period"),
            ("examination_starts_on", "examination_ends_on", "Examination period"),
            (
                "inter_semester_break_starts_on",
                "inter_semester_break_ends_on",
                "Inter-semester break",
            ),
        ]
        for starts_field, ends_field, label in date_pairs:
            starts_on = getattr(self, starts_field)
            ends_on = getattr(self, ends_field)
            if bool(starts_on) != bool(ends_on):
                raise ValidationError({ends_field: f"{label} requires both a start and end date."})
            if starts_on and starts_on > ends_on:
                raise ValidationError({ends_field: f"{label} must end after it starts."})
            if (
                starts_on
                and self.start_date
                and label != "Inter-semester break"
                and starts_on < self.start_date
            ):
                raise ValidationError({starts_field: f"{label} must start inside the semester."})
            if (
                ends_on
                and self.end_date
                and label != "Inter-semester break"
                and ends_on > self.end_date
            ):
                raise ValidationError({ends_field: f"{label} must end inside the semester."})

        if self.inter_semester_break_starts_on and self.end_date:
            if self.inter_semester_break_starts_on <= self.end_date:
                raise ValidationError(
                    {
                        "inter_semester_break_starts_on": (
                            "Inter-semester break must start after the semester ends."
                        )
                    }
                )
        if self.revision_ends_on and self.examination_starts_on:
            if self.revision_ends_on >= self.examination_starts_on:
                raise ValidationError(
                    {"examination_starts_on": "Examinations must start after the revision period."}
                )

    def __str__(self):
        return self.name


class SemesterHoliday(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="holidays")
    name = models.CharField(max_length=255)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("starts_on", "name")

    def clean(self):
        if self.ends_on and self.starts_on > self.ends_on:
            raise ValidationError({"ends_on": "Holiday end date must be after the start date."})

    def __str__(self):
        return f"{self.semester} - {self.name}"


class IELTSSession(models.Model):
    academic_session = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    exam_date = models.DateField()
    capacity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("exam_date", "title")
        unique_together = ("academic_session", "title")

    def clean(self):
        if (
            self.registration_opens_at
            and self.registration_closes_at
            and self.registration_opens_at > self.registration_closes_at
        ):
            raise ValidationError(
                {"registration_closes_at": "IELTS registration must close after it opens."}
            )

    def __str__(self):
        return f"{self.title} ({self.academic_session})"


class Course(models.Model):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=255)
    credits = models.PositiveSmallIntegerField(default=0)
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="dependent_courses",
    )
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    has_lab = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    instructor = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    eligible_schools = models.ManyToManyField(
        School,
        blank=True,
        related_name="eligible_course_offerings",
    )
    section = models.CharField(max_length=30, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    has_final_exam = models.BooleanField(default=True)
    coursework_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    final_exam_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40)
    assessment_overview = models.TextField(blank=True)
    study_guide = models.FileField(upload_to="study-guides/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("course", "semester", "section")

    def __str__(self):
        return f"{self.course.code} {self.section}".strip()


class CourseTutorialGroup(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="tutorial_groups")
    code = models.CharField(max_length=30)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("offering__course__code", "code")
        unique_together = ("offering", "code")

    def clean(self):
        if self.capacity < 1:
            raise ValidationError({"capacity": "Tutorial group capacity must be at least 1."})

    def __str__(self):
        return f"{self.offering.course.code}_{self.code}"


class CourseLabGroup(models.Model):
    tutorial_group = models.ForeignKey(CourseTutorialGroup, on_delete=models.CASCADE, related_name="lab_groups")
    code = models.CharField(max_length=30)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("tutorial_group__offering__course__code", "tutorial_group__code", "code")
        unique_together = ("tutorial_group", "code")

    def clean(self):
        if self.capacity < 1:
            raise ValidationError({"capacity": "Lab group capacity must be at least 1."})

    def __str__(self):
        return f"{self.tutorial_group}_{self.code}"


class ClassGroup(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    cohort = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("program", "semester", "year", "cohort")

    def __str__(self):
        return self.code or f"{self.program.code} {self.cohort}".strip()


class Room(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, blank=True)
    campus = models.CharField(max_length=255, blank=True)
    building = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Building(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.code


class Venue(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="venues")
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.building.name} - {self.name}"


class Hostel(models.Model):
    TYPE_MALE = "male"
    TYPE_FEMALE = "female"
    TYPE_CHOICES = [
        (TYPE_MALE, "Male"),
        (TYPE_FEMALE, "Female"),
    ]

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255, blank=True)
    hostel_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    warden = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hostels_wardened",
    )
    warden_name = models.CharField(max_length=255, blank=True)
    warden_phone = models.CharField(max_length=30, blank=True)
    warden_email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.name or self.code


class HostelRoom(models.Model):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    floor = models.PositiveSmallIntegerField()
    number = models.CharField(max_length=20)
    code = models.CharField(max_length=80, unique=True, blank=True)
    capacity = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("hostel__code", "floor", "number")
        unique_together = ("hostel", "floor", "number")

    def build_code(self):
        room_number = self.number.zfill(2) if self.number.isdigit() else self.number.upper()
        return f"{self.hostel.code.upper()}-{self.floor:02d}-{room_number}"

    def save(self, *args, **kwargs):
        if self.hostel_id:
            self.code = self.build_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class ImportJob(models.Model):
    TYPE_USERS = "users"
    TYPE_RESULTS = "results"
    TYPE_PUBLIC_CONTENT = "public_content"
    TYPE_CHOICES = [
        (TYPE_USERS, "Users"),
        (TYPE_RESULTS, "Results"),
        (TYPE_PUBLIC_CONTENT, "Public Content"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_PREVIEW = "preview"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PREVIEW, "Preview"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    import_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    source_name = models.CharField(max_length=255, blank=True)
    source_file = models.FileField(upload_to="imports/", null=True, blank=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.import_type} import #{self.pk}"


class ClassMeeting(models.Model):
    CLASS_TYPE_LECTURE = "lecture"
    CLASS_TYPE_LAB = "lab"
    CLASS_TYPE_CHOICES = [
        (CLASS_TYPE_LECTURE, "Lecture Class"),
        (CLASS_TYPE_LAB, "Lab Class"),
    ]

    STATUS_IMPORTED = "imported"
    STATUS_SCHEDULED = "scheduled"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_IMPORTED, "Imported"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="class_meetings")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True)
    tutorial_group = models.ForeignKey(CourseTutorialGroup, on_delete=models.SET_NULL, null=True, blank=True)
    lab_group = models.ForeignKey(CourseLabGroup, on_delete=models.SET_NULL, null=True, blank=True)
    timetable_slot = models.ForeignKey(TimetableSlot, on_delete=models.SET_NULL, null=True, blank=True)
    recurring_meeting = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="single_week_adjustments",
    )
    meeting_date = models.DateField(null=True, blank=True)
    day_of_week = models.PositiveSmallIntegerField(choices=TimetableSlot.DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    lecturer = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)
    class_type = models.CharField(max_length=20, choices=CLASS_TYPE_CHOICES, default=CLASS_TYPE_LECTURE)
    topic = models.CharField(max_length=255, blank=True)
    schedule_change_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IMPORTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("day_of_week", "start_time")

    def __str__(self):
        return f"{self.offering} {self.get_day_of_week_display()} {self.start_time}"


class VenueBookingRequest(models.Model):
    TYPE_EVENT = "event"
    TYPE_PERSONAL = "personal"
    TYPE_CHOICES = [
        (TYPE_EVENT, "Event"),
        (TYPE_PERSONAL, "Personal use"),
    ]

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    requester = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="venue_booking_requests",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="booking_requests",
    )
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    purpose = models.CharField(max_length=255)
    explanation = models.TextField()
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_venue_booking_requests",
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("venue", "booking_date", "status")),
        ]

    def __str__(self):
        return f"{self.venue} on {self.booking_date} ({self.status})"


class AcademicEvent(models.Model):
    TYPE_CLASS = "class"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_EXAM = "exam"
    TYPE_REGISTRATION = "registration"
    TYPE_IELTS = "ielts"
    TYPE_LEAVE = "leave"
    TYPE_ELECTION = "election"
    TYPE_PUBLIC = "public"
    TYPE_CHOICES = [
        (TYPE_CLASS, "Class"),
        (TYPE_ASSIGNMENT, "Assignment"),
        (TYPE_EXAM, "Exam"),
        (TYPE_REGISTRATION, "Registration"),
        (TYPE_IELTS, "IELTS"),
        (TYPE_LEAVE, "Leave"),
        (TYPE_ELECTION, "Election"),
        (TYPE_PUBLIC, "Public"),
    ]

    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default=TYPE_PUBLIC)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True)
    offering = models.ForeignKey(CourseOffering, on_delete=models.SET_NULL, null=True, blank=True)
    class_meeting = models.ForeignKey(ClassMeeting, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("starts_at",)

    def __str__(self):
        return self.title


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    updated_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


class ReportExport(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    name = models.CharField(max_length=255)
    export_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    filters = models.JSONField(null=True, blank=True)
    file = models.FileField(upload_to="reports/exports/", null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


class AuditLog(models.Model):
    user = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    object_type = models.CharField(max_length=255, blank=True)
    object_id = models.CharField(max_length=255, blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit: {self.action} by {self.user_id}"

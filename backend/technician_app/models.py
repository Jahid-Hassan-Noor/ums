from django.core.exceptions import ValidationError
from django.db import models

from auth_app.models import Profile


class Technician(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="technician_detail",
    )
    technician_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.technician_id

    @staff_id.setter
    def staff_id(self, value):
        self.technician_id = value


class HelpdeskTicket(models.Model):
    CATEGORY_HOTSPOT = "hotspot_account"
    CATEGORY_EMAIL_PASSWORD = "email_password"
    CATEGORY_ID_CARD = "id_card"
    CATEGORY_PRINTING = "printing_code"
    CATEGORY_MOODLE = "moodle"
    CATEGORY_EMAIL_GROUP = "email_group"
    CATEGORY_WIFI = "wifi"
    CATEGORY_OTHER = "other"
    CATEGORY_CHOICES = [
        (CATEGORY_HOTSPOT, "Hotspot account"),
        (CATEGORY_EMAIL_PASSWORD, "Student email password reset"),
        (CATEGORY_ID_CARD, "Student ID card replacement"),
        (CATEGORY_PRINTING, "Student printing code"),
        (CATEGORY_MOODLE, "Moodle issue"),
        (CATEGORY_EMAIL_GROUP, "Email group issue"),
        (CATEGORY_WIFI, "Wi-Fi issue"),
        (CATEGORY_OTHER, "Other ICT issue"),
    ]

    STATUS_SUBMITTED = "submitted"
    STATUS_ADDRESSED = "addressed"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SOLVED = "solved"
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_ADDRESSED, "Addressed"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_SOLVED, "Solved"),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="ict_helpdesk_tickets",
    )
    assigned_to = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_ict_helpdesk_tickets",
    )
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    resolution_notes = models.TextField(blank=True)
    addressed_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at")

    def clean(self):
        if self.student_id and self.student.role != "student":
            raise ValidationError({"student": "ICT helpdesk tickets can only be submitted by students."})
        if self.assigned_to_id and self.assigned_to.role != "technician":
            raise ValidationError({"assigned_to": "ICT helpdesk tickets can only be assigned to technicians."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"ICT-{self.pk or 'NEW'}: {self.subject}"


class HelpdeskTicketUpdate(models.Model):
    ticket = models.ForeignKey(HelpdeskTicket, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="ict_helpdesk_updates",
    )
    status = models.CharField(max_length=20, choices=HelpdeskTicket.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.ticket_id}: {self.status}"


class Election(models.Model):
    TYPE_SRC = "src"
    TYPE_SCHOOL_COMMITTEE = "school_committee"
    TYPE_CHOICES = [
        (TYPE_SRC, "SRC election"),
        (TYPE_SCHOOL_COMMITTEE, "School committee election"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_UPCOMING = "upcoming"
    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_UPCOMING, "Upcoming"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_PUBLISHED, "Published"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    election_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SRC)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True, related_name="committee_elections")
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    general_selection_count = models.PositiveSmallIntegerField(default=0)
    school_selection_count = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_active = models.BooleanField(default=False)
    results_published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_elections")
    published_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="published_elections")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "Voting must close after it starts."})
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and not self.school_id:
            raise ValidationError({"school": "School committee elections must be assigned to a school."})
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and not self.school_selection_count:
            raise ValidationError({"school_selection_count": "School committee elections need a selection count."})

    def computed_status(self, now=None):
        from django.utils import timezone

        current = now or timezone.now()
        if self.status == self.STATUS_PUBLISHED:
            return self.STATUS_PUBLISHED
        if not self.is_active or self.status == self.STATUS_DRAFT:
            return self.STATUS_DRAFT
        if self.starts_at and current < self.starts_at:
            return self.STATUS_UPCOMING
        if self.ends_at and current > self.ends_at:
            return self.STATUS_CLOSED
        if self.starts_at and (not self.ends_at or current <= self.ends_at):
            return self.STATUS_ACTIVE
        return self.status

    def selection_count_for(self, category, school_id=None):
        if category == ElectionCandidate.CATEGORY_GENERAL:
            return self.general_selection_count
        if self.election_type == self.TYPE_SRC and school_id:
            seat = self.school_seats.filter(school_id=school_id).first()
            return seat.seat_count if seat else 0
        return self.school_selection_count


class SchoolElectionSeat(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="school_seats")
    school = models.ForeignKey("admin_app.School", on_delete=models.CASCADE, related_name="election_seats")
    seat_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("election", "school")

    def __str__(self):
        return f"{self.election.title} - {self.school.name}: {self.seat_count}"


class ElectionCandidate(models.Model):
    CATEGORY_GENERAL = "general"
    CATEGORY_SCHOOL = "school"
    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, "General category"),
        (CATEGORY_SCHOOL, "School category"),
    ]

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="election_candidates")
    display_name = models.CharField(max_length=255, blank=True)
    student_identifier = models.CharField(max_length=80, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True, related_name="election_candidates")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    details = models.TextField(blank=True)
    manifesto = models.TextField(blank=True)
    photo = models.FileField(upload_to="elections/candidates/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_APPROVED)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("election", "student", "category")
        ordering = ("election_id", "category", "school__name", "sort_order", "display_name")

    def __str__(self):
        return self.display_name or f"{self.election_id} - {self.student_id}"

    def clean(self):
        if self.student and self.student.role != Profile.ROLE_STUDENT:
            raise ValidationError({"student": "Election candidates must be students."})
        if not self.display_name and not self.student_id:
            raise ValidationError({"display_name": "Candidate name is required."})
        if not self.election_id:
            return
        if self.election.election_type == Election.TYPE_SCHOOL_COMMITTEE and self.category != self.CATEGORY_SCHOOL:
            raise ValidationError({"category": "School committee elections use the school category."})
        if self.category == self.CATEGORY_SCHOOL and not (self.school_id or self.election.school_id):
            raise ValidationError({"school": "School category candidates must belong to a school."})
        if (
            self.election.election_type == Election.TYPE_SCHOOL_COMMITTEE
            and self.school_id
            and self.school_id != self.election.school_id
        ):
            raise ValidationError({"school": "Candidate school must match the election school."})

    def save(self, *args, **kwargs):
        if self.student_id:
            if not self.display_name:
                user = self.student.user
                self.display_name = f"{user.first_name} {user.last_name}".strip() or user.username
            if not self.student_identifier:
                self.student_identifier = self.student.student_id
            if not self.school_id and self.student.school_id:
                self.school = self.student.school
        if self.election_id and self.election.election_type == Election.TYPE_SCHOOL_COMMITTEE:
            self.category = self.CATEGORY_SCHOOL
            if not self.school_id:
                self.school = self.election.school
        self.full_clean()
        return super().save(*args, **kwargs)


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="election_votes")
    candidate = models.ForeignKey(ElectionCandidate, on_delete=models.CASCADE, related_name="votes")
    category = models.CharField(max_length=20, choices=ElectionCandidate.CATEGORY_CHOICES, default=ElectionCandidate.CATEGORY_GENERAL)
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("election", "student", "candidate")
        indexes = [
            models.Index(fields=["election", "student", "category"]),
            models.Index(fields=["candidate", "category"]),
        ]

    def __str__(self):
        return f"{self.election_id} - {self.student_id}"

    def clean(self):
        if self.student and self.student.role != Profile.ROLE_STUDENT:
            raise ValidationError({"student": "Only students can vote in elections."})
        if self.candidate_id and self.election_id and self.candidate.election_id != self.election_id:
            raise ValidationError({"candidate": "Candidate does not belong to this election."})

    def save(self, *args, **kwargs):
        if self.candidate_id:
            self.category = self.candidate.category
        self.full_clean()
        return super().save(*args, **kwargs)


class ElectionResultSnapshot(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="result_snapshots")
    generated_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True)
    totals = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Election results {self.election_id}"

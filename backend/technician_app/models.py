from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from auth_app.models import Profile


def _normalized_key(value, fallback="custom"):
    key = slugify(str(value or "").strip()).replace("-", "_")
    return (key or fallback)[:80]


def _title_from_key(value):
    return str(value or "").replace("_", " ").strip().title()


def _coerce_positive_int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


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
        (CATEGORY_HOTSPOT, "Account access"),
        (CATEGORY_EMAIL_PASSWORD, "Email or password"),
        (CATEGORY_ID_CARD, "ID card or access card"),
        (CATEGORY_PRINTING, "Printing access"),
        (CATEGORY_MOODLE, "Learning management system"),
        (CATEGORY_EMAIL_GROUP, "Email group or mailing list"),
        (CATEGORY_WIFI, "Wi-Fi or network"),
        (CATEGORY_OTHER, "Other support"),
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
    category = models.CharField(max_length=40)
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
            raise ValidationError({"student": "Service desk tickets can only be submitted by students."})
        if self.assigned_to_id and self.assigned_to.role != "technician":
            raise ValidationError({"assigned_to": "Service desk tickets can only be assigned to technicians."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        from admin_app.settings_registry import helpdesk_reference

        return f"{helpdesk_reference(self.pk or 'NEW')}: {self.subject}"


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
    TYPE_STUDENT_COUNCIL = "student_council"
    TYPE_DEPARTMENT_REPRESENTATIVES = "department_representatives"
    TYPE_CHOICES = [
        (TYPE_STUDENT_COUNCIL, "Student council election"),
        (TYPE_DEPARTMENT_REPRESENTATIVES, "Department representatives election"),
        (TYPE_SRC, "Student representative election"),
        (TYPE_SCHOOL_COMMITTEE, "School representatives election"),
    ]

    CONSTITUENCY_UNIVERSITY = "university"
    CONSTITUENCY_SCHOOL = "school"
    CONSTITUENCY_CENTER = "center"
    CONSTITUENCY_DEPARTMENT = "department"
    CONSTITUENCY_PROGRAM = "program"
    CONSTITUENCY_COHORT = "cohort"
    CONSTITUENCY_CHOICES = [
        (CONSTITUENCY_UNIVERSITY, "University-wide"),
        (CONSTITUENCY_SCHOOL, "School"),
        (CONSTITUENCY_CENTER, "Center"),
        (CONSTITUENCY_DEPARTMENT, "Department"),
        (CONSTITUENCY_PROGRAM, "Program"),
        (CONSTITUENCY_COHORT, "Cohort"),
    ]
    CONSTITUENCY_VALUES = {value for value, _label in CONSTITUENCY_CHOICES}

    SEAT_SCOPE_CONSTITUENCY = "constituency"
    SEAT_SCOPE_CHOICES = [
        (SEAT_SCOPE_CONSTITUENCY, "Election constituency"),
        *CONSTITUENCY_CHOICES,
    ]
    SEAT_SCOPE_VALUES = {value for value, _label in SEAT_SCOPE_CHOICES}

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
    election_type = models.CharField(max_length=80, default=TYPE_STUDENT_COUNCIL)
    election_type_label = models.CharField(max_length=120, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True, related_name="committee_elections")
    constituency_type = models.CharField(max_length=30, choices=CONSTITUENCY_CHOICES, default=CONSTITUENCY_UNIVERSITY)
    constituency_id = models.PositiveIntegerField(null=True, blank=True)
    constituency_label = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    general_selection_count = models.PositiveSmallIntegerField(default=0)
    school_selection_count = models.PositiveSmallIntegerField(default=0)
    seat_rules = models.JSONField(default=list, blank=True)
    nomination_rules = models.JSONField(default=dict, blank=True)
    voter_eligibility = models.JSONField(default=dict, blank=True)
    result_publication_rules = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_active = models.BooleanField(default=False)
    results_published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_elections")
    published_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="published_elections")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_election_type_display(self):
        if self.election_type_label:
            return self.election_type_label
        return dict(self.TYPE_CHOICES).get(self.election_type, _title_from_key(self.election_type))

    @classmethod
    def normalize_seat_rules(cls, seat_rules):
        if not isinstance(seat_rules, list):
            return []

        normalized = []
        seen = set()
        for index, raw_rule in enumerate(seat_rules, start=1):
            if not isinstance(raw_rule, dict):
                continue
            label = str(raw_rule.get("label") or raw_rule.get("name") or "").strip()
            key = _normalized_key(raw_rule.get("key") or label, f"seat_{index}")
            suffix = 2
            unique_key = key
            while unique_key in seen:
                suffix += 1
                unique_key = f"{key[:72]}_{suffix}"
            seen.add(unique_key)

            scope_type = str(
                raw_rule.get("scope_type")
                or raw_rule.get("constituency_type")
                or cls.SEAT_SCOPE_CONSTITUENCY
            ).strip()
            if scope_type not in cls.SEAT_SCOPE_VALUES:
                scope_type = cls.SEAT_SCOPE_CONSTITUENCY

            scope_id = raw_rule.get("scope_id")
            try:
                scope_id = int(scope_id) if scope_id not in (None, "") else None
            except (TypeError, ValueError):
                scope_id = None

            normalized.append(
                {
                    "key": unique_key,
                    "label": label or _title_from_key(unique_key),
                    "selection_count": _coerce_positive_int(raw_rule.get("selection_count"), 1),
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                }
            )
        return normalized

    def configured_seat_rules(self):
        rules = self.normalize_seat_rules(self.seat_rules)
        if rules:
            return rules

        if self.election_type == self.TYPE_SCHOOL_COMMITTEE:
            return [
                {
                    "key": ElectionCandidate.CATEGORY_SCHOOL,
                    "label": "Representatives",
                    "selection_count": self.school_selection_count,
                    "scope_type": self.SEAT_SCOPE_CONSTITUENCY,
                    "scope_id": self.effective_constituency_id(),
                }
            ]

        rules = []
        if self.general_selection_count:
            rules.append(
                {
                    "key": ElectionCandidate.CATEGORY_GENERAL,
                    "label": "General representatives",
                    "selection_count": self.general_selection_count,
                    "scope_type": self.CONSTITUENCY_UNIVERSITY,
                    "scope_id": None,
                }
            )
        if self.election_type == self.TYPE_SRC:
            rules.append(
                {
                    "key": ElectionCandidate.CATEGORY_SCHOOL,
                    "label": "School representatives",
                    "selection_count": self.school_selection_count,
                    "scope_type": self.CONSTITUENCY_SCHOOL,
                    "scope_id": None,
                }
            )
        return rules

    def seat_rule_for(self, category):
        for rule in self.configured_seat_rules():
            if rule["key"] == category:
                return rule
        return None

    def seat_label_for(self, category):
        rule = self.seat_rule_for(category)
        if rule:
            return rule["label"]
        return dict(ElectionCandidate.CATEGORY_CHOICES).get(category, _title_from_key(category))

    def effective_constituency_type(self):
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and self.school_id:
            return self.CONSTITUENCY_SCHOOL
        return self.constituency_type or self.CONSTITUENCY_UNIVERSITY

    def effective_constituency_id(self):
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and self.school_id:
            return self.school_id
        return self.constituency_id

    def _student_scope_id(self, student, scope_type):
        if scope_type == self.CONSTITUENCY_SCHOOL:
            return student.school_id
        if scope_type == self.CONSTITUENCY_CENTER:
            return student.center_id
        if scope_type == self.CONSTITUENCY_DEPARTMENT:
            return student.department_id
        if scope_type == self.CONSTITUENCY_PROGRAM:
            return student.program_id
        if scope_type == self.CONSTITUENCY_COHORT:
            detail = getattr(student, "student_detail", None)
            return getattr(detail, "current_year", None) if detail else None
        return None

    def _matches_eligibility_filters(self, student):
        filters = self.voter_eligibility if isinstance(self.voter_eligibility, dict) else {}
        scope_fields = {
            "school": self.CONSTITUENCY_SCHOOL,
            "center": self.CONSTITUENCY_CENTER,
            "department": self.CONSTITUENCY_DEPARTMENT,
            "program": self.CONSTITUENCY_PROGRAM,
            "current_year": self.CONSTITUENCY_COHORT,
        }
        for field_name, scope_type in scope_fields.items():
            allowed = filters.get(f"{field_name}_ids", filters.get(f"{field_name}s", filters.get(field_name)))
            if allowed in (None, "", []):
                continue
            if not isinstance(allowed, (list, tuple, set)):
                allowed = [allowed]
            allowed_values = {str(value) for value in allowed if value not in (None, "")}
            if allowed_values and str(self._student_scope_id(student, scope_type)) not in allowed_values:
                return False
        return True

    def student_matches_constituency(self, student):
        constituency_type = self.effective_constituency_type()
        constituency_id = self.effective_constituency_id()
        if constituency_type not in self.CONSTITUENCY_VALUES:
            return False
        if constituency_type != self.CONSTITUENCY_UNIVERSITY and constituency_id:
            if str(self._student_scope_id(student, constituency_type)) != str(constituency_id):
                return False
        return self._matches_eligibility_filters(student)

    def results_visible_to_students(self):
        rules = self.result_publication_rules if isinstance(self.result_publication_rules, dict) else {}
        return self.status == self.STATUS_PUBLISHED or bool(rules.get("show_live_results", True))

    def clean(self):
        self.election_type = _normalized_key(self.election_type or self.election_type_label, self.TYPE_STUDENT_COUNCIL)
        if not self.election_type_label:
            self.election_type_label = self.get_election_type_display()
        if self.constituency_type not in self.CONSTITUENCY_VALUES:
            raise ValidationError({"constituency_type": "Select a supported election constituency."})
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and self.school_id:
            self.constituency_type = self.CONSTITUENCY_SCHOOL
            self.constituency_id = self.school_id
        if self.constituency_type == self.CONSTITUENCY_SCHOOL and self.constituency_id and not self.school_id:
            self.school_id = self.constituency_id
        self.seat_rules = self.normalize_seat_rules(self.seat_rules)
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError({"ends_at": "Voting must close after it starts."})
        if self.constituency_type != self.CONSTITUENCY_UNIVERSITY and not (
            self.constituency_id or self.constituency_label
        ):
            raise ValidationError({"constituency_id": "Select or name the election constituency."})
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and not (
            self.school_id or self.constituency_id
        ):
            raise ValidationError({"school": "Select the election constituency."})
        if self.election_type == self.TYPE_SCHOOL_COMMITTEE and not self.school_selection_count and not self.seat_rules:
            raise ValidationError({"school_selection_count": "Configure the required selection count."})

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
        if self.election_type == self.TYPE_SRC and category == ElectionCandidate.CATEGORY_SCHOOL and school_id:
            seat = self.school_seats.filter(school_id=school_id).first()
            if seat:
                return seat.seat_count
        rule = self.seat_rule_for(category)
        if rule:
            return _coerce_positive_int(rule.get("selection_count"))
        if category == ElectionCandidate.CATEGORY_GENERAL:
            return self.general_selection_count
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
    category = models.CharField(max_length=80, default=CATEGORY_GENERAL)
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

    def get_category_display(self):
        if self.election_id:
            return self.election.seat_label_for(self.category)
        return dict(self.CATEGORY_CHOICES).get(self.category, _title_from_key(self.category))

    def clean(self):
        if self.student and self.student.role != Profile.ROLE_STUDENT:
            raise ValidationError({"student": "Election candidates must be students."})
        if not self.display_name and not self.student_id:
            raise ValidationError({"display_name": "Candidate name is required."})
        if not self.election_id:
            return
        self.category = _normalized_key(self.category, self.CATEGORY_GENERAL)
        rule = self.election.seat_rule_for(self.category)
        if not rule:
            raise ValidationError({"category": "Select a configured ballot category."})
        if rule.get("scope_type") == Election.CONSTITUENCY_SCHOOL and not (
            self.school_id or self.election.school_id or rule.get("scope_id")
        ):
            raise ValidationError({"school": "School-scoped candidates must belong to a school."})
        if (
            self.election.effective_constituency_type() == Election.CONSTITUENCY_SCHOOL
            and self.school_id
            and self.election.effective_constituency_id()
            and self.school_id != self.election.effective_constituency_id()
        ):
            raise ValidationError({"school": "Candidate school must match the election constituency."})
        nomination_rules = self.election.nomination_rules if isinstance(self.election.nomination_rules, dict) else {}
        if nomination_rules.get("require_student_profile") and not self.student_id:
            raise ValidationError({"student": "Select a linked student for this candidate."})
        if (
            self.student_id
            and nomination_rules.get("candidate_must_match_constituency", True)
            and not self.election.student_matches_constituency(self.student)
        ):
            raise ValidationError({"student": "Candidate must match the election constituency."})

    def save(self, *args, **kwargs):
        if self.student_id:
            if not self.display_name:
                user = self.student.user
                self.display_name = f"{user.first_name} {user.last_name}".strip() or user.username
            if not self.student_identifier:
                self.student_identifier = self.student.student_id
            if not self.school_id and self.student.school_id:
                self.school = self.student.school
        if self.election_id:
            self.category = _normalized_key(self.category, self.CATEGORY_GENERAL)
            rule = self.election.seat_rule_for(self.category)
            if rule and rule.get("scope_type") == Election.CONSTITUENCY_SCHOOL and not self.school_id:
                if rule.get("scope_id"):
                    self.school_id = rule["scope_id"]
                elif self.election.effective_constituency_type() == Election.CONSTITUENCY_SCHOOL:
                    self.school_id = self.election.effective_constituency_id()
        self.full_clean()
        return super().save(*args, **kwargs)


class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="election_votes")
    candidate = models.ForeignKey(ElectionCandidate, on_delete=models.CASCADE, related_name="votes")
    category = models.CharField(max_length=80, default=ElectionCandidate.CATEGORY_GENERAL)
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

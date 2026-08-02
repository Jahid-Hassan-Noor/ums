import os
import uuid

from django.db import models
from django.utils import timezone


def application_document_path(instance, filename):
    application_id = instance.application_id or "draft"
    safe_name = f"{uuid.uuid4().hex}{os.path.splitext(filename)[1]}"
    return f"applications/{application_id}/{instance.document_type}/{safe_name}"


class Applicant(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="applicant_detail",
    )
    applicant_id = models.CharField(max_length=50, blank=True, db_index=True)
    phone = models.CharField(max_length=40, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    country_of_residence = models.CharField(max_length=100, blank=True)
    passport_or_identity_no = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def user(self):
        return self.profile.user

    def __str__(self):
        return str(self.profile.user)


class ApplicationIntake(models.Model):
    TYPE_UNDERGRADUATE_OCTOBER = "undergraduate_october"
    TYPE_UNDERGRADUATE_MARCH = "undergraduate_march"
    TYPE_POSTGRADUATE = "postgraduate"
    TYPE_FOUNDATION = "foundation"
    TYPE_LANGUAGE_CENTRE = "lc"
    APPLICATION_TYPE_CHOICES = [
        (TYPE_UNDERGRADUATE_OCTOBER, "Undergraduate October"),
        (TYPE_UNDERGRADUATE_MARCH, "Undergraduate March"),
        (TYPE_POSTGRADUATE, "Postgraduate"),
        (TYPE_FOUNDATION, "Foundation"),
        (TYPE_LANGUAGE_CENTRE, "Language Centre"),
    ]

    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=255)
    application_type = models.CharField(
        max_length=30,
        choices=APPLICATION_TYPE_CHOICES,
        default=TYPE_UNDERGRADUATE_OCTOBER,
    )
    academic_year = models.CharField(max_length=20, blank=True)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_active", "-opens_at", "title")

    def __str__(self):
        return self.code


class ApplicationProgramme(models.Model):
    LEVEL_FOUNDATION = "foundation"
    LEVEL_UNDERGRADUATE = "undergraduate"
    LEVEL_POSTGRADUATE = "postgraduate"
    LEVEL_CHOICES = [
        (LEVEL_FOUNDATION, "Foundation"),
        (LEVEL_UNDERGRADUATE, "Undergraduate"),
        (LEVEL_POSTGRADUATE, "Postgraduate"),
    ]

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=255)
    level = models.CharField(
        max_length=30,
        choices=LEVEL_CHOICES,
        default=LEVEL_UNDERGRADUATE,
    )
    school = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.code


class AdmissionApplication(models.Model):
    STEP_PROGRAMME = "programme"
    STEP_PERSONAL = "personal"
    STEP_ACADEMIC = "academic"
    STEP_SCHOLARSHIP = "scholarship"
    STEP_DOCUMENTS = "documents"
    STEP_TRUTH = "truth"
    STEP_SUBMITTED = "submitted"
    STEP_CHOICES = [
        (STEP_PROGRAMME, "Programme Selection"),
        (STEP_PERSONAL, "Personal Information"),
        (STEP_ACADEMIC, "Academic Information"),
        (STEP_SCHOLARSHIP, "Scholarship Application"),
        (STEP_DOCUMENTS, "Documents Upload"),
        (STEP_TRUTH, "Statement of Truth"),
        (STEP_SUBMITTED, "Submitted"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_SCREENING = "screening"
    STATUS_INFO_REQUESTED = "info_requested"
    STATUS_SCHOLARSHIP_REVIEW = "scholarship_review"
    STATUS_INTERVIEW = "interview"
    STATUS_OFFERED = "offered"
    STATUS_WAITLISTED = "waitlisted"
    STATUS_REJECTED = "rejected"
    STATUS_ENROLLED = "enrolled"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_SCREENING, "Screening"),
        (STATUS_INFO_REQUESTED, "Information Requested"),
        (STATUS_SCHOLARSHIP_REVIEW, "Scholarship Review"),
        (STATUS_INTERVIEW, "Interview"),
        (STATUS_OFFERED, "Offered"),
        (STATUS_WAITLISTED, "Waitlisted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_ENROLLED, "Enrolled"),
        (STATUS_WITHDRAWN, "Withdrawn"),
    ]

    MODE_FULL_TIME = "full_time"
    MODE_PART_TIME = "part_time"
    MODE_CHOICES = [
        (MODE_FULL_TIME, "Full-Time"),
        (MODE_PART_TIME, "Part-Time"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_number = models.CharField(max_length=40, unique=True, blank=True)
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    intake = models.ForeignKey(
        ApplicationIntake,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    application_type = models.CharField(
        max_length=30,
        choices=ApplicationIntake.APPLICATION_TYPE_CHOICES,
        default=ApplicationIntake.TYPE_UNDERGRADUATE_OCTOBER,
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    current_step = models.CharField(
        max_length=30,
        choices=STEP_CHOICES,
        default=STEP_PROGRAMME,
    )
    mode_of_study = models.CharField(
        max_length=30,
        choices=MODE_CHOICES,
        default=MODE_FULL_TIME,
    )
    programme_preferences = models.JSONField(default=list, blank=True)
    personal_information = models.JSONField(default=dict, blank=True)
    academic_information = models.JSONField(default=dict, blank=True)
    scholarship_requested = models.BooleanField(default=False)
    scholarship_information = models.JSONField(default=dict, blank=True)
    statement_accepted = models.BooleanField(default=False)
    statement_accepted_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_admission_applications",
    )
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at")

    def __str__(self):
        return self.application_number or str(self.id)

    def save(self, *args, **kwargs):
        if not self.application_number:
            prefix = timezone.now().strftime("AIU-%Y%m")
            self.application_number = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        if self.statement_accepted and not self.statement_accepted_at:
            self.statement_accepted_at = timezone.now()
        super().save(*args, **kwargs)


class ScholarshipApplication(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_SHORTLISTED = "shortlisted"
    STATUS_AWARDED = "awarded"
    STATUS_NOT_AWARDED = "not_awarded"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_SHORTLISTED, "Shortlisted"),
        (STATUS_AWARDED, "Awarded"),
        (STATUS_NOT_AWARDED, "Not Awarded"),
        (STATUS_WITHDRAWN, "Withdrawn"),
    ]

    application = models.OneToOneField(
        AdmissionApplication,
        on_delete=models.CASCADE,
        related_name="scholarship_application",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    household_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    dependents_count = models.PositiveSmallIntegerField(default=0)
    personal_statement = models.TextField(blank=True)
    financial_need_notes = models.TextField(blank=True)
    socioeconomic_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    communication_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attitude_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    statement_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_scholarship_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Scholarship {self.application.application_number}"


class ApplicationDocument(models.Model):
    STATUS_UPLOADED = "uploaded"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Uploaded"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    TYPE_PASSPORT = "passport"
    TYPE_PHOTO = "photo"
    TYPE_TRANSCRIPT = "academic_transcript"
    TYPE_CERTIFICATE = "certificate"
    TYPE_ENGLISH = "english_proficiency"
    TYPE_FINANCIAL = "financial_statement"
    TYPE_PERSONAL_STATEMENT = "personal_statement"
    TYPE_REFERENCE = "reference"
    TYPE_OTHER = "other"
    DOCUMENT_TYPE_CHOICES = [
        (TYPE_PASSPORT, "Passport or Identity Document"),
        (TYPE_PHOTO, "Passport Photo"),
        (TYPE_TRANSCRIPT, "Academic Transcript"),
        (TYPE_CERTIFICATE, "Academic Certificate"),
        (TYPE_ENGLISH, "English Proficiency"),
        (TYPE_FINANCIAL, "Financial Statement"),
        (TYPE_PERSONAL_STATEMENT, "Personal Statement"),
        (TYPE_REFERENCE, "Reference Letter"),
        (TYPE_OTHER, "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        AdmissionApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to=application_document_path)
    original_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_UPLOADED)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_application_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self):
        return f"{self.application.application_number} {self.document_type}"


class ApplicationStatusEvent(models.Model):
    application = models.ForeignKey(
        AdmissionApplication,
        on_delete=models.CASCADE,
        related_name="status_events",
    )
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.application.application_number}: {self.to_status}"

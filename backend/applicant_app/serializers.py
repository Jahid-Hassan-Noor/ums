from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from admin_app.settings_registry import setting_value
from auth_app.models import Profile, ensure_role_detail, prune_role_details
from auth_app.password_policy import password_policy_errors
from applicant_app.admissions_setup import (
    admission_status_choices,
    admissions_setup,
    document_type_config,
    is_image_document_type,
)
from applicant_app.countries import COUNTRY_CHOICES
from core.media_access import protected_media_url
from core.upload_security import (
    ALLOWED_IMAGE_EXTENSIONS,
    IMAGE_EXTENSION_LABEL,
    image_file_extension,
    image_upload_error,
)
from . import models


User = get_user_model()
class ApplicantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = models.Applicant
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "nationality",
            "country_of_residence",
            "passport_or_identity_no",
            "is_active",
            "created_at",
            "updated_at",
        )

    def get_role(self, applicant):
        return Profile.ROLE_APPLICANT


class ApplicantRegisterSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=r"^[\w.@+-]+\Z",
        max_length=150,
        error_messages={
            "invalid": "Username may contain only letters, numbers, and @/./+/-/_ characters."
        },
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    phone = serializers.CharField(max_length=40)
    nationality = serializers.ChoiceField(choices=COUNTRY_CHOICES)
    country_of_residence = serializers.ChoiceField(choices=COUNTRY_CHOICES)
    passport_or_identity_no = serializers.CharField(max_length=100)

    def validate_username(self, value):
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("This username is already taken.")
        if User.objects.filter(email__iexact=username).exists():
            raise serializers.ValidationError("This username is not available.")
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        if (
            User.objects.filter(email__iexact=email).exists()
            or User.objects.filter(username__iexact=email).exists()
        ):
            raise serializers.ValidationError("An account already exists for this email address.")
        return email

    def validate_passport_or_identity_no(self, value):
        identity_no = value.strip()
        if models.Applicant.objects.filter(passport_or_identity_no__iexact=identity_no).exists():
            raise serializers.ValidationError(
                "This passport or identity number is already registered."
            )
        return identity_no

    def validate_password(self, value):
        validate_password(value)
        errors = password_policy_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, attrs):
        for key in ("first_name", "last_name", "phone"):
            attrs[key] = attrs[key].strip()
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("confirm_password", None)
        email = validated_data.pop("email")
        username = validated_data.pop("username")
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=validated_data.pop("first_name").strip(),
            last_name=validated_data.pop("last_name").strip(),
        )
        profile, _created = Profile.objects.get_or_create(user=user)
        profile.role = Profile.ROLE_APPLICANT
        profile.phone = validated_data.get("phone", "")
        profile.save()
        prune_role_details(profile)
        ensure_role_detail(profile)
        user._state.fields_cache.pop("profile", None)
        applicant, _created = models.Applicant.objects.update_or_create(
            profile=profile,
            defaults=validated_data,
        )
        return applicant


class ApplicantLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError({"username": "Username is required."})
        return attrs


class ApplicantUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=40, required=False)
    nationality = serializers.ChoiceField(choices=COUNTRY_CHOICES, required=False)
    country_of_residence = serializers.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
    )
    passport_or_identity_no = serializers.CharField(max_length=100, required=False)

    def validate(self, attrs):
        for key in ("first_name", "last_name", "phone", "passport_or_identity_no"):
            if key in attrs:
                attrs[key] = attrs[key].strip()
        return attrs

    def update(self, applicant, validated_data):
        user_fields = []
        user = applicant.user

        for field in ("first_name", "last_name"):
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
                user_fields.append(field)

        if user_fields:
            user.save(update_fields=user_fields)

        applicant_fields = []
        for field, value in validated_data.items():
            setattr(applicant, field, value)
            applicant_fields.append(field)

        if applicant_fields:
            applicant.save(update_fields=applicant_fields + ["updated_at"])

        return applicant


class AdminApplicantUpdateSerializer(serializers.Serializer):
    username = serializers.RegexField(
        regex=r"^[\w.@+-]+\Z",
        max_length=150,
        required=False,
        error_messages={
            "invalid": "Username may contain only letters, numbers, and @/./+/-/_ characters."
        },
    )
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    nationality = serializers.ChoiceField(choices=COUNTRY_CHOICES, required=False)
    country_of_residence = serializers.ChoiceField(choices=COUNTRY_CHOICES, required=False)
    passport_or_identity_no = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def _applicant(self):
        return self.context.get("applicant")

    def validate_username(self, value):
        username = value.strip()
        applicant = self._applicant()
        queryset = User.objects.filter(username__iexact=username)
        if applicant:
            queryset = queryset.exclude(pk=applicant.user_id)
        if queryset.exists():
            raise serializers.ValidationError("This username is already taken.")
        if User.objects.filter(email__iexact=username).exclude(pk=applicant.user_id if applicant else None).exists():
            raise serializers.ValidationError("This username is not available.")
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        applicant = self._applicant()
        queryset = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email))
        if applicant:
            queryset = queryset.exclude(pk=applicant.user_id)
        if queryset.exists():
            raise serializers.ValidationError("An account already exists for this email address.")
        return email

    def validate_passport_or_identity_no(self, value):
        identity_no = value.strip()
        applicant = self._applicant()
        if not identity_no:
            return identity_no

        queryset = models.Applicant.objects.filter(passport_or_identity_no__iexact=identity_no)
        if applicant:
            queryset = queryset.exclude(pk=applicant.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "This passport or identity number is already registered."
            )
        return identity_no

    def validate(self, attrs):
        for key in ("first_name", "last_name", "phone"):
            if key in attrs and isinstance(attrs[key], str):
                attrs[key] = attrs[key].strip()
        return attrs


class ApplicationIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApplicationIntake
        fields = "__all__"


class ApplicationProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ApplicationProgramme
        fields = "__all__"


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    document_type = serializers.CharField(max_length=50)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = models.ApplicationDocument
        fields = (
            "id",
            "application",
            "document_type",
            "file",
            "file_url",
            "original_name",
            "status",
            "notes",
            "uploaded_at",
            "reviewed_at",
        )
        read_only_fields = (
            "id",
            "application",
            "file_url",
            "original_name",
            "status",
            "notes",
            "uploaded_at",
            "reviewed_at",
        )

    def get_file_url(self, document):
        if not document.file:
            return None
        return protected_media_url(document.file.name)

    def validate_file(self, upload):
        maximum_bytes = setting_value("workflow", "applicant_max_upload_mb") * 1024 * 1024
        if upload.size > maximum_bytes:
            raise serializers.ValidationError(
                f"Applicant documents must be {setting_value('workflow', 'applicant_max_upload_mb')} MB or smaller."
            )
        return upload

    def validate(self, attrs):
        upload = attrs.get("file")
        document_type = attrs.get("document_type")
        if not document_type_config(document_type):
            raise serializers.ValidationError(
                {"document_type": "This document type is not enabled for the current admissions workflow."}
            )
        if not upload:
            return attrs

        extension = image_file_extension(upload)
        maximum_bytes = setting_value("workflow", "applicant_max_upload_mb") * 1024 * 1024
        maximum_label = f"{setting_value('workflow', 'applicant_max_upload_mb')} MB"
        if is_image_document_type(document_type):
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise serializers.ValidationError(
                    {
                        "file": (
                            "Identity and photo documents must be image files: "
                            f"{IMAGE_EXTENSION_LABEL}."
                        )
                    }
                )
            error = image_upload_error(
                upload,
                field_label="Applicant identity/photo document",
                max_bytes=maximum_bytes,
                max_size_label=maximum_label,
            )
            if error:
                raise serializers.ValidationError({"file": error})
            return attrs

        allowed = {
            item.strip().lower().lstrip(".")
            for item in setting_value("workflow", "applicant_allowed_file_extensions").split(",")
            if item.strip()
        }
        if extension not in allowed:
            raise serializers.ValidationError(
                {"file": f"Allowed file extensions: {', '.join(sorted(allowed))}."}
            )
        if extension in ALLOWED_IMAGE_EXTENSIONS:
            error = image_upload_error(
                upload,
                field_label="Applicant document image",
                max_bytes=maximum_bytes,
                max_size_label=maximum_label,
            )
            if error:
                raise serializers.ValidationError({"file": error})
        return attrs


class ScholarshipApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScholarshipApplication
        fields = (
            "id",
            "application",
            "status",
            "household_income",
            "dependents_count",
            "personal_statement",
            "financial_need_notes",
            "socioeconomic_score",
            "communication_score",
            "attitude_score",
            "statement_score",
            "review_notes",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "application",
            "status",
            "socioeconomic_score",
            "communication_score",
            "attitude_score",
            "statement_score",
            "review_notes",
            "reviewed_at",
            "created_at",
            "updated_at",
        )


class ApplicationStatusEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.ApplicationStatusEvent
        fields = (
            "id",
            "from_status",
            "to_status",
            "note",
            "created_by_name",
            "created_at",
        )

    def get_created_by_name(self, event):
        if not event.created_by:
            return None
        user = event.created_by.user
        return user.get_full_name() or user.username


class AdmissionApplicationSerializer(serializers.ModelSerializer):
    application_type = serializers.CharField()
    applicant = ApplicantSerializer(read_only=True)
    intake_detail = ApplicationIntakeSerializer(source="intake", read_only=True)
    scholarship_application = ScholarshipApplicationSerializer(read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    status_events = ApplicationStatusEventSerializer(many=True, read_only=True)

    class Meta:
        model = models.AdmissionApplication
        fields = (
            "id",
            "application_number",
            "applicant",
            "intake",
            "intake_detail",
            "application_type",
            "status",
            "current_step",
            "mode_of_study",
            "programme_preferences",
            "personal_information",
            "academic_information",
            "scholarship_requested",
            "scholarship_information",
            "scholarship_application",
            "statement_accepted",
            "statement_accepted_at",
            "submitted_at",
            "review_notes",
            "documents",
            "status_events",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "application_number",
            "applicant",
            "status",
            "statement_accepted_at",
            "submitted_at",
            "review_notes",
            "documents",
            "status_events",
            "created_at",
            "updated_at",
        )

    def validate_programme_preferences(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Programme preferences must be a list.")
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if len(normalized) != len(set(normalized)):
            raise serializers.ValidationError("Programme preferences must be different.")
        return normalized

    def validate_application_type(self, value):
        normalized = str(value).strip()
        aliases = {
            "undergraduate": models.ApplicationIntake.TYPE_UNDERGRADUATE_OCTOBER,
        }
        normalized = aliases.get(normalized, normalized)
        valid_values = {choice[0] for choice in models.ApplicationIntake.APPLICATION_TYPE_CHOICES}
        if normalized not in valid_values:
            raise serializers.ValidationError("Select a valid application type.")
        return normalized

    def validate(self, attrs):
        setup = admissions_setup()
        scholarship_requested = attrs.get(
            "scholarship_requested",
            getattr(self.instance, "scholarship_requested", False),
        )
        if scholarship_requested and not setup["scholarship_enabled"]:
            raise serializers.ValidationError(
                {"scholarship_requested": "Scholarship applications are not currently enabled."}
            )
        return attrs


class ApplicationSubmitSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Please confirm the statement of truth before submitting.")
        return value


class StaffApplicationStatusSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=30)
    note = serializers.CharField(required=False, allow_blank=True)
    review_notes = serializers.CharField(required=False, allow_blank=True)
    interview_at = serializers.DateTimeField(required=False, allow_null=True)
    interview_location = serializers.CharField(required=False, allow_blank=True, max_length=255)
    interview_details = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        enabled_statuses = {choice[0] for choice in admission_status_choices()}
        if value not in enabled_statuses:
            raise serializers.ValidationError("This status is not enabled for the current admissions workflow.")
        return value


class StaffDocumentReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=models.ApplicationDocument.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class StaffScholarshipReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=models.ScholarshipApplication.STATUS_CHOICES)
    socioeconomic_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    communication_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    attitude_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    statement_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    review_notes = serializers.CharField(required=False, allow_blank=True)

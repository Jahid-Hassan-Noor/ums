from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from admin_app import models
from admin_app.role_config import SPECIAL_OWNER_ROLES, resolve_role_ownership
from auth_app.password_policy import password_policy_errors
from core.media_access import public_profile_picture_url
from core.upload_security import image_upload_error
from student_app.models import Student
from teacher_app.models import TeacherScopeAssignment


User = get_user_model()
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024


def managed_hostel_room(room_code, *, lock=False):
    if not isinstance(room_code, str):
        return None
    normalized = room_code.strip().upper()
    if not normalized:
        return None
    parts = normalized.split("-")
    prefixes = ["-".join(parts[:index]) for index in range(1, len(parts) + 1)]
    rooms = models.HostelRoom.objects.filter(code__in=prefixes).order_by("pk")
    if lock:
        rooms = rooms.select_for_update()
    return max(rooms, key=lambda room: len(room.code), default=None)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        errors = password_policy_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        errors = password_policy_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class TeacherScopeInputSerializer(serializers.Serializer):
    school_id = serializers.PrimaryKeyRelatedField(
        source="school",
        queryset=models.School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    center_id = serializers.PrimaryKeyRelatedField(
        source="center",
        queryset=models.Center.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        if bool(attrs.get("school")) == bool(attrs.get("center")):
            raise serializers.ValidationError("Select exactly one school or centre.")
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=models.Profile.ROLE_CHOICES,
        required=False,
        default=models.Profile.ROLE_STUDENT,
    )
    ums_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True)
    room = serializers.CharField(required=False, allow_blank=True, write_only=True)
    designation = serializers.CharField(required=False, allow_blank=True, write_only=True)
    teacher_assignments = TeacherScopeInputSerializer(
        many=True,
        required=False,
        write_only=True,
    )
    school_id = serializers.PrimaryKeyRelatedField(
        source="school",
        queryset=models.School.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )
    center_id = serializers.PrimaryKeyRelatedField(
        source="center",
        queryset=models.Center.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        source="unit",
        queryset=models.Unit.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )
    department_id = serializers.PrimaryKeyRelatedField(
        source="department",
        queryset=models.Department.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )
    program_id = serializers.PrimaryKeyRelatedField(
        source="program",
        queryset=models.Program.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "role",
            "ums_id",
            "phone_number",
            "room",
            "designation",
            "teacher_assignments",
            "school_id",
            "center_id",
            "unit_id",
            "department_id",
            "program_id",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        errors = password_policy_errors(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, attrs):
        role = attrs.get("role", models.Profile.ROLE_STUDENT)
        school = attrs.get("school")
        center = attrs.get("center")
        unit = attrs.get("unit")
        department = attrs.get("department")
        teacher_assignments = attrs.get("teacher_assignments", [])

        if role == models.Profile.ROLE_ADMIN:
            raise serializers.ValidationError(
                {"role": "Admin accounts must be created with Django createsuperuser."}
            )
        if role == models.Profile.ROLE_APPLICANT:
            raise serializers.ValidationError(
                {"role": "Applicant accounts must be created from the applicant registration page."}
            )
        if unit:
            unit_scopes = [
                ("school", unit.school) if unit.school_id else None,
                ("center", unit.center) if unit.center_id else None,
            ]
            unit_scopes = [scope for scope in unit_scopes if scope]
            if not unit_scopes:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit must belong to a school or centre."}
                )
            if len(unit_scopes) > 1 and not (school or center):
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit belongs to more than one scope. Select its school or centre too."}
                )
            if school and unit.school_id and unit.school_id != school.id:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit does not belong to the selected school."}
                )
            if center and unit.center_id and unit.center_id != center.id:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit does not belong to the selected centre."}
                )
            if department and unit.department_id and unit.department_id != department.id:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit does not belong to the selected department."}
                )
            if not school and not center and len(unit_scopes) == 1:
                kind, unit_parent = unit_scopes[0]
                attrs[kind] = unit_parent
                school = attrs.get("school")
                center = attrs.get("center")
            if not department and unit.department_id:
                attrs["department"] = unit.department
                department = unit.department

        if department:
            if school and department.school_id and department.school_id != school.id:
                raise serializers.ValidationError(
                    {"department_id": "Selected department does not belong to the selected school."}
                )
            if center and department.center_id and department.center_id != center.id:
                raise serializers.ValidationError(
                    {"department_id": "Selected department does not belong to the selected centre."}
                )
            if not school and not center:
                if department.school_id:
                    attrs["school"] = department.school
                    school = department.school
                elif department.center_id:
                    attrs["center"] = department.center
                    center = department.center

        if role == models.Profile.ROLE_EXECUTIVE:
            if not unit:
                raise serializers.ValidationError(
                    {"unit_id": "Executive accounts must be assigned to a specific unit."}
                )
            if bool(school) == bool(center):
                raise serializers.ValidationError(
                    {"unit_id": "The selected executive unit must belong to exactly one school or centre."}
                )
            if school and unit.school_id != school.id:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit does not belong to the selected school."}
                )
            if center and unit.center_id != center.id:
                raise serializers.ValidationError(
                    {"unit_id": "Selected unit does not belong to the selected centre."}
                )
        if role in SPECIAL_OWNER_ROLES:
            try:
                ownership = resolve_role_ownership(
                    role,
                    school=school,
                    center=center,
                    unit=unit,
                    department=department,
                )
            except DjangoValidationError as error:
                raise serializers.ValidationError(error.message_dict) from error
            attrs.update(ownership)
            school = ownership["school"]
            center = ownership["center"]
            unit = ownership["unit"]
            department = ownership["department"]
        if school and center:
            raise serializers.ValidationError(
                {"school_id": "Assign only one school or centre."}
            )

        program = attrs.get("program")
        if program:
            if role != models.Profile.ROLE_STUDENT:
                raise serializers.ValidationError(
                    {"program_id": "Only student accounts can be assigned a program."}
                )
            if school and program.school_id != school.id:
                raise serializers.ValidationError(
                    {"program_id": "Selected program does not belong to the selected school."}
                )
            if center and program.center_id != center.id:
                raise serializers.ValidationError(
                    {"program_id": "Selected program does not belong to the selected centre."}
                )
            if not school and not center:
                if program.school_id:
                    attrs["school"] = program.school
                    school = program.school
                elif program.center_id:
                    attrs["center"] = program.center
                    center = program.center

        if role == models.Profile.ROLE_STUDENT and bool(school) == bool(center):
            raise serializers.ValidationError(
                {"school_id": "Student accounts must be assigned to exactly one school or centre."}
            )

        if role == models.Profile.ROLE_STUDENT:
            room_code = attrs.get("room", "").strip().upper()
            attrs["room"] = room_code
            if room_code:
                managed_room = managed_hostel_room(room_code)
                if managed_room:
                    occupied = Student.objects.filter(
                        Q(room=managed_room.code)
                        | Q(room__startswith=f"{managed_room.code}-")
                    ).count()
                    if occupied >= managed_room.capacity:
                        raise serializers.ValidationError(
                            {"room": f"Hostel room {managed_room.code} is full."}
                        )

        if role == models.Profile.ROLE_TEACHER:
            if not teacher_assignments and bool(school) != bool(center):
                teacher_assignments = [{"school": school, "center": center}]
            if not teacher_assignments:
                raise serializers.ValidationError(
                    {"teacher_assignments": "Teacher accounts must be assigned to at least one school or centre."}
                )

            seen = set()
            for assignment in teacher_assignments:
                assignment_school = assignment.get("school")
                assignment_center = assignment.get("center")
                key = (
                    "school",
                    assignment_school.id,
                ) if assignment_school else ("center", assignment_center.id)
                if key in seen:
                    raise serializers.ValidationError(
                        {"teacher_assignments": "Do not assign the same school or centre more than once."}
                    )
                seen.add(key)

            primary = teacher_assignments[0]
            attrs["school"] = primary.get("school")
            attrs["center"] = primary.get("center")
            attrs["teacher_assignments"] = teacher_assignments
        elif teacher_assignments:
            raise serializers.ValidationError(
                {"teacher_assignments": "Teacher assignments can only be used for teacher accounts."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data.pop("role", models.Profile.ROLE_STUDENT)
        ums_id = validated_data.pop("ums_id", "").strip()
        phone_number = validated_data.pop("phone_number", "").strip()
        room = validated_data.pop("room", "").strip().upper()
        designation = validated_data.pop("designation", "").strip()
        teacher_assignments = validated_data.pop("teacher_assignments", [])
        school = validated_data.pop("school", None)
        center = validated_data.pop("center", None)
        unit = validated_data.pop("unit", None)
        department = validated_data.pop("department", None)
        program = validated_data.pop("program", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        profile, _created = models.Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = phone_number
        profile.designation = designation
        profile.school = school
        profile.center = center
        profile.unit = unit
        profile.department = department
        if role == models.Profile.ROLE_STUDENT:
            profile.program = program
        if not department and unit and unit.department_id:
            profile.department = unit.department
        if role == models.Profile.ROLE_STUDENT:
            profile.student_id = ums_id
        else:
            profile.staff_id = ums_id
        profile.save()
        models.prune_role_details(profile)
        detail = models.ensure_role_detail(profile)
        if role == models.Profile.ROLE_STUDENT and detail and room:
            detail.room = room
            detail.save(update_fields=["room", "updated_at"])
        if role == models.Profile.ROLE_TEACHER:
            for index, assignment in enumerate(teacher_assignments):
                TeacherScopeAssignment.objects.create(
                    teacher=profile,
                    school=assignment.get("school"),
                    center=assignment.get("center"),
                    is_primary=index == 0,
                )
        user._state.fields_cache.pop("profile", None)
        return user


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    ums_id = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    is_email_verified = serializers.SerializerMethodField()
    is_account_banned = serializers.SerializerMethodField()
    executive_scope = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "ums_id",
            "phone_number",
            "profile_picture",
            "is_email_verified",
            "is_account_banned",
            "executive_scope",
        )

    def _profile(self, user):
        try:
            return user.profile
        except models.Profile.DoesNotExist:
            return None

    def get_role(self, user):
        profile = self._profile(user)
        if profile:
            return profile.role
        if user.is_staff or user.is_superuser:
            return models.Profile.ROLE_ADMIN
        return models.Profile.ROLE_STUDENT

    def get_ums_id(self, user):
        profile = self._profile(user)
        if not profile:
            return None
        if profile.role == models.Profile.ROLE_STUDENT:
            try:
                detail = getattr(profile, "student_detail")
            except (Student.DoesNotExist, Exception):
                detail = None
            if detail and detail.student_id:
                return detail.student_id
        detail_names = {
            models.Profile.ROLE_TEACHER: "teacher_detail",
            models.Profile.ROLE_EXECUTIVE: "executive_detail",
            models.Profile.ROLE_LIBRARIAN: "librarian_detail",
            models.Profile.ROLE_CATERER: "caterer_detail",
            models.Profile.ROLE_TECHNICIAN: "technician_detail",
            models.Profile.ROLE_ACCOUNTANT: "accountant_detail",
            models.Profile.ROLE_HR: "hr_detail",
            models.Profile.ROLE_ADMIN: "admin_detail",
        }
        detail_name = detail_names.get(profile.role)
        if detail_name:
            try:
                detail = getattr(profile, detail_name)
            except Exception:
                detail = None
            if detail and detail.staff_id:
                return detail.staff_id
        return profile.student_id or profile.staff_id or None

    def get_phone_number(self, user):
        profile = self._profile(user)
        if not profile:
            return None
        return profile.phone or None

    def get_profile_picture(self, user):
        profile = self._profile(user)
        if not profile or not profile.profile_picture:
            return None
        return public_profile_picture_url(profile)

    def get_is_email_verified(self, user):
        return bool(user.email)

    def get_is_account_banned(self, user):
        profile = self._profile(user)
        return not user.is_active or bool(profile and not profile.is_active)

    def get_executive_scope(self, user):
        profile = self._profile(user)
        if not profile or profile.role != models.Profile.ROLE_EXECUTIVE:
            return None

        scopes = []
        if profile.school_id:
            scopes.append(("school", profile.school))
        if profile.center_id:
            scopes.append(("center", profile.center))
        if profile.unit_id:
            if profile.unit.school_id:
                scopes.append(("school", profile.unit.school))
            if profile.unit.center_id:
                scopes.append(("center", profile.unit.center))

        unique_scopes = {}
        for kind, unit in scopes:
            if unit:
                unique_scopes[(kind, unit.id)] = (kind, unit)

        if len(unique_scopes) != 1:
            return {
                "kind": None,
                "id": None,
                "code": "",
                "name": "Unassigned",
                "academic_center": False,
                "academic_workflows": False,
                "semester_workflows": False,
                "academic_calendar_mode": "",
                "semester_calendar_group": "",
            }

        kind, unit = next(iter(unique_scopes.values()))
        academic_workflows = kind == "school" or unit.uses_semester_calendar()
        return {
            "kind": kind,
            "id": unit.id,
            "code": unit.code,
            "name": unit.name,
            "academic_center": bool(kind == "center" and unit.is_academic_center()),
            "academic_workflows": academic_workflows,
            "semester_workflows": academic_workflows,
            "academic_calendar_mode": unit.academic_calendar_mode if kind == "center" else "",
            "semester_calendar_group": unit.effective_semester_calendar_group()
            if kind == "center" and unit.uses_semester_calendar()
            else "",
            "unit_id": profile.unit_id,
            "unit_name": profile.unit.name if profile.unit_id else "",
        }


class ProfilePictureUpdateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.FileField(required=False, allow_empty_file=False)

    class Meta:
        model = models.Profile
        fields = ("profile_picture",)

    def validate_profile_picture(self, value):
        error = image_upload_error(
            value,
            field_label="Profile picture",
            max_bytes=MAX_PROFILE_PICTURE_SIZE,
            max_size_label="5 MB",
        )
        if error:
            raise serializers.ValidationError(error)
        return value

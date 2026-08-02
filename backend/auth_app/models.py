from django.apps import apps
from django.conf import settings
from django.db import models


class Profile(models.Model):
    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_EXECUTIVE = "executive"
    ROLE_LIBRARIAN = "librarian"
    ROLE_CATERER = "caterer"
    ROLE_TECHNICIAN = "technician"
    ROLE_ACCOUNTANT = "accountant"
    ROLE_HR = "hr"
    ROLE_ADMIN = "admin"
    ROLE_APPLICANT = "applicant"
    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_EXECUTIVE, "Executive"),
        (ROLE_LIBRARIAN, "Librarian"),
        (ROLE_CATERER, "Caterer"),
        (ROLE_TECHNICIAN, "Technician"),
        (ROLE_ACCOUNTANT, "Accountant"),
        (ROLE_HR, "Human Resources"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_APPLICANT, "Applicant"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/pictures/",
        null=True,
        blank=True,
    )
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_requested_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ROLE_DETAIL_RELATED_NAMES = {
        ROLE_STUDENT: "student_detail",
        ROLE_TEACHER: "teacher_detail",
        ROLE_EXECUTIVE: "executive_detail",
        ROLE_LIBRARIAN: "librarian_detail",
        ROLE_CATERER: "caterer_detail",
        ROLE_TECHNICIAN: "technician_detail",
        ROLE_ACCOUNTANT: "accountant_detail",
        ROLE_HR: "hr_detail",
        ROLE_ADMIN: "admin_detail",
        ROLE_APPLICANT: "applicant_detail",
    }
    ROLE_IDENTIFIER_FIELDS = {
        ROLE_STUDENT: "student_id",
        ROLE_TEACHER: "teacher_id",
        ROLE_EXECUTIVE: "executive_id",
        ROLE_LIBRARIAN: "librarian_id",
        ROLE_CATERER: "caterer_id",
        ROLE_TECHNICIAN: "technician_id",
        ROLE_ACCOUNTANT: "accountant_id",
        ROLE_HR: "hr_id",
        ROLE_ADMIN: "admin_id",
        ROLE_APPLICANT: "applicant_id",
    }
    MOVED_DETAIL_FIELDS = {
        "school",
        "center",
        "department",
        "unit",
        "program",
        "designation",
        "student_id",
        "staff_id",
    }

    class Meta:
        db_table = "admin_app_profile"

    def _detail_field_name(self, field_name):
        if field_name == "student_id":
            return "student_id" if self.role == self.ROLE_STUDENT else field_name
        if field_name == "staff_id" and self.role != self.ROLE_STUDENT:
            return self.ROLE_IDENTIFIER_FIELDS.get(self.role, field_name)
        return field_name

    def _role_detail(self):
        related_name = self.ROLE_DETAIL_RELATED_NAMES.get(self.role)
        if not related_name:
            return None
        try:
            return getattr(self, related_name)
        except Exception:
            return None

    def _get_detail_value(self, field_name, default=None):
        detail_field = self._detail_field_name(field_name)
        pending = getattr(self, "_pending_role_detail_values", {})
        if detail_field in pending:
            return pending[detail_field]
        detail = self._role_detail()
        if detail and hasattr(detail, detail_field):
            return getattr(detail, detail_field)
        return default

    def _set_detail_value(self, field_name, value):
        detail_field = self._detail_field_name(field_name)
        pending = getattr(self, "_pending_role_detail_values", {})
        pending[detail_field] = value
        self._pending_role_detail_values = pending
        detail = self._role_detail()
        if detail and hasattr(detail, detail_field):
            setattr(detail, detail_field, value)

    def _get_detail_id(self, field_name):
        detail_field = self._detail_field_name(field_name)
        pending = getattr(self, "_pending_role_detail_values", {})
        if f"{detail_field}_id" in pending:
            return pending[f"{detail_field}_id"]
        if detail_field in pending:
            value = pending[detail_field]
            return getattr(value, "pk", value)
        detail = self._role_detail()
        return getattr(detail, f"{detail_field}_id", None) if detail else None

    def _set_detail_id(self, field_name, value):
        detail_field = self._detail_field_name(field_name)
        pending = getattr(self, "_pending_role_detail_values", {})
        pending[f"{detail_field}_id"] = value
        self._pending_role_detail_values = pending
        detail = self._role_detail()
        if detail and hasattr(detail, f"{detail_field}_id"):
            setattr(detail, f"{detail_field}_id", value)

    @property
    def school(self):
        return self._get_detail_value("school")

    @school.setter
    def school(self, value):
        self._set_detail_value("school", value)

    @property
    def school_id(self):
        return self._get_detail_id("school")

    @school_id.setter
    def school_id(self, value):
        self._set_detail_id("school", value)

    @property
    def center(self):
        return self._get_detail_value("center")

    @center.setter
    def center(self, value):
        self._set_detail_value("center", value)

    @property
    def center_id(self):
        return self._get_detail_id("center")

    @center_id.setter
    def center_id(self, value):
        self._set_detail_id("center", value)

    @property
    def department(self):
        return self._get_detail_value("department")

    @department.setter
    def department(self, value):
        self._set_detail_value("department", value)

    @property
    def department_id(self):
        return self._get_detail_id("department")

    @department_id.setter
    def department_id(self, value):
        self._set_detail_id("department", value)

    @property
    def unit(self):
        return self._get_detail_value("unit")

    @unit.setter
    def unit(self, value):
        self._set_detail_value("unit", value)

    @property
    def unit_id(self):
        return self._get_detail_id("unit")

    @unit_id.setter
    def unit_id(self, value):
        self._set_detail_id("unit", value)

    @property
    def program(self):
        return self._get_detail_value("program")

    @program.setter
    def program(self, value):
        self._set_detail_value("program", value)

    @property
    def program_id(self):
        return self._get_detail_id("program")

    @program_id.setter
    def program_id(self, value):
        self._set_detail_id("program", value)

    @property
    def designation(self):
        return self._get_detail_value("designation", "")

    @designation.setter
    def designation(self, value):
        self._set_detail_value("designation", value)

    @property
    def student_id(self):
        return self._get_detail_value("student_id", "")

    @student_id.setter
    def student_id(self, value):
        self._set_detail_value("student_id", value)

    @property
    def staff_id(self):
        return self._get_detail_value("staff_id", "")

    @staff_id.setter
    def staff_id(self, value):
        self._set_detail_value("staff_id", value)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = [
                field for field in update_fields if field not in self.MOVED_DETAIL_FIELDS
            ]
        result = super().save(*args, **kwargs)
        ensure_role_detail(self)
        return result

    def __str__(self):
        return f"{self.user} ({self.role})"


class Admin(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="admin_detail",
    )
    admin_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    access_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_app_admin"
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.admin_id

    @staff_id.setter
    def staff_id(self, value):
        self.admin_id = value


AdminProfile = Admin


ROLE_DETAIL_MODELS = {
    Profile.ROLE_STUDENT: ("student_app", "Student"),
    Profile.ROLE_TEACHER: ("teacher_app", "Teacher"),
    Profile.ROLE_EXECUTIVE: ("executive_app", "Executive"),
    Profile.ROLE_LIBRARIAN: ("librarian_app", "Librarian"),
    Profile.ROLE_CATERER: ("caterer_app", "Caterer"),
    Profile.ROLE_TECHNICIAN: ("technician_app", "Technician"),
    Profile.ROLE_ACCOUNTANT: ("accountant_app", "Accountant"),
    Profile.ROLE_HR: ("hr_app", "HRStaff"),
    Profile.ROLE_ADMIN: ("auth_app", "Admin"),
    Profile.ROLE_APPLICANT: ("applicant_app", "Applicant"),
}


def role_for_user(user):
    return Profile.ROLE_ADMIN if user.is_superuser else Profile.ROLE_STUDENT


def role_detail_defaults(profile):
    identifier_field = Profile.ROLE_IDENTIFIER_FIELDS.get(profile.role)
    defaults = {}
    if identifier_field:
        defaults[identifier_field] = profile._get_detail_value(identifier_field, "")
    if profile.role not in {Profile.ROLE_STUDENT, Profile.ROLE_APPLICANT}:
        defaults["designation"] = profile.designation
    if profile.role == Profile.ROLE_APPLICANT:
        defaults["phone"] = profile.phone
    return defaults


def ensure_role_detail(profile):
    model_path = ROLE_DETAIL_MODELS.get(profile.role)
    if not model_path:
        return None

    try:
        detail_model = apps.get_model(*model_path)
    except LookupError:
        return None

    defaults = role_detail_defaults(profile)
    detail, _created = detail_model.objects.get_or_create(
        profile=profile,
        defaults=defaults,
    )

    changed_fields = []
    pending = getattr(profile, "_pending_role_detail_values", {})
    for field_name, value in pending.items():
        model_field_name = field_name.removesuffix("_id")
        try:
            detail._meta.get_field(model_field_name)
        except Exception:
            continue
        setattr(detail, field_name, value)
        changed_fields.append(model_field_name)
    for field_name, value in defaults.items():
        if value and hasattr(detail, field_name) and not getattr(detail, field_name):
            setattr(detail, field_name, value)
            changed_fields.append(field_name)
    if changed_fields:
        detail.save(update_fields=sorted(set(changed_fields)) + ["updated_at"])
    profile._pending_role_detail_values = {}
    related_name = Profile.ROLE_DETAIL_RELATED_NAMES.get(profile.role)
    if related_name:
        setattr(profile, related_name, detail)

    return detail


def prune_role_details(profile):
    for role, model_path in ROLE_DETAIL_MODELS.items():
        if role == profile.role:
            continue
        try:
            detail_model = apps.get_model(*model_path)
        except LookupError:
            continue
        detail_model.objects.filter(profile=profile).delete()

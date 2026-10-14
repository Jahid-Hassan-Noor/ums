from django.db.models import Q
from rest_framework import serializers

from admin_app import models
from admin_app.settings_registry import (
    hostel_policy_settings,
    hostel_residence_type_label,
    hostel_residence_type_values,
    hostel_room_code,
    normalize_hostel_room_code,
)
from student_app.models import Student


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.School
        fields = "__all__"


class CenterSerializer(serializers.ModelSerializer):
    center_type_label = serializers.CharField(source="get_center_type_display", read_only=True)
    academic_calendar_mode_label = serializers.CharField(
        source="get_academic_calendar_mode_display",
        read_only=True,
    )
    academic_workflows = serializers.SerializerMethodField()
    semester_calendar_group_effective = serializers.SerializerMethodField()

    class Meta:
        model = models.Center
        fields = "__all__"

    def validate(self, attrs):
        center_type = attrs.get("center_type", getattr(self.instance, "center_type", models.Center.CENTER_ACADEMIC))
        if center_type == "administrative":
            center_type = models.Center.CENTER_NON_ACADEMIC
            attrs["center_type"] = center_type
        calendar_mode = attrs.get(
            "academic_calendar_mode",
            getattr(self.instance, "academic_calendar_mode", models.Center.CALENDAR_SEMESTER),
        )
        if center_type != models.Center.CENTER_ACADEMIC:
            attrs["academic_calendar_mode"] = models.Center.CALENDAR_SEMESTER
            attrs["semester_calendar_group"] = ""
            attrs["annual_session_limit"] = 0
            return attrs
        if calendar_mode == models.Center.CALENDAR_SEMESTER:
            code = attrs.get("code", getattr(self.instance, "code", ""))
            calendar_group = attrs.get(
                "semester_calendar_group",
                getattr(self.instance, "semester_calendar_group", ""),
            )
            if not calendar_group:
                temporary = models.Center(code=code)
                calendar_group = temporary.default_semester_calendar_group()
            attrs["semester_calendar_group"] = calendar_group
            attrs["annual_session_limit"] = 0
        else:
            attrs["semester_calendar_group"] = ""
        return attrs

    def get_academic_workflows(self, center):
        return center.uses_semester_calendar()

    def get_semester_calendar_group_effective(self, center):
        return center.effective_semester_calendar_group() if center.uses_semester_calendar() else ""


class DepartmentSerializer(serializers.ModelSerializer):
    school_detail = SchoolSerializer(source="school", read_only=True)
    center_detail = CenterSerializer(source="center", read_only=True)

    class Meta:
        model = models.Department
        fields = "__all__"

    def validate(self, attrs):
        school = attrs.get("school", getattr(self.instance, "school", None))
        center = attrs.get("center", getattr(self.instance, "center", None))
        if not school and not center:
            raise serializers.ValidationError(
                {"school": "Department must belong to a school or centre."}
            )
        return attrs


class UnitSerializer(serializers.ModelSerializer):
    school_detail = SchoolSerializer(source="school", read_only=True)
    center_detail = CenterSerializer(source="center", read_only=True)
    department_detail = DepartmentSerializer(source="department", read_only=True)
    assigned_executives = serializers.SerializerMethodField()

    class Meta:
        model = models.Unit
        fields = "__all__"

    def validate(self, attrs):
        school = attrs.get("school", getattr(self.instance, "school", None))
        center = attrs.get("center", getattr(self.instance, "center", None))
        department = attrs.get("department", getattr(self.instance, "department", None))

        if school and center:
            raise serializers.ValidationError(
                {"school": "Unit must belong to either a school or centre, not both."}
            )

        if department:
            if school and department.center_id:
                raise serializers.ValidationError(
                    {"department": "Selected department belongs to a centre, not the selected school."}
                )
            if center and department.school_id:
                raise serializers.ValidationError(
                    {"department": "Selected department belongs to a school, not the selected centre."}
                )
            if school and department.school_id and department.school_id != school.id:
                raise serializers.ValidationError(
                    {"department": "Selected department does not belong to the selected school."}
                )
            if center and department.center_id and department.center_id != center.id:
                raise serializers.ValidationError(
                    {"department": "Selected department does not belong to the selected centre."}
                )
            if not school and not center and department.school_id and department.center_id:
                raise serializers.ValidationError(
                    {"department": "Select either the department school or centre for this unit."}
                )
            if not school and not center and department.school_id:
                attrs["school"] = department.school
                school = department.school
            if not school and not center and department.center_id:
                attrs["center"] = department.center
                center = department.center

        if not school and not center:
            raise serializers.ValidationError(
                {"school": "Unit must belong to a school or centre."}
            )
        return attrs

    def get_assigned_executives(self, unit):
        profiles = (
            models.Profile.objects.select_related("user", "executive_detail")
            .filter(
                role=models.Profile.ROLE_EXECUTIVE,
                executive_detail__unit=unit,
                is_active=True,
            )
            .order_by("user__first_name", "user__last_name", "user__username")
        )
        return [
            {
                "id": profile.id,
                "name": f"{profile.user.first_name} {profile.user.last_name}".strip()
                or profile.user.username,
                "username": profile.user.username,
                "designation": profile.designation,
                "staff_id": profile.staff_id,
            }
            for profile in profiles
        ]


class ProgramSerializer(serializers.ModelSerializer):
    school_detail = SchoolSerializer(source="school", read_only=True)
    center_detail = CenterSerializer(source="center", read_only=True)
    department_detail = DepartmentSerializer(source="department", read_only=True)

    class Meta:
        model = models.Program
        fields = "__all__"

    def validate(self, attrs):
        school = attrs.get("school", getattr(self.instance, "school", None))
        center = attrs.get("center", getattr(self.instance, "center", None))
        department = attrs.get("department", getattr(self.instance, "department", None))

        if department:
            if not school and department.school_id:
                attrs["school"] = department.school
                school = department.school
            if not center and department.center_id:
                attrs["center"] = department.center
                center = department.center

        if not school and not center:
            raise serializers.ValidationError(
                {"school": "Program must belong to a school or centre."}
            )
        program_type = attrs.get("program_type", getattr(self.instance, "program_type", models.Program.PROGRAM_ACADEMIC))
        if (
            center
            and program_type == models.Program.PROGRAM_ACADEMIC
            and not center.is_academic_center()
        ):
            raise serializers.ValidationError(
                {"program_type": "Academic programmes can only be assigned to academic centres."}
            )
        return attrs


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Semester
        fields = "__all__"


class SemesterHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SemesterHoliday
        fields = "__all__"


class SemesterConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SemesterConfiguration
        fields = "__all__"


class AcademicSessionSerializer(serializers.ModelSerializer):
    center_detail = CenterSerializer(source="center", read_only=True)

    class Meta:
        model = models.AcademicSession
        fields = "__all__"


IELTSSessionSerializer = AcademicSessionSerializer


class CourseSerializer(serializers.ModelSerializer):
    school_detail = SchoolSerializer(source="school", read_only=True)
    center_detail = CenterSerializer(source="center", read_only=True)

    class Meta:
        model = models.Course
        fields = "__all__"


class CourseOfferingSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source="course", read_only=True)
    semester_detail = SemesterSerializer(source="semester", read_only=True)
    eligible_school_details = SchoolSerializer(source="eligible_schools", many=True, read_only=True)
    eligible_center_details = CenterSerializer(source="eligible_centers", many=True, read_only=True)

    class Meta:
        model = models.CourseOffering
        fields = "__all__"


class CourseLabGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CourseLabGroup
        fields = "__all__"


class CourseTutorialGroupSerializer(serializers.ModelSerializer):
    lab_groups = CourseLabGroupSerializer(many=True, read_only=True)

    class Meta:
        model = models.CourseTutorialGroup
        fields = "__all__"


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Building
        fields = "__all__"


class VenueSerializer(serializers.ModelSerializer):
    building_detail = BuildingSerializer(source="building", read_only=True)
    category_label = serializers.SerializerMethodField()

    class Meta:
        model = models.Venue
        fields = "__all__"

    def get_category_label(self, venue):
        from admin_app.settings_registry import venue_category_label

        return venue_category_label(venue.category)

    def validate_category(self, value):
        from admin_app.settings_registry import venue_category_values

        normalized = str(value or "classroom").strip().lower() or "classroom"
        if normalized not in venue_category_values():
            raise serializers.ValidationError("Select a configured venue category.")
        return normalized


def _student_room_filter(room_code):
    return Q(room=room_code) | Q(room__startswith=f"{room_code}-")


def _student_detail(student):
    user = student.profile.user
    name = f"{user.first_name} {user.last_name}".strip() or user.username
    return {
        "id": student.id,
        "profile_id": student.profile_id,
        "student_id": student.student_id,
        "name": name,
        "email": user.email,
        "room": student.room,
    }


class HostelSerializer(serializers.ModelSerializer):
    hostel_type = serializers.CharField(max_length=10)
    hostel_type_label = serializers.SerializerMethodField()
    room_count = serializers.SerializerMethodField()
    resident_count = serializers.SerializerMethodField()
    warden_detail = serializers.SerializerMethodField()

    class Meta:
        model = models.Hostel
        fields = "__all__"

    def validate_code(self, value):
        return value.strip().upper()

    def validate_hostel_type(self, value):
        normalized = str(value or "").strip().lower()
        if normalized not in hostel_residence_type_values():
            raise serializers.ValidationError("Select a configured residence type.")
        return normalized

    def get_hostel_type_label(self, hostel):
        return hostel_residence_type_label(hostel.hostel_type)

    def get_room_count(self, hostel):
        return hostel.rooms.count()

    def get_resident_count(self, hostel):
        return Student.objects.filter(room__startswith=f"{hostel.code}-").count()

    def get_warden_detail(self, hostel):
        if not hostel.warden_id:
            return None
        user = hostel.warden.user
        return {
            "id": hostel.warden_id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "staff_id": hostel.warden.staff_id,
        }


class HostelRoomSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_blank=True, max_length=80)
    hostel_detail = HostelSerializer(source="hostel", read_only=True)
    residents = serializers.SerializerMethodField()
    resident_count = serializers.SerializerMethodField()
    available_sections = serializers.SerializerMethodField()

    class Meta:
        model = models.HostelRoom
        fields = "__all__"

    def validate_code(self, value):
        return normalize_hostel_room_code(value)

    def validate_capacity(self, value):
        max_capacity = hostel_policy_settings()["max_room_capacity"]
        if value < 1:
            raise serializers.ValidationError("Room capacity must be at least 1.")
        if value > max_capacity:
            raise serializers.ValidationError(
                f"Room capacity cannot exceed the configured maximum of {max_capacity}."
            )
        return value

    def validate(self, attrs):
        policy = hostel_policy_settings()
        if not self.instance and attrs.get("capacity") is None:
            attrs["capacity"] = policy["default_room_capacity"]

        hostel = attrs.get("hostel", getattr(self.instance, "hostel", None))
        floor = attrs.get("floor", getattr(self.instance, "floor", None))
        number = attrs.get("number", getattr(self.instance, "number", ""))
        submitted_code = attrs.get("code")
        should_generate_code = not submitted_code

        if self.instance and not submitted_code:
            existing_generated = hostel_room_code(
                self.instance.hostel.code,
                self.instance.floor,
                self.instance.number,
            )
            should_generate_code = self.instance.code == existing_generated

        if should_generate_code and hostel and floor is not None and number:
            attrs["code"] = hostel_room_code(hostel.code, floor, number)

        code = attrs.get("code", getattr(self.instance, "code", ""))
        if not code:
            raise serializers.ValidationError({"code": "Room code could not be generated."})
        duplicate = models.HostelRoom.objects.filter(code=code)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError({"code": "A hostel room with this code already exists."})
        if self.instance:
            occupied = Student.objects.filter(_student_room_filter(self.instance.code)).count()
            capacity = attrs.get("capacity", self.instance.capacity)
            if capacity < occupied:
                raise serializers.ValidationError(
                    {"capacity": f"Room capacity cannot be below its {occupied} current residents."}
                )
        return attrs

    def get_residents(self, room):
        students = (
            Student.objects.select_related("profile__user")
            .filter(_student_room_filter(room.code))
            .order_by("room", "student_id")
        )
        return [_student_detail(student) for student in students]

    def get_resident_count(self, room):
        return Student.objects.filter(_student_room_filter(room.code)).count()

    def get_available_sections(self, room):
        rule = hostel_policy_settings()["bed_assignment_rule"]
        if rule == "room_only":
            return [room.code]
        if rule == "manual":
            return []
        return [chr(65 + index) for index in range(room.capacity or 0)]

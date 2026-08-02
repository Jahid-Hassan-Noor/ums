from django.db.models import Q
from rest_framework import serializers

from admin_app import models
from student_app.models import Student


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.School
        fields = "__all__"


class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Center
        fields = "__all__"


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
        return attrs


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Semester
        fields = "__all__"


class SemesterHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SemesterHoliday
        fields = "__all__"


class IELTSSessionSerializer(serializers.ModelSerializer):
    center_detail = CenterSerializer(source="center", read_only=True)

    class Meta:
        model = models.IELTSSession
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    school_detail = SchoolSerializer(source="school", read_only=True)
    center_detail = CenterSerializer(source="center", read_only=True)

    class Meta:
        model = models.Course
        fields = "__all__"


class CourseOfferingSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source="course", read_only=True)
    semester_detail = SemesterSerializer(source="semester", read_only=True)

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

    class Meta:
        model = models.Venue
        fields = "__all__"


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
    hostel_type_label = serializers.CharField(source="get_hostel_type_display", read_only=True)
    room_count = serializers.SerializerMethodField()
    resident_count = serializers.SerializerMethodField()
    warden_detail = serializers.SerializerMethodField()

    class Meta:
        model = models.Hostel
        fields = "__all__"

    def validate_code(self, value):
        return value.strip().upper()

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
    hostel_detail = HostelSerializer(source="hostel", read_only=True)
    residents = serializers.SerializerMethodField()
    resident_count = serializers.SerializerMethodField()
    available_sections = serializers.SerializerMethodField()

    class Meta:
        model = models.HostelRoom
        fields = "__all__"
        read_only_fields = ("code",)

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
        return [chr(65 + index) for index in range(room.capacity or 0)]

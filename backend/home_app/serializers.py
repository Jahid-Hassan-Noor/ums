from rest_framework import serializers
from home_app import models
from admin_app import models as admin_models
from core.upload_security import image_upload_error


class PublicPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PublicPage
        fields = "__all__"


class PublicAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PublicAnnouncement
        fields = "__all__"


class PublicNewsSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.PublicNews
        fields = "__all__"

    def get_image_url(self, news):
        if not news.image:
            return ""
        request = self.context.get("request")
        url = news.image.url
        return request.build_absolute_uri(url) if request else url

    def validate_image(self, upload):
        if not upload:
            return upload
        error = image_upload_error(upload, field_label="News image")
        if error:
            raise serializers.ValidationError(error)
        return upload


class PublicEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PublicEvent
        fields = "__all__"


class OfficialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OfficialLink
        fields = "__all__"


def _active_program_names(queryset, fallback):
    names = list(
        queryset.filter(is_active=True)
        .order_by("name")
        .values_list("name", flat=True)
    )
    return names or fallback


class PublicSchoolSerializer(serializers.ModelSerializer):
    programmes = serializers.SerializerMethodField()

    class Meta:
        model = admin_models.School
        fields = (
            "id",
            "code",
            "slug",
            "name",
            "description",
            "about",
            "vision",
            "mission",
            "programmes",
            "image_url",
            "is_active",
        )

    def get_programmes(self, school):
        return _active_program_names(
            admin_models.Program.objects.filter(
                school=school,
                program_type=admin_models.Program.PROGRAM_ACADEMIC,
            ),
            school.programmes,
        )


class PublicCenterSerializer(serializers.ModelSerializer):
    offerings = serializers.SerializerMethodField()
    academic_workflows = serializers.SerializerMethodField()

    class Meta:
        model = admin_models.Center
        fields = (
            "id",
            "code",
            "slug",
            "name",
            "description",
            "about",
            "offerings",
            "image_url",
            "is_active",
            "academic_workflows",
        )

    def get_offerings(self, center):
        return _active_program_names(
            admin_models.Program.objects.filter(center=center),
            center.offerings,
        )

    def get_academic_workflows(self, center):
        return admin_models.Program.objects.filter(
            center=center,
            program_type=admin_models.Program.PROGRAM_ACADEMIC,
            is_active=True,
        ).exists()


class PublicDepartmentSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)

    class Meta:
        model = admin_models.Department
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "school",
            "center",
            "school_name",
            "center_name",
        )


class PublicUnitSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    assigned_executives = serializers.SerializerMethodField()

    class Meta:
        model = admin_models.Unit
        fields = (
            "id",
            "code",
            "name",
            "unit_type",
            "description",
            "is_active",
            "school",
            "center",
            "department",
            "school_name",
            "center_name",
            "department_name",
            "assigned_executives",
        )

    def get_assigned_executives(self, unit):
        profiles = (
            admin_models.Profile.objects.select_related("user", "executive_detail")
            .filter(
                role=admin_models.Profile.ROLE_EXECUTIVE,
                executive_detail__unit=unit,
                is_active=True,
            )
            .order_by("user__first_name", "user__last_name", "user__username")
        )
        return [
            {
                "name": f"{profile.user.first_name} {profile.user.last_name}".strip()
                or profile.user.username,
                "designation": profile.designation,
            }
            for profile in profiles
        ]

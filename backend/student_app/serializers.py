from rest_framework import serializers
from admin_app.serializers import (
    CourseLabGroupSerializer,
    CourseOfferingSerializer,
    CourseTutorialGroupSerializer,
    SemesterSerializer,
)
from student_app import models


class RegistrationPeriodSerializer(serializers.ModelSerializer):
    semester_detail = SemesterSerializer(source="semester", read_only=True)

    class Meta:
        model = models.RegistrationPeriod
        fields = "__all__"


class CourseRegistrationSerializer(serializers.ModelSerializer):
    offering_detail = CourseOfferingSerializer(source="offering", read_only=True)
    period_detail = RegistrationPeriodSerializer(source="period", read_only=True)
    tutorial_group_detail = CourseTutorialGroupSerializer(source="tutorial_group", read_only=True)
    lab_group_detail = CourseLabGroupSerializer(source="lab_group", read_only=True)

    class Meta:
        model = models.CourseRegistration
        fields = "__all__"

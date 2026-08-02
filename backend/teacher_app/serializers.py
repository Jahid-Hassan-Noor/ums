from rest_framework import serializers
from teacher_app import models


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Assignment
        fields = "__all__"

    def validate_max_files(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Students can submit between 1 and 5 files.")
        return value

    def validate_max_file_size_mb(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError("Each file must be limited to between 1 and 100 MB.")
        return value

    def validate_accepted_file_types(self, value):
        valid = {choice for choice, _label in models.Assignment.FILE_CHOICES}
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Select at least one accepted file format.")
        if set(value) - valid:
            raise serializers.ValidationError("Select only supported file formats.")
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        opens_at = attrs.get("opens_at", getattr(self.instance, "opens_at", None))
        due_date = attrs.get("due_date", getattr(self.instance, "due_date", None))
        cutoff_at = attrs.get("cutoff_at", getattr(self.instance, "cutoff_at", None))
        activity_kind = attrs.get("activity_kind", getattr(self.instance, "activity_kind", models.Assignment.ACTIVITY_ASSIGNMENT))
        collaboration_mode = attrs.get(
            "collaboration_mode",
            getattr(self.instance, "collaboration_mode", models.Assignment.COLLABORATION_INDIVIDUAL),
        )
        max_group_members = attrs.get(
            "max_group_members",
            getattr(self.instance, "max_group_members", 1),
        )
        min_distinct_countries = attrs.get(
            "min_distinct_countries",
            getattr(self.instance, "min_distinct_countries", 0),
        )
        section = attrs.get("section", getattr(self.instance, "section", None))
        if activity_kind == models.Assignment.ACTIVITY_LAB and (
            not section or section.section_type != models.CourseSection.TYPE_LAB_WORK
        ):
            raise serializers.ValidationError({"section": "Lab activities must be linked to a lab-work course section."})
        if collaboration_mode == models.Assignment.COLLABORATION_GROUP:
            if max_group_members < 2 or max_group_members > 20:
                raise serializers.ValidationError({
                    "max_group_members": "Group assignments allow between 2 and 20 members."
                })
            if min_distinct_countries > max_group_members:
                raise serializers.ValidationError({
                    "min_distinct_countries": "Country diversity cannot exceed the maximum group size."
                })
        elif max_group_members != 1:
            raise serializers.ValidationError({
                "max_group_members": "Individual assignments must have a group size of 1."
            })
        if opens_at and due_date and opens_at > due_date:
            raise serializers.ValidationError({"due_date": "Assignment deadline must be after the opening time."})
        if due_date and cutoff_at and due_date > cutoff_at:
            raise serializers.ValidationError({"cutoff_at": "Cutoff time must be after the assignment deadline."})
        return attrs


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment_detail = AssignmentSerializer(source="assignment", read_only=True)

    class Meta:
        model = models.AssignmentSubmission
        fields = "__all__"

import json

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from admin_app.settings_registry import setting_value
from teacher_app.assignment_service import (
    get_teacher_profile,
    notify_assignment_students,
    serialize_assignment,
    teacher_offerings,
)
from teacher_app.models import Assignment, AssignmentRubric, CourseActivity, CourseSection
from teacher_app.serializers import AssignmentSerializer


def serialize_offering(offering):
    return {
        "id": offering.id,
        "course_code": offering.course.code,
        "course_title": offering.course.title,
        "section": offering.section,
        "semester": offering.semester.name,
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "section_type": section.section_type,
                "section_type_label": section.get_section_type_display(),
            }
            for section in offering.course_sections.all()
        ],
    }


class TeacherAssignmentCreate(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        profile = get_teacher_profile(request.user)
        offerings = teacher_offerings(profile)
        return Response(
            {
                "title": "Create Assignment",
                "section": "teacher",
                "offerings": [serialize_offering(offering) for offering in offerings],
                "submission_types": [
                    {"value": value, "label": label}
                    for value, label in Assignment.SUBMISSION_CHOICES
                ],
                "activity_types": [
                    {"value": value, "label": label}
                    for value, label in Assignment.ACTIVITY_CHOICES
                ],
                "collaboration_modes": [
                    {"value": value, "label": label}
                    for value, label in Assignment.COLLABORATION_CHOICES
                ],
                "file_types": [
                    {"value": value, "label": label}
                    for value, label in Assignment.FILE_CHOICES
                ],
                "max_file_limit": 5,
                "max_file_size_limit_mb": 100,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        profile = get_teacher_profile(request.user)
        offering = teacher_offerings(profile).filter(pk=request.data.get("offering_id")).first()
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)

        section = CourseSection.objects.filter(
            pk=request.data.get("section_id"),
            offering=offering,
        ).first()
        accepted_file_types = request.data.get("accepted_file_types")
        if accepted_file_types is None:
            accepted_file_types = [request.data.get("accepted_file_type", Assignment.FILE_PDF)]
        if isinstance(accepted_file_types, str):
            try:
                accepted_file_types = json.loads(accepted_file_types)
            except json.JSONDecodeError:
                accepted_file_types = [accepted_file_types]
        accepted_file_types = list(dict.fromkeys(accepted_file_types))
        payload = {
            "offering": offering.id,
            "section": section.id if section else None,
            "activity_kind": request.data.get("activity_kind", Assignment.ACTIVITY_ASSIGNMENT),
            "collaboration_mode": request.data.get(
                "collaboration_mode",
                Assignment.COLLABORATION_INDIVIDUAL,
            ),
            "max_group_members": request.data.get("max_group_members", 1),
            "require_same_tutorial_group": request.data.get("require_same_tutorial_group", False),
            "require_same_lab_group": request.data.get("require_same_lab_group", False),
            "min_distinct_countries": request.data.get("min_distinct_countries", 0),
            "group_rules": request.data.get("group_rules", ""),
            "title": request.data.get("title", ""),
            "description": request.data.get("description", ""),
            "instructions": request.data.get("instructions", request.data.get("description", "")),
            "file_instructions": request.data.get("file_instructions", ""),
            "opens_at": request.data.get("opens_at"),
            "due_date": request.data.get("due_date") or request.data.get("deadline"),
            "cutoff_at": request.data.get("cutoff_at"),
            "max_score": request.data.get("max_score", 100),
            "submission_type": request.data.get("submission_type", Assignment.SUBMISSION_BOTH),
            "accepted_file_type": accepted_file_types[0] if accepted_file_types else Assignment.FILE_PDF,
            "accepted_file_types": accepted_file_types,
            "max_files": request.data.get("max_files", 1),
            "max_file_size_mb": request.data.get("max_file_size_mb", 10),
            "allow_multiple_submissions": request.data.get("allow_multiple_submissions", False),
            "allow_late_submissions": request.data.get(
                "allow_late_submissions",
                setting_value("academic", "assignment_late_submission_default"),
            ),
            "status": request.data.get("status", Assignment.STATUS_PUBLISHED),
            "created_by": profile.id,
        }
        serializer = AssignmentSerializer(data=payload)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_criteria = request.data.get("rubric_criteria", [])
        if isinstance(raw_criteria, str):
            try:
                raw_criteria = json.loads(raw_criteria) if raw_criteria.strip() else []
            except json.JSONDecodeError:
                return Response(
                    {"rubric_criteria": ["Rubric criteria must be valid JSON."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            assignment = serializer.save()
            rubric = None
            if request.data.get("rubric_title") or raw_criteria:
                rubric = AssignmentRubric.objects.create(
                    assignment=assignment,
                    title=str(request.data.get("rubric_title") or f"{assignment.title} rubric").strip(),
                    criteria=raw_criteria if isinstance(raw_criteria, list) else [],
                    max_score=assignment.max_score,
                    created_by=profile,
                )
            if assignment.due_date:
                CourseActivity.objects.create(
                    offering=offering,
                    section=section,
                    assignment=assignment,
                    activity_type=CourseActivity.TYPE_ASSIGNMENT,
                    title=assignment.title,
                    opens_at=assignment.opens_at,
                    due_at=assignment.due_date,
                    closes_at=assignment.cutoff_at,
                    completion_policy=CourseActivity.COMPLETION_SUBMIT,
                    is_required=True,
                )
        if assignment.status == Assignment.STATUS_PUBLISHED:
            notify_assignment_students(assignment)
        return Response(
            {
                "message": "Assignment created successfully.",
                "assignment": serialize_assignment(assignment),
                "rubric_id": rubric.id if rubric else None,
            },
            status=status.HTTP_201_CREATED,
        )

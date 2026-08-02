from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from core.common.request_utils import parse_bool as _parse_bool, parse_int as _parse_int
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.course_content_service import (
    create_course_announcement,
    offering_for_teacher,
    serialize_announcement,
    serialize_activity,
    serialize_assessment_plan,
    serialize_course_content,
    serialize_folder,
    serialize_resource,
    serialize_section,
    update_assessment_plan,
    validate_resource_file,
)
from teacher_app.models import CourseActivity, CourseResource, CourseResourceFolder, CourseSection


class TeacherCourseResources(APIView):
    permission_classes = [IsTeacherRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = offering_for_teacher(profile, course_id)
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "title": "Course Resources",
                "section": "teacher",
                **serialize_course_content(offering, include_slot_selection_details=True),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = offering_for_teacher(profile, course_id)
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)

        action = str(request.data.get("action", "create_resource")).strip().lower()
        if action == "create_section":
            section_type = request.data.get("section_type", CourseSection.TYPE_TOPIC)
            if section_type == CourseSection.TYPE_LAB_WORK and not offering.course.has_lab:
                return Response({"detail": "Lab work can only be added to courses marked as having labs."}, status=status.HTTP_400_BAD_REQUEST)
            section = CourseSection.objects.create(
                offering=offering,
                title=str(request.data.get("title", "")).strip(),
                summary=str(request.data.get("summary", "")).strip(),
                section_type=section_type,
                week_number=request.data.get("week_number") or None,
                topic_label=str(request.data.get("topic_label", "")).strip(),
                starts_on=parse_date(str(request.data.get("starts_on") or "")),
                ends_on=parse_date(str(request.data.get("ends_on") or "")),
                sort_order=_parse_int(request.data.get("sort_order")),
                is_published=_parse_bool(request.data.get("is_published"), True),
            )
            return Response(
                {"message": "Course section saved.", "section": serialize_section(section)},
                status=status.HTTP_201_CREATED,
            )

        if action == "create_folder":
            parent = CourseResourceFolder.objects.filter(
                pk=request.data.get("parent_id"),
                offering=offering,
            ).first()
            folder = CourseResourceFolder.objects.create(
                offering=offering,
                parent=parent,
                title=str(request.data.get("title", "")).strip(),
                description=str(request.data.get("description", "")).strip(),
                sort_order=_parse_int(request.data.get("sort_order")),
                is_published=_parse_bool(request.data.get("is_published"), True),
                created_by=profile,
            )
            return Response(
                {"message": "Course folder saved.", "folder": serialize_folder(folder)},
                status=status.HTTP_201_CREATED,
            )

        if action == "create_announcement":
            announcement = create_course_announcement(offering, profile, request.data)
            return Response(
                {
                    "message": "Course announcement published.",
                    "announcement": serialize_announcement(
                        announcement,
                        include_selection_details=True,
                    ),
                },
                status=status.HTTP_201_CREATED,
            )

        if action == "create_activity":
            section = CourseSection.objects.filter(
                pk=request.data.get("section_id"),
                offering=offering,
            ).first()
            assignment = offering.assignment_set.filter(pk=request.data.get("assignment_id")).first()
            resource = CourseResource.objects.filter(
                pk=request.data.get("resource_id"),
                offering=offering,
            ).first()
            activity = CourseActivity.objects.create(
                offering=offering,
                section=section,
                assignment=assignment,
                resource=resource,
                activity_type=request.data.get("activity_type", CourseActivity.TYPE_RESOURCE),
                title=str(request.data.get("title", "")).strip(),
                opens_at=parse_datetime(str(request.data.get("opens_at") or "")),
                due_at=parse_datetime(str(request.data.get("due_at") or "")),
                closes_at=parse_datetime(str(request.data.get("closes_at") or "")),
                completion_policy=request.data.get("completion_policy", CourseActivity.COMPLETION_VIEW),
                is_required=_parse_bool(request.data.get("is_required"), True),
                sort_order=_parse_int(request.data.get("sort_order")),
            )
            return Response(
                {"message": "Course activity saved.", "activity": serialize_activity(activity)},
                status=status.HTTP_201_CREATED,
            )

        if action == "update_assessment":
            try:
                updated_offering = update_assessment_plan(
                    offering,
                    profile,
                    request.data,
                    upload=request.FILES.get("study_guide"),
                )
            except ValidationError as exc:
                return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {
                    "message": "Assessment plan saved.",
                    "assessment": serialize_assessment_plan(updated_offering),
                },
                status=status.HTTP_200_OK,
            )

        section = CourseSection.objects.filter(
            pk=request.data.get("section_id"),
            offering=offering,
        ).first()
        upload = request.FILES.get("file")
        file_error = validate_resource_file(upload)
        if file_error:
            return Response({"detail": file_error}, status=status.HTTP_400_BAD_REQUEST)
        folder = CourseResourceFolder.objects.filter(
            pk=request.data.get("folder_id"),
            offering=offering,
        ).first()
        if not section and not folder:
            section = CourseSection.objects.filter(offering=offering).order_by("sort_order", "created_at").first()

        resource = CourseResource.objects.create(
            offering=offering,
            section=section,
            folder=folder,
            resource_type=CourseResource.TYPE_FILE if upload else request.data.get("resource_type", CourseResource.TYPE_LINK),
            title=str(request.data.get("title", "")).strip(),
            description=str(request.data.get("description", "")).strip(),
            file=upload,
            url=str(request.data.get("url", "")).strip(),
            content=str(request.data.get("content", "")).strip(),
            visible_from=request.data.get("visible_from") or None,
            sort_order=_parse_int(request.data.get("sort_order")),
            is_published=_parse_bool(request.data.get("is_published"), True),
            created_by=profile,
        )
        return Response(
            {"message": "Course resource saved.", "resource": serialize_resource(resource)},
            status=status.HTTP_201_CREATED,
        )

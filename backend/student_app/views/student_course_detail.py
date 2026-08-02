from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.models import Enrollment
from student_app.registration_service import get_student_profile
from teacher_app.course_content_service import (
    cancel_announcement_slot,
    select_announcement_slot,
    serialize_announcement,
    serialize_course_content,
)
from teacher_app.models import CourseAnnouncement


class StudentCourseDetail(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request, course_id):
        student = get_student_profile(request.user)
        enrollment = (
            Enrollment.objects.select_related("offering", "offering__course", "offering__semester")
            .filter(student=student, offering_id=course_id, completed_at__isnull=True)
            .first()
        )
        if not enrollment:
            return Response({"detail": "Course not found for this student."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "title": "Course Detail",
                "section": "student",
                **serialize_course_content(
                    enrollment.offering,
                    published_only=True,
                    student=student,
                ),
                "enrollment": {
                    "id": enrollment.id,
                    "tutorial_group": enrollment.tutorial_group.code if enrollment.tutorial_group else "",
                    "lab_group": enrollment.lab_group.code if enrollment.lab_group else "",
                    "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                },
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, course_id):
        student = get_student_profile(request.user)
        enrollment = Enrollment.objects.filter(
            student=student,
            offering_id=course_id,
            completed_at__isnull=True,
        ).first()
        if not enrollment:
            return Response({"detail": "Course not found for this student."}, status=status.HTTP_404_NOT_FOUND)
        announcement = (
            CourseAnnouncement.objects.prefetch_related(
                "slots",
                "slots__selections",
                "slots__selections__student",
                "slots__selections__student__user",
                "slots__selections__assignment_group",
                "slots__selections__assignment_group__memberships",
            )
            .select_related("assignment")
            .filter(
                pk=request.data.get("announcement_id"),
                offering_id=course_id,
                is_published=True,
            )
            .first()
        )
        if not announcement:
            return Response({"detail": "Course announcement not found."}, status=status.HTTP_404_NOT_FOUND)
        action = str(request.data.get("action", "select_slot")).strip().lower()
        if action == "cancel_slot":
            cancel_announcement_slot(announcement, student)
            message = "Slot selection cancelled."
        elif action == "select_slot":
            select_announcement_slot(
                announcement,
                student,
                request.data.get("slot_id"),
                group_name=request.data.get("group_name", ""),
            )
            message = "Slot selected successfully."
        else:
            return Response({"detail": "Unsupported announcement action."}, status=status.HTTP_400_BAD_REQUEST)
        announcement = CourseAnnouncement.objects.select_related("assignment").prefetch_related(
            "slots",
            "slots__selections",
            "slots__selections__student",
            "slots__selections__student__user",
            "slots__selections__assignment_group",
            "slots__selections__assignment_group__memberships",
        ).get(pk=announcement.pk)
        return Response(
            {
                "message": message,
                "announcement": serialize_announcement(announcement, student=student),
            },
            status=status.HTTP_200_OK,
        )

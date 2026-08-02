from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from teacher_app.assignment_service import get_teacher_profile
from teacher_app.attendance_service import serialize_meeting, teacher_meetings
from teacher_app.course_content_service import offering_for_teacher, serialize_course_content


class TeacherCourseDetail(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request, course_id):
        profile = get_teacher_profile(request.user)
        offering = offering_for_teacher(profile, course_id)
        if not offering:
            return Response({"detail": "Course offering not found for this teacher."}, status=status.HTTP_404_NOT_FOUND)
        meetings = teacher_meetings(profile).filter(offering=offering)
        return Response(
            {
                "title": "Course Detail",
                "section": "teacher",
                **serialize_course_content(offering, include_slot_selection_details=True),
                "meetings": [serialize_meeting(meeting) for meeting in meetings],
            },
            status=status.HTTP_200_OK,
        )

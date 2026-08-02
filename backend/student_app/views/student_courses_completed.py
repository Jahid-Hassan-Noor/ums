from rest_framework import status
from auth_app.permissions import IsStudentRole
from rest_framework.response import Response
from rest_framework.views import APIView
from student_app.models import Enrollment, TranscriptRecord
from student_app.registration_service import get_student_profile


class StudentCoursesCompleted(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        transcripts = []
        completed_enrollments = []
        if student:
            transcripts = list(
                TranscriptRecord.objects.select_related("semester", "offering", "offering__course")
                .filter(student=student, published_at__isnull=False)
                .order_by("-semester__start_date", "course_code", "id")
            )
            transcript_offering_ids = {record.offering_id for record in transcripts if record.offering_id}
            completed_enrollments = list(
                Enrollment.objects.select_related("offering", "offering__course", "offering__semester")
                .filter(student=student, completed_at__isnull=False)
                .exclude(offering_id__in=transcript_offering_ids)
                .order_by("-offering__semester__start_date", "offering__course__code")
            )

        courses = []
        total_credits = 0
        for record in transcripts:
            credit_hours = float(record.credit_hours or 0)
            total_credits += credit_hours
            course_code = record.course_code or (record.offering.course.code if record.offering_id else "")
            course_title = record.course_title or (record.offering.course.title if record.offering_id else "")
            courses.append(
                {
                    "id": f"transcript-{record.id}",
                    "source": "transcript",
                    "offering_id": record.offering_id,
                    "course_code": course_code,
                    "course_title": course_title,
                    "credit_hours": str(record.credit_hours),
                    "semester": {
                        "id": record.semester_id,
                        "name": record.semester.name if record.semester_id else "Unassigned semester",
                        "academic_session": record.semester.academic_session if record.semester_id else "",
                    },
                    "score": str(record.score) if record.score is not None else "",
                    "grade": record.grade,
                    "grade_points": str(record.grade_points) if record.grade_points is not None else "",
                    "gpa": str(record.gpa) if record.gpa is not None else "",
                    "cgpa": str(record.cgpa) if record.cgpa is not None else "",
                    "completed_at": record.published_at.isoformat() if record.published_at else None,
                    "status": "Published",
                }
            )

        for enrollment in completed_enrollments:
            offering = enrollment.offering
            total_credits += offering.course.credits
            courses.append(
                {
                    "id": f"enrollment-{enrollment.id}",
                    "source": "enrollment",
                    "offering_id": offering.id,
                    "course_code": offering.course.code,
                    "course_title": offering.course.title,
                    "credit_hours": str(offering.course.credits),
                    "semester": {
                        "id": offering.semester_id,
                        "name": offering.semester.name,
                        "academic_session": offering.semester.academic_session,
                    },
                    "score": "",
                    "grade": "",
                    "grade_points": "",
                    "gpa": "",
                    "cgpa": "",
                    "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                    "status": "Completed",
                }
            )

        return Response(
            {
                "title": "Completed Courses",
                "section": "student",
                "summary": {
                    "course_count": len(courses),
                    "completed_credit_hours": total_credits,
                },
                "courses": courses,
            },
            status=status.HTTP_200_OK,
        )

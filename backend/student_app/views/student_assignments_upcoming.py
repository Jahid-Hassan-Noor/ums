from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from student_app.views.student_assignments import assignment_list_response


class StudentAssignmentsUpcoming(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return assignment_list_response(request, "Upcoming Assignments", bucket="upcoming")

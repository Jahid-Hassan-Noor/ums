from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsStudentRole
from student_app.results_service import exam_slip_payload, exam_slip_pdf_response


class StudentExamSlip(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return Response(exam_slip_payload(request), status=status.HTTP_200_OK)


class StudentExamSlipPdf(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        return exam_slip_pdf_response(request)

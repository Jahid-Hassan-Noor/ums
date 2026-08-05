from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from technician_app import models
from technician_app.election_service import (
    cast_student_vote,
    is_visible_to_student,
    student_election_payload,
)
from auth_app.permissions import IsStudentRole


class StudentElections(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = request.user.profile
        elections = (
            models.Election.objects.select_related("school")
            .prefetch_related("school_seats__school")
            .annotate(candidate_count=Count("candidates", distinct=True), vote_count=Count("votes", distinct=True))
            .filter(is_active=True)
            .order_by("-starts_at", "-created_at")
        )
        visible_elections = [
            student_election_payload(election, student)
            for election in elections
            if is_visible_to_student(election, student)
        ]
        return Response(
            {
                "title": "Elections",
                "section": "student",
                "school": {
                    "id": student.school_id,
                    "code": student.school.code if student.school_id else "",
                    "name": student.school.name if student.school_id else "",
                },
                "elections": visible_elections,
            },
            status=status.HTTP_200_OK,
        )


class StudentElectionVote(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, pk):
        student = request.user.profile
        try:
            election = models.Election.objects.select_related("school").get(pk=pk)
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)

        category = request.data.get("category")
        candidate_ids = request.data.get("candidate_ids", [])
        if not isinstance(candidate_ids, list):
            return Response({"detail": "Candidate selections must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        error, response_status = cast_student_vote(election, student, category, candidate_ids)
        if error:
            return Response({"detail": error}, status=response_status)

        election = models.Election.objects.select_related("school").get(pk=pk)
        return Response(
            {
                "message": "Ballot submitted successfully.",
                "election": student_election_payload(election, student),
            },
            status=status.HTTP_201_CREATED,
        )

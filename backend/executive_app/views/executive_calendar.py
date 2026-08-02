from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsExecutiveRole


class ExecutiveCalendar(APIView):
    permission_classes = [IsExecutiveRole]
    def get(self, request):
        return Response({"title": "Calendar", "section": "executive"}, status=status.HTTP_200_OK)


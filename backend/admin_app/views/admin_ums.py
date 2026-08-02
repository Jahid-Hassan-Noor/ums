from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole


class AdminUms(APIView):
    permission_classes = [IsAdminRole]
    def get(self, request):
        return Response({"title": "Admin Portal", "section": "admin"}, status=status.HTTP_200_OK)


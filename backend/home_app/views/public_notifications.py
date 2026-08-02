from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from auth_app.permissions import IsActiveUmsUser


class PublicNotifications(APIView):
    permission_classes = [IsActiveUmsUser]

    def get(self, request):
        return Response({"title": "Notifications", "section": "public"}, status=status.HTTP_200_OK)

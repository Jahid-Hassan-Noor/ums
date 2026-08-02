from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class PublicLogin(APIView):
    def get(self, request):
        return Response({"title": "Login", "section": "public"}, status=status.HTTP_200_OK)


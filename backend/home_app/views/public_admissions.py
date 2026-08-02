from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.views.public_helpers import public_page_payload


class PublicAdmissions(APIView):
    def get(self, request):
        return Response(
            public_page_payload(request, "/admissions", "Admissions", "public"),
            status=status.HTTP_200_OK,
        )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.views.public_helpers import public_page_payload


class PublicServices(APIView):
    def get(self, request):
        return Response(
            public_page_payload(request, "/services", "Services", "public"),
            status=status.HTTP_200_OK,
        )

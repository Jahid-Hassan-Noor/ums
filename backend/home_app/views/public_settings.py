from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.settings_registry import public_settings_payload


class PublicSettings(APIView):
    def get(self, request):
        return Response(public_settings_payload())

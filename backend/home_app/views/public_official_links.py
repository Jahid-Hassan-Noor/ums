from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from home_app.serializers import OfficialLinkSerializer
from home_app.views.public_helpers import public_official_links, public_page_payload


class PublicOfficialLinks(APIView):
    def get(self, request):
        payload = public_page_payload(
            request,
            "/official-links",
            "Official Links",
            "public",
        )
        payload.update(
            {
                "official_links": OfficialLinkSerializer(
                    public_official_links(),
                    many=True,
                ).data,
            }
        )
        return Response(payload, status=status.HTTP_200_OK)

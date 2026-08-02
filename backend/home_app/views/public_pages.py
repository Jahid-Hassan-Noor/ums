from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from home_app.serializers import PublicPageSerializer
from home_app.views.public_helpers import get_public_page, normalize_route_path


class PublicPageDetail(APIView):
    def get(self, request, route_path=None):
        requested_path = request.query_params.get("path") or route_path or "/"
        page = get_public_page(route_path=normalize_route_path(requested_path))
        if not page:
            return Response(
                {"detail": "Public page not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "title": page.title,
                "section": "public",
                "page": PublicPageSerializer(
                    page,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )

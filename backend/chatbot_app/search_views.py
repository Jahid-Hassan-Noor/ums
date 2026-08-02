from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot_app.search_serializers import ChatbotSearchQuerySerializer
from chatbot_app.search_services import search_documents


class ChatbotSearchView(APIView):
    permission_classes = [AllowAny]

    def _search(self, request, data):
        serializer = ChatbotSearchQuerySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data
        return Response(
            search_documents(
                user=request.user,
                query=params["query"],
                mode=params["mode"],
                domain=params.get("domain"),
                document_type=params.get("type"),
                limit=params.get("limit"),
                page=params.get("page", 1),
                page_size=params.get("page_size"),
            )
        )

    def get(self, request):
        return self._search(request, request.query_params)

    def post(self, request):
        return self._search(request, request.data)

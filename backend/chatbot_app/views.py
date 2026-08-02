from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot_app.agent import answer_question
from chatbot_app.serializers import ChatbotQuerySerializer


class ChatbotQueryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatbotQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(answer_question(request.user, serializer.validated_data["question"]))

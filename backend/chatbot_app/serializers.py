from rest_framework import serializers


class ChatbotQuerySerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000, trim_whitespace=True)

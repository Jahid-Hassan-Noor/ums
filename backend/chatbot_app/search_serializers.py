from rest_framework import serializers

from chatbot_app.search_services import MAX_QUERY_LENGTH, MIN_QUERY_LENGTH


class ChatbotSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    query = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    mode = serializers.ChoiceField(
        choices=("topbar", "full", "chatbot"),
        default="topbar",
    )
    domain = serializers.CharField(required=False, allow_blank=True, max_length=80)
    type = serializers.CharField(required=False, allow_blank=True, max_length=80)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=50)

    def validate(self, attrs):
        query = (attrs.get("query") or attrs.get("q") or "").strip()
        if len(query) < MIN_QUERY_LENGTH:
            raise serializers.ValidationError(
                {"query": f"Search query must be at least {MIN_QUERY_LENGTH} characters."}
            )
        if len(query) > MAX_QUERY_LENGTH:
            raise serializers.ValidationError(
                {"query": f"Search query must be {MAX_QUERY_LENGTH} characters or fewer."}
            )
        attrs["query"] = query
        attrs["domain"] = (attrs.get("domain") or "").strip() or None
        attrs["type"] = (attrs.get("type") or "").strip() or None
        return attrs

from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_serializer_context


class GenericApiPayloadSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    data = serializers.DictField(required=False)


class PortalAutoSchema(AutoSchema):
    def _get_serializer(self):
        view = self.view
        if isinstance(view, APIView) and not isinstance(view, GenericAPIView):
            serializer_class = getattr(view, "serializer_class", None)
            if serializer_class:
                return serializer_class
            if not callable(getattr(view, "get_serializer", None)) and not callable(
                getattr(view, "get_serializer_class", None)
            ):
                return GenericApiPayloadSerializer(
                    context=build_serializer_context(view)
                )
        return super()._get_serializer()

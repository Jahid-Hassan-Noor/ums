from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsApplicantRole
from applicant_app import models
from applicant_app.serializers import ApplicationDocumentSerializer
from applicant_app.views.helpers import applicant_for_user


class ApplicationDocumentCollectionView(APIView):
    permission_classes = [IsApplicantRole]

    def get_application(self, request, application_id):
        applicant = applicant_for_user(request.user)
        if not applicant:
            return None
        return get_object_or_404(models.AdmissionApplication, id=application_id, applicant=applicant)

    def get(self, request, application_id, *args, **kwargs):
        application = self.get_application(request, application_id)
        if application is None:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            ApplicationDocumentSerializer(application.documents.all(), many=True, context={"request": request}).data
        )

    def post(self, request, application_id, *args, **kwargs):
        application = self.get_application(request, application_id)
        if application is None:
            return Response({"detail": "Applicant profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ApplicationDocumentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        upload = request.FILES.get("file")
        document = serializer.save(
            application=application,
            original_name=getattr(upload, "name", "") if upload else "",
        )
        return Response(
            ApplicationDocumentSerializer(document, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


__all__ = ["ApplicationDocumentCollectionView"]

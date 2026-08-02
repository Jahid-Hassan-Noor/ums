from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from applicant_app.countries import COUNTRY_CHOICES
from applicant_app.admissions_setup import admissions_setup_payload
from applicant_app import models
from applicant_app.serializers import (
    ApplicationIntakeSerializer,
    ApplicationProgrammeSerializer,
)


class ApplicantOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        intakes = models.ApplicationIntake.objects.filter(is_active=True)
        programmes = models.ApplicationProgramme.objects.filter(is_active=True)
        return Response(
            {
                "intakes": ApplicationIntakeSerializer(intakes, many=True).data,
                "programmes": ApplicationProgrammeSerializer(programmes, many=True).data,
                "application_types": [
                    {"value": value, "label": label}
                    for value, label in models.ApplicationIntake.APPLICATION_TYPE_CHOICES
                ],
                "document_types": [
                    {"value": value, "label": label}
                    for value, label in models.ApplicationDocument.DOCUMENT_TYPE_CHOICES
                ],
                "countries": [
                    {"value": value, "label": label}
                    for value, label in COUNTRY_CHOICES
                ],
                "steps": [
                    {"value": value, "label": label}
                    for value, label in models.AdmissionApplication.STEP_CHOICES
                ],
                "admissions_setup": admissions_setup_payload()["settings"],
            },
            status=status.HTTP_200_OK,
        )


__all__ = ["ApplicantOptionsView"]

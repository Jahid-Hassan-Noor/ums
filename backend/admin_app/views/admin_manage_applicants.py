from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsAdminRole
from admin_app.report_exports import completed_xlsx_response
from applicant_app import models as applicant_models
from applicant_app.admissions_setup import admissions_setup_payload, update_admissions_setup
from applicant_app.serializers import (
    AdmissionApplicationSerializer,
    ApplicantSerializer,
    AdminApplicantUpdateSerializer,
)


def _option(value, label):
    return {"value": str(value), "label": str(label)}


def _admin_applicant_payload(applicant):
    payload = dict(ApplicantSerializer(applicant).data)
    payload["id"] = applicant.id
    return payload


def _applicant_rows():
    applicants = list(
        applicant_models.Applicant.objects.select_related("profile__user").order_by(
            "-created_at"
        )
    )
    applications = (
        applicant_models.AdmissionApplication.objects.select_related("intake")
        .filter(applicant_id__in=[applicant.id for applicant in applicants])
        .order_by("applicant_id", "-updated_at", "-created_at")
    )
    latest_by_applicant = {}
    for application in applications:
        latest_by_applicant.setdefault(application.applicant_id, application)

    rows = []
    for applicant in applicants:
        user = applicant.user
        application = latest_by_applicant.get(applicant.id)
        row = {
            "id": applicant.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "username": user.username,
            "email": user.email,
            "phone": applicant.phone,
            "nationality": applicant.nationality,
            "country": applicant.country_of_residence,
            "is_active": bool(applicant.is_active and applicant.profile.is_active and user.is_active),
            "intake_id": application.intake_id if application else None,
            "intake": application.intake.title if application and application.intake_id else "",
            "application_number": application.application_number if application else "",
            "application_status": application.status if application else "",
            "application_status_label": application.get_status_display() if application else "",
            "created_at": applicant.created_at,
        }
        row["search_text"] = " ".join(str(value or "") for value in row.values()).lower()
        rows.append(row)
    return rows


def _filter_applicant_rows(rows, params):
    query = str(params.get("q", "")).strip().lower()
    nationality = str(params.get("nationality", "")).strip()
    country = str(params.get("country", "")).strip()
    account_status = str(params.get("account_status", "")).strip()
    intake = str(params.get("intake", "")).strip()
    application_status = str(params.get("application_status", "")).strip()

    filtered = []
    for row in rows:
        if query and query not in row["search_text"]:
            continue
        if nationality and row["nationality"] != nationality:
            continue
        if country and row["country"] != country:
            continue
        if account_status == "active" and not row["is_active"]:
            continue
        if account_status == "inactive" and row["is_active"]:
            continue
        if intake and str(row["intake_id"] or "") != intake:
            continue
        if application_status and row["application_status"] != application_status:
            continue
        filtered.append(row)

    reverse = str(params.get("sort", "asc")).strip().lower() == "desc"
    filtered.sort(key=lambda row: row["name"].lower(), reverse=reverse)
    return filtered


def _applicant_filters(rows):
    intakes = {
        row["intake_id"]: row["intake"]
        for row in rows
        if row["intake_id"] and row["intake"]
    }
    return {
        "nationalities": [
            _option(value, value)
            for value in sorted({row["nationality"] for row in rows if row["nationality"]})
        ],
        "countries": [
            _option(value, value)
            for value in sorted({row["country"] for row in rows if row["country"]})
        ],
        "account_statuses": [_option("active", "Active"), _option("inactive", "Inactive")],
        "intakes": [
            _option(value, label)
            for value, label in sorted(intakes.items(), key=lambda item: item[1])
        ],
        "application_statuses": [
            _option(value, label)
            for value, label in applicant_models.AdmissionApplication.STATUS_CHOICES
        ],
    }


class AdminManageApplicants(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        applicants = applicant_models.Applicant.objects.select_related(
            "profile__user"
        ).order_by("-created_at")
        active_intake_ids = list(
            applicant_models.ApplicationIntake.objects.filter(is_active=True)
            .values_list("id", flat=True)
        )
        if active_intake_ids:
            current_applicant_ids = (
                applicant_models.AdmissionApplication.objects.filter(
                    intake_id__in=active_intake_ids
                )
                .values_list("applicant_id", flat=True)
                .distinct()
            )
            previous_applicant_ids = (
                applicant_models.AdmissionApplication.objects.exclude(
                    intake_id__in=active_intake_ids
                )
                .values_list("applicant_id", flat=True)
                .distinct()
            )
        else:
            current_applicant_ids = []
            previous_applicant_ids = (
                applicant_models.AdmissionApplication.objects.values_list(
                    "applicant_id", flat=True
                ).distinct()
            )

        total_count = applicants.count()
        active_count = applicants.filter(is_active=True).count()

        summary = {
            "total": total_count,
            "active": active_count,
            "inactive": total_count - active_count,
            "current_session": applicant_models.Applicant.objects.filter(
                id__in=current_applicant_ids
            ).count(),
            "previous_sessions": applicant_models.Applicant.objects.filter(
                id__in=previous_applicant_ids
            ).count(),
        }

        report_rows = _applicant_rows()
        filtered_report_rows = _filter_applicant_rows(report_rows, request.query_params)
        return Response(
            {
                "title": "Manage Applicants",
                "section": "admin",
                "summary": summary,
                "report_summary": {
                    "total": len(report_rows),
                    "filtered": len(filtered_report_rows),
                },
                "filters": _applicant_filters(report_rows),
                "applicants": [
                    _admin_applicant_payload(applicant)
                    for applicant in applicants
                ],
            },
            status=status.HTTP_200_OK,
        )


class AdminManageApplicantsExport(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        rows = _filter_applicant_rows(_applicant_rows(), request.query_params)
        body = [
            [
                "Name",
                "Username",
                "Email",
                "Phone",
                "Nationality",
                "Country of Residence",
                "Account Status",
                "Latest Intake",
                "Application Number",
                "Application Status",
                "Created",
            ]
        ]
        for row in rows:
            body.append(
                [
                    row["name"],
                    row["username"],
                    row["email"],
                    row["phone"],
                    row["nationality"],
                    row["country"],
                    "Active" if row["is_active"] else "Inactive",
                    row["intake"],
                    row["application_number"],
                    row["application_status_label"],
                    row["created_at"],
                ]
            )
        suffix = (
            "filtered"
            if any(key != "sort" and value for key, value in request.query_params.items())
            else "all"
        )
        return completed_xlsx_response(
            request,
            name="Applicants",
            export_type="applicants",
            filename=f"admin-applicants-{suffix}.xlsx",
            sheet_name="Applicants",
            rows=body,
        )


class AdminManageApplicantDetail(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, applicant_id):
        applicant = get_object_or_404(
            applicant_models.Applicant.objects.select_related("profile__user"),
            id=applicant_id,
        )
        applications = (
            applicant_models.AdmissionApplication.objects.select_related(
                "applicant__profile__user",
                "intake",
            )
            .prefetch_related(
                "documents",
                "status_events",
            )
            .filter(applicant=applicant)
            .order_by("-updated_at", "-created_at")
        )
        return Response(
            {
                "applicant": _admin_applicant_payload(applicant),
                "applications": AdmissionApplicationSerializer(
                    applications,
                    many=True,
                    context={"request": request},
                ).data,
                "admissions_setup": admissions_setup_payload()["settings"],
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request, applicant_id):
        applicant = get_object_or_404(
            applicant_models.Applicant.objects.select_related("profile__user"),
            id=applicant_id,
        )
        serializer = AdminApplicantUpdateSerializer(
            data=request.data, context={"applicant": applicant}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = applicant.user
        profile = applicant.profile
        user_fields = []

        if "username" in data:
            user.username = data.pop("username")
            user_fields.append("username")
        if "email" in data:
            user.email = data.pop("email")
            user_fields.append("email")
        if "first_name" in data:
            user.first_name = data.pop("first_name")
            user_fields.append("first_name")
        if "last_name" in data:
            user.last_name = data.pop("last_name")
            user_fields.append("last_name")

        applicant_fields = []
        profile_fields = []

        if "phone" in data:
            applicant.phone = data["phone"]
            applicant_fields.append("phone")
            profile.phone = data["phone"]
            profile_fields.append("phone")

        for field in ("nationality", "country_of_residence", "passport_or_identity_no"):
            if field in data:
                setattr(applicant, field, data[field])
                applicant_fields.append(field)

        if "is_active" in data:
            applicant.is_active = data["is_active"]
            profile.is_active = data["is_active"]
            user.is_active = data["is_active"]
            applicant_fields.append("is_active")
            profile_fields.append("is_active")
            user_fields.append("is_active")

        if user_fields:
            user.save(update_fields=sorted(set(user_fields)))

        if profile_fields:
            profile.save(update_fields=sorted(set(profile_fields)) + ["updated_at"])

        if applicant_fields:
            applicant.save(update_fields=sorted(set(applicant_fields)) + ["updated_at"])

        return Response(
            {"applicant": _admin_applicant_payload(applicant)},
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def delete(self, request, applicant_id):
        applicant = get_object_or_404(
            applicant_models.Applicant.objects.select_related("profile__user"),
            id=applicant_id,
        )
        applicant.is_active = False
        applicant.save(update_fields=["is_active", "updated_at"])

        profile = applicant.profile
        profile.is_active = False
        profile.save(update_fields=["is_active", "updated_at"])

        user = applicant.user
        if user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active"])

        return Response(
            {"message": "Applicant account disabled."},
            status=status.HTTP_200_OK,
        )


class AdminManageApplicantsSetup(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(admissions_setup_payload(), status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        try:
            setup = update_admissions_setup(
                request.data,
                updated_by=getattr(request.user, "profile", None),
            )
        except ValidationError as error:
            return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Admissions setup updated successfully.",
                **admissions_setup_payload(),
                "settings": setup,
            },
            status=status.HTTP_200_OK,
        )


__all__ = [
    "AdminManageApplicants",
    "AdminManageApplicantsExport",
    "AdminManageApplicantDetail",
    "AdminManageApplicantsSetup",
]

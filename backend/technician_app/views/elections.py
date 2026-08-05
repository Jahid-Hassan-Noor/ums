from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import Center, Department, Program, School
from auth_app.models import Profile
from auth_app.permissions import IsTechnicianRole
from core.common.errors import first_error
from core.common.request_utils import parse_json
from core.upload_security import image_upload_error
from student_app.models import Student as StudentDetail
from technician_app import models
from technician_app.election_notifications import notify_candidate, notify_election_students
from technician_app.election_service import (
    candidate_payload,
    election_payload,
    profile_option,
    result_groups_for,
    school_option,
)


def _request_profile(request):
    return getattr(request.user, "profile", None)


def _parse_aware_datetime(value):
    if value in (None, ""):
        return None
    parsed = parse_datetime(str(value))
    if not parsed:
        raise ValidationError({"datetime": "Enter a valid date and time."})
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _maybe_int(value):
    if value in (None, ""):
        return None
    return int(value)


def _bool_value(value, default=False):
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _choice_options(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _organization_options(model):
    return [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "label": f"{item.code} - {item.name}",
        }
        for item in model.objects.filter(is_active=True).order_by("name")
    ]


def _cohort_options():
    years = (
        StudentDetail.objects.filter(current_year__isnull=False)
        .order_by("current_year")
        .values_list("current_year", flat=True)
        .distinct()
    )
    return [{"id": year, "code": str(year), "name": f"Year {year}", "label": f"Year {year}"} for year in years]


def _constituency_options():
    return {
        models.Election.CONSTITUENCY_SCHOOL: _organization_options(School),
        models.Election.CONSTITUENCY_CENTER: _organization_options(Center),
        models.Election.CONSTITUENCY_DEPARTMENT: _organization_options(Department),
        models.Election.CONSTITUENCY_PROGRAM: _organization_options(Program),
        models.Election.CONSTITUENCY_COHORT: _cohort_options(),
    }


def _election_type_options(elections=None):
    options = {value: label for value, label in models.Election.TYPE_CHOICES}
    for election in elections or []:
        options[election.election_type] = election.get_election_type_display()
    return [{"value": value, "label": label} for value, label in options.items()]


def _validate_constituency(payload):
    constituency_type = payload.get("constituency_type")
    constituency_id = payload.get("constituency_id")
    if constituency_type == models.Election.CONSTITUENCY_UNIVERSITY or not constituency_id:
        return
    model_by_type = {
        models.Election.CONSTITUENCY_SCHOOL: School,
        models.Election.CONSTITUENCY_CENTER: Center,
        models.Election.CONSTITUENCY_DEPARTMENT: Department,
        models.Election.CONSTITUENCY_PROGRAM: Program,
    }
    model = model_by_type.get(constituency_type)
    if model and not model.objects.filter(pk=constituency_id, is_active=True).exists():
        raise ValidationError({"constituency_id": "Select an active election constituency."})


def _schools():
    return [school_option(school) for school in School.objects.filter(is_active=True).order_by("name")]


def _student_options():
    students = (
        Profile.objects.select_related(
            "user",
            "student_detail",
            "student_detail__school",
            "student_detail__center",
            "student_detail__department",
            "student_detail__program",
        )
        .filter(role=Profile.ROLE_STUDENT, is_active=True)
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    return [profile_option(student) for student in students]


def _elections_queryset():
    return (
        models.Election.objects.select_related("school")
        .prefetch_related("school_seats__school")
        .annotate(candidate_count=Count("candidates", distinct=True), vote_count=Count("votes", distinct=True))
        .order_by("-starts_at", "-created_at")
    )


def _candidate_queryset():
    return (
        models.ElectionCandidate.objects.select_related(
            "election",
            "school",
            "student__user",
            "student__student_detail__school",
            "student__student_detail__center",
            "student__student_detail__department",
            "student__student_detail__program",
        )
        .annotate(vote_count=Count("votes"))
        .order_by("election__title", "category", "school__name", "sort_order", "display_name")
    )


def _json_value(data, key, current, default):
    if key not in data:
        return current if current is not None else default
    value = data.get(key)
    if isinstance(value, str):
        parsed = parse_json(value)
        return parsed if parsed is not None else default
    return value if value is not None else default


def _election_form_payload(data, election=None):
    election_type = data.get("election_type", getattr(election, "election_type", models.Election.TYPE_STUDENT_COUNCIL))
    election_type_label = str(data.get("election_type_label", getattr(election, "election_type_label", "")) or "").strip()
    constituency_type = data.get(
        "constituency_type",
        getattr(election, "constituency_type", models.Election.CONSTITUENCY_UNIVERSITY),
    )
    constituency_id = (
        _maybe_int(data.get("constituency_id"))
        if "constituency_id" in data
        else getattr(election, "constituency_id", None)
    )
    school_id = (
        _maybe_int(data.get("school"))
        if "school" in data
        else getattr(election, "school_id", None)
    )
    if election_type == models.Election.TYPE_SCHOOL_COMMITTEE:
        constituency_type = models.Election.CONSTITUENCY_SCHOOL
        constituency_id = school_id or constituency_id
    if constituency_type == models.Election.CONSTITUENCY_SCHOOL:
        school_id = constituency_id or school_id
    else:
        school_id = None
    return {
        "title": str(data.get("title", getattr(election, "title", "")) or "").strip(),
        "description": str(data.get("description", getattr(election, "description", "")) or ""),
        "election_type": election_type,
        "election_type_label": election_type_label,
        "school_id": school_id,
        "constituency_type": constituency_type,
        "constituency_id": constituency_id,
        "constituency_label": str(
            data.get("constituency_label", getattr(election, "constituency_label", "")) or ""
        ).strip(),
        "starts_at": _parse_aware_datetime(data.get("starts_at")) if "starts_at" in data else getattr(election, "starts_at", None),
        "ends_at": _parse_aware_datetime(data.get("ends_at")) if "ends_at" in data else getattr(election, "ends_at", None),
        "general_selection_count": int(data.get("general_selection_count", getattr(election, "general_selection_count", 0)) or 0),
        "school_selection_count": int(data.get("school_selection_count", getattr(election, "school_selection_count", 0)) or 0),
        "seat_rules": _json_value(data, "seat_rules", getattr(election, "seat_rules", None), []),
        "nomination_rules": _json_value(data, "nomination_rules", getattr(election, "nomination_rules", None), {}),
        "voter_eligibility": _json_value(data, "voter_eligibility", getattr(election, "voter_eligibility", None), {}),
        "result_publication_rules": _json_value(
            data,
            "result_publication_rules",
            getattr(election, "result_publication_rules", None),
            {},
        ),
        "school_seats": data.get("school_seats"),
        "status": data.get(
            "status",
            getattr(election, "status", models.Election.STATUS_UPCOMING if _bool_value(data.get("is_active")) else models.Election.STATUS_DRAFT),
        ),
        "is_active": _bool_value(data.get("is_active"), getattr(election, "is_active", False)),
    }


def _save_election(election, payload, request):
    if not payload["title"]:
        raise ValidationError({"title": "Election title is required."})
    _validate_constituency(payload)
    for field, value in payload.items():
        if field == "school_seats":
            continue
        setattr(election, field, value)
    if not election.created_by_id:
        election.created_by = _request_profile(request)
    election.full_clean()
    election.save()

    school_seats = payload.get("school_seats")
    if school_seats is not None and election.election_type == models.Election.TYPE_SRC:
        election.school_seats.all().delete()
        for seat_data in school_seats:
            school_id = seat_data.get("school_id")
            seat_count = int(seat_data.get("seat_count", 0))
            if school_id and seat_count > 0:
                models.SchoolElectionSeat.objects.create(
                    election=election,
                    school_id=school_id,
                    seat_count=seat_count,
                )
    elif election.election_type != models.Election.TYPE_SRC:
        election.school_seats.all().delete()

    return election


def _candidate_form_payload(data, candidate=None):
    election_id = _maybe_int(data.get("election", getattr(candidate, "election_id", None)))
    if not election_id:
        raise ValidationError({"election": "Election is required."})
    election = models.Election.objects.get(pk=election_id)
    category = data.get("category", getattr(candidate, "category", ""))
    if not category:
        rules = election.configured_seat_rules()
        category = rules[0]["key"] if rules else models.ElectionCandidate.CATEGORY_GENERAL
    payload = {
        "election": election,
        "student_id": _maybe_int(data.get("student")) if "student" in data else getattr(candidate, "student_id", None),
        "display_name": str(data.get("display_name", getattr(candidate, "display_name", "")) or "").strip(),
        "student_identifier": str(data.get("student_identifier", getattr(candidate, "student_identifier", "")) or "").strip(),
        "school_id": _maybe_int(data.get("school")) if "school" in data else getattr(candidate, "school_id", None),
        "category": category,
        "details": str(data.get("details", getattr(candidate, "details", "")) or ""),
        "manifesto": str(data.get("manifesto", getattr(candidate, "manifesto", "")) or ""),
        "status": data.get("status", getattr(candidate, "status", models.ElectionCandidate.STATUS_APPROVED)),
        "sort_order": int(data.get("sort_order", getattr(candidate, "sort_order", 0)) or 0),
    }
    photo = data.get("photo")
    if hasattr(photo, "read"):
        error = image_upload_error(photo, field_label="Candidate photo")
        if error:
            raise ValidationError({"photo": error})
        payload["photo"] = photo
    return payload


def _save_candidate(candidate, payload):
    for field, value in payload.items():
        setattr(candidate, field, value)
    candidate.save()
    return candidate


class TechnicianElections(APIView):
    permission_classes = [IsTechnicianRole]

    def get(self, request):
        elections = list(_elections_queryset())
        return Response(
            {
                "title": "Elections",
                "section": "technician",
                "elections": [election_payload(election) for election in elections],
                "schools": _schools(),
                "type_options": _election_type_options(elections),
                "status_options": _choice_options(models.Election.STATUS_CHOICES),
                "constituency_type_options": _choice_options(models.Election.CONSTITUENCY_CHOICES),
                "constituency_options": _constituency_options(),
                "seat_scope_options": _choice_options(models.Election.SEAT_SCOPE_CHOICES),
                "summary": {
                    "total": len(elections),
                    "active": sum(1 for election in elections if election.computed_status() == models.Election.STATUS_ACTIVE),
                    "upcoming": sum(1 for election in elections if election.computed_status() == models.Election.STATUS_UPCOMING),
                    "closed": sum(1 for election in elections if election.computed_status() in {models.Election.STATUS_CLOSED, models.Election.STATUS_PUBLISHED}),
                },
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            election = _save_election(models.Election(), _election_form_payload(request.data), request)
        except (ValidationError, ValueError) as error:
            errors = getattr(error, "message_dict", None) or getattr(error, "messages", None) or str(error)
            return Response({"detail": first_error(errors), "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if election.is_active or election.status in {
            models.Election.STATUS_UPCOMING,
            models.Election.STATUS_ACTIVE,
        }:
            notify_election_students(
                election,
                event_type="elections.opened",
                verb=f"Election available: {election.title}",
            )
        return Response(
            {"message": "Election created successfully.", "election": election_payload(election)},
            status=status.HTTP_201_CREATED,
        )


class TechnicianElectionDetail(APIView):
    permission_classes = [IsTechnicianRole]

    def _get_election(self, pk):
        return models.Election.objects.select_related("school").prefetch_related("school_seats__school").get(pk=pk)

    def patch(self, request, pk):
        try:
            election = self._get_election(pk)
            was_available = election.is_active or election.status in {
                models.Election.STATUS_UPCOMING,
                models.Election.STATUS_ACTIVE,
            }
            election = _save_election(election, _election_form_payload(request.data, election), request)
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError) as error:
            errors = getattr(error, "message_dict", None) or getattr(error, "messages", None) or str(error)
            return Response({"detail": first_error(errors), "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        is_available = election.is_active or election.status in {
            models.Election.STATUS_UPCOMING,
            models.Election.STATUS_ACTIVE,
        }
        if is_available and not was_available:
            notify_election_students(
                election,
                event_type="elections.opened",
                verb=f"Election available: {election.title}",
            )
        return Response(
            {"message": "Election updated successfully.", "election": election_payload(election)},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            election = self._get_election(pk)
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)
        election.delete()
        return Response({"message": "Election deleted successfully."}, status=status.HTTP_200_OK)


class TechnicianElectionsCandidates(APIView):
    permission_classes = [IsTechnicianRole]

    def get(self, request):
        candidates = _candidate_queryset()
        election_id = request.query_params.get("election")
        if election_id:
            candidates = candidates.filter(election_id=election_id)
        return Response(
            {
                "title": "Election Candidates",
                "section": "technician",
                "candidates": [candidate_payload(candidate, request) for candidate in candidates],
                "elections": [election_payload(election) for election in _elections_queryset()],
                "schools": _schools(),
                "students": _student_options(),
                "category_options": _choice_options(models.ElectionCandidate.CATEGORY_CHOICES),
                "status_options": _choice_options(models.ElectionCandidate.STATUS_CHOICES),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            candidate = _save_candidate(models.ElectionCandidate(), _candidate_form_payload(request.data))
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError) as error:
            errors = getattr(error, "message_dict", None) or getattr(error, "messages", None) or str(error)
            return Response({"detail": first_error(errors), "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        notify_candidate(
            candidate,
            _request_profile(request),
            f"You were added as a candidate for {candidate.election.title}.",
        )
        return Response(
            {"message": "Candidate saved successfully.", "candidate": candidate_payload(candidate, request)},
            status=status.HTTP_201_CREATED,
        )


class TechnicianElectionCandidateDetail(APIView):
    permission_classes = [IsTechnicianRole]

    def _get_candidate(self, pk):
        return models.ElectionCandidate.objects.select_related(
            "election", "school", "student__user", "student__student_detail__school"
        ).get(pk=pk)

    def patch(self, request, pk):
        try:
            candidate = self._get_candidate(pk)
            old_status = candidate.status
            candidate = _save_candidate(candidate, _candidate_form_payload(request.data, candidate))
        except models.ElectionCandidate.DoesNotExist:
            return Response({"detail": "Candidate not found."}, status=status.HTTP_404_NOT_FOUND)
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError) as error:
            errors = getattr(error, "message_dict", None) or getattr(error, "messages", None) or str(error)
            return Response({"detail": first_error(errors), "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if candidate.status != old_status:
            notify_candidate(
                candidate,
                _request_profile(request),
                (
                    f"Your candidate status for {candidate.election.title} changed to "
                    f"{candidate.get_status_display()}."
                ),
            )
        return Response(
            {"message": "Candidate updated successfully.", "candidate": candidate_payload(candidate, request)},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            candidate = self._get_candidate(pk)
        except models.ElectionCandidate.DoesNotExist:
            return Response({"detail": "Candidate not found."}, status=status.HTTP_404_NOT_FOUND)
        candidate.delete()
        return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)


class TechnicianElectionsResults(APIView):
    permission_classes = [IsTechnicianRole]

    def get(self, request):
        elections = _elections_queryset()
        election_id = request.query_params.get("election")
        if election_id:
            elections = elections.filter(id=election_id)
        rows = []
        for election in elections:
            payload = election_payload(election)
            payload["results"] = result_groups_for(election)
            rows.append(payload)
        return Response(
            {
                "title": "Election Results",
                "section": "technician",
                "elections": rows,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        election_id = request.data.get("election")
        try:
            election = models.Election.objects.get(pk=election_id)
        except models.Election.DoesNotExist:
            return Response({"detail": "Election not found."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        publication_rules = election.result_publication_rules if isinstance(election.result_publication_rules, dict) else {}
        if publication_rules.get("publish_after_close") and election.computed_status(now) not in {
            models.Election.STATUS_CLOSED,
            models.Election.STATUS_PUBLISHED,
        }:
            return Response(
                {"detail": "Results can only be published after voting closes."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = _request_profile(request)
        groups = result_groups_for(election)
        snapshot = models.ElectionResultSnapshot.objects.create(
            election=election,
            generated_by=profile,
            totals={"groups": groups},
            published_at=now,
        )
        election.status = models.Election.STATUS_PUBLISHED
        election.results_published_at = now
        election.published_by = profile
        election.save(update_fields=["status", "results_published_at", "published_by", "updated_at"])
        notify_election_students(
            election,
            event_type="elections.results_published",
            verb=f"Election results published: {election.title}",
        )
        return Response(
            {
                "message": "Election results snapshot saved.",
                "snapshot_id": snapshot.id,
                "election": election_payload(election),
                "results": groups,
            },
            status=status.HTTP_201_CREATED,
        )

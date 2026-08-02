from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from core.common.errors import first_error
from core.common.profiles import profile_display_name
from core.media_access import protected_media_url
from technician_app import models


def profile_option(profile):
    return {
        "id": profile.id,
        "name": profile_display_name(profile),
        "username": profile.user.username,
        "student_id": profile.student_id,
        "school": profile.school_id,
        "school_code": profile.school.code if profile.school_id else "",
        "school_name": profile.school.name if profile.school_id else "",
    }


def school_option(school):
    return {
        "id": school.id,
        "code": school.code,
        "name": school.name,
        "label": f"{school.code} - {school.name}",
    }


def _seconds_until(value, now):
    if not value:
        return 0
    return max(0, int((value - now).total_seconds()))


def countdown_for(election, now=None):
    current = now or timezone.now()
    computed_status = election.computed_status(current)
    if computed_status == models.Election.STATUS_UPCOMING:
        return {
            "label": "Election starts in",
            "target_at": election.starts_at.isoformat() if election.starts_at else None,
            "seconds_remaining": _seconds_until(election.starts_at, current),
        }
    if computed_status == models.Election.STATUS_ACTIVE:
        return {
            "label": "Voting closes in",
            "target_at": election.ends_at.isoformat() if election.ends_at else None,
            "seconds_remaining": _seconds_until(election.ends_at, current),
        }
    if computed_status in {models.Election.STATUS_CLOSED, models.Election.STATUS_PUBLISHED}:
        return {
            "label": "Voting closed",
            "target_at": election.ends_at.isoformat() if election.ends_at else None,
            "seconds_remaining": 0,
        }
    return {
        "label": "Draft election",
        "target_at": election.starts_at.isoformat() if election.starts_at else None,
        "seconds_remaining": 0,
    }


def election_payload(election, now=None):
    current = now or timezone.now()
    computed_status = election.computed_status(current)
    return {
        "id": election.id,
        "title": election.title,
        "description": election.description,
        "election_type": election.election_type,
        "election_type_label": election.get_election_type_display(),
        "school": election.school_id,
        "school_detail": school_option(election.school) if election.school_id else None,
        "starts_at": election.starts_at.isoformat() if election.starts_at else None,
        "ends_at": election.ends_at.isoformat() if election.ends_at else None,
        "general_selection_count": election.general_selection_count,
        "school_selection_count": election.school_selection_count,
        "school_seats": (
            [
                {
                    "school_id": seat.school_id,
                    "school_code": seat.school.code,
                    "school_name": seat.school.name,
                    "seat_count": seat.seat_count,
                }
                for seat in election.school_seats.select_related("school").all()
            ]
            if election.election_type == election.TYPE_SRC
            else []
        ),
        "status": election.status,
        "computed_status": computed_status,
        "is_active": election.is_active,
        "results_published_at": election.results_published_at.isoformat() if election.results_published_at else None,
        "created_at": election.created_at.isoformat() if election.created_at else None,
        "updated_at": election.updated_at.isoformat() if election.updated_at else None,
        "candidate_count": getattr(election, "candidate_count", None),
        "vote_count": getattr(election, "vote_count", None),
        "countdown": countdown_for(election, current),
    }


def photo_url(candidate, request=None):
    if not candidate.photo:
        return ""
    try:
        url = protected_media_url(candidate.photo.name)
    except ValueError:
        return ""
    return url


def candidate_payload(candidate, request=None):
    return {
        "id": candidate.id,
        "election": candidate.election_id,
        "student": candidate.student_id,
        "student_detail": profile_option(candidate.student) if candidate.student_id else None,
        "display_name": candidate.display_name,
        "student_identifier": candidate.student_identifier,
        "school": candidate.school_id,
        "school_detail": school_option(candidate.school) if candidate.school_id else None,
        "category": candidate.category,
        "category_label": candidate.get_category_display(),
        "details": candidate.details,
        "manifesto": candidate.manifesto,
        "photo_url": photo_url(candidate, request),
        "status": candidate.status,
        "status_label": candidate.get_status_display(),
        "sort_order": candidate.sort_order,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "vote_count": getattr(candidate, "vote_count", 0),
    }


def _approved_candidates(election):
    return (
        election.candidates.select_related(
            "student__user", "student__student_detail__school", "school"
        )
        .filter(status=models.ElectionCandidate.STATUS_APPROVED)
        .annotate(vote_count=Count("votes"))
    )


def _result_group(label, category, candidates):
    rows = sorted(
        [candidate_payload(candidate) for candidate in candidates],
        key=lambda row: (-row["vote_count"], row["display_name"].lower()),
    )
    return {
        "label": label,
        "category": category,
        "total_votes": sum(row["vote_count"] for row in rows),
        "candidates": rows,
    }


def result_groups_for(election):
    candidates = list(_approved_candidates(election))
    if election.election_type == models.Election.TYPE_SCHOOL_COMMITTEE:
        return [
            _result_group(
                election.school.name if election.school_id else "School Committee",
                models.ElectionCandidate.CATEGORY_SCHOOL,
                [candidate for candidate in candidates if candidate.category == models.ElectionCandidate.CATEGORY_SCHOOL],
            )
        ]

    groups = [
        _result_group(
            "SRC General Category",
            models.ElectionCandidate.CATEGORY_GENERAL,
            [candidate for candidate in candidates if candidate.category == models.ElectionCandidate.CATEGORY_GENERAL],
        )
    ]
    school_candidates = [
        candidate for candidate in candidates if candidate.category == models.ElectionCandidate.CATEGORY_SCHOOL
    ]
    schools = sorted(
        {
            candidate.school_id: candidate.school
            for candidate in school_candidates
            if candidate.school_id
        }.values(),
        key=lambda school: school.name,
    )
    for school in schools:
        groups.append(
            _result_group(
                f"{school.code} SRC School Category",
                models.ElectionCandidate.CATEGORY_SCHOOL,
                [candidate for candidate in school_candidates if candidate.school_id == school.id],
            )
        )
    unassigned = [candidate for candidate in school_candidates if not candidate.school_id]
    if unassigned:
        groups.append(
            _result_group("Unassigned SRC School Category", models.ElectionCandidate.CATEGORY_SCHOOL, unassigned)
        )
    return groups


def is_visible_to_student(election, student):
    if not election.is_active:
        return False
    if election.election_type == models.Election.TYPE_SRC:
        return True
    return bool(student.school_id and election.school_id == student.school_id)


def ballot_categories_for(election, student):
    if election.election_type == models.Election.TYPE_SRC:
        categories = []
        if election.general_selection_count:
            categories.append(models.ElectionCandidate.CATEGORY_GENERAL)
        if (
            student.school_id
            and election.school_seats.filter(school_id=student.school_id, seat_count__gt=0).exists()
        ):
            categories.append(models.ElectionCandidate.CATEGORY_SCHOOL)
        return categories
    if student.school_id and election.school_id == student.school_id:
        return [models.ElectionCandidate.CATEGORY_SCHOOL]
    return []


def eligible_candidates_for(election, student, category):
    qs = _approved_candidates(election).filter(category=category)
    if category == models.ElectionCandidate.CATEGORY_GENERAL:
        return qs if election.election_type == models.Election.TYPE_SRC else qs.none()
    if election.election_type == models.Election.TYPE_SRC:
        return qs.filter(school_id=student.school_id) if student.school_id else qs.none()
    return qs.filter(Q(school_id=student.school_id) | Q(school__isnull=True))


def ballot_label(election, category, student):
    if category == models.ElectionCandidate.CATEGORY_GENERAL:
        return "SRC General Ballot"
    if election.election_type == models.Election.TYPE_SRC:
        code = student.school.code if student.school_id else "School"
        return f"{code} SRC School Ballot"
    return "School Committee Ballot"


def student_election_payload(election, student):
    existing_votes = list(
        election.votes.filter(student=student).values_list("category", "candidate_id")
    )
    selected_by_category = {}
    for category, candidate_id in existing_votes:
        selected_by_category.setdefault(category, []).append(candidate_id)

    ballots = []
    for category in ballot_categories_for(election, student):
        candidates = eligible_candidates_for(election, student, category)
        ballots.append(
            {
                "category": category,
                "label": ballot_label(election, category, student),
                "required_count": election.selection_count_for(category, student.school_id),
                "submitted": category in selected_by_category,
                "selected_candidate_ids": selected_by_category.get(category, []),
                "candidates": [candidate_payload(candidate) for candidate in candidates],
            }
        )

    payload = election_payload(election)
    payload.update(
        {
            "ballots": ballots,
            "results": result_groups_for(election),
            "can_vote": election.computed_status() == models.Election.STATUS_ACTIVE,
        }
    )
    return payload


def cast_student_vote(election, student, category, candidate_ids):
    if not is_visible_to_student(election, student):
        return "This election is not available for your school.", 403
    if election.computed_status() != models.Election.STATUS_ACTIVE:
        return "Voting is not open for this election.", 403
    if category not in ballot_categories_for(election, student):
        return "This ballot is not available to you.", 400

    required_count = election.selection_count_for(category, student.school_id)
    normalized_ids = []
    for candidate_id in candidate_ids:
        try:
            normalized_id = int(candidate_id)
        except (TypeError, ValueError):
            return "Candidate selection is invalid.", 400
        if normalized_id not in normalized_ids:
            normalized_ids.append(normalized_id)

    if len(normalized_ids) != len(candidate_ids):
        return "Candidate selections cannot contain duplicates.", 400
    if required_count and len(normalized_ids) != required_count:
        return f"Select exactly {required_count} candidate{'s' if required_count != 1 else ''}.", 400
    if not required_count:
        return "This ballot has no configured selection count.", 400

    if election.votes.filter(student=student, category=category).exists():
        return "You have already submitted this ballot.", 409

    eligible_ids = set(
        eligible_candidates_for(election, student, category)
        .filter(id__in=normalized_ids)
        .values_list("id", flat=True)
    )
    if eligible_ids != set(normalized_ids):
        return "One or more selected candidates are not available for this ballot.", 400

    try:
        with transaction.atomic():
            for candidate_id in normalized_ids:
                models.Vote.objects.create(
                    election=election,
                    student=student,
                    candidate_id=candidate_id,
                    category=category,
                )
    except (IntegrityError, ValidationError):
        return "Unable to submit this ballot.", 400

    return "", 201

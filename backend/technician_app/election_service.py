from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from admin_app import models as admin_models
from core.common.profiles import profile_display_name
from core.media_access import protected_media_url
from technician_app import models


ORG_MODELS_BY_CONSTITUENCY = {
    models.Election.CONSTITUENCY_SCHOOL: admin_models.School,
    models.Election.CONSTITUENCY_CENTER: admin_models.Center,
    models.Election.CONSTITUENCY_DEPARTMENT: admin_models.Department,
    models.Election.CONSTITUENCY_PROGRAM: admin_models.Program,
}


def profile_option(profile):
    detail = getattr(profile, "student_detail", None)
    return {
        "id": profile.id,
        "name": profile_display_name(profile),
        "username": profile.user.username,
        "student_id": profile.student_id,
        "school": profile.school_id,
        "school_code": profile.school.code if profile.school_id else "",
        "school_name": profile.school.name if profile.school_id else "",
        "center": profile.center_id,
        "department": profile.department_id,
        "program": profile.program_id,
        "current_year": getattr(detail, "current_year", None) if detail else None,
    }


def school_option(school):
    return {
        "id": school.id,
        "code": school.code,
        "name": school.name,
        "label": f"{school.code} - {school.name}",
    }


def organization_option(item):
    return {
        "id": item.id,
        "code": getattr(item, "code", ""),
        "name": getattr(item, "name", ""),
        "label": f"{getattr(item, 'code', '')} - {getattr(item, 'name', '')}".strip(" -"),
    }


def _title_from_key(value):
    return str(value or "").replace("_", " ").strip().title()


def _scope_id_for_student(student, scope_type):
    if scope_type == models.Election.CONSTITUENCY_SCHOOL:
        return student.school_id
    if scope_type == models.Election.CONSTITUENCY_CENTER:
        return student.center_id
    if scope_type == models.Election.CONSTITUENCY_DEPARTMENT:
        return student.department_id
    if scope_type == models.Election.CONSTITUENCY_PROGRAM:
        return student.program_id
    if scope_type == models.Election.CONSTITUENCY_COHORT:
        detail = getattr(student, "student_detail", None)
        return getattr(detail, "current_year", None) if detail else None
    return None


def constituency_label_for(election):
    if election.election_type == models.Election.TYPE_SCHOOL_COMMITTEE and election.school_id:
        return election.school.name
    if election.constituency_label:
        return election.constituency_label
    constituency_type = election.effective_constituency_type()
    constituency_id = election.effective_constituency_id()
    if constituency_type == models.Election.CONSTITUENCY_UNIVERSITY:
        return "University-wide"
    if constituency_type == models.Election.CONSTITUENCY_COHORT and constituency_id:
        return f"Cohort {constituency_id}"
    model = ORG_MODELS_BY_CONSTITUENCY.get(constituency_type)
    if not model or not constituency_id:
        return _title_from_key(constituency_type)
    try:
        item = model.objects.get(pk=constituency_id)
    except model.DoesNotExist:
        return _title_from_key(constituency_type)
    return getattr(item, "name", "") or getattr(item, "code", "") or str(item)


def constituency_detail_for(election):
    constituency_type = election.effective_constituency_type()
    constituency_id = election.effective_constituency_id()
    label = constituency_label_for(election)
    detail = {
        "type": constituency_type,
        "id": constituency_id,
        "label": label,
        "code": "",
        "name": label,
    }
    if constituency_type == models.Election.CONSTITUENCY_UNIVERSITY:
        return detail
    if constituency_type == models.Election.CONSTITUENCY_COHORT:
        detail["code"] = str(constituency_id or "")
        return detail
    model = ORG_MODELS_BY_CONSTITUENCY.get(constituency_type)
    if not model or not constituency_id:
        return detail
    try:
        item = model.objects.get(pk=constituency_id)
    except model.DoesNotExist:
        return detail
    return {
        "type": constituency_type,
        **organization_option(item),
    }


def category_options_for(election):
    return [
        {
            "value": rule["key"],
            "label": rule["label"],
            "scope_type": rule.get("scope_type", models.Election.SEAT_SCOPE_CONSTITUENCY),
            "scope_id": rule.get("scope_id"),
        }
        for rule in election.configured_seat_rules()
    ]


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
    seat_rules = election.configured_seat_rules()
    return {
        "id": election.id,
        "title": election.title,
        "description": election.description,
        "election_type": election.election_type,
        "election_type_label": election.get_election_type_display(),
        "constituency_type": election.effective_constituency_type(),
        "constituency_type_label": dict(models.Election.CONSTITUENCY_CHOICES).get(
            election.effective_constituency_type(),
            _title_from_key(election.effective_constituency_type()),
        ),
        "constituency_id": election.effective_constituency_id(),
        "constituency_label": constituency_label_for(election),
        "constituency_detail": constituency_detail_for(election),
        "school": election.school_id,
        "school_detail": school_option(election.school) if election.school_id else None,
        "starts_at": election.starts_at.isoformat() if election.starts_at else None,
        "ends_at": election.ends_at.isoformat() if election.ends_at else None,
        "general_selection_count": election.general_selection_count,
        "school_selection_count": election.school_selection_count,
        "seat_rules": seat_rules,
        "category_options": category_options_for(election),
        "nomination_rules": election.nomination_rules or {},
        "voter_eligibility": election.voter_eligibility or {},
        "result_publication_rules": election.result_publication_rules or {},
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
            "student__user",
            "student__student_detail__school",
            "student__student_detail__center",
            "student__student_detail__department",
            "student__student_detail__program",
            "school",
        )
        .filter(status=models.ElectionCandidate.STATUS_APPROVED)
        .annotate(vote_count=Count("votes"))
    )


def _result_group(label, category, candidates, category_label=None):
    rows = sorted(
        [candidate_payload(candidate) for candidate in candidates],
        key=lambda row: (-row["vote_count"], row["display_name"].lower()),
    )
    return {
        "label": label,
        "category": category,
        "category_label": category_label or label,
        "total_votes": sum(row["vote_count"] for row in rows),
        "candidates": rows,
    }


def result_groups_for(election):
    candidates = list(_approved_candidates(election))
    groups = []
    configured_categories = set()
    for rule in election.configured_seat_rules():
        category = rule["key"]
        configured_categories.add(category)
        category_candidates = [candidate for candidate in candidates if candidate.category == category]
        if (
            rule.get("scope_type") == models.Election.CONSTITUENCY_SCHOOL
            and not rule.get("scope_id")
            and election.election_type == models.Election.TYPE_SRC
        ):
            schools = sorted(
                {
                    candidate.school_id: candidate.school
                    for candidate in category_candidates
                    if candidate.school_id
                }.values(),
                key=lambda school: school.name,
            )
            for school in schools:
                groups.append(
                    _result_group(
                        f"{school.code} {rule['label']}",
                        category,
                        [candidate for candidate in category_candidates if candidate.school_id == school.id],
                        rule["label"],
                    )
                )
            unassigned = [candidate for candidate in category_candidates if not candidate.school_id]
            if unassigned:
                groups.append(_result_group(f"Unassigned {rule['label']}", category, unassigned, rule["label"]))
            continue

        label = rule["label"]
        if rule.get("scope_type") == models.Election.SEAT_SCOPE_CONSTITUENCY:
            label = label if election.effective_constituency_type() == models.Election.CONSTITUENCY_UNIVERSITY else f"{constituency_label_for(election)} {label}"
        groups.append(_result_group(label, category, category_candidates, rule["label"]))

    extra_categories = sorted({candidate.category for candidate in candidates} - configured_categories)
    for category in extra_categories:
        label = election.seat_label_for(category)
        groups.append(
            _result_group(label, category, [candidate for candidate in candidates if candidate.category == category], label)
        )
    return groups


def is_visible_to_student(election, student):
    if not election.is_active:
        return False
    return election.student_matches_constituency(student)


def _rule_is_available_to_student(election, student, rule):
    if not election.student_matches_constituency(student):
        return False
    scope_type = rule.get("scope_type", models.Election.SEAT_SCOPE_CONSTITUENCY)
    scope_id = rule.get("scope_id")
    if scope_type in {
        models.Election.SEAT_SCOPE_CONSTITUENCY,
        models.Election.CONSTITUENCY_UNIVERSITY,
    }:
        return True
    student_scope_id = _scope_id_for_student(student, scope_type)
    if scope_id:
        return str(student_scope_id) == str(scope_id)
    return bool(student_scope_id)


def ballot_categories_for(election, student):
    categories = []
    for rule in election.configured_seat_rules():
        category = rule["key"]
        if category in categories:
            continue
        if not _rule_is_available_to_student(election, student, rule):
            continue
        if election.selection_count_for(category, student.school_id) > 0:
            categories.append(category)
    return categories


def _candidate_scope_filter(scope_type, target_id):
    if not target_id:
        return Q()
    if scope_type == models.Election.CONSTITUENCY_SCHOOL:
        return (
            Q(school_id=target_id)
            | Q(student__student_detail__school_id=target_id)
            | Q(school__isnull=True, student__isnull=True)
        )
    if scope_type == models.Election.CONSTITUENCY_CENTER:
        return Q(student__student_detail__center_id=target_id) | Q(student__isnull=True)
    if scope_type == models.Election.CONSTITUENCY_DEPARTMENT:
        return Q(student__student_detail__department_id=target_id) | Q(student__isnull=True)
    if scope_type == models.Election.CONSTITUENCY_PROGRAM:
        return Q(student__student_detail__program_id=target_id) | Q(student__isnull=True)
    if scope_type == models.Election.CONSTITUENCY_COHORT:
        return Q(student__student_detail__current_year=target_id) | Q(student__isnull=True)
    return Q()


def eligible_candidates_for(election, student, category):
    qs = _approved_candidates(election).filter(category=category)
    rule = election.seat_rule_for(category)
    if not rule:
        return qs.none()
    scope_type = rule.get("scope_type", models.Election.SEAT_SCOPE_CONSTITUENCY)
    target_id = rule.get("scope_id")
    if scope_type == models.Election.SEAT_SCOPE_CONSTITUENCY:
        scope_type = election.effective_constituency_type()
        target_id = election.effective_constituency_id()
    elif not target_id:
        target_id = _scope_id_for_student(student, scope_type)
    return qs.filter(_candidate_scope_filter(scope_type, target_id))


def ballot_label(election, category, student):
    rule = election.seat_rule_for(category)
    return rule["label"] if rule else election.seat_label_for(category)


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
            "results": result_groups_for(election) if election.results_visible_to_students() else [],
            "can_vote": election.computed_status() == models.Election.STATUS_ACTIVE,
        }
    )
    return payload


def cast_student_vote(election, student, category, candidate_ids):
    if not is_visible_to_student(election, student):
        return "This election is not available for your constituency.", 403
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

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from core.common.request_utils import parse_bool as _parse_bool
from core.media_access import protected_media_url
from notifications_package.service import notify_profiles
from rest_framework.exceptions import ValidationError
from student_app.models import Enrollment
from teacher_app.assignment_service import (
    profile_display_name,
    serialize_assignment,
    teacher_offerings,
)
from teacher_app.assignment_group_service import (
    ensure_group_ready,
    group_for_student,
    group_rule_status,
)
from teacher_app.models import (
    Assignment,
    CourseActivity,
    CourseAnnouncement,
    CourseAnnouncementSlot,
    CourseAnnouncementSlotSelection,
    CourseResource,
    CourseResourceFolder,
    CourseSection,
)


RESOURCE_EXTENSIONS = {".pdf", ".ppt", ".pptx"}
STUDY_GUIDE_EXTENSIONS = {".pdf"}
PERCENT_QUANT = Decimal("0.01")


def offering_for_teacher(profile, offering_id):
    return teacher_offerings(profile).filter(pk=offering_id).first()


def serialize_resource(resource):
    return {
        "id": resource.id,
        "resource_type": resource.resource_type,
        "title": resource.title,
        "description": resource.description,
        "file": protected_media_url(resource.file.name) if resource.file else None,
        "url": resource.url,
        "content": resource.content,
        "visible_from": resource.visible_from.isoformat() if resource.visible_from else None,
        "section_id": resource.section_id,
        "folder_id": resource.folder_id,
        "sort_order": resource.sort_order,
        "is_published": resource.is_published,
        "created_by": profile_display_name(resource.created_by),
    }


def _format_percentage(value):
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        decimal_value = Decimal("0.00")
    return str(decimal_value.quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP))


def serialize_assessment_plan(offering):
    study_guide = offering.study_guide
    study_guide_name = study_guide.name.rsplit("/", 1)[-1] if study_guide else ""
    return {
        "has_final_exam": offering.has_final_exam,
        "coursework_percentage": _format_percentage(offering.coursework_percentage),
        "final_exam_percentage": _format_percentage(
            offering.final_exam_percentage if offering.has_final_exam else Decimal("0.00")
        ),
        "assessment_overview": offering.assessment_overview,
        "study_guide": protected_media_url(study_guide.name) if study_guide else None,
        "study_guide_name": study_guide_name,
    }


def serialize_section(section, *, published_only=False):
    resources = section.resources.all()
    assignments = section.assignments.select_related(
        "offering",
        "offering__course",
        "offering__semester",
        "created_by",
        "created_by__user",
    ).all()
    activities = section.activities.select_related("assignment", "resource").all()
    if published_only:
        resources = resources.filter(is_published=True)
        assignments = assignments.exclude(status=Assignment.STATUS_DRAFT)
    return {
        "id": section.id,
        "title": section.title,
        "summary": section.summary,
        "section_type": section.section_type,
        "week_number": section.week_number,
        "topic_label": section.topic_label,
        "starts_on": section.starts_on.isoformat() if section.starts_on else None,
        "ends_on": section.ends_on.isoformat() if section.ends_on else None,
        "sort_order": section.sort_order,
        "is_published": section.is_published,
        "resources": [serialize_resource(resource) for resource in resources],
        "assignments": [serialize_assignment(assignment) for assignment in assignments],
        "activities": [serialize_activity(activity) for activity in activities],
    }


def serialize_announcement_slot(slot, *, student=None, include_selection_details=False):
    selections = list(slot.selections.all())
    own_selection = next(
        (
            selection
            for selection in selections
            if student and (
                selection.student_id == student.id
                or (
                    selection.assignment_group_id
                    and any(
                        membership.student_id == student.id
                        for membership in selection.assignment_group.memberships.all()
                    )
                )
            )
        ),
        None,
    )
    can_select = True
    selection_block_reason = ""
    if (
        student
        and slot.announcement.assignment_id
        and slot.announcement.assignment.collaboration_mode == Assignment.COLLABORATION_GROUP
    ):
        group = group_for_student(slot.announcement.assignment, student)
        if not group:
            can_select = False
            selection_block_reason = "Create or join the project group first."
        elif group.leader_id != student.id:
            can_select = False
            selection_block_reason = "Only the group leader can select the presentation slot."
        else:
            rule_status = group_rule_status(group)
            if rule_status["violations"]:
                can_select = False
                selection_block_reason = rule_status["violations"][0]
    payload = {
        "id": slot.id,
        "label": slot.label,
        "starts_at": slot.starts_at.isoformat() if slot.starts_at else None,
        "ends_at": slot.ends_at.isoformat() if slot.ends_at else None,
        "capacity": slot.capacity,
        "selection_type": slot.selection_type,
        "selection_type_label": slot.get_selection_type_display(),
        "instructions": slot.instructions,
        "is_active": slot.is_active,
        "selected_count": len(selections),
        "remaining": max(slot.capacity - len(selections), 0),
        "is_full": len(selections) >= slot.capacity,
        "is_selected": own_selection is not None,
        "can_manage_selection": bool(own_selection and own_selection.student_id == getattr(student, "id", None)),
        "can_select": can_select,
        "selection_block_reason": selection_block_reason,
        "own_selection": {
            "id": own_selection.id,
            "group_name": own_selection.group_name,
        } if own_selection else None,
    }
    if include_selection_details:
        payload["selections"] = [
            {
                "id": selection.id,
                "student_id": selection.student_id,
                "student": profile_display_name(selection.student),
                "group_name": selection.group_name,
                "assignment_group_id": selection.assignment_group_id,
                "created_at": selection.created_at.isoformat() if selection.created_at else None,
            }
            for selection in selections
        ]
    return payload


def serialize_announcement(announcement, *, student=None, include_selection_details=False):
    return {
        "id": announcement.id,
        "title": announcement.title,
        "body": announcement.body,
        "announcement_type": announcement.announcement_type,
        "assignment_id": announcement.assignment_id,
        "assignment_title": announcement.assignment.title if announcement.assignment_id else "",
        "assignment_collaboration_mode": (
            announcement.assignment.collaboration_mode
            if announcement.assignment_id
            else ""
        ),
        "scheduled_for": announcement.scheduled_for.isoformat() if announcement.scheduled_for else None,
        "visible_from": announcement.visible_from.isoformat() if announcement.visible_from else None,
        "is_published": announcement.is_published,
        "created_by": profile_display_name(announcement.created_by),
        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
        "slots": [
            serialize_announcement_slot(
                slot,
                student=student,
                include_selection_details=include_selection_details,
            )
            for slot in announcement.slots.all()
        ],
    }


def serialize_folder(folder, *, published_only=False):
    resources = folder.resources.all()
    if published_only:
        resources = resources.filter(is_published=True)
    return {
        "id": folder.id,
        "parent_id": folder.parent_id,
        "title": folder.title,
        "description": folder.description,
        "sort_order": folder.sort_order,
        "is_published": folder.is_published,
        "created_by": profile_display_name(folder.created_by),
        "resources": [serialize_resource(resource) for resource in resources],
    }


def serialize_activity(activity):
    return {
        "id": activity.id,
        "section_id": activity.section_id,
        "assignment_id": activity.assignment_id,
        "resource_id": activity.resource_id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "opens_at": activity.opens_at.isoformat() if activity.opens_at else None,
        "due_at": activity.due_at.isoformat() if activity.due_at else None,
        "closes_at": activity.closes_at.isoformat() if activity.closes_at else None,
        "completion_policy": activity.completion_policy,
        "is_required": activity.is_required,
        "sort_order": activity.sort_order,
    }


def serialize_course_content(
    offering,
    *,
    published_only=False,
    student=None,
    include_slot_selection_details=False,
):
    sections = offering.course_sections.prefetch_related(
        "resources",
        "resources__created_by",
        "resources__created_by__user",
        "assignments",
        "assignments__created_by",
        "assignments__created_by__user",
        "activities",
    ).all()
    folders = offering.resource_folders.select_related("created_by", "created_by__user").prefetch_related(
        "resources",
        "resources__created_by",
        "resources__created_by__user",
    )
    resources = offering.course_resources.filter(section__isnull=True, folder__isnull=True).select_related(
        "created_by",
        "created_by__user",
    )
    announcements = offering.announcements.select_related(
        "created_by",
        "created_by__user",
        "assignment",
    ).prefetch_related(
        "slots",
        "slots__selections",
        "slots__selections__student",
        "slots__selections__student__user",
        "slots__selections__assignment_group",
        "slots__selections__assignment_group__memberships",
    ).all()
    assignments = Assignment.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
        "created_by",
        "created_by__user",
    ).filter(offering=offering)
    activities = offering.activities.select_related("assignment", "resource").all()
    if published_only:
        sections = sections.filter(is_published=True)
        folders = folders.filter(is_published=True)
        resources = resources.filter(is_published=True)
        announcements = announcements.filter(is_published=True)
        assignments = assignments.exclude(status=Assignment.STATUS_DRAFT)
    return {
        "course": {
            "id": offering.id,
            "code": offering.course.code,
            "title": offering.course.title,
            "section": offering.section,
            "has_lab": offering.course.has_lab,
            "semester": offering.semester.name,
        },
        "assessment": serialize_assessment_plan(offering),
        "section_types": [
            {"value": value, "label": label}
            for value, label in CourseSection.TYPE_CHOICES
        ],
        "announcement_types": [
            {"value": value, "label": label}
            for value, label in CourseAnnouncement.TYPE_CHOICES
        ],
        "resource_types": [
            {"value": value, "label": label}
            for value, label in CourseResource.TYPE_CHOICES
        ],
        "activity_types": [
            {"value": value, "label": label}
            for value, label in CourseActivity.TYPE_CHOICES
        ],
        "completion_policies": [
            {"value": value, "label": label}
            for value, label in CourseActivity.COMPLETION_CHOICES
        ],
        "sections": [serialize_section(section, published_only=published_only) for section in sections],
        "folders": [serialize_folder(folder, published_only=published_only) for folder in folders],
        "resources": [serialize_resource(resource) for resource in resources],
        "announcements": [
            serialize_announcement(
                announcement,
                student=student,
                include_selection_details=include_slot_selection_details,
            )
            for announcement in announcements
        ],
        "assignments": [serialize_assignment(assignment) for assignment in assignments],
        "activities": [serialize_activity(activity) for activity in activities],
    }


def validate_resource_file(upload):
    if not upload:
        return None
    extension = Path(upload.name).suffix.lower()
    if extension not in RESOURCE_EXTENSIONS:
        return "Course materials must be PDF, PPT, or PPTX files."
    return None


def validate_study_guide_file(upload):
    if not upload:
        return None
    extension = Path(upload.name).suffix.lower()
    if extension not in STUDY_GUIDE_EXTENSIONS:
        return "Study guides must be uploaded as PDF files."
    return None


def notify_course_students(offering, actor, verb, data):
    payload = dict(data or {})
    event_type = payload.pop("event_type", "courses.updated")
    url = payload.pop("url", None)
    notify_profiles(
        Enrollment.objects.filter(
            offering=offering,
            completed_at__isnull=True,
        ).values_list("student_id", flat=True),
        actor=actor,
        event_type=event_type,
        verb=verb,
        data=payload,
        url=url,
    )


def _parse_percentage(value, field_name):
    if value in (None, ""):
        value = 0
    try:
        percentage = Decimal(str(value)).quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({field_name: "Enter a valid percentage."}) from exc
    if percentage < Decimal("0.00") or percentage > Decimal("100.00"):
        raise ValidationError({field_name: "Percentage must be between 0 and 100."})
    return percentage


@transaction.atomic
def update_assessment_plan(offering, actor, data, upload=None):
    has_final_exam = _parse_bool(data.get("has_final_exam"), True)
    if has_final_exam:
        final_percentage = _parse_percentage(
            data.get("final_exam_percentage", offering.final_exam_percentage),
            "final_exam_percentage",
        )
        coursework_value = data.get("coursework_percentage")
        coursework_percentage = (
            Decimal("100.00") - final_percentage
            if coursework_value in (None, "")
            else _parse_percentage(coursework_value, "coursework_percentage")
        )
        if final_percentage <= Decimal("0.00"):
            raise ValidationError({"final_exam_percentage": "Final exam percentage must be greater than 0."})
    else:
        final_percentage = Decimal("0.00")
        coursework_percentage = Decimal("100.00")

    if coursework_percentage + final_percentage != Decimal("100.00"):
        raise ValidationError({"detail": "Coursework and final exam percentages must add up to 100."})

    file_error = validate_study_guide_file(upload)
    if file_error:
        raise ValidationError({"study_guide": file_error})

    clear_study_guide = _parse_bool(data.get("clear_study_guide"), False)
    if clear_study_guide and offering.study_guide:
        offering.study_guide.delete(save=False)
        offering.study_guide = None
    if upload:
        offering.study_guide = upload

    offering.has_final_exam = has_final_exam
    offering.final_exam_percentage = final_percentage
    offering.coursework_percentage = coursework_percentage
    offering.assessment_overview = str(data.get("assessment_overview", "")).strip()
    update_fields = [
        "has_final_exam",
        "final_exam_percentage",
        "coursework_percentage",
        "assessment_overview",
        "study_guide",
        "updated_at",
    ]
    offering.save(update_fields=update_fields)
    return offering


def _parse_slot_datetime(value, field_name):
    parsed = parse_datetime(str(value or ""))
    if not parsed:
        raise ValidationError({"slots": f"Each slot requires a valid {field_name}."})
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _slot_rows(data):
    raw_slots = data.get("slots", [])
    if isinstance(raw_slots, str):
        try:
            raw_slots = json.loads(raw_slots) if raw_slots.strip() else []
        except json.JSONDecodeError as exc:
            raise ValidationError({"slots": "Slot details must be valid JSON."}) from exc
    if not isinstance(raw_slots, list):
        raise ValidationError({"slots": "Slot details must be a list."})
    return raw_slots


@transaction.atomic
def create_course_announcement(offering, actor, data):
    assignment = None
    if data.get("assignment_id"):
        assignment = Assignment.objects.filter(
            pk=data.get("assignment_id"),
            offering=offering,
        ).first()
        if not assignment:
            raise ValidationError({"assignment_id": "The linked assignment must belong to this course."})
    announcement = CourseAnnouncement.objects.create(
        offering=offering,
        assignment=assignment,
        title=str(data.get("title", "")).strip(),
        body=str(data.get("body", data.get("description", ""))).strip(),
        announcement_type=data.get("announcement_type", CourseAnnouncement.TYPE_GENERAL),
        scheduled_for=data.get("scheduled_for") or None,
        visible_from=data.get("visible_from") or None,
        is_published=_parse_bool(data.get("is_published"), True),
        created_by=actor,
    )
    for index, row in enumerate(_slot_rows(data), start=1):
        if not isinstance(row, dict):
            raise ValidationError({"slots": f"Slot {index} is invalid."})
        starts_at = _parse_slot_datetime(row.get("starts_at"), "start date and time")
        ends_at = (
            _parse_slot_datetime(row.get("ends_at"), "end date and time")
            if row.get("ends_at")
            else None
        )
        try:
            capacity = int(row.get("capacity", 1))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"slots": f"Slot {index} capacity must be a number."}) from exc
        slot = CourseAnnouncementSlot(
            announcement=announcement,
            label=str(row.get("label", "")).strip(),
            starts_at=starts_at,
            ends_at=ends_at,
            capacity=capacity,
            selection_type=row.get("selection_type", CourseAnnouncementSlot.SELECTION_INDIVIDUAL),
            instructions=str(row.get("instructions", "")).strip(),
            is_active=_parse_bool(row.get("is_active"), True),
        )
        try:
            if assignment and assignment.collaboration_mode == Assignment.COLLABORATION_GROUP:
                if slot.selection_type != CourseAnnouncementSlot.SELECTION_GROUP:
                    raise ValidationError("Group assignments require group presentation slots.")
            if assignment and assignment.collaboration_mode == Assignment.COLLABORATION_INDIVIDUAL:
                if slot.selection_type != CourseAnnouncementSlot.SELECTION_INDIVIDUAL:
                    raise ValidationError("Individual assignments require individual presentation slots.")
            slot.full_clean()
        except Exception as exc:
            raise ValidationError({"slots": f"Slot {index}: {exc}"}) from exc
        slot.save()
    if announcement.is_published:
        notify_course_students(
            offering,
            actor,
            f"New {announcement.get_announcement_type_display().lower()} announcement: {announcement.title}",
            {
                "announcement_id": announcement.id,
                "offering_id": offering.id,
                "course_code": offering.course.code,
                "announcement_type": announcement.announcement_type,
                "event_type": "courses.announcement_published",
                "url": "/student/dashboard",
            },
        )
    return announcement


@transaction.atomic
def select_announcement_slot(announcement, student, slot_id, *, group_name=""):
    slot = (
        CourseAnnouncementSlot.objects.select_for_update()
        .filter(pk=slot_id, announcement=announcement, is_active=True)
        .first()
    )
    if not slot:
        raise ValidationError({"detail": "This slot is no longer available."})
    assignment_group = None
    if announcement.assignment_id:
        if announcement.assignment.collaboration_mode == Assignment.COLLABORATION_GROUP:
            assignment_group = group_for_student(announcement.assignment, student)
            if not assignment_group:
                raise ValidationError({"detail": "Create or join a project group before selecting a group slot."})
            if assignment_group.leader_id != student.id:
                raise ValidationError({"detail": "Only the group leader can select the presentation slot."})
            ensure_group_ready(assignment_group)
            group_name = assignment_group.name
        elif slot.selection_type != CourseAnnouncementSlot.SELECTION_INDIVIDUAL:
            raise ValidationError({"detail": "This individual assignment requires an individual slot."})
    existing_query = CourseAnnouncementSlotSelection.objects.select_for_update().filter(
        announcement=announcement,
    )
    existing = (
        existing_query.filter(assignment_group=assignment_group).first()
        if assignment_group
        else existing_query.filter(student=student).first()
    )
    occupied = slot.selections.exclude(pk=existing.pk if existing else None).count()
    if occupied >= slot.capacity:
        raise ValidationError({"detail": "This slot has reached its selection limit."})
    group_name = str(group_name or "").strip()
    if slot.selection_type == CourseAnnouncementSlot.SELECTION_GROUP and not group_name:
        raise ValidationError({"group_name": "Enter your group name before selecting this slot."})
    if existing:
        existing.slot = slot
        existing.student = student
        existing.assignment_group = assignment_group
        existing.group_name = group_name if slot.selection_type == CourseAnnouncementSlot.SELECTION_GROUP else ""
        existing.full_clean()
        existing.save(update_fields=["slot", "student", "assignment_group", "group_name", "updated_at"])
        selection = existing
    else:
        selection = CourseAnnouncementSlotSelection(
            announcement=announcement,
            slot=slot,
            student=student,
            assignment_group=assignment_group,
            group_name=group_name if slot.selection_type == CourseAnnouncementSlot.SELECTION_GROUP else "",
        )
        selection.full_clean()
        selection.save()
    notify_profiles(
        [announcement.created_by_id] if announcement.created_by_id else [],
        actor=student,
        event_type="courses.announcement_slot_selected",
        verb=f"{profile_display_name(student)} selected {slot.label or announcement.title}.",
        data={
            "announcement_id": announcement.id,
            "slot_id": slot.id,
            "offering_id": announcement.offering_id,
            "group_name": selection.group_name,
        },
        url=f"/teacher/courses/{announcement.offering_id}",
    )
    return selection


def cancel_announcement_slot(announcement, student):
    filters = {"announcement": announcement, "student": student}
    if (
        announcement.assignment_id
        and announcement.assignment.collaboration_mode == Assignment.COLLABORATION_GROUP
    ):
        group = group_for_student(announcement.assignment, student)
        if not group or group.leader_id != student.id:
            raise ValidationError({"detail": "Only the group leader can cancel the presentation slot."})
        filters = {"announcement": announcement, "assignment_group": group}
    deleted, _details = CourseAnnouncementSlotSelection.objects.filter(**filters).delete()
    return bool(deleted)

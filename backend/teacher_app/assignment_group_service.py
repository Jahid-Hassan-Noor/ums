from django.db import IntegrityError, transaction
from django.utils import timezone
from notifications_package.service import notify_profile
from rest_framework.exceptions import ValidationError

from applicant_app.models import AdmissionApplication, Applicant
from student_app.models import Enrollment
from teacher_app.assignment_service import profile_display_name
from teacher_app.models import (
    Assignment,
    AssignmentGroup,
    AssignmentGroupInvitation,
    AssignmentGroupMembership,
)


def profile_country(profile):
    applicant = Applicant.objects.filter(profile=profile).first()
    if applicant:
        country = applicant.country_of_residence or applicant.nationality
        if country:
            return country.strip()
    application = (
        AdmissionApplication.objects.filter(applicant__profile=profile)
        .order_by("-updated_at", "-created_at")
        .first()
    )
    personal = application.personal_information if application else {}
    return str(
        personal.get("country")
        or personal.get("country_of_residence")
        or personal.get("nationality")
        or ""
    ).strip()


def assignment_enrollments(assignment):
    return (
        Enrollment.objects.select_related(
            "student",
            "student__user",
            "tutorial_group",
            "lab_group",
        )
        .filter(offering=assignment.offering, completed_at__isnull=True)
        .order_by("student__user__first_name", "student__user__last_name", "student__user__username")
    )


def enrollment_for_student(assignment, student):
    return assignment_enrollments(assignment).filter(student=student).first()


def group_for_student(assignment, student):
    membership = (
        AssignmentGroupMembership.objects.select_related(
            "group",
            "group__leader",
            "group__leader__user",
        )
        .filter(assignment=assignment, student=student)
        .first()
    )
    return membership.group if membership else None


def _student_summary(profile, enrollment=None):
    return {
        "id": profile.id,
        "name": profile_display_name(profile),
        "username": profile.user.username,
        "tutorial_group": enrollment.tutorial_group.code if enrollment and enrollment.tutorial_group else "",
        "tutorial_group_id": enrollment.tutorial_group_id if enrollment else None,
        "lab_group": enrollment.lab_group.code if enrollment and enrollment.lab_group else "",
        "lab_group_id": enrollment.lab_group_id if enrollment else None,
        "country": profile_country(profile),
    }


def membership_rule_error(assignment, leader_enrollment, invitee_enrollment):
    if assignment.require_same_tutorial_group:
        if (
            not leader_enrollment.tutorial_group_id
            or leader_enrollment.tutorial_group_id != invitee_enrollment.tutorial_group_id
        ):
            return "Group members must belong to the leader's tutorial group."
    if assignment.require_same_lab_group:
        if (
            not leader_enrollment.lab_group_id
            or leader_enrollment.lab_group_id != invitee_enrollment.lab_group_id
        ):
            return "Group members must belong to the leader's lab group."
    return None


def group_rule_status(group):
    assignment = group.assignment
    memberships = list(
        group.memberships.select_related("student", "student__user").all()
    )
    countries = sorted(
        {
            country
            for country in (profile_country(membership.student) for membership in memberships)
            if country
        }
    )
    violations = []
    if len(memberships) > assignment.max_group_members:
        violations.append(f"Group exceeds the {assignment.max_group_members}-member limit.")
    if assignment.min_distinct_countries and len(countries) < assignment.min_distinct_countries:
        violations.append(
            f"Group requires members from at least {assignment.min_distinct_countries} different countries."
        )
    return {
        "member_count": len(memberships),
        "max_members": assignment.max_group_members,
        "countries": countries,
        "country_count": len(countries),
        "required_country_count": assignment.min_distinct_countries,
        "violations": violations,
        "is_ready": not violations,
    }


def ensure_group_ready(group):
    status = group_rule_status(group)
    if status["violations"]:
        raise ValidationError({"detail": status["violations"][0]})
    return status


def serialize_group(group, *, viewer=None):
    enrollment_map = {
        enrollment.student_id: enrollment
        for enrollment in assignment_enrollments(group.assignment).filter(
            student_id__in=group.memberships.values_list("student_id", flat=True)
        )
    }
    members = [
        {
            **_student_summary(membership.student, enrollment_map.get(membership.student_id)),
            "is_leader": membership.student_id == group.leader_id,
            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
        }
        for membership in group.memberships.select_related("student", "student__user").all()
    ]
    return {
        "id": group.id,
        "name": group.name,
        "leader_id": group.leader_id,
        "leader": profile_display_name(group.leader),
        "is_leader": bool(viewer and group.leader_id == viewer.id),
        "members": members,
        "rule_status": group_rule_status(group),
    }


def serialize_invitation(invitation):
    return {
        "id": invitation.id,
        "group_id": invitation.group_id,
        "group_name": invitation.group.name,
        "leader": profile_display_name(invitation.group.leader),
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
    }


def group_workspace(assignment, student):
    if assignment.collaboration_mode != Assignment.COLLABORATION_GROUP:
        return None
    group = group_for_student(assignment, student)
    invitations = (
        AssignmentGroupInvitation.objects.select_related(
            "group",
            "group__leader",
            "group__leader__user",
        )
        .filter(
            assignment=assignment,
            invitee=student,
            status=AssignmentGroupInvitation.STATUS_PENDING,
        )
    )
    eligible_students = []
    if group and group.leader_id == student.id:
        grouped_student_ids = set(
            AssignmentGroupMembership.objects.filter(assignment=assignment).values_list("student_id", flat=True)
        )
        pending_by_student = {
            invitation.invitee_id: invitation
            for invitation in group.invitations.filter(status=AssignmentGroupInvitation.STATUS_PENDING)
        }
        leader_enrollment = enrollment_for_student(assignment, student)
        for enrollment in assignment_enrollments(assignment):
            if enrollment.student_id == student.id or enrollment.student_id in grouped_student_ids:
                continue
            rule_error = membership_rule_error(assignment, leader_enrollment, enrollment)
            candidate = _student_summary(enrollment.student, enrollment)
            candidate.update({
                "eligibility_error": rule_error,
                "invitation_status": (
                    pending_by_student[enrollment.student_id].status
                    if enrollment.student_id in pending_by_student
                    else ""
                ),
            })
            eligible_students.append(candidate)
    return {
        "config": {
            "max_members": assignment.max_group_members,
            "require_same_tutorial_group": assignment.require_same_tutorial_group,
            "require_same_lab_group": assignment.require_same_lab_group,
            "min_distinct_countries": assignment.min_distinct_countries,
            "extra_rules": assignment.group_rules,
        },
        "current_group": serialize_group(group, viewer=student) if group else None,
        "invitations": [serialize_invitation(invitation) for invitation in invitations],
        "eligible_students": eligible_students,
    }


def teacher_group_overview(assignment):
    if assignment.collaboration_mode != Assignment.COLLABORATION_GROUP:
        return []
    return [
        serialize_group(group)
        for group in assignment.groups.select_related("leader", "leader__user").prefetch_related(
            "memberships",
            "memberships__student",
            "memberships__student__user",
        )
    ]


@transaction.atomic
def create_group(assignment, leader, name):
    if assignment.collaboration_mode != Assignment.COLLABORATION_GROUP:
        raise ValidationError({"detail": "This is not a group assignment."})
    if not enrollment_for_student(assignment, leader):
        raise ValidationError({"detail": "Only enrolled students can create a group."})
    if group_for_student(assignment, leader):
        raise ValidationError({"detail": "You already belong to a group for this assignment."})
    name = str(name or "").strip()
    if not name:
        raise ValidationError({"name": "Enter a group name."})
    try:
        group = AssignmentGroup.objects.create(assignment=assignment, name=name, leader=leader)
        AssignmentGroupMembership.objects.create(
            assignment=assignment,
            group=group,
            student=leader,
        )
    except IntegrityError as exc:
        raise ValidationError({"detail": "This group name is already in use."}) from exc
    return group


@transaction.atomic
def invite_student(group, leader, invitee_id):
    group = AssignmentGroup.objects.select_for_update().select_related("assignment", "leader").get(pk=group.pk)
    if group.leader_id != leader.id:
        raise ValidationError({"detail": "Only the group leader can invite members."})
    if group.memberships.count() >= group.assignment.max_group_members:
        raise ValidationError({"detail": "This group has reached its maximum member capacity."})
    invitee_enrollment = assignment_enrollments(group.assignment).filter(student_id=invitee_id).first()
    leader_enrollment = enrollment_for_student(group.assignment, leader)
    if not invitee_enrollment:
        raise ValidationError({"detail": "The invited student is not enrolled in this course."})
    if AssignmentGroupMembership.objects.filter(
        assignment=group.assignment,
        student_id=invitee_id,
    ).exists():
        raise ValidationError({"detail": "This student already belongs to a group for this assignment."})
    rule_error = membership_rule_error(group.assignment, leader_enrollment, invitee_enrollment)
    if rule_error:
        raise ValidationError({"detail": rule_error})
    invitation, _created = AssignmentGroupInvitation.objects.update_or_create(
        group=group,
        invitee_id=invitee_id,
        defaults={
            "assignment": group.assignment,
            "invited_by": leader,
            "status": AssignmentGroupInvitation.STATUS_PENDING,
            "responded_at": None,
        },
    )
    notify_profile(
        invitation.invitee,
        actor=leader,
        event_type="assignments.group_invitation",
        verb=f"{profile_display_name(leader)} invited you to join {group.name}.",
        data={"assignment_id": group.assignment_id, "group_id": group.id},
        url=f"/student/assignments/{group.assignment_id}",
    )
    return invitation


@transaction.atomic
def respond_to_invitation(invitation, student, accept):
    invitation = (
        AssignmentGroupInvitation.objects.select_for_update()
        .select_related("group", "group__assignment", "group__leader")
        .filter(pk=invitation.pk, invitee=student, status=AssignmentGroupInvitation.STATUS_PENDING)
        .first()
    )
    if not invitation:
        raise ValidationError({"detail": "This invitation is no longer available."})
    if not accept:
        invitation.status = AssignmentGroupInvitation.STATUS_DECLINED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])
        return invitation
    group = AssignmentGroup.objects.select_for_update().get(pk=invitation.group_id)
    assignment = invitation.assignment
    if AssignmentGroupMembership.objects.filter(assignment=assignment, student=student).exists():
        raise ValidationError({"detail": "You already belong to a group for this assignment."})
    if group.memberships.count() >= assignment.max_group_members:
        raise ValidationError({"detail": "This group has reached its maximum member capacity."})
    leader_enrollment = enrollment_for_student(assignment, group.leader)
    invitee_enrollment = enrollment_for_student(assignment, student)
    rule_error = membership_rule_error(assignment, leader_enrollment, invitee_enrollment)
    if rule_error:
        raise ValidationError({"detail": rule_error})
    AssignmentGroupMembership.objects.create(
        assignment=assignment,
        group=group,
        student=student,
    )
    invitation.status = AssignmentGroupInvitation.STATUS_ACCEPTED
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["status", "responded_at"])
    AssignmentGroupInvitation.objects.filter(
        assignment=assignment,
        invitee=student,
        status=AssignmentGroupInvitation.STATUS_PENDING,
    ).exclude(pk=invitation.pk).update(
        status=AssignmentGroupInvitation.STATUS_CANCELLED,
        responded_at=timezone.now(),
    )
    notify_profile(
        group.leader,
        actor=student,
        event_type="assignments.group_joined",
        verb=f"{profile_display_name(student)} joined {group.name}.",
        data={"assignment_id": assignment.id, "group_id": group.id},
        url=f"/student/assignments/{assignment.id}",
    )
    return invitation


@transaction.atomic
def remove_group_member(group, leader, student_id):
    group = AssignmentGroup.objects.select_for_update().select_related("assignment").get(pk=group.pk)
    if group.leader_id != leader.id:
        raise ValidationError({"detail": "Only the group leader can remove members."})
    if int(student_id) == group.leader_id:
        raise ValidationError({"detail": "The group leader cannot remove themselves."})
    deleted, _details = AssignmentGroupMembership.objects.filter(
        group=group,
        student_id=student_id,
    ).delete()
    if not deleted:
        raise ValidationError({"detail": "Group member not found."})


@transaction.atomic
def delete_group(group, leader):
    group = AssignmentGroup.objects.select_for_update().get(pk=group.pk)
    if group.leader_id != leader.id:
        raise ValidationError({"detail": "Only the group leader can delete the group."})
    group.delete()


@transaction.atomic
def leave_group(group, student):
    group = AssignmentGroup.objects.select_for_update().get(pk=group.pk)
    if group.leader_id == student.id:
        raise ValidationError({
            "detail": "Group leaders must delete the group instead of leaving it."
        })
    deleted, _details = AssignmentGroupMembership.objects.filter(group=group, student=student).delete()
    if not deleted:
        raise ValidationError({"detail": "You are not a member of this group."})

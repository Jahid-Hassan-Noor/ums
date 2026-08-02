from django.utils import timezone

from admin_app.models import Profile
from notifications_package.service import notify_profile, notify_roles
from technician_app.models import HelpdeskTicket, HelpdeskTicketUpdate


def profile_name(profile):
    return (
        f"{profile.user.first_name} {profile.user.last_name}".strip()
        or profile.user.username
    )


def ticket_payload(ticket):
    return {
        "id": ticket.id,
        "reference": f"ICT-{ticket.id:05d}",
        "category": ticket.category,
        "category_label": ticket.get_category_display(),
        "subject": ticket.subject,
        "description": ticket.description,
        "location": ticket.location,
        "status": ticket.status,
        "status_label": ticket.get_status_display(),
        "resolution_notes": ticket.resolution_notes,
        "student": {
            "id": ticket.student_id,
            "name": profile_name(ticket.student),
            "student_id": ticket.student.student_id,
            "email": ticket.student.user.email,
            "phone": ticket.student.phone,
        },
        "assigned_to": (
            {
                "id": ticket.assigned_to_id,
                "name": profile_name(ticket.assigned_to),
            }
            if ticket.assigned_to_id
            else None
        ),
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
        "updates": [
            {
                "id": update.id,
                "status": update.status,
                "status_label": update.get_status_display(),
                "note": update.note,
                "author_name": profile_name(update.author) if update.author_id else "System",
                "created_at": update.created_at.isoformat(),
            }
            for update in ticket.updates.all()
        ],
    }


def ticket_queryset():
    return HelpdeskTicket.objects.select_related(
        "student__user",
        "assigned_to__user",
    ).prefetch_related("updates__author__user")


def notify_technicians(ticket):
    notify_roles(
        [Profile.ROLE_TECHNICIAN],
        actor=ticket.student,
        event_type="helpdesk.created",
        verb=f"New ICT helpdesk ticket {ticket.subject}",
        data={"ticket_id": ticket.id, "category": ticket.category},
        url="/technician/helpdesk",
    )


def update_ticket(ticket, technician, status_value, note):
    ticket.status = status_value
    ticket.assigned_to = ticket.assigned_to or technician
    if status_value in {HelpdeskTicket.STATUS_ADDRESSED, HelpdeskTicket.STATUS_IN_PROGRESS}:
        ticket.addressed_at = ticket.addressed_at or timezone.now()
        ticket.solved_at = None
    elif status_value == HelpdeskTicket.STATUS_SOLVED:
        ticket.addressed_at = ticket.addressed_at or timezone.now()
        ticket.solved_at = timezone.now()
        if note:
            ticket.resolution_notes = note
    elif status_value == HelpdeskTicket.STATUS_SUBMITTED:
        ticket.solved_at = None
    ticket.save()
    HelpdeskTicketUpdate.objects.create(
        ticket=ticket,
        author=technician,
        status=status_value,
        note=note,
    )
    notify_profile(
        ticket.student,
        actor=technician,
        event_type="helpdesk.status_changed",
        verb=f"{ticket.get_status_display()}: {ticket.subject}",
        data={"ticket_id": ticket.id, "status": ticket.status},
        url="/student/ict-helpdesk",
    )
    return ticket

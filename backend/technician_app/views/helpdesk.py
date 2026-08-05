from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.settings_registry import (
    helpdesk_category_options,
    helpdesk_label,
    helpdesk_status_options,
)
from auth_app.permissions import IsStudentRole, IsTechnicianRole
from technician_app.models import HelpdeskTicket, HelpdeskTicketUpdate
from technician_app.service import (
    default_assignee_for_category,
    notify_technicians,
    ticket_payload,
    ticket_queryset,
    update_ticket,
)


def category_options():
    return helpdesk_category_options()


def status_options():
    return helpdesk_status_options()


class StudentHelpdeskTickets(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        tickets = ticket_queryset().filter(student=request.user.profile)
        title = helpdesk_label()
        return Response(
            {
                "title": title,
                "section": "student",
                "categories": category_options(),
                "tickets": [ticket_payload(ticket) for ticket in tickets],
            }
        )

    def post(self, request):
        category = str(request.data.get("category") or "").strip()
        title = helpdesk_label()
        valid_categories = {option["value"] for option in category_options()}
        if category not in valid_categories:
            return Response({"detail": f"Select a valid {title} category."}, status=status.HTTP_400_BAD_REQUEST)
        subject = str(request.data.get("subject") or "").strip()
        description = str(request.data.get("description") or "").strip()
        if not subject or not description:
            return Response(
                {"detail": "Subject and issue description are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ticket = HelpdeskTicket.objects.create(
            student=request.user.profile,
            assigned_to=default_assignee_for_category(category),
            category=category,
            subject=subject,
            description=description,
            location=str(request.data.get("location") or "").strip(),
        )
        HelpdeskTicketUpdate.objects.create(
            ticket=ticket,
            author=request.user.profile,
            status=HelpdeskTicket.STATUS_SUBMITTED,
            note=f"Issue submitted to {title}.",
        )
        notify_technicians(ticket)
        ticket = ticket_queryset().get(pk=ticket.pk)
        return Response(
            {"message": f"{title} ticket submitted successfully.", "ticket": ticket_payload(ticket)},
            status=status.HTTP_201_CREATED,
        )


class TechnicianHelpdeskDashboard(APIView):
    permission_classes = [IsTechnicianRole]

    def get(self, request):
        tickets = list(ticket_queryset())
        statuses = status_options()
        return Response(
            {
                "title": helpdesk_label(),
                "section": "technician",
                "summary": {
                    "total": len(tickets),
                    **{
                        value: sum(1 for ticket in tickets if ticket.status == value)
                        for value in [option["value"] for option in statuses]
                    },
                },
                "statuses": statuses,
                "tickets": [ticket_payload(ticket) for ticket in tickets],
            }
        )


class TechnicianHelpdeskTicketDetail(APIView):
    permission_classes = [IsTechnicianRole]

    def patch(self, request, pk):
        ticket = ticket_queryset().filter(pk=pk).first()
        if not ticket:
            return Response({"detail": "Service desk ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        status_value = str(request.data.get("status") or "").strip()
        valid_statuses = {option["value"] for option in status_options()}
        if status_value not in valid_statuses:
            return Response({"detail": "Select a valid ticket status."}, status=status.HTTP_400_BAD_REQUEST)
        note = str(request.data.get("note") or "").strip()
        ticket = update_ticket(ticket, request.user.profile, status_value, note)
        ticket = ticket_queryset().get(pk=ticket.pk)
        return Response({"message": "Service desk ticket updated successfully.", "ticket": ticket_payload(ticket)})


__all__ = [
    "StudentHelpdeskTickets",
    "TechnicianHelpdeskDashboard",
    "TechnicianHelpdeskTicketDetail",
]

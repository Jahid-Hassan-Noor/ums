from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import VenueBookingRequest
from auth_app.permissions import IsTechnicianRole
from technician_app.venue_booking_service import (
    BookingConflictError,
    bookings_queryset,
    decide_booking,
    serialize_booking,
    venues_payload,
)


class TechnicianVenueBookings(APIView):
    permission_classes = [IsTechnicianRole]

    def get(self, request):
        return Response(
            {
                "role": "technician",
                "venues": venues_payload(),
                "requests": [serialize_booking(booking) for booking in bookings_queryset()],
            }
        )


class TechnicianVenueBookingDecision(APIView):
    permission_classes = [IsTechnicianRole]

    def post(self, request, pk):
        decision = str(request.data.get("decision") or "").strip().lower()
        rejection_reason = str(request.data.get("rejection_reason") or "").strip()
        if decision not in {
            VenueBookingRequest.STATUS_APPROVED,
            VenueBookingRequest.STATUS_REJECTED,
        }:
            return Response(
                {"detail": "Decision must be approved or rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            booking = decide_booking(pk, request.user.profile, decision, rejection_reason)
        except BookingConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Venue booking request {booking.status}.",
                "request": serialize_booking(booking),
            }
        )


__all__ = ["TechnicianVenueBookings", "TechnicianVenueBookingDecision"]

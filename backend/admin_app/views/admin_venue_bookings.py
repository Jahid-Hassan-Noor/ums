from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import VenueBookingRequest
from auth_app.permissions import IsAdminRole
from technician_app.venue_booking_service import (
    BookingConflictError,
    BookingPolicyError,
    booking_policy_payload,
    bookings_queryset,
    can_review_venue_bookings,
    decide_booking,
    serialize_booking,
    venues_payload,
)


class AdminVenueBookings(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        if not can_review_venue_bookings(request.user.profile):
            return Response(
                {"detail": "Venue booking requests are not assigned to admins."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "role": "admin",
                "policy": booking_policy_payload(),
                "venues": venues_payload(),
                "requests": [serialize_booking(booking) for booking in bookings_queryset()],
            }
        )


class AdminVenueBookingDecision(APIView):
    permission_classes = [IsAdminRole]

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
        except BookingPolicyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Venue booking request {booking.status}.",
                "request": serialize_booking(booking),
            }
        )


__all__ = ["AdminVenueBookings", "AdminVenueBookingDecision"]

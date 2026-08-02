from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsTeacherRole
from technician_app.venue_booking_service import (
    BookingConflictError,
    bookings_queryset,
    cancel_booking,
    serialize_booking,
    submit_booking,
    validate_booking_payload,
    venues_payload,
)
from teacher_app.assignment_service import get_teacher_profile


class TeacherVenueBookings(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        teacher = get_teacher_profile(request.user)
        return Response(
            {
                "role": "teacher",
                "venues": venues_payload(),
                "requests": [
                    serialize_booking(booking)
                    for booking in bookings_queryset().filter(requester=teacher)
                ],
            }
        )

    def post(self, request):
        teacher = get_teacher_profile(request.user)
        payload, error = validate_booking_payload(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = submit_booking(teacher, payload)
        except BookingConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "message": "Venue booking request submitted for technician review.",
                "request": serialize_booking(bookings_queryset().get(pk=booking.pk)),
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherVenueBookingCancel(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request, pk):
        teacher = get_teacher_profile(request.user)
        try:
            booking = cancel_booking(pk, teacher)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Venue booking cancelled.",
                "request": serialize_booking(booking),
            }
        )


__all__ = ["TeacherVenueBookings", "TeacherVenueBookingCancel"]

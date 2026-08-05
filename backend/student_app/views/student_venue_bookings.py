from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from technician_app.venue_booking_service import (
    BookingConflictError,
    booking_policy_payload,
    bookings_queryset,
    cancel_booking,
    serialize_booking,
    submit_booking,
    validate_booking_payload,
    venues_payload,
)
from student_app.registration_service import get_student_profile


class StudentVenueBookings(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        return Response(
            {
                "role": "student",
                "policy": booking_policy_payload(),
                "venues": venues_payload(),
                "requests": [
                    serialize_booking(booking)
                    for booking in bookings_queryset().filter(requester=student)
                ],
            }
        )

    def post(self, request):
        student = get_student_profile(request.user)
        payload, error = validate_booking_payload(request.data, requester_role=student.role)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        try:
            booking = submit_booking(student, payload)
        except BookingConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "message": "Venue booking request submitted for technician review.",
                "request": serialize_booking(bookings_queryset().get(pk=booking.pk)),
            },
            status=status.HTTP_201_CREATED,
        )


class StudentVenueBookingCancel(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, pk):
        student = get_student_profile(request.user)
        try:
            booking = cancel_booking(pk, student)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "message": "Venue booking cancelled.",
                "request": serialize_booking(booking),
            }
        )


__all__ = ["StudentVenueBookings", "StudentVenueBookingCancel"]

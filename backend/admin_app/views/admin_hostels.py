from rest_framework import status
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from admin_app.hostel_student_life import (
    hostel_student_life_payload,
    save_hostel_student_life,
)
from auth_app.permissions import IsAdminRole
from admin_app.serializers import HostelRoomSerializer, HostelSerializer
from core.common.errors import first_error as _first_error
from core.common.profiles import profile_display_name
from student_app.models import Student


def _student_name(student):
    return profile_display_name(student.profile)


def _room_section(room_code, assigned_room):
    prefix = f"{room_code}-"
    if assigned_room.startswith(prefix):
        return assigned_room.removeprefix(prefix)
    return ""


def _replace_student_room_prefix(old_code, new_code):
    if not old_code or old_code == new_code:
        return

    students = Student.objects.filter(room=old_code) | Student.objects.filter(
        room__startswith=f"{old_code}-"
    )
    for student in students:
        if student.room == old_code:
            student.room = new_code
        else:
            student.room = f"{new_code}{student.room.removeprefix(old_code)}"
        student.save(update_fields=["room", "updated_at"])


def _export_rows():
    rows = []
    seen_hostel_ids = set()
    rooms = (
        models.HostelRoom.objects.select_related("hostel")
        .all()
        .order_by("hostel__code", "floor", "number")
    )

    for room in rooms:
        hostel = room.hostel
        seen_hostel_ids.add(hostel.id)
        residents = (
            Student.objects.select_related("profile__user")
            .filter(Q(room=room.code) | Q(room__startswith=f"{room.code}-"))
            .order_by("room", "student_id")
        )
        base = {
            "hostel_code": hostel.code,
            "hostel_name": hostel.name,
            "hostel_type": hostel.get_hostel_type_display(),
            "warden_name": hostel.warden_name,
            "warden_phone": hostel.warden_phone,
            "warden_email": hostel.warden_email,
            "room_code": room.code,
            "floor": room.floor,
            "room_number": room.number,
            "room_capacity": room.capacity,
        }
        if not residents:
            rows.append(
                {
                    **base,
                    "room_section": "",
                    "student_room": "",
                    "student_id": "",
                    "student_name": "",
                    "student_email": "",
                }
            )
            continue
        for student in residents:
            rows.append(
                {
                    **base,
                    "room_section": _room_section(room.code, student.room),
                    "student_room": student.room,
                    "student_id": student.student_id or student.profile.student_id,
                    "student_name": _student_name(student),
                    "student_email": student.profile.user.email,
                }
            )

    empty_hostels = models.Hostel.objects.exclude(id__in=seen_hostel_ids).order_by("code")
    for hostel in empty_hostels:
        rows.append(
            {
                "hostel_code": hostel.code,
                "hostel_name": hostel.name,
                "hostel_type": hostel.get_hostel_type_display(),
                "warden_name": hostel.warden_name,
                "warden_phone": hostel.warden_phone,
                "warden_email": hostel.warden_email,
                "room_code": "",
                "floor": "",
                "room_number": "",
                "room_capacity": "",
                "room_section": "",
                "student_room": "",
                "student_id": "",
                "student_name": "",
                "student_email": "",
            }
        )

    return rows


class AdminHostels(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        hostels = models.Hostel.objects.all().order_by("code")
        rooms = models.HostelRoom.objects.select_related("hostel").all()

        return Response(
            {
                "title": "Hostels",
                "section": "admin",
                "hostels": HostelSerializer(hostels, many=True).data,
                "rooms": HostelRoomSerializer(rooms, many=True).data,
                "student_life": hostel_student_life_payload(),
            },
            status=status.HTTP_200_OK,
        )


class AdminHostelStudentLife(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "title": "Hostel Student Information",
                "section": "admin",
                "student_life": hostel_student_life_payload(),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        raw_payload = request.data.get("student_life", request.data)
        try:
            student_life = save_hostel_student_life(
                raw_payload,
                getattr(request.user, "profile", None),
            )
        except ValidationError as error:
            return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Student hostel information updated successfully.",
                "student_life": student_life,
            },
            status=status.HTTP_200_OK,
        )


class AdminHostelsCRUDView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = HostelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        hostel = serializer.save()
        return Response(
            {
                "message": "Hostel created successfully.",
                "hostel": HostelSerializer(hostel).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminHostelDetailView(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            hostel = models.Hostel.objects.get(pk=pk)
        except models.Hostel.DoesNotExist:
            return Response(
                {"detail": "Hostel not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_room_codes = {room.id: room.code for room in hostel.rooms.all()}
        serializer = HostelSerializer(hostel, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        hostel = serializer.save()
        for room in hostel.rooms.all():
            room.save(update_fields=["code", "updated_at"])
            _replace_student_room_prefix(old_room_codes.get(room.id), room.code)
        return Response(
            {
                "message": "Hostel updated successfully.",
                "hostel": HostelSerializer(hostel).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            hostel = models.Hostel.objects.get(pk=pk)
        except models.Hostel.DoesNotExist:
            return Response(
                {"detail": "Hostel not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        hostel.delete()
        return Response(
            {"message": "Hostel deleted successfully."},
            status=status.HTTP_200_OK,
        )


class AdminHostelRoomsView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = HostelRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        room = serializer.save()
        return Response(
            {
                "message": "Hostel room created successfully.",
                "room": HostelRoomSerializer(room).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminHostelRoomDetailView(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            room = models.HostelRoom.objects.get(pk=pk)
        except models.HostelRoom.DoesNotExist:
            return Response(
                {"detail": "Hostel room not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_code = room.code
        serializer = HostelRoomSerializer(room, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        room = serializer.save()
        _replace_student_room_prefix(old_code, room.code)
        return Response(
            {
                "message": "Hostel room updated successfully.",
                "room": HostelRoomSerializer(room).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            room = models.HostelRoom.objects.get(pk=pk)
        except models.HostelRoom.DoesNotExist:
            return Response(
                {"detail": "Hostel room not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        room.delete()
        return Response(
            {"message": "Hostel room deleted successfully."},
            status=status.HTTP_200_OK,
        )


class AdminHostelExport(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "filename": "hostel-details.csv",
                "rows": _export_rows(),
            },
            status=status.HTTP_200_OK,
        )

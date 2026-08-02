from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole
from librarian_app.models import (
    Book,
    BookAcquisitionRequest,
    BookCopy,
    BorrowingLimit,
    BorrowRequest,
    Laptop,
    LibraryRoom,
    Loan,
)
from librarian_app.serializers import (
    BookAcquisitionRequestSerializer,
    BookSerializer,
    BorrowRequestSerializer,
    BorrowingLimitSerializer,
    LaptopSerializer,
    LoanSerializer,
    StudentLibraryRoomSerializer,
)
from librarian_app.service import (
    cancel_room_reservation,
    get_borrowing_limit,
    notify_librarians_of_book_acquisition_request,
    notify_librarians_of_request,
)


def _library_services():
    from admin_app.settings_registry import all_settings
    values = all_settings().get("librarian_library", {})
    return {
        "books_enabled": bool(values.get("books_enabled", True)),
        "laptops_enabled": bool(values.get("laptops_enabled", True)),
        "rooms_enabled": bool(values.get("rooms_enabled", True)),
    }


class StudentLibrary(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = request.user.profile
        section = request.query_params.get("section", "").strip().lower()
        query = request.query_params.get("q", "").strip()

        books = Book.objects.none()
        if section in {"", "books"} and query:
            books = Book.objects.prefetch_related("copies").filter(
                Q(title__icontains=query) | Q(author__icontains=query),
                is_active=True,
            )[:50]

        laptops = Laptop.objects.none()
        if section in {"", "laptops"}:
            laptops = (
                Laptop.objects.filter(status=Laptop.STATUS_AVAILABLE)
                .exclude(loans__status=Loan.STATUS_ACTIVE)
                .distinct()
            )

        rooms = LibraryRoom.objects.none()
        if section in {"", "rooms"}:
            rooms = (
                LibraryRoom.objects.filter(status=LibraryRoom.STATUS_AVAILABLE)
                .exclude(loans__status=Loan.STATUS_ACTIVE)
                .exclude(reservation_requests__status=BorrowRequest.STATUS_PENDING)
                .distinct()
            )

        requests = BorrowRequest.objects.select_related("student__user", "book", "laptop", "room").filter(
            student=student
        )
        loans = Loan.objects.select_related(
            "student__user",
            "book_copy__book",
            "book_copy__shelf",
            "laptop",
            "room",
        ).filter(student=student)
        acquisition_requests = BookAcquisitionRequest.objects.select_related(
            "student__user",
            "added_book",
        ).filter(student=student)

        if section == "books":
            requests = requests.filter(asset_type=BorrowRequest.ASSET_BOOK)
            loans = loans.filter(book_copy__isnull=False)
        elif section == "laptops":
            requests = requests.filter(asset_type=BorrowRequest.ASSET_LAPTOP)
            loans = loans.filter(laptop__isnull=False)
            acquisition_requests = acquisition_requests.none()
        elif section == "rooms":
            requests = requests.filter(asset_type=BorrowRequest.ASSET_ROOM)
            loans = loans.filter(room__isnull=False)
            acquisition_requests = acquisition_requests.none()

        return Response(
            {
                "title": "Library",
                "section": "student",
                "books": BookSerializer(books, many=True).data,
                "laptops": LaptopSerializer(laptops, many=True).data,
                "rooms": StudentLibraryRoomSerializer(rooms, many=True).data,
                "requests": BorrowRequestSerializer(requests, many=True).data,
                "loans": LoanSerializer(loans, many=True).data,
                "acquisition_requests": BookAcquisitionRequestSerializer(
                    acquisition_requests,
                    many=True,
                ).data,
                "borrowing_limit": BorrowingLimitSerializer(get_borrowing_limit(student)).data,
                "active_book_loans": Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, book_copy__isnull=False).count(),
                "active_laptop_loans": Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, laptop__isnull=False).count(),
                "active_room_loans": Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, room__isnull=False).count(),
                "pending_book_requests": BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_BOOK, status=BorrowRequest.STATUS_PENDING).count(),
                "pending_laptop_requests": BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_LAPTOP, status=BorrowRequest.STATUS_PENDING).count(),
                "pending_room_requests": BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_ROOM, status=BorrowRequest.STATUS_PENDING).count(),
                "library_services": _library_services(),
            }
        )

    def post(self, request):
        student = request.user.profile
        asset_type = request.data.get("asset_type")
        notes = str(request.data.get("notes") or "").strip()
        services = _library_services()
        if asset_type == BorrowRequest.ASSET_BOOK and not services["books_enabled"]:
            return Response({"detail": "Book borrowing is temporarily unavailable. Please try again later."}, status=status.HTTP_400_BAD_REQUEST)
        if asset_type == BorrowRequest.ASSET_LAPTOP and not services["laptops_enabled"]:
            return Response({"detail": "Laptop borrowing is currently disabled."}, status=status.HTTP_400_BAD_REQUEST)
        if asset_type == BorrowRequest.ASSET_ROOM and not services["rooms_enabled"]:
            return Response({"detail": "Discussion room booking is currently disabled."}, status=status.HTTP_400_BAD_REQUEST)
        if asset_type == BorrowRequest.ASSET_BOOK:
            book = Book.objects.filter(pk=request.data.get("book_id"), is_active=True).first()
            if not book or not book.copies.filter(status=BookCopy.STATUS_AVAILABLE).exists():
                return Response({"detail": "This book is not currently available."}, status=status.HTTP_400_BAD_REQUEST)
            if BorrowRequest.objects.filter(student=student, book=book, status=BorrowRequest.STATUS_PENDING).exists():
                return Response({"detail": "You already have a pending request for this book."}, status=status.HTTP_400_BAD_REQUEST)
            limit = get_borrowing_limit(student)
            active_book_loans = Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, book_copy__isnull=False).count()
            pending_book_requests = BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_BOOK, status=BorrowRequest.STATUS_PENDING).count()
            held_books = active_book_loans + pending_book_requests
            if held_books >= limit.max_keep_at_a_time:
                return Response(
                    {"detail": f"You already hold or have pending requests for {held_books} book(s). Return a book before requesting another (limit: {limit.max_keep_at_a_time})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if held_books >= limit.max_borrow_at_a_time:
                return Response(
                    {"detail": f"You have reached the borrow limit of {limit.max_borrow_at_a_time} book(s) at a time."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            borrow_request = BorrowRequest.objects.create(student=student, asset_type=asset_type, book=book, notes=notes)
        elif asset_type == BorrowRequest.ASSET_LAPTOP:
            laptop = Laptop.objects.filter(pk=request.data.get("laptop_id"), status=Laptop.STATUS_AVAILABLE).first()
            if not laptop:
                return Response({"detail": "This laptop is not currently available."}, status=status.HTTP_400_BAD_REQUEST)
            if BorrowRequest.objects.filter(student=student, laptop=laptop, status=BorrowRequest.STATUS_PENDING).exists():
                return Response({"detail": "You already have a pending request for this laptop."}, status=status.HTTP_400_BAD_REQUEST)
            active_laptop_loans = Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, laptop__isnull=False).count()
            pending_laptop_requests = BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_LAPTOP, status=BorrowRequest.STATUS_PENDING).count()
            if active_laptop_loans >= 1 or pending_laptop_requests >= 1:
                return Response(
                    {"detail": "You already have a laptop on loan or pending. Return it before borrowing another."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            borrow_request = BorrowRequest.objects.create(student=student, asset_type=asset_type, laptop=laptop, notes=notes)
        elif asset_type == BorrowRequest.ASSET_ROOM:
            with transaction.atomic():
                room = LibraryRoom.objects.select_for_update().filter(
                    pk=request.data.get("room_id"),
                    status=LibraryRoom.STATUS_AVAILABLE,
                ).first()
                if (
                    not room
                    or room.loans.filter(status=Loan.STATUS_ACTIVE).exists()
                    or room.reservation_requests.filter(status=BorrowRequest.STATUS_PENDING).exists()
                ):
                    return Response(
                        {"detail": "This discussion room is not currently available for reservation."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                active_room_loans = Loan.objects.filter(student=student, status=Loan.STATUS_ACTIVE, room__isnull=False).count()
                pending_room_requests = BorrowRequest.objects.filter(student=student, asset_type=BorrowRequest.ASSET_ROOM, status=BorrowRequest.STATUS_PENDING).count()
                if active_room_loans >= 1 or pending_room_requests >= 1:
                    return Response(
                        {"detail": "You already have a room allocated or pending. Return it before reserving another."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                borrow_request = BorrowRequest.objects.create(
                    student=student,
                    asset_type=asset_type,
                    room=room,
                    notes=notes,
                )
        else:
            return Response(
                {"detail": "Select a book, laptop, or discussion room."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        notify_librarians_of_request(borrow_request)
        return Response({"request": BorrowRequestSerializer(borrow_request).data}, status=status.HTTP_201_CREATED)


class StudentBookAcquisitionRequests(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request):
        serializer = BookAcquisitionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data["title"].strip()
        author = serializer.validated_data["author"].strip()
        student = request.user.profile

        if BookAcquisitionRequest.objects.filter(
            student=student,
            title__iexact=title,
            author__iexact=author,
            status=BookAcquisitionRequest.STATUS_PENDING,
        ).exists():
            return Response(
                {"detail": "You already have a pending request for this book."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        acquisition_request = serializer.save(
            student=student,
            title=title,
            author=author,
        )
        notify_librarians_of_book_acquisition_request(acquisition_request)
        return Response(
            {"request": BookAcquisitionRequestSerializer(acquisition_request).data},
            status=status.HTTP_201_CREATED,
        )


class StudentLibraryRoomReservationCancel(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, pk):
        try:
            borrow_request = cancel_room_reservation(pk, student=request.user.profile)
        except ValidationError as exc:
            message = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Room reservation cancelled.",
                "request": BorrowRequestSerializer(borrow_request).data,
            }
        )

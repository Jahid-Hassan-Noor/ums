from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app.models import Profile
from auth_app.permissions import IsLibrarianRole
from librarian_app.models import (
    Book,
    BookAcquisitionRequest,
    BookCopy,
    BorrowingLimit,
    BorrowRequest,
    Laptop,
    LibraryRoom,
    Loan,
    Shelf,
)
from librarian_app.serializers import (
    BookAcquisitionRequestSerializer,
    BookCopySerializer,
    BookSerializer,
    BorrowingLimitSerializer,
    BorrowRequestSerializer,
    LaptopSerializer,
    LibraryRoomSerializer,
    LoanSerializer,
    ShelfSerializer,
    profile_payload,
)
from librarian_app.service import (
    enabled_library_asset_types,
    issue_loan,
    library_asset_enabled,
    library_policy_payload,
    library_policy_settings,
    normalize_library_policy_updates,
    notify_student_book_acquisition_decision,
    notify_student_request_decision,
    return_loan,
    renew_loan,
    apply_overdue_fine,
    waive_fine,
    mark_lost,
)


def _validation_response(error):
    if hasattr(error, "message_dict"):
        return Response(error.message_dict, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "; ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)


class LibrarianUms(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        return Response({"title": "Librarian Portal", "section": "librarian"})


class LibrarianDashboard(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        policy = library_policy_settings()
        enabled_assets = enabled_library_asset_types(policy)
        pending_borrow_requests = BorrowRequest.objects.filter(
            status=BorrowRequest.STATUS_PENDING,
            asset_type__in=enabled_assets,
        ).count()
        pending_acquisition_requests = (
            BookAcquisitionRequest.objects.filter(status=BookAcquisitionRequest.STATUS_PENDING).count()
            if library_asset_enabled(BorrowRequest.ASSET_BOOK, policy)
            else 0
        )
        books_enabled = library_asset_enabled(BorrowRequest.ASSET_BOOK, policy)
        laptops_enabled = library_asset_enabled(BorrowRequest.ASSET_LAPTOP, policy)
        rooms_enabled = library_asset_enabled(BorrowRequest.ASSET_ROOM, policy)
        return Response(
            {
                "title": "Dashboard",
                "section": "librarian",
                "summary": {
                    "book_titles": Book.objects.filter(is_active=True).count() if books_enabled else 0,
                    "available_books": BookCopy.objects.filter(status=BookCopy.STATUS_AVAILABLE).count() if books_enabled else 0,
                    "available_laptops": Laptop.objects.filter(status=Laptop.STATUS_AVAILABLE).count() if laptops_enabled else 0,
                    "available_rooms": (
                        LibraryRoom.objects.filter(status=LibraryRoom.STATUS_AVAILABLE)
                        .exclude(reservation_requests__status=BorrowRequest.STATUS_PENDING)
                        .count()
                        if rooms_enabled
                        else 0
                    ),
                    "pending_requests": pending_borrow_requests + pending_acquisition_requests,
                    "pending_borrow_requests": pending_borrow_requests,
                    "pending_book_requests": pending_acquisition_requests,
                    "active_loans": Loan.objects.filter(status=Loan.STATUS_ACTIVE).count(),
                    "overdue_loans": sum(1 for loan in Loan.objects.filter(status=Loan.STATUS_ACTIVE) if loan.is_overdue),
                },
                "library_policy": library_policy_payload(policy=policy),
            }
        )


class LibrarianBooks(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        policy = library_policy_settings()
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK, policy):
            return Response({"books": [], "library_policy": library_policy_payload(policy=policy)})
        books = Book.objects.prefetch_related("copies")
        query = request.query_params.get("q", "").strip()
        if query:
            books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(isbn__icontains=query))
        return Response({"books": BookSerializer(books, many=True).data})

    def post(self, request):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response(
                {"detail": "Book borrowing is temporarily unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.save(created_by=request.user.profile)
        return Response({"book": BookSerializer(book).data}, status=status.HTTP_201_CREATED)


class LibrarianBookDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        book = Book.objects.filter(pk=pk).first()
        if not book:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"book": serializer.data})

    def delete(self, request, pk):
        book = Book.objects.filter(pk=pk).first()
        if not book:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        book.is_active = False
        book.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class LibrarianBookAcquisitionRequests(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response({"requests": []})
        acquisition_requests = BookAcquisitionRequest.objects.select_related(
            "student__user",
            "added_book",
            "reviewed_by__user",
        )
        request_status = request.query_params.get("status")
        if request_status:
            acquisition_requests = acquisition_requests.filter(status=request_status)
        return Response(
            {
                "requests": BookAcquisitionRequestSerializer(
                    acquisition_requests,
                    many=True,
                ).data
            }
        )


class LibrarianBookAcquisitionRequestDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response(
                {"detail": "Book borrowing is temporarily unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        acquisition_request = BookAcquisitionRequest.objects.filter(
            pk=pk,
            status=BookAcquisitionRequest.STATUS_PENDING,
        ).first()
        if not acquisition_request:
            return Response({"detail": "Pending book request not found."}, status=status.HTTP_404_NOT_FOUND)

        next_status = request.data.get("status")
        if next_status not in {
            BookAcquisitionRequest.STATUS_ADDED,
            BookAcquisitionRequest.STATUS_UNAVAILABLE,
        }:
            return Response(
                {"detail": "Set the request status to added or unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        added_book = None
        if next_status == BookAcquisitionRequest.STATUS_ADDED:
            added_book = Book.objects.filter(
                pk=request.data.get("book_id"),
                is_active=True,
            ).first()
            if not added_book:
                return Response(
                    {"detail": "Select the catalog book that was added."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        acquisition_request.status = next_status
        acquisition_request.added_book = added_book
        acquisition_request.reviewed_by = request.user.profile
        acquisition_request.review_note = str(request.data.get("review_note") or "").strip()
        if next_status == BookAcquisitionRequest.STATUS_UNAVAILABLE and not acquisition_request.review_note:
            acquisition_request.review_note = "This book is not available to add to the library."
        acquisition_request.save(
            update_fields=[
                "status",
                "added_book",
                "reviewed_by",
                "review_note",
                "updated_at",
            ]
        )
        notify_student_book_acquisition_decision(acquisition_request)
        return Response({"request": BookAcquisitionRequestSerializer(acquisition_request).data})


class LibrarianBookCopies(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request, book_id):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response({"copies": []})
        copies = BookCopy.objects.select_related("book", "shelf").filter(book_id=book_id)
        return Response({"copies": BookCopySerializer(copies, many=True).data})

    def post(self, request, book_id):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response(
                {"detail": "Book borrowing is temporarily unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Book.objects.filter(pk=book_id).exists():
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookCopySerializer(data={**request.data, "book": book_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"copy": serializer.data}, status=status.HTTP_201_CREATED)


class LibrarianBookCopyDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        copy = BookCopy.objects.filter(pk=pk).first()
        if not copy:
            return Response({"detail": "Book copy not found."}, status=status.HTTP_404_NOT_FOUND)
        requested_status = request.data.get("status")
        has_active_loan = copy.loans.filter(status=Loan.STATUS_ACTIVE).exists()
        if requested_status == BookCopy.STATUS_LOANED and not has_active_loan:
            return Response({"detail": "Loaned status is set through circulation."}, status=status.HTTP_400_BAD_REQUEST)
        if has_active_loan and requested_status and requested_status != BookCopy.STATUS_LOANED:
            return Response({"detail": "Return or close the active loan before changing status."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = BookCopySerializer(copy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"copy": serializer.data})


class LibrarianCopies(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        if not library_asset_enabled(BorrowRequest.ASSET_BOOK):
            return Response({"copies": []})
        copies = BookCopy.objects.select_related("book", "shelf")
        copy_status = request.query_params.get("status")
        if copy_status:
            copies = copies.filter(status=copy_status)
        return Response({"copies": BookCopySerializer(copies, many=True).data})


class LibrarianShelves(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        return Response({"shelves": ShelfSerializer(Shelf.objects.all(), many=True).data})

    def post(self, request):
        serializer = ShelfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"shelf": serializer.data}, status=status.HTTP_201_CREATED)


class LibrarianShelfDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        shelf = Shelf.objects.filter(pk=pk).first()
        if not shelf:
            return Response({"detail": "Shelf not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ShelfSerializer(shelf, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"shelf": serializer.data})


class LibrarianLaptops(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        policy = library_policy_settings()
        if not library_asset_enabled(BorrowRequest.ASSET_LAPTOP, policy):
            return Response({"laptops": [], "library_policy": library_policy_payload(policy=policy)})
        return Response({"laptops": LaptopSerializer(Laptop.objects.all(), many=True).data})

    def post(self, request):
        if not library_asset_enabled(BorrowRequest.ASSET_LAPTOP):
            return Response(
                {"detail": "Laptop borrowing is currently disabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = LaptopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"laptop": serializer.data}, status=status.HTTP_201_CREATED)


class LibrarianLaptopDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        laptop = Laptop.objects.filter(pk=pk).first()
        if not laptop:
            return Response({"detail": "Laptop not found."}, status=status.HTTP_404_NOT_FOUND)
        requested_status = request.data.get("status")
        has_active_loan = laptop.loans.filter(status=Loan.STATUS_ACTIVE).exists()
        if requested_status == Laptop.STATUS_LOANED and not has_active_loan:
            return Response({"detail": "Loaned status is set through circulation."}, status=status.HTTP_400_BAD_REQUEST)
        if has_active_loan and requested_status and requested_status != Laptop.STATUS_LOANED:
            return Response({"detail": "Return or close the active loan before changing status."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LaptopSerializer(laptop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"laptop": serializer.data})


class LibrarianRooms(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        policy = library_policy_settings()
        if not library_asset_enabled(BorrowRequest.ASSET_ROOM, policy):
            return Response({"rooms": [], "library_policy": library_policy_payload(policy=policy)})
        rooms = LibraryRoom.objects.prefetch_related("reservation_requests")
        return Response({"rooms": LibraryRoomSerializer(rooms, many=True).data})

    def post(self, request):
        if not library_asset_enabled(BorrowRequest.ASSET_ROOM):
            return Response(
                {"detail": "Discussion room booking is currently disabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = LibraryRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        return Response({"room": LibraryRoomSerializer(room).data}, status=status.HTTP_201_CREATED)


class LibrarianRoomDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        room = LibraryRoom.objects.filter(pk=pk).first()
        if not room:
            return Response({"detail": "Discussion room not found."}, status=status.HTTP_404_NOT_FOUND)

        requested_status = request.data.get("status")
        has_active_loan = room.loans.filter(status=Loan.STATUS_ACTIVE).exists()
        has_pending_reservation = room.reservation_requests.filter(
            status=BorrowRequest.STATUS_PENDING
        ).exists()
        if requested_status == LibraryRoom.STATUS_IN_USE and not has_active_loan:
            return Response(
                {"detail": "In-use status is set when the room key is allocated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if has_active_loan and requested_status and requested_status != LibraryRoom.STATUS_IN_USE:
            return Response(
                {"detail": "Record the room key return before changing its status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            has_pending_reservation
            and requested_status
            and requested_status != LibraryRoom.STATUS_AVAILABLE
        ):
            return Response(
                {"detail": "Reject the pending reservation before making this room unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LibraryRoomSerializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"room": serializer.data})


class LibrarianStudents(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        students = Profile.objects.select_related("user", "student_detail").filter(
            role=Profile.ROLE_STUDENT,
            is_active=True,
        )
        query = request.query_params.get("q", "").strip()
        if query:
            students = students.filter(
                Q(user__username__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(student_detail__student_id__icontains=query)
            )
        return Response({"students": [profile_payload(student) for student in students[:100]]})


class LibrarianRequests(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        policy = library_policy_settings()
        requests = BorrowRequest.objects.select_related("student__user", "book", "laptop", "room")
        requests = requests.filter(asset_type__in=enabled_library_asset_types(policy))
        request_status = request.query_params.get("status")
        if request_status:
            requests = requests.filter(status=request_status)
        return Response({
            "requests": BorrowRequestSerializer(requests, many=True).data,
            "library_policy": library_policy_payload(policy=policy),
        })


class LibrarianRequestDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def patch(self, request, pk):
        borrow_request = BorrowRequest.objects.filter(pk=pk, status=BorrowRequest.STATUS_PENDING).first()
        if not borrow_request:
            return Response({"detail": "Pending request not found."}, status=status.HTTP_404_NOT_FOUND)
        next_status = request.data.get("status")
        if next_status not in {BorrowRequest.STATUS_REJECTED, BorrowRequest.STATUS_CANCELLED}:
            return Response({"detail": "Requests are fulfilled by assigning a loan."}, status=status.HTTP_400_BAD_REQUEST)
        borrow_request.status = next_status
        borrow_request.reviewed_by = request.user.profile
        borrow_request.review_note = str(request.data.get("review_note") or "").strip()
        borrow_request.save(update_fields=["status", "reviewed_by", "review_note", "updated_at"])
        notify_student_request_decision(borrow_request)
        return Response({"request": BorrowRequestSerializer(borrow_request).data})


class LibrarianLoans(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        loans = Loan.objects.select_related(
            "student__user",
            "book_copy__book",
            "book_copy__shelf",
            "laptop",
            "room",
        )
        loan_status = request.query_params.get("status")
        if loan_status:
            loans = loans.filter(status=loan_status)
        return Response({"loans": LoanSerializer(loans, many=True).data})

    def post(self, request):
        due_at = parse_datetime(str(request.data.get("due_at") or ""))
        if not due_at:
            return Response({"detail": "Provide a valid due_at date and time."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            loan = issue_loan(
                student_id=request.data.get("student_id"),
                assigned_by=request.user.profile,
                due_at=due_at,
                book_copy_id=request.data.get("book_copy_id"),
                laptop_id=request.data.get("laptop_id"),
                room_id=request.data.get("room_id"),
                request_id=request.data.get("request_id"),
                notes=str(request.data.get("notes") or "").strip(),
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data}, status=status.HTTP_201_CREATED)


class LibrarianLoanReturn(APIView):
    permission_classes = [IsLibrarianRole]

    def post(self, request, pk):
        try:
            loan = return_loan(
                pk,
                returned_by=request.user.profile,
                condition_notes=str(request.data.get("condition_notes") or "").strip(),
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data})


class LibrarianLoanRenew(APIView):
    permission_classes = [IsLibrarianRole]

    def post(self, request, pk):
        try:
            loan = renew_loan(
                pk,
                due_at=parse_datetime(request.data.get("due_at")) if request.data.get("due_at") else None,
                requested_by=request.user.profile,
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data})

class LibrarianLoanApplyFine(APIView):
    permission_classes = [IsLibrarianRole]

    def post(self, request, pk):
        try:
            loan = apply_overdue_fine(pk, daily_rate=request.data.get("daily_rate"))
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data})

class LibrarianLoanWaiveFine(APIView):
    permission_classes = [IsLibrarianRole]

    def post(self, request, pk):
        try:
            loan = waive_fine(
                pk,
                waived_by=request.user.profile,
                note=request.data.get("note", ""),
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data})

class LibrarianLoanMarkLost(APIView):
    permission_classes = [IsLibrarianRole]

    def post(self, request, pk):
        try:
            loan = mark_lost(
                pk,
                lost_charge=float(request.data.get("lost_charge")),
                marked_by=request.user.profile,
                note=request.data.get("note", ""),
            )
        except ValidationError as error:
            return _validation_response(error)
        return Response({"loan": LoanSerializer(loan).data})


class LibrarianBorrowingLimits(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        limits = BorrowingLimit.objects.select_related("student__user").all()
        return Response({"limits": BorrowingLimitSerializer(limits, many=True).data})

    def post(self, request):
        serializer = BorrowingLimitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_id = serializer.validated_data.get("student_id")
        is_default = serializer.validated_data.get("is_default", False)

        if is_default and student_id:
            return Response(
                {"detail": "A default limit cannot be tied to a specific student."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_default:
            existing = BorrowingLimit.objects.filter(is_default=True).first()
            if existing:
                existing.max_borrow_at_a_time = serializer.validated_data["max_borrow_at_a_time"]
                existing.max_keep_at_a_time = serializer.validated_data["max_keep_at_a_time"]
                existing.save(update_fields=["max_borrow_at_a_time", "max_keep_at_a_time", "updated_at"])
                return Response({"limit": BorrowingLimitSerializer(existing).data})

        if student_id:
            existing = BorrowingLimit.objects.filter(student_id=student_id).first()
            if existing:
                existing.max_borrow_at_a_time = serializer.validated_data["max_borrow_at_a_time"]
                existing.max_keep_at_a_time = serializer.validated_data["max_keep_at_a_time"]
                existing.is_default = is_default
                existing.save(update_fields=["max_borrow_at_a_time", "max_keep_at_a_time", "is_default", "updated_at"])
                return Response({"limit": BorrowingLimitSerializer(existing).data})

        limit = serializer.save()
        return Response({"limit": BorrowingLimitSerializer(limit).data}, status=status.HTTP_201_CREATED)


class LibrarianBorrowingLimitDetail(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request, pk):
        limit = BorrowingLimit.objects.select_related("student__user").filter(pk=pk).first()
        if not limit:
            return Response({"detail": "Borrowing limit not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"limit": BorrowingLimitSerializer(limit).data})

    def patch(self, request, pk):
        limit = BorrowingLimit.objects.filter(pk=pk).first()
        if not limit:
            return Response({"detail": "Borrowing limit not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BorrowingLimitSerializer(limit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"limit": serializer.data})

    def delete(self, request, pk):
        limit = BorrowingLimit.objects.filter(pk=pk).first()
        if not limit:
            return Response({"detail": "Borrowing limit not found."}, status=status.HTTP_404_NOT_FOUND)
        if limit.is_default:
            return Response({"detail": "Cannot delete the default borrowing limit."}, status=status.HTTP_400_BAD_REQUEST)
        limit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LibrarianLibrarySettings(APIView):
    permission_classes = [IsLibrarianRole]

    def get(self, request):
        return Response(library_policy_payload())

    def patch(self, request):
        from admin_app.models import SystemSetting
        from admin_app.settings_registry import all_settings, setting_key, invalidate_settings_cache
        current = all_settings().get("librarian_library", {})
        try:
            updates = normalize_library_policy_updates(request.data)
        except ValidationError as error:
            return _validation_response(error)
        if not updates:
            return Response({"detail": "No settings provided."}, status=status.HTTP_400_BAD_REQUEST)
        merged = {**current, **updates}
        SystemSetting.objects.update_or_create(
            key=setting_key("librarian_library"),
            defaults={
                "value": merged,
                "description": "Library service policy managed by librarian.",
            },
        )
        invalidate_settings_cache()
        return Response(library_policy_payload(policy=library_policy_settings(merged)))

from rest_framework import serializers

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
    Fine,
    WaitlistEntry,
    InventoryAudit,
    InventoryAuditItem,
    AcquisitionBudget,
)

class FineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fine
        fields = "__all__"
        read_only_fields = ("issued_at",)

class WaitlistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = "__all__"
        read_only_fields = ("placed_at",)

class InventoryAuditItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryAuditItem
        fields = "__all__"
        read_only_fields = ("id",)

class InventoryAuditSerializer(serializers.ModelSerializer):
    items = InventoryAuditItemSerializer(many=True, read_only=True)
    class Meta:
        model = InventoryAudit
        fields = "__all__"
        read_only_fields = ("audit_date",)

class AcquisitionBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcquisitionBudget
        fields = "__all__"
        read_only_fields = ("spent_amount",)



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


class ShelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class BookCopySerializer(serializers.ModelSerializer):
    shelf_detail = ShelfSerializer(source="shelf", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = BookCopy
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class BookSerializer(serializers.ModelSerializer):
    total_copies = serializers.SerializerMethodField()
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = "__all__"
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_total_copies(self, book):
        return book.copies.count()

    def get_available_copies(self, book):
        return book.copies.filter(status=BookCopy.STATUS_AVAILABLE).count()


class LaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laptop
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class LibraryRoomSerializer(serializers.ModelSerializer):
    availability_status = serializers.SerializerMethodField()

    class Meta:
        model = LibraryRoom
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def get_availability_status(self, room):
        if room.status != LibraryRoom.STATUS_AVAILABLE:
            return room.status
        if room.reservation_requests.filter(status=BorrowRequest.STATUS_PENDING).exists():
            return "reserved"
        return LibraryRoom.STATUS_AVAILABLE


class StudentLibraryRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryRoom
        fields = (
            "id",
            "code",
            "name",
            "location",
            "capacity",
            "facilities",
            "default_duration_minutes",
        )


def profile_payload(profile):
    user = profile.user
    return {
        "id": profile.id,
        "name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "username": user.username,
        "student_id": profile.student_id,
        "email": user.email,
    }


class BorrowRequestSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField()
    book_detail = BookSerializer(source="book", read_only=True)
    laptop_detail = LaptopSerializer(source="laptop", read_only=True)
    room_detail = LibraryRoomSerializer(source="room", read_only=True)

    class Meta:
        model = BorrowRequest
        fields = "__all__"
        read_only_fields = ("student", "reviewed_by", "status", "review_note", "created_at", "updated_at")

    def get_student_detail(self, request):
        return profile_payload(request.student)


class BookAcquisitionRequestSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField()
    added_book_detail = BookSerializer(source="added_book", read_only=True)

    class Meta:
        model = BookAcquisitionRequest
        fields = "__all__"
        read_only_fields = (
            "student",
            "status",
            "added_book",
            "reviewed_by",
            "review_note",
            "created_at",
            "updated_at",
        )

    def get_student_detail(self, request):
        return profile_payload(request.student)


class LoanSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField()
    book_copy_detail = BookCopySerializer(source="book_copy", read_only=True)
    laptop_detail = LaptopSerializer(source="laptop", read_only=True)
    room_detail = LibraryRoomSerializer(source="room", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Loan
        fields = "__all__"
        read_only_fields = (
            "assigned_by",
            "borrowed_at",
            "returned_at",
            "status",
            "return_condition_notes",
            "created_at",
            "updated_at",
        )

    def get_student_detail(self, loan):
        return profile_payload(loan.student)


class BorrowingLimitSerializer(serializers.ModelSerializer):
    student_detail = serializers.SerializerMethodField()

    class Meta:
        model = BorrowingLimit
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def get_student_detail(self, obj):
        if obj.student_id:
            return profile_payload(obj.student)
        return None

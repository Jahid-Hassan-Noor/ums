from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Librarian(models.Model):
    profile = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="librarian_detail",
    )
    librarian_id = models.CharField(max_length=50, blank=True, db_index=True)
    designation = models.CharField(max_length=255, blank=True)
    school = models.ForeignKey("admin_app.School", on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey("admin_app.Center", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("admin_app.Department", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("admin_app.Unit", on_delete=models.SET_NULL, null=True, blank=True)
    office_location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.profile.user)

    @property
    def staff_id(self):
        return self.librarian_id

    @staff_id.setter
    def staff_id(self, value):
        self.librarian_id = value


class Shelf(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Book(models.Model):
    isbn = models.CharField(max_length=30, blank=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_library_books",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title", "author")

    def __str__(self):
        return self.title


class BookAcquisitionRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ADDED = "added"
    STATUS_UNAVAILABLE = "unavailable"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ADDED, "Added"),
        (STATUS_UNAVAILABLE, "Unavailable"),
    ]

    student = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="library_book_acquisition_requests",
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    added_book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acquisition_requests",
    )
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_library_book_acquisition_requests",
    )
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if self.student_id and self.student.role != "student":
            raise ValidationError("Book acquisition requests can only belong to students.")
        if self.status == self.STATUS_ADDED and not self.added_book_id:
            raise ValidationError("Select the catalog book that was added.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookCopy(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_LOANED = "loaned"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_LOST = "lost"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_LOANED, "Loaned"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_LOST, "Lost"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    accession_number = models.CharField(max_length=80, unique=True)
    shelf = models.ForeignKey(Shelf, on_delete=models.SET_NULL, null=True, blank=True, related_name="book_copies")
    shelf_position = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    condition_notes = models.TextField(blank=True)
    acquired_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("book__title", "accession_number")

    def __str__(self):
        return f"{self.book.title} ({self.accession_number})"


class Laptop(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_LOANED = "loaned"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_RETIRED = "retired"
    STATUS_LOST = "lost"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_LOANED, "Loaned"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_RETIRED, "Retired"),
        (STATUS_LOST, "Lost"),
    ]

    asset_tag = models.CharField(max_length=80, unique=True)
    serial_number = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=120)
    specifications = models.TextField(blank=True)
    storage_location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    condition_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("asset_tag",)

    def __str__(self):
        return f"{self.asset_tag} - {self.brand} {self.model}"


class LibraryRoom(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_IN_USE = "in_use"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_IN_USE, "In use"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.PositiveSmallIntegerField(default=1)
    facilities = models.TextField(blank=True)
    key_reference = models.CharField(max_length=100, blank=True)
    default_duration_minutes = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(15)],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class BorrowRequest(models.Model):
    ASSET_BOOK = "book"
    ASSET_LAPTOP = "laptop"
    ASSET_ROOM = "room"
    ASSET_CHOICES = [
        (ASSET_BOOK, "Book"),
        (ASSET_LAPTOP, "Laptop"),
        (ASSET_ROOM, "Discussion room"),
    ]
    STATUS_PENDING = "pending"
    STATUS_FULFILLED = "fulfilled"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_FULFILLED, "Fulfilled"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="library_borrow_requests")
    asset_type = models.CharField(max_length=20, choices=ASSET_CHOICES)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True, related_name="borrow_requests")
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE, null=True, blank=True, related_name="borrow_requests")
    room = models.ForeignKey(
        LibraryRoom,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reservation_requests",
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        "auth_app.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_library_requests",
    )
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("room",),
                condition=Q(asset_type="room", status="pending"),
                name="unique_pending_library_room_reservation",
            ),
        ]

    def clean(self):
        if self.student_id and self.student.role != "student":
            raise ValidationError("Borrowing requests can only belong to students.")
        if self.asset_type == self.ASSET_BOOK and (not self.book_id or self.laptop_id or self.room_id):
            raise ValidationError("Book requests must select one book title.")
        if self.asset_type == self.ASSET_LAPTOP and (not self.laptop_id or self.book_id or self.room_id):
            raise ValidationError("Laptop requests must select one laptop.")
        if self.asset_type == self.ASSET_ROOM and (not self.room_id or self.book_id or self.laptop_id):
            raise ValidationError("Room reservations must select one discussion room.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Loan(models.Model):
    # Renewal policy fields
    renewal_count = models.PositiveSmallIntegerField(default=0)
    max_renewals = models.PositiveSmallIntegerField(default=2)
    # Fine tracking fields
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    # Lost item flag and charge
    is_lost = models.BooleanField(default=False)
    lost_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    STATUS_ACTIVE = "active"
    STATUS_RETURNED = "returned"
    STATUS_LOST = "lost"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_RETURNED, "Returned"),
        (STATUS_LOST, "Lost"),
    ]

    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name="library_loans")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, null=True, blank=True, related_name="loans")
    laptop = models.ForeignKey(Laptop, on_delete=models.PROTECT, null=True, blank=True, related_name="loans")
    room = models.ForeignKey(
        LibraryRoom,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="loans",
    )
    request = models.OneToOneField(BorrowRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="loan")
    assigned_by = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, related_name="assigned_library_loans")
    borrowed_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes = models.TextField(blank=True)
    return_condition_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-borrowed_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("book_copy",),
                condition=Q(status="active"),
                name="unique_active_book_copy_loan",
            ),
            models.UniqueConstraint(
                fields=("laptop",),
                condition=Q(status="active"),
                name="unique_active_laptop_loan",
            ),
            models.UniqueConstraint(
                fields=("room",),
                condition=Q(status="active"),
                name="unique_active_library_room_loan",
            ),
        ]

    def clean(self):
        if self.student_id and self.student.role != "student":
            raise ValidationError("Loans can only be assigned to students.")
        if sum(bool(asset_id) for asset_id in (self.book_copy_id, self.laptop_id, self.room_id)) != 1:
            raise ValidationError("Assign exactly one book copy, laptop, or discussion room.")
        if self.due_at and self.borrowed_at and self.due_at <= self.borrowed_at:
            raise ValidationError("Due date must be after the borrowing date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return self.status == self.STATUS_ACTIVE and self.due_at < timezone.now()

class Fine(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='fines')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    issued_at = models.DateTimeField(auto_now_add=True)
    waived = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ('-issued_at',)

    def __str__(self):
        status = 'Waived' if self.waived else 'Active'
        return f"Fine {self.amount} for Loan {self.loan.id} ({status})"

class WaitlistEntry(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='waitlist')
    student = models.ForeignKey("auth_app.Profile", on_delete=models.CASCADE, related_name='waitlist_entries')
    placed_at = models.DateTimeField(auto_now_add=True)
    priority = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('book', 'student')
        ordering = ('priority', 'placed_at')

    def __str__(self):
        return f"{self.student.user.username} waitlisted for {self.book.title}"

class InventoryAudit(models.Model):
    auditor = models.ForeignKey("auth_app.Profile", on_delete=models.SET_NULL, null=True, related_name='audits')
    audit_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

class InventoryAuditItem(models.Model):
    audit = models.ForeignKey(InventoryAudit, on_delete=models.CASCADE, related_name='items')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.SET_NULL, null=True, blank=True)
    laptop = models.ForeignKey(Laptop, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(LibraryRoom, on_delete=models.SET_NULL, null=True, blank=True)
    condition = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Audit item for {self.audit.id}"

class AcquisitionBudget(models.Model):
    fiscal_year = models.CharField(max_length=9)  # e.g., "2025-2026"
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('fiscal_year',)

    def __str__(self):
        return f"Budget {self.fiscal_year}: {self.allocated_amount}"


class BorrowingLimit(models.Model):
    """Per-student or default borrowing limits for books.

    Laptops and rooms are always limited to 1 at a time (enforced in service layer).
    """
    student = models.OneToOneField(
        "auth_app.Profile",
        on_delete=models.CASCADE,
        related_name="borrowing_limit",
        null=True,
        blank=True,
    )
    max_borrow_at_a_time = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Maximum books a student can borrow simultaneously.",
    )
    max_keep_at_a_time = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Maximum books a student can hold at any time (active loans).",
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=Q(is_default=True),
                name="unique_default_borrowing_limit",
            ),
        ]

    def clean(self):
        if self.max_borrow_at_a_time > self.max_keep_at_a_time:
            raise ValidationError(
                "Max borrow at a time cannot exceed max keep at a time."
            )
        if self.is_default and self.student_id:
            raise ValidationError("The default limit should not be tied to a specific student.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        label = f"Student #{self.student_id}" if self.student_id else "Default"
        return f"BorrowingLimit({label}: borrow={self.max_borrow_at_a_time}, keep={self.max_keep_at_a_time})"

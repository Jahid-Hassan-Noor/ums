from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accountant_app.models import FinanceGatewayConfig, Fine as FinanceFine
from admin_app.models import Center, Profile, Unit
from auth_app.serializers import RegisterSerializer
from librarian_app.models import (
    Book,
    BookAcquisitionRequest,
    BookCopy,
    BorrowRequest,
    Laptop,
    Librarian,
    LibraryRoom,
    Loan,
    Shelf,
)


User = get_user_model()


class LibrarianWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.center = Center.objects.create(code="COR", name="Centre of Reference (Library)")
        self.unit = Unit.objects.create(
            code="COR-ADMIN",
            name="Library Administrative Unit",
            center=self.center,
        )
        self.librarian_user = User.objects.create_user(username="librarian", password="pass")
        self.librarian = self.librarian_user.profile
        self.librarian.role = Profile.ROLE_LIBRARIAN
        self.librarian.center = self.center
        self.librarian.unit = self.unit
        self.librarian.save()
        self.student_user = User.objects.create_user(username="student", password="pass")
        self.student = self.student_user.profile
        self.admin_user = User.objects.create_superuser(username="admin", email="admin@example.com", password="pass")

    def test_librarian_account_is_created_under_cor(self):
        serializer = RegisterSerializer(
            data={
                "username": "new_librarian",
                "email": "new-librarian@example.com",
                "first_name": "New",
                "last_name": "Librarian",
                "password": "StrongPass123!",
                "role": Profile.ROLE_LIBRARIAN,
                "ums_id": "LIB-100",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.profile.center, self.center)
        self.assertEqual(user.profile.unit, self.unit)
        self.assertTrue(Librarian.objects.filter(profile=user.profile, librarian_id="LIB-100").exists())

    def test_admin_can_create_and_manage_librarian_account(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/admin/create-account/librarian",
            {
                "username": "managed_librarian",
                "email": "managed@example.com",
                "first_name": "Managed",
                "last_name": "Librarian",
                "password": "StrongPass123!",
                "ums_id": "LIB-200",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        profile = Profile.objects.get(user__username="managed_librarian")
        self.assertEqual(profile.center, self.center)
        self.assertEqual(profile.unit, self.unit)

        response = self.client.patch(
            f"/admin/manage/librarians?profile_id={profile.id}",
            {"designation": "Senior Librarian", "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        profile.refresh_from_db()
        self.assertEqual(profile.librarian_detail.designation, "Senior Librarian")
        self.assertFalse(profile.is_active)

    def test_student_request_can_be_fulfilled_and_returned(self):
        shelf = Shelf.objects.create(code="A-01", name="Main Shelf", location="Level 1")
        book = Book.objects.create(title="Library Systems", author="AIU")
        copy = BookCopy.objects.create(book=book, accession_number="BK-001", shelf=shelf)

        self.client.force_authenticate(user=self.student_user)
        request_response = self.client.post(
            "/student/library",
            {"asset_type": "book", "book_id": book.id},
            format="json",
        )
        self.assertEqual(request_response.status_code, 201, request_response.json())
        request_id = request_response.json()["request"]["id"]
        self.assertTrue(
            self.librarian.notifications.filter(
                data__event_type="library.borrow_requested",
                data__borrow_request_id=request_id,
            ).exists()
        )

        self.client.force_authenticate(user=self.librarian_user)
        loan_response = self.client.post(
            "/librarian/loans",
            {
                "student_id": self.student.id,
                "book_copy_id": copy.id,
                "request_id": request_id,
                "due_at": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(loan_response.status_code, 201, loan_response.json())
        copy.refresh_from_db()
        self.assertEqual(copy.status, BookCopy.STATUS_LOANED)
        self.assertEqual(BorrowRequest.objects.get(pk=request_id).status, BorrowRequest.STATUS_FULFILLED)
        self.assertTrue(
            self.student.notifications.filter(
                data__event_type="library.loan_issued",
                data__borrow_request_id=request_id,
            ).exists()
        )

        loan_id = loan_response.json()["loan"]["id"]
        return_response = self.client.post(
            f"/librarian/loans/{loan_id}/return",
            {"condition_notes": "Returned in good condition."},
            format="json",
        )
        self.assertEqual(return_response.status_code, 200, return_response.json())
        copy.refresh_from_db()
        self.assertEqual(copy.status, BookCopy.STATUS_AVAILABLE)
        self.assertEqual(Loan.objects.get(pk=loan_id).status, Loan.STATUS_RETURNED)
        self.assertTrue(
            self.student.notifications.filter(
                data__event_type="library.loan_returned",
                data__loan_id=loan_id,
            ).exists()
        )

    def test_library_overdue_fine_appears_on_student_finance_surface_and_can_be_paid(self):
        shelf = Shelf.objects.create(code="F-01", name="Fine Shelf", location="Level 1")
        book = Book.objects.create(title="Overdue Finance", author="AIU")
        copy = BookCopy.objects.create(book=book, accession_number="BK-FINE-001", shelf=shelf)
        loan = Loan.objects.create(
            student=self.student,
            book_copy=copy,
            assigned_by=self.librarian,
            borrowed_at=timezone.now() - timezone.timedelta(days=4),
            due_at=timezone.now() - timezone.timedelta(days=3, hours=1),
        )
        FinanceGatewayConfig.objects.update_or_create(
            pk=1,
            defaults={
                "provider": "toyyibpay",
                "mode": "sandbox",
                "merchant_name": "AIU Sandbox",
                "api_base_url": "https://payments.example.test/create",
                "checkout_base_url": "https://payments.example.test/pay",
                "category_code": "CAT123",
                "secret_key": "my-secret-key",
                "callback_token": "callback-123",
                "is_active": True,
            },
        )

        self.client.force_authenticate(user=self.librarian_user)
        fine_response = self.client.post(
            f"/librarian/loans/{loan.id}/apply-fine",
            {"daily_rate": "2.50"},
            format="json",
        )
        self.assertEqual(fine_response.status_code, 200, fine_response.json())
        finance_fine = FinanceFine.objects.get(
            student=self.student,
            description__contains=f"Library loan #{loan.id}",
        )
        self.assertEqual(finance_fine.reason, "Library overdue fine for Overdue Finance")
        self.assertEqual(finance_fine.amount, Decimal("7.50"))
        self.assertEqual(finance_fine.status, FinanceFine.STATUS_PENDING)
        self.assertTrue(
            self.student.notifications.filter(
                data__event_type="fine_issued",
                data__fine_id=finance_fine.id,
            ).exists()
        )

        self.client.force_authenticate(user=self.student_user)
        list_response = self.client.get("/finance/my-fines")
        self.assertEqual(list_response.status_code, 200, list_response.json())
        listed_fines = list_response.json()["fines"]
        self.assertEqual(len(listed_fines), 1)
        self.assertEqual(listed_fines[0]["id"], finance_fine.id)
        self.assertEqual(listed_fines[0]["amount"], "7.50")

        with patch(
            "accountant_app.service._create_gateway_checkout",
            return_value={
                "raw": [{"BillCode": "BILL-LIB-FINE-1"}],
                "gateway_reference": "BILL-LIB-FINE-1",
                "checkout_url": "https://payments.example.test/pay/BILL-LIB-FINE-1",
            },
        ):
            pay_response = self.client.post(
                f"/finance/my-fines/{finance_fine.id}/pay",
                {},
                format="json",
            )

        self.assertEqual(pay_response.status_code, 200, pay_response.json())
        self.assertEqual(
            pay_response.json()["checkout_url"],
            "https://payments.example.test/pay/BILL-LIB-FINE-1",
        )
        finance_fine.refresh_from_db()
        self.assertEqual(finance_fine.gateway_bill_code, "BILL-LIB-FINE-1")

    def test_library_lost_item_charge_appears_on_student_finance_surface(self):
        shelf = Shelf.objects.create(code="L-01", name="Lost Shelf", location="Level 1")
        book = Book.objects.create(title="Lost Finance", author="AIU")
        copy = BookCopy.objects.create(book=book, accession_number="BK-LOST-001", shelf=shelf)
        loan = Loan.objects.create(
            student=self.student,
            book_copy=copy,
            assigned_by=self.librarian,
            due_at=timezone.now() + timezone.timedelta(days=7),
        )

        self.client.force_authenticate(user=self.librarian_user)
        lost_response = self.client.post(
            f"/librarian/loans/{loan.id}/mark-lost",
            {"lost_charge": "125.00", "note": "Replacement copy required."},
            format="json",
        )
        self.assertEqual(lost_response.status_code, 200, lost_response.json())

        finance_fine = FinanceFine.objects.get(
            student=self.student,
            description__contains=f"Library loan #{loan.id}",
        )
        self.assertEqual(finance_fine.reason, "Library lost item charge for Lost Finance")
        self.assertEqual(finance_fine.amount, Decimal("125.00"))
        self.client.force_authenticate(user=self.student_user)
        list_response = self.client.get("/finance/my-fines")
        self.assertEqual(list_response.status_code, 200, list_response.json())
        self.assertEqual(list_response.json()["fines"][0]["id"], finance_fine.id)
        self.assertEqual(list_response.json()["fines"][0]["amount"], "125.00")

    def test_librarian_routes_reject_student_role(self):
        self.client.force_authenticate(user=self.student_user)
        self.assertEqual(self.client.get("/librarian/dashboard").status_code, 403)

    def test_students_can_request_available_laptops(self):
        laptop = Laptop.objects.create(asset_tag="LT-001", brand="Dell", model="Latitude")
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            "/student/library",
            {"asset_type": "laptop", "laptop_id": laptop.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())

    def test_room_reservation_key_allocation_and_return_workflow(self):
        self.client.force_authenticate(user=self.librarian_user)
        room_response = self.client.post(
            "/librarian/rooms",
            {
                "code": "DR-01",
                "name": "Discussion Room 1",
                "location": "Library Level 2",
                "capacity": 6,
                "facilities": "Display and whiteboard",
                "key_reference": "KEY-DR-01",
                "default_duration_minutes": 90,
            },
            format="json",
        )
        self.assertEqual(room_response.status_code, 201, room_response.json())
        room = LibraryRoom.objects.get(pk=room_response.json()["room"]["id"])

        self.client.force_authenticate(user=self.student_user)
        availability_response = self.client.get("/student/library", {"section": "rooms"})
        self.assertEqual(availability_response.status_code, 200, availability_response.json())
        self.assertEqual(
            [available_room["id"] for available_room in availability_response.json()["rooms"]],
            [room.id],
        )

        reservation_response = self.client.post(
            "/student/library",
            {"asset_type": "room", "room_id": room.id, "notes": "Group project meeting."},
            format="json",
        )
        self.assertEqual(reservation_response.status_code, 201, reservation_response.json())
        reservation_id = reservation_response.json()["request"]["id"]

        hidden_response = self.client.get("/student/library", {"section": "rooms"})
        self.assertEqual(hidden_response.status_code, 200, hidden_response.json())
        self.assertEqual(hidden_response.json()["rooms"], [])

        second_student_user = User.objects.create_user(username="second_student", password="pass")
        self.client.force_authenticate(user=second_student_user)
        unavailable_response = self.client.post(
            "/student/library",
            {"asset_type": "room", "room_id": room.id},
            format="json",
        )
        self.assertEqual(unavailable_response.status_code, 400, unavailable_response.json())

        self.client.force_authenticate(user=self.librarian_user)
        allocation_response = self.client.post(
            "/librarian/loans",
            {
                "student_id": self.student.id,
                "room_id": room.id,
                "request_id": reservation_id,
                "due_at": (timezone.now() + timezone.timedelta(minutes=90)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(allocation_response.status_code, 201, allocation_response.json())
        allocation_id = allocation_response.json()["loan"]["id"]
        room.refresh_from_db()
        self.assertEqual(room.status, LibraryRoom.STATUS_IN_USE)
        self.assertEqual(
            BorrowRequest.objects.get(pk=reservation_id).status,
            BorrowRequest.STATUS_FULFILLED,
        )
        self.assertEqual(allocation_response.json()["loan"]["room_detail"]["key_reference"], "KEY-DR-01")

        return_response = self.client.post(
            f"/librarian/loans/{allocation_id}/return",
            {},
            format="json",
        )
        self.assertEqual(return_response.status_code, 200, return_response.json())
        room.refresh_from_db()
        self.assertEqual(room.status, LibraryRoom.STATUS_AVAILABLE)
        self.assertEqual(Loan.objects.get(pk=allocation_id).status, Loan.STATUS_RETURNED)

        self.client.force_authenticate(user=self.student_user)
        available_again_response = self.client.get("/student/library", {"section": "rooms"})
        self.assertEqual(available_again_response.status_code, 200, available_again_response.json())
        self.assertEqual(
            [available_room["id"] for available_room in available_again_response.json()["rooms"]],
            [room.id],
        )

    def test_student_can_cancel_pending_room_reservation(self):
        room = LibraryRoom.objects.create(
            code="DR-02",
            name="Discussion Room 2",
            location="Library Level 2",
            capacity=4,
            facilities="Whiteboard",
        )
        self.client.force_authenticate(user=self.student_user)
        reservation_response = self.client.post(
            "/student/library",
            {"asset_type": "room", "room_id": room.id, "notes": "Study group."},
            format="json",
        )
        self.assertEqual(reservation_response.status_code, 201, reservation_response.json())
        reservation_id = reservation_response.json()["request"]["id"]

        cancel_response = self.client.post(
            f"/student/library/room-reservations/{reservation_id}/cancel",
            {},
            format="json",
        )

        self.assertEqual(cancel_response.status_code, 200, cancel_response.json())
        reservation = BorrowRequest.objects.get(pk=reservation_id)
        self.assertEqual(reservation.status, BorrowRequest.STATUS_CANCELLED)
        self.assertTrue(
            self.librarian.notifications.filter(
                data__event_type="library.room_reservation_cancelled",
                data__borrow_request_id=reservation_id,
            ).exists()
        )

        availability_response = self.client.get("/student/library", {"section": "rooms"})
        self.assertEqual(availability_response.status_code, 200, availability_response.json())
        self.assertEqual(
            [available_room["id"] for available_room in availability_response.json()["rooms"]],
            [room.id],
        )

        second_student_user = User.objects.create_user(username="room_cancel_second_student", password="pass")
        self.client.force_authenticate(user=second_student_user)
        reserve_again_response = self.client.post(
            "/student/library",
            {"asset_type": "room", "room_id": room.id},
            format="json",
        )
        self.assertEqual(reserve_again_response.status_code, 201, reserve_again_response.json())

    def test_student_book_catalog_requires_a_title_or_author_search(self):
        Book.objects.create(title="Distributed Systems", author="Andrew Tanenbaum")
        Book.objects.create(title="Computer Networks", author="James Kurose")
        self.client.force_authenticate(user=self.student_user)

        blank_response = self.client.get("/student/library", {"section": "books"})
        self.assertEqual(blank_response.status_code, 200, blank_response.json())
        self.assertEqual(blank_response.json()["books"], [])

        title_response = self.client.get(
            "/student/library",
            {"section": "books", "q": "distributed"},
        )
        self.assertEqual(title_response.status_code, 200, title_response.json())
        self.assertEqual([book["title"] for book in title_response.json()["books"]], ["Distributed Systems"])

        author_response = self.client.get(
            "/student/library",
            {"section": "books", "q": "kurose"},
        )
        self.assertEqual(author_response.status_code, 200, author_response.json())
        self.assertEqual([book["title"] for book in author_response.json()["books"]], ["Computer Networks"])

    def test_student_only_sees_available_laptops_without_active_loans(self):
        visible = Laptop.objects.create(asset_tag="LT-AVAILABLE", brand="Dell", model="Latitude")
        Laptop.objects.create(
            asset_tag="LT-MAINTENANCE",
            brand="Lenovo",
            model="ThinkPad",
            status=Laptop.STATUS_MAINTENANCE,
        )
        actively_loaned = Laptop.objects.create(asset_tag="LT-ACTIVE-LOAN", brand="HP", model="EliteBook")
        Loan.objects.create(
            student=self.student,
            laptop=actively_loaned,
            assigned_by=self.librarian,
            due_at=timezone.now() + timezone.timedelta(days=7),
        )

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/student/library", {"section": "laptops"})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual([laptop["id"] for laptop in response.json()["laptops"]], [visible.id])

    def test_librarian_can_resolve_student_book_acquisition_requests(self):
        self.client.force_authenticate(user=self.student_user)
        request_response = self.client.post(
            "/student/library/book-requests",
            {
                "title": "Designing Data-Intensive Applications",
                "author": "Martin Kleppmann",
                "notes": "Needed for the distributed systems course.",
            },
            format="json",
        )
        self.assertEqual(request_response.status_code, 201, request_response.json())
        acquisition_request_id = request_response.json()["request"]["id"]
        self.assertTrue(
            self.librarian.notifications.filter(
                data__event_type="library.book_acquisition_requested",
                data__book_acquisition_request_id=acquisition_request_id,
            ).exists()
        )

        added_book = Book.objects.create(
            title="Designing Data-Intensive Applications",
            author="Martin Kleppmann",
        )
        self.client.force_authenticate(user=self.librarian_user)
        added_response = self.client.patch(
            f"/librarian/book-requests/{acquisition_request_id}",
            {
                "status": "added",
                "book_id": added_book.id,
                "review_note": "The title has been added to the catalog.",
            },
            format="json",
        )
        self.assertEqual(added_response.status_code, 200, added_response.json())
        acquisition_request = BookAcquisitionRequest.objects.get(pk=acquisition_request_id)
        self.assertEqual(acquisition_request.status, BookAcquisitionRequest.STATUS_ADDED)
        self.assertEqual(acquisition_request.added_book, added_book)
        self.assertTrue(
            self.student.notifications.filter(
                data__event_type="library.book_acquisition_decided",
                data__book_acquisition_request_id=acquisition_request_id,
            ).exists()
        )

        self.client.force_authenticate(user=self.student_user)
        unavailable_request = self.client.post(
            "/student/library/book-requests",
            {"title": "Out of Print Reference", "author": "Unknown Author"},
            format="json",
        )
        self.assertEqual(unavailable_request.status_code, 201, unavailable_request.json())

        self.client.force_authenticate(user=self.librarian_user)
        unavailable_response = self.client.patch(
            f"/librarian/book-requests/{unavailable_request.json()['request']['id']}",
            {"status": "unavailable"},
            format="json",
        )
        self.assertEqual(unavailable_response.status_code, 200, unavailable_response.json())
        self.assertEqual(
            unavailable_response.json()["request"]["review_note"],
            "This book is not available to add to the library.",
        )

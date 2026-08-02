from django.urls import path

from librarian_app.views import *


urlpatterns = [
    path("", LibrarianUms.as_view()),
    path("dashboard", LibrarianDashboard.as_view()),
    path("books", LibrarianBooks.as_view()),
    path("books/<int:pk>", LibrarianBookDetail.as_view()),
    path("book-requests", LibrarianBookAcquisitionRequests.as_view()),
    path("book-requests/<int:pk>", LibrarianBookAcquisitionRequestDetail.as_view()),
    path("books/<int:book_id>/copies", LibrarianBookCopies.as_view()),
    path("copies", LibrarianCopies.as_view()),
    path("copies/<int:pk>", LibrarianBookCopyDetail.as_view()),
    path("shelves", LibrarianShelves.as_view()),
    path("shelves/<int:pk>", LibrarianShelfDetail.as_view()),
    path("laptops", LibrarianLaptops.as_view()),
    path("laptops/<int:pk>", LibrarianLaptopDetail.as_view()),
    path("rooms", LibrarianRooms.as_view()),
    path("rooms/<int:pk>", LibrarianRoomDetail.as_view()),
    path("students", LibrarianStudents.as_view()),
    path("requests", LibrarianRequests.as_view()),
    path("requests/<int:pk>", LibrarianRequestDetail.as_view()),
    path("loans", LibrarianLoans.as_view()),
    path("loans/<int:pk>/return", LibrarianLoanReturn.as_view()),
    path("loans/<int:pk>/renew", LibrarianLoanRenew.as_view()),
    path("loans/<int:pk>/apply-fine", LibrarianLoanApplyFine.as_view()),
    path("loans/<int:pk>/mark-lost", LibrarianLoanMarkLost.as_view()),
    path("borrowing-limits", LibrarianBorrowingLimits.as_view()),
    path("borrowing-limits/<int:pk>", LibrarianBorrowingLimitDetail.as_view()),
    path("library-settings", LibrarianLibrarySettings.as_view()),
]

from django.contrib import admin

from librarian_app.models import Book, BookCopy, BorrowRequest, Laptop, Librarian, LibraryRoom, Loan, Shelf


admin.site.register(Book)
admin.site.register(BookCopy)
admin.site.register(BorrowRequest)
admin.site.register(Laptop)
admin.site.register(Librarian)
admin.site.register(LibraryRoom)
admin.site.register(Loan)
admin.site.register(Shelf)

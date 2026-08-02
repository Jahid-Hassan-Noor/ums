from student_app.views.student_attendance_qr import StudentAttendanceQR


class StudentAttendanceCode(StudentAttendanceQR):
    """Code submissions use the same validation path as scanned QR tokens."""

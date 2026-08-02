from django.contrib import admin
from .models import (
    AttendanceCodeSubmission,
    AttendanceRecord,
    CourseRegistration,
    EmergencyContact,
    Enrollment,
    Exam,
    ExamSlip,
    LeaveApproval,
    LeaveRequest,
    RegistrationPeriod,
    Student,
    StudentAffairsContact,
    TranscriptRecord,
    WardenSchedule,
)

admin.site.register(AttendanceCodeSubmission)
admin.site.register(AttendanceRecord)
admin.site.register(CourseRegistration)
admin.site.register(EmergencyContact)
admin.site.register(Enrollment)
admin.site.register(Exam)
admin.site.register(ExamSlip)
admin.site.register(LeaveApproval)
admin.site.register(LeaveRequest)
admin.site.register(RegistrationPeriod)
admin.site.register(Student)
admin.site.register(StudentAffairsContact)
admin.site.register(TranscriptRecord)
admin.site.register(WardenSchedule)

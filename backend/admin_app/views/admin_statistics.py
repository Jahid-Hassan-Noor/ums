from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auth_app.permissions import IsAdminRole
from admin_app.models import (
    School,
    Center,
    Department,
    Program,
    Profile,
    Building,
    Venue,
    Semester,
    Hostel,
    HostelRoom,
    Course,
    CourseOffering,
    ClassMeeting,
    AuditLog,
)
from applicant_app.models import AdmissionApplication
from librarian_app.models import Loan
from notifications_package.models import Notification
from student_app.models import CourseRegistration
from teacher_app.models import Assignment, AttendanceSession
from technician_app.models import HelpdeskTicket


def _insight_level(value, *, watch=1, risk=None):
    if risk is not None and value >= risk:
        return "risk"
    if value >= watch:
        return "watch"
    return "healthy"


def _admin_insights():
    now = timezone.now()
    open_tickets = HelpdeskTicket.objects.exclude(status=HelpdeskTicket.STATUS_SOLVED)
    aged_tickets = open_tickets.filter(created_at__lte=now - timedelta(days=3)).count()
    pending_registrations = CourseRegistration.objects.filter(
        status=CourseRegistration.STATUS_PENDING
    ).count()
    overdue_assignments = Assignment.objects.filter(
        status=Assignment.STATUS_PUBLISHED,
        due_date__lt=now,
    ).count()
    open_attendance_sessions = AttendanceSession.objects.filter(
        status=AttendanceSession.STATUS_OPEN
    ).count()
    overdue_loans = sum(
        1 for loan in Loan.objects.filter(status=Loan.STATUS_ACTIVE).only("status", "due_at")
        if loan.is_overdue
    )

    return [
        {
            "key": "support_ticket_aging",
            "label": "Support Ticket Aging",
            "value": aged_tickets,
            "total": open_tickets.count(),
            "level": _insight_level(aged_tickets, watch=1, risk=5),
            "description": "ICT tickets open for three or more days.",
            "action": "Review technician workload and unresolved student issues.",
        },
        {
            "key": "registration_bottleneck",
            "label": "Registration Bottleneck",
            "value": pending_registrations,
            "total": CourseRegistration.objects.count(),
            "level": _insight_level(pending_registrations, watch=1, risk=25),
            "description": "Course registration requests still awaiting a decision.",
            "action": "Check executive approval queues for active registration periods.",
        },
        {
            "key": "assignment_overdue_rate",
            "label": "Overdue Assignment Load",
            "value": overdue_assignments,
            "total": Assignment.objects.exclude(status=Assignment.STATUS_ARCHIVED).count(),
            "level": _insight_level(overdue_assignments, watch=1, risk=25),
            "description": "Published assignments with due dates already passed.",
            "action": "Ask teachers to close, grade, or follow up on late submissions.",
        },
        {
            "key": "attendance_session_drift",
            "label": "Open Attendance Sessions",
            "value": open_attendance_sessions,
            "total": AttendanceSession.objects.exclude(status=AttendanceSession.STATUS_CANCELLED).count(),
            "level": _insight_level(open_attendance_sessions, watch=1, risk=10),
            "description": "Attendance sessions still open in the system.",
            "action": "Close stale sessions before attendance reports are finalized.",
        },
        {
            "key": "library_overdue_loans",
            "label": "Library Overdue Loans",
            "value": overdue_loans,
            "total": Loan.objects.filter(status=Loan.STATUS_ACTIVE).count(),
            "level": _insight_level(overdue_loans, watch=1, risk=10),
            "description": "Active library loans past their due date.",
            "action": "Escalate overdue circulation follow-up through the library desk.",
        },
    ]


class AdminStatistics(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        # 1. User counts
        student_count = Profile.objects.filter(role=Profile.ROLE_STUDENT).count()
        teacher_count = Profile.objects.filter(role=Profile.ROLE_TEACHER).count()
        executive_count = Profile.objects.filter(role=Profile.ROLE_EXECUTIVE).count()
        librarian_count = Profile.objects.filter(role=Profile.ROLE_LIBRARIAN).count()
        admin_count = Profile.objects.filter(role=Profile.ROLE_ADMIN).count()
        applicant_count = Profile.objects.filter(role=Profile.ROLE_APPLICANT).count()
        total_users = Profile.objects.count()

        # 2. Academic structure
        school_count = School.objects.count()
        center_count = Center.objects.count()
        department_count = Department.objects.count()
        program_count = Program.objects.count()
        active_semester_count = Semester.objects.filter(is_active=True).count()

        # 3. Facilities & Infrastructure
        building_count = Building.objects.count()
        venue_count = Venue.objects.count()
        venue_total_capacity = Venue.objects.aggregate(total_cap=Sum("capacity"))["total_cap"] or 0
        hostel_count = Hostel.objects.count()
        hostel_room_count = HostelRoom.objects.count()
        hostel_total_capacity = HostelRoom.objects.aggregate(total_cap=Sum("capacity"))["total_cap"] or 0

        # 4. Admissions Funnel
        total_applications = AdmissionApplication.objects.count()
        app_status_counts = {}
        for s_code, _s_label in AdmissionApplication.STATUS_CHOICES:
            app_status_counts[s_code] = AdmissionApplication.objects.filter(status=s_code).count()

        # 5. Academics details
        course_count = Course.objects.count()
        course_offering_count = CourseOffering.objects.count()
        class_meeting_count = ClassMeeting.objects.count()

        # Recent activity data
        recent_logs_qs = AuditLog.objects.select_related('user__user').order_by('-created_at')[:5]
        recent_logs = [
            {
                "id": log.id,
                "action": log.action,
                "user": log.user.user.username if log.user_id and log.user else None,
                "timestamp": log.created_at.isoformat(),
            }
            for log in recent_logs_qs
        ]

        # Notification counts (unread)
        unread_notifications = Notification.objects.filter(unread=True).count()

        data = {
            "title": "System Statistics",
            "section": "admin",
            "users": {
                "student": student_count,
                "teacher": teacher_count,
                "executive": executive_count,
                "librarian": librarian_count,
                "admin": admin_count,
                "applicant": applicant_count,
                "total": total_users,
            },
            "academic_units": {
                "schools": school_count,
                "centers": center_count,
                "departments": department_count,
                "programs": program_count,
                "active_semesters": active_semester_count,
            },
            "infrastructure": {
                "buildings": building_count,
                "venues": venue_count,
                "venue_capacity": venue_total_capacity,
                "hostels": hostel_count,
                "hostel_rooms": hostel_room_count,
                "hostel_capacity": hostel_total_capacity,
            },
            "applications": {
                "total": total_applications,
                **app_status_counts,
            },
            "academics": {
                "courses": course_count,
                "offerings": course_offering_count,
                "meetings": class_meeting_count,
            },
            "notifications": {
                "unread": unread_notifications,
            },
            "insights": _admin_insights(),
            "recent_audit_logs": recent_logs,
        }
        return Response(data, status=status.HTTP_200_OK)

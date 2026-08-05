from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import (
    Building,
    ClassMeeting,
    Course,
    CourseOffering,
    Profile,
    School,
    Semester,
    SystemSetting,
    Venue,
    VenueBookingRequest,
)
from admin_app.settings_registry import invalidate_settings_cache, setting_key


User = get_user_model()


class VenueBookingWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.building = Building.objects.create(code="LIB", name="Library Building")
        self.venue = Venue.objects.create(building=self.building, code="LIB-HALL", name="Library Hall")
        self.student = self._profile("booking_student", Profile.ROLE_STUDENT)
        self.teacher = self._profile("booking_teacher", Profile.ROLE_TEACHER)
        self.technician = self._profile("booking_technician", Profile.ROLE_TECHNICIAN)
        self.admin = self._profile("booking_admin", Profile.ROLE_ADMIN)
        self.booking_date = timezone.localdate() + timedelta(days=14)

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.save(update_fields=["role", "updated_at"])
        return profile

    def _payload(self, **overrides):
        payload = {
            "venue_id": self.venue.id,
            "booking_type": VenueBookingRequest.TYPE_EVENT,
            "purpose": "Student society workshop",
            "explanation": "A detailed workshop for students to practise public speaking.",
            "booking_date": self.booking_date.isoformat(),
            "start_time": "10:00",
            "end_time": "12:00",
        }
        payload.update(overrides)
        return payload

    def _create_request(self, requester=None, **overrides):
        data = {
            "requester": requester or self.student,
            "venue": self.venue,
            "booking_type": VenueBookingRequest.TYPE_EVENT,
            "purpose": "Student society workshop",
            "explanation": "A detailed workshop for students to practise public speaking.",
            "booking_date": self.booking_date,
            "start_time": "10:00",
            "end_time": "12:00",
        }
        data.update(overrides)
        return VenueBookingRequest.objects.create(**data)

    def _create_recurring_class(self):
        school = School.objects.create(code="SCS", name="School of Computing")
        semester = Semester.objects.create(
            name="Venue Test Semester",
            academic_session="2026/2027",
            start_date=self.booking_date - timedelta(days=1),
            end_date=self.booking_date + timedelta(days=30),
        )
        course = Course.objects.create(code="VBT1001", title="Venue Conflict Testing", credits=3, school=school)
        offering = CourseOffering.objects.create(course=course, semester=semester, section="C1")
        return ClassMeeting.objects.create(
            offering=offering,
            semester=semester,
            venue=self.venue,
            day_of_week=self.booking_date.isoweekday(),
            start_time="11:00",
            end_time="13:00",
            status=ClassMeeting.STATUS_SCHEDULED,
        )

    def _update_policy(self, **values):
        SystemSetting.objects.update_or_create(
            key=setting_key("venue_booking_policy"),
            defaults={"value": values},
        )
        invalidate_settings_cache()

    def tearDown(self):
        invalidate_settings_cache()

    def test_student_and_teacher_can_submit_and_technician_is_notified(self):
        self.client.force_authenticate(self.student.user)
        student_response = self.client.post("/student/venue-bookings", self._payload(), format="json")

        self.client.force_authenticate(self.teacher.user)
        teacher_response = self.client.post(
            "/teacher/venue-bookings",
            self._payload(start_time="13:00", end_time="14:00"),
            format="json",
        )

        self.assertEqual(student_response.status_code, 201)
        self.assertEqual(teacher_response.status_code, 201)
        self.assertEqual(VenueBookingRequest.objects.count(), 2)
        self.assertEqual(
            self.technician.notifications.filter(data__venue_booking_request_id__isnull=False).count(),
            2,
        )
        self.assertEqual(
            self.admin.notifications.filter(data__venue_booking_request_id__isnull=False).count(),
            0,
        )

    def test_recurring_class_blocks_request_but_cancelled_date_does_not(self):
        recurring = self._create_recurring_class()
        self.client.force_authenticate(self.student.user)

        blocked = self.client.post("/student/venue-bookings", self._payload(), format="json")

        ClassMeeting.objects.create(
            offering=recurring.offering,
            semester=recurring.semester,
            recurring_meeting=recurring,
            meeting_date=self.booking_date,
            venue=self.venue,
            day_of_week=self.booking_date.isoweekday(),
            start_time=recurring.start_time,
            end_time=recurring.end_time,
            status=ClassMeeting.STATUS_CANCELLED,
        )
        allowed = self.client.post("/student/venue-bookings", self._payload(), format="json")

        self.assertEqual(blocked.status_code, 409)
        self.assertIn("assigned to class", blocked.data["detail"])
        self.assertEqual(allowed.status_code, 201)

    def test_approved_booking_blocks_new_request(self):
        self._create_request(
            requester=self.teacher,
            status=VenueBookingRequest.STATUS_APPROVED,
            start_time="09:00",
            end_time="11:00",
        )
        self.client.force_authenticate(self.student.user)

        response = self.client.post("/student/venue-bookings", self._payload(), format="json")

        self.assertEqual(response.status_code, 409)
        self.assertIn("already assigned", response.data["detail"])

    def test_student_and_teacher_can_cancel_owned_bookings(self):
        pending = self._create_request(requester=self.student)
        approved = self._create_request(
            requester=self.teacher,
            status=VenueBookingRequest.STATUS_APPROVED,
            start_time="13:00",
            end_time="15:00",
        )

        self.client.force_authenticate(self.student.user)
        student_response = self.client.post(
            f"/student/venue-bookings/{pending.id}/cancel",
            {},
            format="json",
        )

        self.client.force_authenticate(self.teacher.user)
        teacher_response = self.client.post(
            f"/teacher/venue-bookings/{approved.id}/cancel",
            {},
            format="json",
        )

        self.assertEqual(student_response.status_code, 200, student_response.json())
        self.assertEqual(teacher_response.status_code, 200, teacher_response.json())
        pending.refresh_from_db()
        approved.refresh_from_db()
        self.assertEqual(pending.status, VenueBookingRequest.STATUS_CANCELLED)
        self.assertEqual(approved.status, VenueBookingRequest.STATUS_CANCELLED)
        self.assertTrue(
            self.technician.notifications.filter(
                data__event_type="venues.booking_cancelled",
                data__venue_booking_request_id=pending.id,
            ).exists()
        )

        self.client.force_authenticate(self.student.user)
        available_again_response = self.client.post(
            "/student/venue-bookings",
            self._payload(start_time="13:30", end_time="14:30"),
            format="json",
        )
        self.assertEqual(available_again_response.status_code, 201, available_again_response.json())

    def test_requester_cannot_cancel_someone_elses_booking(self):
        booking = self._create_request(requester=self.teacher)
        self.client.force_authenticate(self.student.user)

        response = self.client.post(
            f"/student/venue-bookings/{booking.id}/cancel",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        booking.refresh_from_db()
        self.assertEqual(booking.status, VenueBookingRequest.STATUS_PENDING)

    def test_technician_approval_rechecks_conflict_and_notifies_requester(self):
        first = self._create_request()
        second = self._create_request(requester=self.teacher)
        self.client.force_authenticate(self.technician.user)

        first_response = self.client.post(
            f"/ict-helpdesk/technician/venue-bookings/{first.id}/decision",
            {"decision": VenueBookingRequest.STATUS_APPROVED},
            format="json",
        )
        second_response = self.client.post(
            f"/ict-helpdesk/technician/venue-bookings/{second.id}/decision",
            {"decision": VenueBookingRequest.STATUS_APPROVED},
            format="json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, VenueBookingRequest.STATUS_APPROVED)
        self.assertEqual(first.reviewed_by, self.technician)
        self.assertEqual(second.status, VenueBookingRequest.STATUS_PENDING)
        self.assertTrue(self.student.notifications.filter(data__venue_booking_request_id=first.id).exists())

    def test_technician_rejection_requires_reason_and_returns_it_to_requester(self):
        booking = self._create_request()
        self.client.force_authenticate(self.technician.user)

        missing_reason = self.client.post(
            f"/ict-helpdesk/technician/venue-bookings/{booking.id}/decision",
            {"decision": VenueBookingRequest.STATUS_REJECTED},
            format="json",
        )
        response = self.client.post(
            f"/ict-helpdesk/technician/venue-bookings/{booking.id}/decision",
            {
                "decision": VenueBookingRequest.STATUS_REJECTED,
                "rejection_reason": "The venue needs maintenance preparation.",
            },
            format="json",
        )

        self.assertEqual(missing_reason.status_code, 400)
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, VenueBookingRequest.STATUS_REJECTED)
        self.assertEqual(booking.reviewed_by, self.technician)
        self.assertEqual(booking.rejection_reason, "The venue needs maintenance preparation.")
        self.assertTrue(self.student.notifications.filter(data__venue_booking_request_id=booking.id).exists())

    def test_only_technicians_can_manage_booking_review_endpoints(self):
        booking = self._create_request()

        self.client.force_authenticate(self.admin.user)
        legacy_get = self.client.get("/admin/venue-bookings")
        legacy_decision = self.client.post(
            f"/admin/venue-bookings/{booking.id}/decision",
            {"decision": VenueBookingRequest.STATUS_APPROVED},
            format="json",
        )

        self.client.force_authenticate(self.student.user)
        student_get = self.client.get("/ict-helpdesk/technician/venue-bookings")
        student_decision = self.client.post(
            f"/ict-helpdesk/technician/venue-bookings/{booking.id}/decision",
            {"decision": VenueBookingRequest.STATUS_APPROVED},
            format="json",
        )

        self.client.force_authenticate(self.technician.user)
        technician_get = self.client.get("/ict-helpdesk/technician/venue-bookings")

        self.assertEqual(legacy_get.status_code, 404)
        self.assertEqual(legacy_decision.status_code, 404)
        self.assertEqual(student_get.status_code, 403)
        self.assertEqual(student_decision.status_code, 403)
        self.assertEqual(technician_get.status_code, 200, technician_get.json())
        self.assertEqual(technician_get.json()["role"], "technician")

    def test_custom_venue_categories_are_exposed_and_validated(self):
        self._update_policy(
            venue_category_options="seminar|Seminar room\nevent_hall|Event hall",
        )
        self.client.force_authenticate(self.admin.user)

        response = self.client.post(
            "/admin/venues/venues",
            {
                "building": self.building.id,
                "code": "EVENT-HALL",
                "name": "Event Hall",
                "category": "event_hall",
            },
            format="json",
        )
        invalid = self.client.post(
            "/admin/venues/venues",
            {
                "building": self.building.id,
                "code": "UNKNOWN-HALL",
                "name": "Unknown Hall",
                "category": "auditorium",
            },
            format="json",
        )
        listing = self.client.get("/admin/venues")

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.data["venue"]["category"], "event_hall")
        self.assertEqual(response.data["venue"]["category_label"], "Event hall")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("category", invalid.data["errors"])
        self.assertIn(
            {"value": "seminar", "label": "Seminar room"},
            listing.data["policy"]["venue_categories"],
        )

    def test_policy_restricts_requester_role_blackouts_duration_and_required_fields(self):
        self._update_policy(
            requester_roles="teacher",
            blackout_dates=self.booking_date.isoformat(),
            min_duration_minutes=60,
            max_duration_hours=2,
            required_fields_personal="purpose",
        )

        self.client.force_authenticate(self.student.user)
        student_response = self.client.post("/student/venue-bookings", self._payload(), format="json")

        self.client.force_authenticate(self.teacher.user)
        blackout_response = self.client.post("/teacher/venue-bookings", self._payload(), format="json")
        too_long_response = self.client.post(
            "/teacher/venue-bookings",
            self._payload(
                booking_date=(self.booking_date + timedelta(days=1)).isoformat(),
                start_time="09:00",
                end_time="12:30",
            ),
            format="json",
        )
        personal_response = self.client.post(
            "/teacher/venue-bookings",
            self._payload(
                booking_type=VenueBookingRequest.TYPE_PERSONAL,
                explanation="",
                booking_date=(self.booking_date + timedelta(days=1)).isoformat(),
                start_time="13:00",
                end_time="14:00",
            ),
            format="json",
        )

        self.assertEqual(student_response.status_code, 400)
        self.assertIn("not allowed", student_response.data["detail"])
        self.assertEqual(blackout_response.status_code, 400)
        self.assertIn("blackout", blackout_response.data["detail"])
        self.assertEqual(too_long_response.status_code, 400)
        self.assertIn("cannot exceed 2 hour", too_long_response.data["detail"])
        self.assertEqual(personal_response.status_code, 201, personal_response.json())

    def test_auto_approval_policy_approves_conflict_free_request_without_reviewer_notification(self):
        self._update_policy(approval_mode="auto_approve")
        self.client.force_authenticate(self.student.user)

        response = self.client.post("/student/venue-bookings", self._payload(), format="json")

        self.assertEqual(response.status_code, 201, response.json())
        booking = VenueBookingRequest.objects.get(pk=response.data["request"]["id"])
        self.assertEqual(booking.status, VenueBookingRequest.STATUS_APPROVED)
        self.assertIsNotNone(booking.reviewed_at)
        self.assertEqual(
            self.technician.notifications.filter(data__venue_booking_request_id=booking.id).count(),
            0,
        )

    def test_admin_reviewer_policy_moves_approval_endpoint(self):
        self._update_policy(reviewer_role=Profile.ROLE_ADMIN)
        booking = self._create_request()

        self.client.force_authenticate(self.technician.user)
        technician_get = self.client.get("/ict-helpdesk/technician/venue-bookings")

        self.client.force_authenticate(self.admin.user)
        admin_get = self.client.get("/admin/venue-bookings")
        admin_decision = self.client.post(
            f"/admin/venue-bookings/{booking.id}/decision",
            {"decision": VenueBookingRequest.STATUS_APPROVED},
            format="json",
        )

        self.assertEqual(technician_get.status_code, 404)
        self.assertEqual(admin_get.status_code, 200, admin_get.json())
        self.assertEqual(admin_get.json()["role"], "admin")
        self.assertEqual(admin_decision.status_code, 200, admin_decision.json())
        booking.refresh_from_db()
        self.assertEqual(booking.status, VenueBookingRequest.STATUS_APPROVED)
        self.assertEqual(booking.reviewed_by, self.admin)

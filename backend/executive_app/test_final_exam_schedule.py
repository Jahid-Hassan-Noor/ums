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
    Venue,
    VenueBookingRequest,
)
from student_app.models import Enrollment, ExamVenueAllocation


User = get_user_model()


class FinalExamScheduleTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.exam_date = self.today + timedelta(days=30)
        self.school = School.objects.create(code="EXAM", name="Exam School")
        self.semester = Semester.objects.create(
            name="Final Exam Semester",
            academic_session="2026/2027",
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=70),
            examination_starts_on=self.exam_date,
            examination_ends_on=self.exam_date + timedelta(days=10),
        )
        self.building = Building.objects.create(code="EH", name="Exam Halls")
        self.hall = Venue.objects.create(
            building=self.building,
            code="EH-1",
            name="Exam Hall 1",
            capacity=50,
        )
        self.room = Venue.objects.create(
            building=self.building,
            code="EH-2",
            name="Exam Hall 2",
            capacity=20,
        )
        self.executive = self._profile("exam_exec", Profile.ROLE_EXECUTIVE)
        self.client = APIClient()
        self.client.force_authenticate(self.executive.user)
        self.offerings = [self._offering(index) for index in range(1, 5)]

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def _offering(self, index):
        course = Course.objects.create(
            code=f"EXM{index}001",
            title=f"Exam Course {index}",
            credits=3,
            school=self.school,
        )
        return CourseOffering.objects.create(
            course=course,
            semester=self.semester,
            section="A",
            capacity=50,
        )

    def _enroll(self, offering, username):
        student = self._profile(username, Profile.ROLE_STUDENT)
        Enrollment.objects.create(
            student=student,
            offering=offering,
            created_by=self.executive,
        )
        return student

    def _payload(self, offering, *, venue=None, seats=1, **overrides):
        payload = {
            "schedule_kind": "final_exam",
            "offering_id": offering.id,
            "exam_date": self.exam_date.isoformat(),
            "start_time": "09:30",
            "end_time": "12:30",
            "venue_allocations": [
                {
                    "venue_id": (venue or self.hall).id,
                    "seats": seats,
                }
            ],
        }
        payload.update(overrides)
        return payload

    def test_coursework_only_offering_is_excluded_from_final_exam_scheduling(self):
        offering = self.offerings[0]
        offering.has_final_exam = False
        offering.coursework_percentage = "100.00"
        offering.final_exam_percentage = "0.00"
        offering.save(
            update_fields=[
                "has_final_exam",
                "coursework_percentage",
                "final_exam_percentage",
                "updated_at",
            ]
        )

        options = self.client.get("/executive/manage/schedule")
        response = self.client.post(
            "/executive/manage/schedule",
            self._payload(offering),
            format="json",
        )

        self.assertEqual(options.status_code, 200, options.json())
        self.assertNotIn(offering.id, [row["id"] for row in options.data["exam_offerings"]])
        self.assertEqual(response.status_code, 409, response.json())
        self.assertIn("coursework-only", response.data["detail"])

    def test_final_exams_can_share_a_venue_until_capacity_is_exceeded(self):
        first = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0], seats=25),
            format="json",
        )
        second = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[1], seats=25),
            format="json",
        )
        over_capacity = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[2], seats=1),
            format="json",
        )

        self.assertEqual(first.status_code, 201, first.json())
        self.assertEqual(second.status_code, 201, second.json())
        self.assertEqual(over_capacity.status_code, 409, over_capacity.json())
        self.assertIn("capacity is 50", over_capacity.data["detail"])
        self.assertEqual(ExamVenueAllocation.objects.filter(venue=self.hall).count(), 2)

    def test_overlapping_exams_report_students_enrolled_in_both_courses(self):
        student = self._enroll(self.offerings[0], "shared_exam_student")
        Enrollment.objects.create(
            student=student,
            offering=self.offerings[1],
            created_by=self.executive,
        )
        first = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )
        conflict = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[1], venue=self.room),
            format="json",
        )

        self.assertEqual(first.status_code, 201, first.json())
        self.assertEqual(conflict.status_code, 409, conflict.json())
        self.assertIn(self.offerings[0].course.code, conflict.data["detail"])
        self.assertIn("shared_exam_student", conflict.data["detail"])
        self.assertEqual(conflict.data["conflicts"][0]["student_count"], 1)

    def test_one_exam_can_reserve_multiple_venues_for_all_enrolled_students(self):
        for index in range(3):
            self._enroll(self.offerings[0], f"split_exam_student_{index}")
        response = self.client.post(
            "/executive/manage/schedule",
            self._payload(
                self.offerings[0],
                venue_allocations=[
                    {"venue_id": self.hall.id, "seats": 2},
                    {"venue_id": self.room.id, "seats": 1},
                ],
            ),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.data["final_exam"]["enrollment_count"], 3)
        self.assertEqual(len(response.data["final_exam"]["venue_allocations"]), 2)

    def test_exam_schedule_is_locked_when_the_exam_period_starts(self):
        created = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )
        self.semester.examination_starts_on = self.today
        self.semester.examination_ends_on = self.today + timedelta(days=10)
        self.semester.save(update_fields=["examination_starts_on", "examination_ends_on", "updated_at"])

        locked = self.client.post(
            "/executive/manage/schedule",
            self._payload(
                self.offerings[0],
                exam_id=created.data["final_exam"]["id"],
            ),
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.json())
        self.assertEqual(locked.status_code, 409, locked.json())
        self.assertIn("locked", locked.data["detail"])

    def test_student_sees_final_exam_on_existing_timetable(self):
        student = self._enroll(self.offerings[0], "exam_timetable_student")
        created = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )
        self.client.force_authenticate(student.user)

        response = self.client.get("/student/timetable")

        self.assertEqual(created.status_code, 201, created.json())
        self.assertEqual(response.status_code, 200, response.json())
        event = next(
            event
            for event in response.data["schedule"]["events"]
            if event["id"] == f"final-exam-{created.data['final_exam']['id']}"
        )
        self.assertEqual(event["event_type"], "final_exam")
        self.assertEqual(event["category"], "assessment")
        self.assertIn(self.hall.name, event["location"])

    def test_final_exam_and_ordinary_venue_booking_cannot_overlap(self):
        requester = self._profile("exam_booking_student", Profile.ROLE_STUDENT)
        created = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )
        self.client.force_authenticate(requester.user)
        booking = self.client.post(
            "/student/venue-bookings",
            {
                "venue_id": self.hall.id,
                "booking_type": VenueBookingRequest.TYPE_EVENT,
                "purpose": "Student society workshop",
                "explanation": "A detailed workshop request that overlaps the final exam.",
                "booking_date": self.exam_date.isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
            },
            format="json",
        )

        self.assertEqual(created.status_code, 201, created.json())
        self.assertEqual(booking.status_code, 409, booking.json())
        self.assertIn("final exam", booking.data["detail"])

    def test_approved_venue_booking_blocks_final_exam(self):
        requester = self._profile("approved_booking_student", Profile.ROLE_STUDENT)
        VenueBookingRequest.objects.create(
            requester=requester,
            venue=self.hall,
            booking_type=VenueBookingRequest.TYPE_EVENT,
            purpose="Approved event",
            explanation="An approved event already uses this venue during the requested time.",
            booking_date=self.exam_date,
            start_time="10:00",
            end_time="11:00",
            status=VenueBookingRequest.STATUS_APPROVED,
        )

        response = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )

        self.assertEqual(response.status_code, 409, response.json())
        self.assertIn("already assigned", response.data["detail"])

    def test_recurring_classes_do_not_block_exams_after_the_teaching_period(self):
        ClassMeeting.objects.create(
            offering=self.offerings[1],
            semester=self.semester,
            venue=self.hall,
            day_of_week=self.exam_date.isoweekday(),
            start_time="09:30",
            end_time="12:30",
            status=ClassMeeting.STATUS_SCHEDULED,
        )

        response = self.client.post(
            "/executive/manage/schedule",
            self._payload(self.offerings[0]),
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())

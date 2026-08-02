from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import Center, ClassMeeting, Course, CourseLabGroup, CourseOffering, CourseTutorialGroup, Profile, School, Semester, TimetableSlot
from student_app.leave_service import decide_leave_approval, submit_leave_request
from student_app.models import CourseRegistration, Enrollment, LeaveApproval, LeaveRequest, RegistrationPeriod, TranscriptRecord
from student_app.registration_service import (
    active_semester,
    change_registered_group,
    drop_student_course,
    register_student,
    student_offerings,
)
from technician_app.models import Election, ElectionCandidate, SchoolElectionSeat, Vote


User = get_user_model()


class CourseRegistrationRuleTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        self.semester = Semester.objects.create(
            name="Semester 1, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            max_credit_hours=3,
            is_active=True,
        )
        now = timezone.now()
        self.period = RegistrationPeriod.objects.create(
            semester=self.semester,
            title="Course Registration",
            phase=RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            opens_at=now - timezone.timedelta(days=1),
            closes_at=now + timezone.timedelta(days=1),
        )
        self.course = Course.objects.create(
            code="CCS1001",
            title="Portal Engineering",
            credits=3,
            school=self.school,
        )
        self.extra_course = Course.objects.create(
            code="CCS1002",
            title="Credit Overflow",
            credits=1,
            school=self.school,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            section="C1",
            capacity=5,
        )
        self.extra_offering = CourseOffering.objects.create(
            course=self.extra_course,
            semester=self.semester,
            section="C1",
            capacity=5,
        )
        self.student = self._student("student_one")

    def _student(self, username):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.school = self.school
        profile.student_id = username.upper()
        profile.save(update_fields=["school", "student_id", "updated_at"])
        return profile

    def _executive(self):
        user = User.objects.create_user(username="exec_one", password="pass")
        profile = user.profile
        profile.role = Profile.ROLE_EXECUTIVE
        profile.school = self.school
        profile.staff_id = "EXEC-1"
        profile.save(update_fields=["role", "school", "staff_id", "updated_at"])
        return profile

    def test_student_cannot_exceed_semester_credit_limit(self):
        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.status, CourseRegistration.STATUS_APPROVED)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                offering=self.offering,
                registration=registration,
            ).exists()
        )

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.extra_offering,
            actor=self.student,
        )
        self.assertEqual(response_status, 400)
        self.assertIn("maximum 3 credit hours", error)

    def test_drop_only_phase_rejects_student_add(self):
        self.period.phase = RegistrationPeriod.PHASE_DROP_ONLY
        self.period.save(update_fields=["phase", "updated_at"])

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )

        self.assertEqual(response_status, 403)
        self.assertIn("only allows students to drop", error)

    def test_student_must_complete_prerequisite_before_registration(self):
        self.course.prerequisites.add(self.extra_course)

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )

        self.assertEqual(response_status, 400)
        self.assertIn(self.extra_course.code, error)

        Enrollment.objects.create(
            student=self.student,
            offering=self.extra_offering,
            completed_at=timezone.now(),
        )
        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )

        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.status, CourseRegistration.STATUS_APPROVED)

    def test_tutorial_group_capacity_is_enforced(self):
        group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="C1",
            capacity=1,
        )
        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
            tutorial_group_code=group.code,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        second_student = self._student("student_two")
        _registration, error, response_status = register_student(
            student=second_student,
            offering=self.offering,
            actor=second_student,
            tutorial_group_code=group.code,
        )
        self.assertEqual(response_status, 409)
        self.assertIn("already full", error)

    def test_student_must_drop_before_registering_same_course_in_another_section(self):
        first_group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="C1",
            capacity=5,
        )
        second_offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            section="C2",
            capacity=5,
        )
        second_group = CourseTutorialGroup.objects.create(
            offering=second_offering,
            code="C2",
            capacity=5,
        )

        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
            tutorial_group_code=first_group.code,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        _registration, error, response_status = register_student(
            student=self.student,
            offering=second_offering,
            actor=self.student,
            tutorial_group_code=second_group.code,
        )
        self.assertEqual(response_status, 409)
        self.assertIn("already registered", error)
        self.assertIn("Drop the current registration", error)

        dropped, error, response_status = drop_student_course(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 200)
        self.assertEqual(dropped.status, CourseRegistration.STATUS_DROPPED)

        registration, error, response_status = register_student(
            student=self.student,
            offering=second_offering,
            actor=self.student,
            tutorial_group_code=second_group.code,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.offering, second_offering)

    def test_registered_group_cannot_be_changed_in_place(self):
        first_group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="C1",
            capacity=5,
        )
        second_group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="C2",
            capacity=5,
        )
        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
            tutorial_group_code=first_group.code,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        error, response_status = change_registered_group(
            registration=registration,
            tutorial_group_id=second_group.id,
        )

        self.assertEqual(response_status, 409)
        self.assertIn("Drop the current course registration", error)
        registration.refresh_from_db()
        self.assertEqual(registration.tutorial_group, first_group)

    def test_passed_course_cannot_be_retaken_but_failed_course_can(self):
        previous_semester = Semester.objects.create(
            name="Semester 2, Session 2025/2026",
            academic_session="2025/2026",
            start_date="2026-03-23",
            end_date="2026-07-17",
            is_active=False,
        )
        previous_offering = CourseOffering.objects.create(
            course=self.course,
            semester=previous_semester,
            section="C1",
            capacity=5,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=previous_offering,
            completed_at=timezone.now(),
        )
        TranscriptRecord.objects.create(
            student=self.student,
            semester=previous_semester,
            offering=previous_offering,
            course_code=self.course.code,
            course_title=self.course.title,
            credit_hours=self.course.credits,
            score=75,
            grade="A-",
            grade_points="3.67",
            published_at=timezone.now(),
        )

        _registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )
        self.assertEqual(response_status, 409)
        self.assertIn("already completed with a passing grade", error)

        failed_student = self._student("failed_student")
        Enrollment.objects.create(
            student=failed_student,
            offering=previous_offering,
            completed_at=timezone.now(),
        )
        TranscriptRecord.objects.create(
            student=failed_student,
            semester=previous_semester,
            offering=previous_offering,
            course_code=self.course.code,
            course_title=self.course.title,
            credit_hours=self.course.credits,
            score=45,
            grade="C-",
            grade_points="1.67",
            published_at=timezone.now(),
        )

        registration, error, response_status = register_student(
            student=failed_student,
            offering=self.offering,
            actor=failed_student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.status, CourseRegistration.STATUS_APPROVED)

    def test_overlapping_course_meetings_block_registration(self):
        self.semester.max_credit_hours = 6
        self.semester.save(update_fields=["max_credit_hours", "updated_at"])
        conflict_course = Course.objects.create(
            code="CCS1003",
            title="Conflicting Systems",
            credits=3,
            school=self.school,
        )
        conflict_offering = CourseOffering.objects.create(
            course=conflict_course,
            semester=self.semester,
            section="C1",
            capacity=5,
        )
        ClassMeeting.objects.create(
            offering=self.offering,
            semester=self.semester,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(11, 0),
            status=ClassMeeting.STATUS_SCHEDULED,
        )
        ClassMeeting.objects.create(
            offering=conflict_offering,
            semester=self.semester,
            day_of_week=1,
            start_time=time(10, 30),
            end_time=time(12, 0),
            status=ClassMeeting.STATUS_SCHEDULED,
        )

        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        _registration, error, response_status = register_student(
            student=self.student,
            offering=conflict_offering,
            actor=self.student,
        )
        self.assertEqual(response_status, 409)
        self.assertIn(f"timetable conflict with {self.course.code}", error)
        self.assertIn("executive", error)

    def test_timetable_conflict_only_uses_the_selected_lab_group(self):
        self.semester.max_credit_hours = 6
        self.semester.save(update_fields=["max_credit_hours", "updated_at"])
        lab_course = Course.objects.create(
            code="CCS1004",
            title="Group-Specific Systems Lab",
            credits=3,
            school=self.school,
            has_lab=True,
        )
        lab_offering = CourseOffering.objects.create(
            course=lab_course,
            semester=self.semester,
            section="C1",
            capacity=5,
        )
        tutorial_group = CourseTutorialGroup.objects.create(
            offering=lab_offering,
            code="C1",
            capacity=5,
        )
        conflicting_lab = CourseLabGroup.objects.create(
            tutorial_group=tutorial_group,
            code="A",
            capacity=5,
        )
        available_lab = CourseLabGroup.objects.create(
            tutorial_group=tutorial_group,
            code="B",
            capacity=5,
        )
        ClassMeeting.objects.create(
            offering=self.offering,
            semester=self.semester,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(11, 0),
            status=ClassMeeting.STATUS_SCHEDULED,
        )
        ClassMeeting.objects.create(
            offering=lab_offering,
            semester=self.semester,
            tutorial_group=tutorial_group,
            lab_group=conflicting_lab,
            day_of_week=1,
            start_time=time(10, 0),
            end_time=time(12, 0),
            class_type=ClassMeeting.CLASS_TYPE_LAB,
            status=ClassMeeting.STATUS_SCHEDULED,
        )
        ClassMeeting.objects.create(
            offering=lab_offering,
            semester=self.semester,
            tutorial_group=tutorial_group,
            lab_group=available_lab,
            day_of_week=1,
            start_time=time(12, 0),
            end_time=time(14, 0),
            class_type=ClassMeeting.CLASS_TYPE_LAB,
            status=ClassMeeting.STATUS_SCHEDULED,
        )

        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        registration, error, response_status = register_student(
            student=self.student,
            offering=lab_offering,
            actor=self.student,
            tutorial_group_id=tutorial_group.id,
            lab_group_id=available_lab.id,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.lab_group, available_lab)

        second_student = self._student("conflicting_lab_student")
        registration, error, response_status = register_student(
            student=second_student,
            offering=self.offering,
            actor=second_student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)

        _registration, error, response_status = register_student(
            student=second_student,
            offering=lab_offering,
            actor=second_student,
            tutorial_group_id=tutorial_group.id,
            lab_group_id=conflicting_lab.id,
        )
        self.assertEqual(response_status, 409)
        self.assertIn("timetable conflict", error)

    def test_student_can_only_register_for_own_or_explicitly_eligible_school_offerings(self):
        other_school = School.objects.create(code="SBS", name="School of Business Studies")
        other_course = Course.objects.create(
            code="SBS1001",
            title="Business for Engineers",
            credits=3,
            school=other_school,
        )
        other_offering = CourseOffering.objects.create(
            course=other_course,
            semester=self.semester,
            section="B1",
            capacity=5,
        )

        self.assertFalse(student_offerings(self.student, self.semester).filter(pk=other_offering.pk).exists())
        _registration, error, response_status = register_student(
            student=self.student,
            offering=other_offering,
            actor=self.student,
        )
        self.assertEqual(response_status, 403)
        self.assertIn("not available", error)

        other_offering.eligible_schools.add(self.school)
        registration, error, response_status = register_student(
            student=self.student,
            offering=other_offering,
            actor=self.student,
        )
        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.status, CourseRegistration.STATUS_APPROVED)

        unassigned_student = self._student("student_without_school")
        unassigned_student.school = None
        unassigned_student.save(update_fields=["school", "updated_at"])
        self.assertFalse(student_offerings(unassigned_student, self.semester).exists())

    def test_executive_manual_registration_creates_approved_enrollment_after_period(self):
        self.period.is_active = False
        self.period.save(update_fields=["is_active", "updated_at"])
        executive = self._executive()

        registration, error, response_status = register_student(
            student=self.student,
            offering=self.offering,
            actor=executive,
            manual=True,
        )

        self.assertIsNone(error)
        self.assertEqual(response_status, 201)
        self.assertEqual(registration.status, CourseRegistration.STATUS_APPROVED)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                offering=self.offering,
                registration=registration,
            ).exists()
        )

    def test_pre_registration_can_target_a_planned_upcoming_semester(self):
        self.period.is_active = False
        self.period.save(update_fields=["is_active", "updated_at"])
        planned = Semester.objects.create(
            name="Planned Semester 2, Session 2026/2027",
            academic_session="2026/2027",
            start_date=timezone.localdate() + timezone.timedelta(days=30),
            end_date=timezone.localdate() + timezone.timedelta(days=150),
            is_active=False,
        )
        RegistrationPeriod.objects.create(
            semester=planned,
            title="Course Pre-Registration",
            phase=RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            opens_at=timezone.now() - timezone.timedelta(days=1),
            closes_at=timezone.now() + timezone.timedelta(days=1),
        )
        foundation = Semester.objects.create(
            name="CFGS Planned Semester",
            academic_session="2026/2027",
            calendar_group=Semester.CALENDAR_FOUNDATION,
            start_date=timezone.localdate() + timezone.timedelta(days=20),
            end_date=timezone.localdate() + timezone.timedelta(days=140),
            is_active=False,
        )
        RegistrationPeriod.objects.create(
            semester=foundation,
            title="CFGS Course Pre-Registration",
            phase=RegistrationPeriod.PHASE_COURSE_REGISTRATION,
            opens_at=timezone.now() - timezone.timedelta(days=2),
            closes_at=timezone.now() + timezone.timedelta(days=1),
        )

        self.assertEqual(active_semester(student=self.student, prefer_registration=True), planned)

        language_center = Center.objects.create(code="LC", name="Language Centre")
        lc_student = self._student("lc_student")
        lc_student.school = None
        lc_student.center = language_center
        lc_student.save(update_fields=["school", "center", "updated_at"])
        self.assertIsNone(active_semester(student=lc_student, prefer_registration=True))


class StudentCoursePageEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="SCS-PAGE", name="School of Course Pages")
        self.semester = Semester.objects.create(
            name="Semester 1, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            max_credit_hours=18,
            is_active=True,
        )
        self.previous_semester = Semester.objects.create(
            name="Semester 2, Session 2025/2026",
            academic_session="2025/2026",
            start_date="2026-03-23",
            end_date="2026-07-17",
            max_credit_hours=18,
            is_active=False,
        )
        self.student = self._profile("course_page_student", Profile.ROLE_STUDENT, "SCS-PAGE-001")
        self.teacher = self._profile("course_page_teacher", Profile.ROLE_TEACHER, "T-SCS-PAGE-001")
        self.course = Course.objects.create(
            code="CCS2001",
            title="Student Portal Interfaces",
            credits=3,
            school=self.school,
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="C1",
            capacity=30,
        )
        self.tutorial_group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="C1",
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            tutorial_group=self.tutorial_group,
            created_by=self.teacher,
        )
        self.completed_course = Course.objects.create(
            code="CCS1001",
            title="Completed Portal Foundations",
            credits=3,
            school=self.school,
        )
        self.completed_offering = CourseOffering.objects.create(
            course=self.completed_course,
            semester=self.previous_semester,
            instructor=self.teacher,
            section="C1",
            capacity=30,
        )
        Enrollment.objects.create(
            student=self.student,
            offering=self.completed_offering,
            completed_at=timezone.now(),
            created_by=self.teacher,
        )
        TranscriptRecord.objects.create(
            student=self.student,
            semester=self.previous_semester,
            offering=self.completed_offering,
            course_code=self.completed_course.code,
            course_title=self.completed_course.title,
            credit_hours=3,
            score=88,
            grade="A",
            grade_points=4,
            gpa=4,
            cgpa=4,
            published_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.student.user)

    def _profile(self, username, role, identifier):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        if role == Profile.ROLE_STUDENT:
            profile.student_id = identifier
        else:
            profile.staff_id = identifier
        profile.save(update_fields=["role", "school", "student_id", "staff_id", "updated_at"])
        return profile

    def test_current_courses_endpoint_returns_active_enrollment_details(self):
        response = self.client.get("/student/courses/current")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["course_count"], 1)
        self.assertEqual(data["summary"]["registered_credit_hours"], 3)
        self.assertEqual(data["courses"][0]["course"]["code"], self.course.code)
        self.assertEqual(data["courses"][0]["tutorial_group"], self.tutorial_group.code)
        self.assertEqual(data["courses"][0]["semester"]["id"], self.semester.id)

    def test_completed_courses_endpoint_prefers_published_transcript_records(self):
        response = self.client.get("/student/courses/completed")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["course_count"], 1)
        self.assertEqual(data["summary"]["completed_credit_hours"], 3)
        self.assertEqual(data["courses"][0]["course_code"], self.completed_course.code)
        self.assertEqual(data["courses"][0]["grade"], "A")
        self.assertEqual(data["courses"][0]["status"], "Published")

    def test_registration_history_endpoint_returns_records_with_summary(self):
        CourseRegistration.objects.create(
            student=self.student,
            offering=self.offering,
            tutorial_group=self.tutorial_group,
            status=CourseRegistration.STATUS_APPROVED,
            registered_by=self.student,
            approved_by=self.teacher,
            approved_at=timezone.now(),
        )
        CourseRegistration.objects.create(
            student=self.student,
            offering=self.completed_offering,
            status=CourseRegistration.STATUS_DROPPED,
            registered_by=self.student,
            approved_by=self.teacher,
            approved_at=timezone.now(),
            decision_note="Dropped after programme change.",
        )

        response = self.client.get("/student/registration/history")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["total"], 2)
        self.assertEqual(data["summary"]["approved"], 1)
        self.assertEqual(data["summary"]["dropped"], 1)
        self.assertEqual(data["summary"]["credit_hours"], 3)
        self.assertEqual(data["summary"]["semesters"], 2)
        self.assertEqual(
            data["registrations"][0]["offering_detail"]["course_detail"]["code"],
            self.course.code,
        )
        self.assertEqual(
            data["registrations"][1]["offering_detail"]["course_detail"]["code"],
            self.completed_course.code,
        )


class LeaveApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        self.semester = Semester.objects.create(
            name="Semester 2, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2027-03-22",
            end_date="2027-07-16",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CCS4444",
            title="Distributed Portals",
            credits=3,
            school=self.school,
        )
        self.teacher = self._profile("leave_teacher", Profile.ROLE_TEACHER, "Lecturer")
        self.dean = self._profile("leave_dean", Profile.ROLE_TEACHER, "Dean")
        self.student = self._profile("leave_student", Profile.ROLE_STUDENT, "Student")
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="C1",
            capacity=30,
        )
        self.meeting = ClassMeeting.objects.create(
            offering=self.offering,
            semester=self.semester,
            day_of_week=TimetableSlot.MONDAY,
            start_time="09:00",
            end_time="10:00",
            lecturer=self.teacher,
            class_type=ClassMeeting.CLASS_TYPE_LECTURE,
            status=ClassMeeting.STATUS_SCHEDULED,
        )
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.teacher)

    def _profile(self, username, role, designation):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.designation = designation
        profile.save(update_fields=["role", "school", "designation", "updated_at"])
        return profile

    def test_leave_request_notifies_teacher_and_dean_then_approves_after_all_decisions(self):
        leave_day = date(2027, 3, 22)
        leave_request = submit_leave_request(
            self.student,
            start_date=leave_day,
            end_date=leave_day,
            reason="Medical appointment.",
        )

        approvals = LeaveApproval.objects.filter(leave_request=leave_request)
        self.assertEqual(approvals.count(), 2)
        self.assertTrue(approvals.filter(approver=self.teacher, approval_role=LeaveApproval.ROLE_TEACHER).exists())
        self.assertTrue(approvals.filter(approver=self.dean, approval_role=LeaveApproval.ROLE_DEAN).exists())
        self.assertTrue(self.teacher.notifications.filter(data__leave_request_id=leave_request.id).exists())
        self.assertTrue(self.dean.notifications.filter(data__leave_request_id=leave_request.id).exists())

        decide_leave_approval(
            approvals.get(approver=self.teacher),
            decision=LeaveApproval.STATUS_APPROVED,
            note="Class teacher approved.",
        )
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, LeaveRequest.STATUS_PENDING)

        decide_leave_approval(
            approvals.get(approver=self.dean),
            decision=LeaveApproval.STATUS_APPROVED,
            note="Dean approved.",
        )
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, LeaveRequest.STATUS_APPROVED)
        self.assertTrue(
            self.student.notifications.filter(
                verb="Your leave of advance has been approved.",
                data__leave_request_id=leave_request.id,
            ).exists()
        )

    def test_leave_apis_expose_tracking_history_and_teacher_decisions(self):
        leave_day = date(2027, 3, 22)
        leave_request = submit_leave_request(
            self.student,
            start_date=leave_day,
            end_date=leave_day,
            reason="Family matter.",
        )

        self.client.force_authenticate(user=self.student.user)
        response = self.client.get("/student/leave")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["leave_requests"][0]
        self.assertEqual(payload["id"], leave_request.id)
        self.assertEqual(payload["approval_summary"]["total"], 2)
        self.assertEqual(payload["approval_summary"]["pending"], 2)
        teacher_approval = next(
            item for item in payload["approvals"] if item["approval_role"] == LeaveApproval.ROLE_TEACHER
        )
        self.assertEqual(teacher_approval["class_meeting"]["course_code"], self.course.code)
        self.assertEqual(teacher_approval["class_meeting"]["day_label"], "Monday")

        history = self.client.get("/student/leave/history")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["leave_requests"], [])

        self.client.force_authenticate(user=self.teacher.user)
        teacher_response = self.client.get("/teacher/leave-requests")
        self.assertEqual(teacher_response.status_code, 200)
        teacher_payload = teacher_response.json()["leave_requests"][0]
        teacher_current = [
            item for item in teacher_payload["approvals"] if item["is_current_approver"]
        ]
        self.assertEqual(len(teacher_current), 1)
        self.assertEqual(teacher_current[0]["approval_role"], LeaveApproval.ROLE_TEACHER)

        teacher_decision = self.client.post(
            "/teacher/leave-requests",
            {
                "approval_id": teacher_current[0]["id"],
                "decision": LeaveApproval.STATUS_APPROVED,
                "note": "Teacher approved.",
            },
            format="json",
        )
        self.assertEqual(teacher_decision.status_code, 200)
        self.assertEqual(teacher_decision.json()["leave_request"]["status"], LeaveRequest.STATUS_PENDING)

        self.client.force_authenticate(user=self.dean.user)
        dean_response = self.client.get("/teacher/leave-requests")
        self.assertEqual(dean_response.status_code, 200)
        dean_payload = dean_response.json()["leave_requests"][0]
        dean_current = [
            item for item in dean_payload["approvals"] if item["is_current_approver"]
        ]
        self.assertEqual(len(dean_current), 1)
        self.assertEqual(dean_current[0]["approval_role"], LeaveApproval.ROLE_DEAN)

        dean_decision = self.client.post(
            "/teacher/leave-requests",
            {
                "approval_id": dean_current[0]["id"],
                "decision": LeaveApproval.STATUS_APPROVED,
                "note": "Dean approved.",
            },
            format="json",
        )
        self.assertEqual(dean_decision.status_code, 200)
        self.assertEqual(dean_decision.json()["leave_request"]["status"], LeaveRequest.STATUS_APPROVED)

        self.client.force_authenticate(user=self.student.user)
        history = self.client.get("/student/leave/history")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["leave_requests"][0]["status"], LeaveRequest.STATUS_APPROVED)


class StudentElectionWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sci = School.objects.create(code="SCI", name="School of Computing")
        self.biz = School.objects.create(code="BUS", name="School of Business")
        self.sci_student = self._student("sci_voter", self.sci)
        self.biz_student = self._student("biz_voter", self.biz)

    def _student(self, username, school):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.school = school
        profile.student_id = username.upper()
        profile.save(update_fields=["school", "student_id", "updated_at"])
        return profile

    def _active_election(self, **overrides):
        school_seats = overrides.pop("school_seats", None) if "school_seats" in overrides else None
        payload = {
            "title": "SRC 2026",
            "election_type": Election.TYPE_SRC,
            "starts_at": timezone.now() - timezone.timedelta(hours=1),
            "ends_at": timezone.now() + timezone.timedelta(hours=1),
            "general_selection_count": 2,
            "school_selection_count": 0,
            "status": Election.STATUS_UPCOMING,
            "is_active": True,
        }
        payload.update(overrides)
        election = Election.objects.create(**payload)
        if election.election_type == Election.TYPE_SRC:
            seats = school_seats or [(self.sci, 1)]
            for school, count in seats:
                SchoolElectionSeat.objects.create(election=election, school=school, seat_count=count)
        return election

    def _candidate(self, election, name, category, school=None):
        return ElectionCandidate.objects.create(
            election=election,
            display_name=name,
            student_identifier=name.upper().replace(" ", "-"),
            category=category,
            school=school,
            status=ElectionCandidate.STATUS_APPROVED,
        )

    def test_src_voting_uses_separate_exact_count_ballots(self):
        election = self._active_election()
        general_one = self._candidate(election, "General One", ElectionCandidate.CATEGORY_GENERAL)
        general_two = self._candidate(election, "General Two", ElectionCandidate.CATEGORY_GENERAL)
        self._candidate(election, "General Three", ElectionCandidate.CATEGORY_GENERAL)
        school_candidate = self._candidate(election, "SCI Candidate", ElectionCandidate.CATEGORY_SCHOOL, self.sci)

        self.client.force_authenticate(user=self.sci_student.user)
        too_few = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_GENERAL, "candidate_ids": [general_one.id]},
            format="json",
        )
        self.assertEqual(too_few.status_code, 400)
        self.assertIn("Select exactly 2", too_few.json()["detail"])

        general_vote = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_GENERAL, "candidate_ids": [general_one.id, general_two.id]},
            format="json",
        )
        self.assertEqual(general_vote.status_code, 201, general_vote.json())

        duplicate_general = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_GENERAL, "candidate_ids": [general_one.id, general_two.id]},
            format="json",
        )
        self.assertEqual(duplicate_general.status_code, 409)

        school_vote = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_SCHOOL, "candidate_ids": [school_candidate.id]},
            format="json",
        )
        self.assertEqual(school_vote.status_code, 201, school_vote.json())
        self.assertEqual(Vote.objects.filter(election=election, student=self.sci_student).count(), 3)

        results = self.client.get("/student/elections")
        self.assertEqual(results.status_code, 200)
        groups = results.json()["elections"][0]["results"]
        general_group = next(group for group in groups if group["category"] == ElectionCandidate.CATEGORY_GENERAL)
        self.assertEqual(general_group["total_votes"], 2)

    def test_school_committee_is_visible_only_to_matching_school_students(self):
        election = self._active_election(
            title="SCI Committee 2026",
            election_type=Election.TYPE_SCHOOL_COMMITTEE,
            school=self.sci,
            general_selection_count=0,
            school_selection_count=1,
        )
        candidate = self._candidate(election, "SCI Committee Candidate", ElectionCandidate.CATEGORY_SCHOOL, self.sci)

        self.client.force_authenticate(user=self.biz_student.user)
        business_view = self.client.get("/student/elections")
        self.assertEqual(business_view.status_code, 200)
        self.assertEqual(business_view.json()["elections"], [])
        blocked_vote = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_SCHOOL, "candidate_ids": [candidate.id]},
            format="json",
        )
        self.assertEqual(blocked_vote.status_code, 403)

        self.client.force_authenticate(user=self.sci_student.user)
        science_view = self.client.get("/student/elections")
        self.assertEqual(science_view.status_code, 200)
        self.assertEqual(science_view.json()["elections"][0]["id"], election.id)
        accepted_vote = self.client.post(
            f"/student/elections/{election.id}/vote",
            {"category": ElectionCandidate.CATEGORY_SCHOOL, "candidate_ids": [candidate.id]},
            format="json",
        )
        self.assertEqual(accepted_vote.status_code, 201, accepted_vote.json())

    def test_published_election_results_notify_eligible_students(self):
        election = self._active_election()
        admin = User.objects.create_superuser(
            username="election_admin",
            email="election-admin@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=admin)
        admin_response = self.client.post(
            "/admin/elections/results",
            {"election": election.id},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 404)

        technician = User.objects.create_user(username="election_technician", password="pass")
        technician.profile.role = Profile.ROLE_TECHNICIAN
        technician.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=technician)

        response = self.client.post(
            "/ict-helpdesk/technician/elections/results",
            {"election": election.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.json())
        for student in (self.sci_student, self.biz_student):
            self.assertTrue(
                student.notifications.filter(
                    data__event_type="elections.results_published",
                    data__election_id=election.id,
                ).exists()
            )

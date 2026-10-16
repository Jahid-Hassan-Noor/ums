from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from admin_app.models import (
    Course,
    CourseLabGroup,
    CourseOffering,
    CourseTutorialGroup,
    Profile,
    School,
    Semester,
)
from applicant_app.models import Applicant
from student_app.models import Enrollment
from teacher_app.models import (
    Assignment,
    AssignmentComment,
    AssignmentFeedback,
    AssignmentGroup,
    AssignmentGroupInvitation,
    AssignmentGroupMembership,
    AssignmentRubric,
    AssignmentSubmission,
    CourseActivity,
    CourseAnnouncement,
    CourseAnnouncementSlot,
    CourseAnnouncementSlotSelection,
    CourseResource,
    CourseResourceFolder,
    CourseSection,
)
from teacher_app.assignment_service import can_submit_assignment, validate_submission_files


User = get_user_model()


class LearningManagementPortalApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code="SCS", name="School of Computer Science")
        self.semester = Semester.objects.create(
            name="Semester 1, Session 2026/2027",
            academic_session="2026/2027",
            start_date="2026-10-26",
            end_date="2027-02-26",
            is_active=True,
        )
        self.course = Course.objects.create(
            code="CCS4443",
            title="Software Studio",
            credits=3,
            school=self.school,
            has_lab=True,
        )
        self.teacher = self._profile("lms_teacher", Profile.ROLE_TEACHER)
        self.student = self._profile("lms_student", Profile.ROLE_STUDENT)
        self.offering = CourseOffering.objects.create(
            course=self.course,
            semester=self.semester,
            instructor=self.teacher,
            section="A1",
            capacity=30,
        )
        Enrollment.objects.create(student=self.student, offering=self.offering, created_by=self.teacher)

    def _profile(self, username, role):
        user = User.objects.create_user(username=username, password="pass")
        profile = user.profile
        profile.role = role
        profile.school = self.school
        profile.save(update_fields=["role", "school", "updated_at"])
        return profile

    def test_teacher_builds_course_content_and_student_receives_published_workspace(self):
        self.client.force_authenticate(user=self.teacher.user)

        assessment_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "update_assessment",
                "has_final_exam": "false",
                "coursework_percentage": "100",
                "final_exam_percentage": "0",
                "assessment_overview": "Assessment is based on studio coursework and project delivery.",
                "study_guide": SimpleUploadedFile(
                    "study-guide.pdf",
                    b"%PDF-1.4 study guide",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(assessment_response.status_code, 200, assessment_response.json())
        self.assertFalse(assessment_response.json()["assessment"]["has_final_exam"])

        section_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_section",
                "title": "Week 1",
                "summary": "Orientation and setup",
                "section_type": "topic",
                "week_number": 1,
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(section_response.status_code, 201, section_response.json())
        section_id = section_response.json()["section"]["id"]

        folder_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_folder",
                "title": "Lecture slides",
                "description": "Weekly presentation files",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(folder_response.status_code, 201, folder_response.json())
        folder_id = folder_response.json()["folder"]["id"]

        resource_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_resource",
                "section_id": section_id,
                "folder_id": folder_id,
                "title": "Studio brief",
                "description": "Read before the first class",
                "file": SimpleUploadedFile("brief.pdf", b"brief", content_type="application/pdf"),
                "is_published": True,
            },
            format="multipart",
        )
        self.assertEqual(resource_response.status_code, 201, resource_response.json())

        announcement_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_announcement",
                "title": "Welcome",
                "body": "The course workspace is ready.",
                "announcement_type": "general",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(announcement_response.status_code, 201, announcement_response.json())

        activity_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_activity",
                "section_id": section_id,
                "resource_id": resource_response.json()["resource"]["id"],
                "title": "Read the studio brief",
                "activity_type": "resource",
                "due_at": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
                "completion_policy": "view",
                "is_required": True,
            },
            format="json",
        )
        self.assertEqual(activity_response.status_code, 201, activity_response.json())

        self.client.force_authenticate(user=self.student.user)
        student_response = self.client.get(f"/student/courses/{self.offering.id}")
        self.assertEqual(student_response.status_code, 200, student_response.json())
        payload = student_response.json()
        self.assertEqual(payload["sections"][0]["title"], "Week 1")
        self.assertEqual(payload["folders"][0]["title"], "Lecture slides")
        self.assertEqual(payload["announcements"][0]["title"], "Welcome")
        self.assertEqual(payload["activities"][0]["title"], "Read the studio brief")
        self.assertFalse(payload["assessment"]["has_final_exam"])
        self.assertEqual(payload["assessment"]["coursework_percentage"], "100.00")
        self.assertIn("study-guide", payload["assessment"]["study_guide"])
        self.assertTrue(payload["assessment"]["study_guide"].endswith(".pdf"))

    def test_teacher_course_roster_returns_scoped_students_groups_and_attendance(self):
        tutorial_group = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="T01",
            capacity=30,
        )
        enrollment = Enrollment.objects.get(
            student=self.student,
            offering=self.offering,
        )
        enrollment.tutorial_group = tutorial_group
        enrollment.save(update_fields=["tutorial_group"])

        self.client.force_authenticate(user=self.teacher.user)
        response = self.client.get(f"/teacher/courses/{self.offering.id}/roster")

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["course"]["code"], self.course.code)
        self.assertEqual(response.json()["summary"]["students"], 1)
        self.assertEqual(response.json()["summary"]["tutorial_groups"], 1)
        self.assertEqual(response.json()["students"][0]["profile_id"], self.student.id)
        self.assertEqual(response.json()["students"][0]["tutorial_group"], "T01")
        self.assertEqual(response.json()["students"][0]["total_classes"], 0)

        other_teacher = self._profile("other_lms_teacher", Profile.ROLE_TEACHER)
        self.client.force_authenticate(user=other_teacher.user)
        forbidden = self.client.get(f"/teacher/courses/{self.offering.id}/roster")
        self.assertEqual(forbidden.status_code, 404)

    def test_teacher_clears_and_reuploads_study_guide(self):
        self.client.force_authenticate(user=self.teacher.user)

        upload_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "update_assessment",
                "has_final_exam": "true",
                "coursework_percentage": "60",
                "final_exam_percentage": "40",
                "assessment_overview": "Assessment is split between coursework and final exam.",
                "study_guide": SimpleUploadedFile(
                    "clear-flow-guide.pdf",
                    b"%PDF-1.4 first guide",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.json())
        self.assertIn("clear-flow-guide", upload_response.json()["assessment"]["study_guide"])

        clear_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "update_assessment",
                "has_final_exam": "true",
                "coursework_percentage": "60",
                "final_exam_percentage": "40",
                "assessment_overview": "Assessment is split between coursework and final exam.",
                "clear_study_guide": "true",
            },
            format="multipart",
        )
        self.assertEqual(clear_response.status_code, 200, clear_response.json())
        self.assertIsNone(clear_response.json()["assessment"]["study_guide"])
        self.assertEqual(clear_response.json()["assessment"]["study_guide_name"], "")
        self.offering.refresh_from_db()
        self.assertFalse(self.offering.study_guide)

        reupload_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "update_assessment",
                "has_final_exam": "true",
                "coursework_percentage": "60",
                "final_exam_percentage": "40",
                "assessment_overview": "Assessment is split between coursework and final exam.",
                "study_guide": SimpleUploadedFile(
                    "replacement-clear-flow-guide.pdf",
                    b"%PDF-1.4 replacement guide",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(reupload_response.status_code, 200, reupload_response.json())
        self.assertIn("replacement-clear-flow-guide", reupload_response.json()["assessment"]["study_guide"])

    def test_assignment_rubric_comment_submission_and_feedback_flow(self):
        self.client.force_authenticate(user=self.teacher.user)
        due_at = timezone.now() + timezone.timedelta(days=4)
        create_response = self.client.post(
            "/teacher/assignments/create",
            {
                "offering_id": self.offering.id,
                "title": "Prototype review",
                "description": "Submit the first prototype.",
                "instructions": "Upload a PDF report.",
                "due_date": due_at.isoformat(),
                "max_score": 100,
                "submission_type": "both",
                "accepted_file_types": ["pdf", "doc"],
                "max_files": 2,
                "max_file_size_mb": 5,
                "allow_late_submissions": True,
                "status": "published",
                "rubric_title": "Prototype rubric",
                "rubric_criteria": [
                    {"title": "Design", "max_score": 40},
                    {"title": "Implementation", "max_score": 60},
                ],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.json())
        assignment_id = create_response.json()["assignment"]["id"]
        assignment = Assignment.objects.get(pk=assignment_id)
        self.assertEqual(assignment.accepted_file_types, ["pdf", "doc"])
        self.assertEqual(assignment.max_files, 2)
        self.assertEqual(assignment.max_file_size_mb, 5)
        self.assertTrue(assignment.allow_late_submissions)
        self.assertTrue(AssignmentRubric.objects.filter(assignment_id=assignment_id).exists())
        self.assertTrue(CourseActivity.objects.filter(assignment_id=assignment_id, due_at=due_at).exists())

        self.client.force_authenticate(user=self.student.user)
        comment_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {"body": "May I include an appendix?"},
            format="json",
        )
        self.assertEqual(comment_response.status_code, 201, comment_response.json())

        submit_response = self.client.post(
            f"/student/assignments/{assignment_id}/submit",
            {
                "content": "Prototype summary",
                "files": SimpleUploadedFile("prototype.pdf", b"prototype", content_type="application/pdf"),
            },
            format="multipart",
        )
        self.assertEqual(submit_response.status_code, 201, submit_response.json())
        submission_id = submit_response.json()["submission"]["id"]

        self.client.force_authenticate(user=self.teacher.user)
        detail_response = self.client.get(f"/teacher/assignments/{assignment_id}")
        self.assertEqual(detail_response.status_code, 200, detail_response.json())
        self.assertEqual(detail_response.json()["comments"][0]["body"], "May I include an appendix?")
        attachment_name = detail_response.json()["submissions"][0]["attachments"][0]["name"]
        self.assertTrue(attachment_name.startswith("prototype"))
        self.assertTrue(attachment_name.endswith(".pdf"))

        grade_response = self.client.post(
            f"/teacher/assignments/{assignment_id}",
            {
                "action": "grade_submission",
                "submission_id": submission_id,
                "grade": 88,
                "feedback": "Strong prototype. Tighten the final explanation.",
                "rubric_id": create_response.json()["rubric_id"],
                "rubric_scores": {"Design": 35, "Implementation": 53},
            },
            format="json",
        )
        self.assertEqual(grade_response.status_code, 200, grade_response.json())
        self.assertTrue(AssignmentFeedback.objects.filter(submission_id=submission_id).exists())

        self.client.force_authenticate(user=self.student.user)
        student_detail = self.client.get(f"/student/assignments/{assignment_id}")
        self.assertEqual(student_detail.status_code, 200, student_detail.json())
        self.assertEqual(student_detail.json()["submission"]["grade"], "88.00")
        self.assertEqual(
            student_detail.json()["submission"]["feedback"],
            "Strong prototype. Tighten the final explanation.",
        )
        self.assertEqual(student_detail.json()["rubrics"][0]["title"], "Prototype rubric")

        self.assertEqual(CourseSection.objects.count(), 0)
        self.assertEqual(CourseResourceFolder.objects.count(), 0)
        self.assertEqual(CourseResource.objects.count(), 0)
        self.assertEqual(CourseAnnouncement.objects.count(), 0)
        self.assertEqual(Assignment.objects.count(), 1)
        self.assertEqual(AssignmentSubmission.objects.count(), 1)
        self.assertEqual(AssignmentComment.objects.count(), 1)

    def test_course_presentation_slots_are_scoped_capacity_limited_and_selectable(self):
        second_student = self._profile("lms_student_two", Profile.ROLE_STUDENT)
        outsider = self._profile("lms_student_outside_course", Profile.ROLE_STUDENT)
        Enrollment.objects.create(student=second_student, offering=self.offering, created_by=self.teacher)
        starts_at = timezone.now() + timezone.timedelta(days=3)

        self.client.force_authenticate(user=self.teacher.user)
        create_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_announcement",
                "title": "Project presentations",
                "body": "Select one presentation slot.",
                "announcement_type": "presentation",
                "is_published": True,
                "slots": [
                    {
                        "label": "Morning individual slot",
                        "starts_at": starts_at.isoformat(),
                        "ends_at": (starts_at + timezone.timedelta(minutes=15)).isoformat(),
                        "capacity": 1,
                        "selection_type": "individual",
                    },
                    {
                        "label": "Afternoon group slot",
                        "starts_at": (starts_at + timezone.timedelta(hours=4)).isoformat(),
                        "ends_at": (starts_at + timezone.timedelta(hours=4, minutes=30)).isoformat(),
                        "capacity": 2,
                        "selection_type": "group",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.json())
        announcement_id = create_response.json()["announcement"]["id"]
        slots = create_response.json()["announcement"]["slots"]
        self.assertEqual(len(slots), 2)
        self.assertEqual(CourseAnnouncementSlot.objects.filter(announcement_id=announcement_id).count(), 2)

        self.client.force_authenticate(user=self.student.user)
        course_response = self.client.get(f"/student/courses/{self.offering.id}")
        self.assertEqual(course_response.status_code, 200, course_response.json())
        announcement = next(
            row for row in course_response.json()["announcements"]
            if row["id"] == announcement_id
        )
        individual_slot = next(slot for slot in announcement["slots"] if slot["selection_type"] == "individual")
        group_slot = next(slot for slot in announcement["slots"] if slot["selection_type"] == "group")

        self.client.force_authenticate(user=outsider.user)
        outside_course_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement_id,
                "slot_id": individual_slot["id"],
            },
            format="json",
        )
        self.assertEqual(outside_course_response.status_code, 404, outside_course_response.json())

        self.client.force_authenticate(user=self.student.user)
        select_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement_id,
                "slot_id": individual_slot["id"],
            },
            format="json",
        )
        self.assertEqual(select_response.status_code, 200, select_response.json())
        self.assertTrue(
            CourseAnnouncementSlotSelection.objects.filter(
                announcement_id=announcement_id,
                student=self.student,
                slot_id=individual_slot["id"],
            ).exists()
        )

        self.client.force_authenticate(user=second_student.user)
        full_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement_id,
                "slot_id": individual_slot["id"],
            },
            format="json",
        )
        self.assertEqual(full_response.status_code, 400, full_response.json())

        missing_group_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement_id,
                "slot_id": group_slot["id"],
            },
            format="json",
        )
        self.assertEqual(missing_group_response.status_code, 400, missing_group_response.json())

        group_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement_id,
                "slot_id": group_slot["id"],
                "group_name": "Team Aurora",
            },
            format="json",
        )
        self.assertEqual(group_response.status_code, 200, group_response.json())
        self.assertEqual(
            CourseAnnouncementSlotSelection.objects.get(
                announcement_id=announcement_id,
                student=second_student,
            ).group_name,
            "Team Aurora",
        )

        cancel_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "cancel_slot",
                "announcement_id": announcement_id,
            },
            format="json",
        )
        self.assertEqual(cancel_response.status_code, 200, cancel_response.json())
        self.assertFalse(
            CourseAnnouncementSlotSelection.objects.filter(
                announcement_id=announcement_id,
                student=second_student,
            ).exists()
        )

    def test_group_project_rules_leader_submission_and_presentation_selection(self):
        teammate = self._profile("lms_group_teammate", Profile.ROLE_STUDENT)
        same_tutorial_student = self._profile("lms_group_same_tutorial", Profile.ROLE_STUDENT)
        other_tutorial_student = self._profile("lms_group_other_tutorial", Profile.ROLE_STUDENT)
        teammate_enrollment = Enrollment.objects.create(
            student=teammate,
            offering=self.offering,
            created_by=self.teacher,
        )
        same_tutorial_enrollment = Enrollment.objects.create(
            student=same_tutorial_student,
            offering=self.offering,
            created_by=self.teacher,
        )
        other_tutorial_enrollment = Enrollment.objects.create(
            student=other_tutorial_student,
            offering=self.offering,
            created_by=self.teacher,
        )
        leader_enrollment = Enrollment.objects.get(student=self.student, offering=self.offering)

        tutorial_a = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="T01",
            capacity=20,
        )
        lab_a = CourseLabGroup.objects.create(
            tutorial_group=tutorial_a,
            code="L01",
            capacity=20,
        )
        tutorial_b = CourseTutorialGroup.objects.create(
            offering=self.offering,
            code="T02",
            capacity=20,
        )
        lab_b = CourseLabGroup.objects.create(
            tutorial_group=tutorial_b,
            code="L02",
            capacity=20,
        )
        leader_enrollment.tutorial_group = tutorial_a
        leader_enrollment.lab_group = lab_a
        leader_enrollment.save(update_fields=["tutorial_group", "lab_group"])
        teammate_enrollment.tutorial_group = tutorial_a
        teammate_enrollment.lab_group = lab_a
        teammate_enrollment.save(update_fields=["tutorial_group", "lab_group"])
        same_tutorial_enrollment.tutorial_group = tutorial_a
        same_tutorial_enrollment.lab_group = lab_a
        same_tutorial_enrollment.save(update_fields=["tutorial_group", "lab_group"])
        other_tutorial_enrollment.tutorial_group = tutorial_b
        other_tutorial_enrollment.lab_group = lab_b
        other_tutorial_enrollment.save(update_fields=["tutorial_group", "lab_group"])

        Applicant.objects.create(
            profile=self.student,
            nationality="Nigeria",
            country_of_residence="Nigeria",
        )
        Applicant.objects.create(
            profile=teammate,
            nationality="Malaysia",
            country_of_residence="Malaysia",
        )

        self.client.force_authenticate(user=self.teacher.user)
        assignment_response = self.client.post(
            "/teacher/assignments/create",
            {
                "offering_id": self.offering.id,
                "title": "International studio project",
                "description": "Build and present the final course project.",
                "due_date": (timezone.now() + timezone.timedelta(days=7)).isoformat(),
                "submission_type": "text",
                "accepted_file_types": ["pdf"],
                "collaboration_mode": "group",
                "max_group_members": 2,
                "require_same_tutorial_group": True,
                "require_same_lab_group": True,
                "min_distinct_countries": 2,
                "group_rules": "Document how the team divided the work.",
                "status": "published",
            },
            format="json",
        )
        self.assertEqual(assignment_response.status_code, 201, assignment_response.json())
        assignment_id = assignment_response.json()["assignment"]["id"]

        self.client.force_authenticate(user=self.student.user)
        create_group_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {"action": "create_group", "name": "Team Atlas"},
            format="json",
        )
        self.assertEqual(create_group_response.status_code, 200, create_group_response.json())
        group = AssignmentGroup.objects.get(assignment_id=assignment_id)
        self.assertEqual(group.leader, self.student)
        self.assertTrue(
            AssignmentGroupMembership.objects.filter(
                assignment_id=assignment_id,
                group=group,
                student=self.student,
            ).exists()
        )

        incomplete_group_submission = self.client.post(
            f"/student/assignments/{assignment_id}/submit",
            {"content": "Not ready yet."},
            format="json",
        )
        self.assertEqual(incomplete_group_submission.status_code, 400, incomplete_group_submission.json())

        invalid_tutorial_invitation = self.client.post(
            f"/student/assignments/{assignment_id}",
            {
                "action": "invite_member",
                "student_id": other_tutorial_student.id,
            },
            format="json",
        )
        self.assertEqual(invalid_tutorial_invitation.status_code, 400, invalid_tutorial_invitation.json())

        invite_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {
                "action": "invite_member",
                "student_id": teammate.id,
            },
            format="json",
        )
        self.assertEqual(invite_response.status_code, 200, invite_response.json())
        invitation = AssignmentGroupInvitation.objects.get(
            assignment_id=assignment_id,
            invitee=teammate,
        )

        self.client.force_authenticate(user=teammate.user)
        accept_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {
                "action": "accept_invitation",
                "invitation_id": invitation.id,
            },
            format="json",
        )
        self.assertEqual(accept_response.status_code, 200, accept_response.json())
        self.assertEqual(accept_response.json()["group_workspace"]["current_group"]["rule_status"]["country_count"], 2)
        self.assertTrue(accept_response.json()["group_workspace"]["current_group"]["rule_status"]["is_ready"])

        duplicate_group_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {"action": "create_group", "name": "Team Duplicate"},
            format="json",
        )
        self.assertEqual(duplicate_group_response.status_code, 400, duplicate_group_response.json())

        non_leader_submission = self.client.post(
            f"/student/assignments/{assignment_id}/submit",
            {"content": "A teammate must not submit."},
            format="json",
        )
        self.assertEqual(non_leader_submission.status_code, 403, non_leader_submission.json())

        self.client.force_authenticate(user=self.student.user)
        capacity_response = self.client.post(
            f"/student/assignments/{assignment_id}",
            {
                "action": "invite_member",
                "student_id": same_tutorial_student.id,
            },
            format="json",
        )
        self.assertEqual(capacity_response.status_code, 400, capacity_response.json())

        leader_submission = self.client.post(
            f"/student/assignments/{assignment_id}/submit",
            {"content": "Final work submitted for Team Atlas."},
            format="json",
        )
        self.assertEqual(leader_submission.status_code, 201, leader_submission.json())
        submission = AssignmentSubmission.objects.get(assignment_id=assignment_id)
        self.assertEqual(submission.student, self.student)
        self.assertEqual(submission.assignment_group, group)

        starts_at = timezone.now() + timezone.timedelta(days=5)
        self.client.force_authenticate(user=self.teacher.user)
        announcement_response = self.client.post(
            f"/teacher/courses/{self.offering.id}/resources",
            {
                "action": "create_announcement",
                "assignment_id": assignment_id,
                "title": "International studio presentations",
                "body": "The group leader must choose one slot.",
                "announcement_type": "presentation",
                "is_published": True,
                "slots": [
                    {
                        "label": "Studio presentation slot",
                        "starts_at": starts_at.isoformat(),
                        "ends_at": (starts_at + timezone.timedelta(minutes=20)).isoformat(),
                        "capacity": 2,
                        "selection_type": "group",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(announcement_response.status_code, 201, announcement_response.json())
        announcement = announcement_response.json()["announcement"]
        slot_id = announcement["slots"][0]["id"]

        self.client.force_authenticate(user=teammate.user)
        teammate_slot_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement["id"],
                "slot_id": slot_id,
            },
            format="json",
        )
        self.assertEqual(teammate_slot_response.status_code, 400, teammate_slot_response.json())

        self.client.force_authenticate(user=self.student.user)
        leader_slot_response = self.client.post(
            f"/student/courses/{self.offering.id}",
            {
                "action": "select_slot",
                "announcement_id": announcement["id"],
                "slot_id": slot_id,
            },
            format="json",
        )
        self.assertEqual(leader_slot_response.status_code, 200, leader_slot_response.json())
        selection = CourseAnnouncementSlotSelection.objects.get(announcement_id=announcement["id"])
        self.assertEqual(selection.student, self.student)
        self.assertEqual(selection.assignment_group, group)
        self.assertEqual(selection.group_name, "Team Atlas")

        self.client.force_authenticate(user=self.teacher.user)
        teacher_detail = self.client.get(f"/teacher/assignments/{assignment_id}")
        self.assertEqual(teacher_detail.status_code, 200, teacher_detail.json())
        self.assertEqual(teacher_detail.json()["groups"][0]["name"], "Team Atlas")
        self.assertTrue(teacher_detail.json()["groups"][0]["rule_status"]["is_ready"])

    def test_group_leader_can_remove_members_and_delete_the_group(self):
        teammate = self._profile("lms_removable_teammate", Profile.ROLE_STUDENT)
        Enrollment.objects.create(student=teammate, offering=self.offering, created_by=self.teacher)
        assignment = Assignment.objects.create(
            offering=self.offering,
            title="Removable project group",
            collaboration_mode=Assignment.COLLABORATION_GROUP,
            max_group_members=3,
            submission_type=Assignment.SUBMISSION_TEXT,
            accepted_file_types=[Assignment.FILE_PDF],
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )

        self.client.force_authenticate(user=self.student.user)
        create_response = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "create_group", "name": "Team Cleanup"},
            format="json",
        )
        self.assertEqual(create_response.status_code, 200, create_response.json())
        group = AssignmentGroup.objects.get(assignment=assignment)

        invite_response = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "invite_member", "student_id": teammate.id},
            format="json",
        )
        self.assertEqual(invite_response.status_code, 200, invite_response.json())
        invitation = AssignmentGroupInvitation.objects.get(group=group, invitee=teammate)

        self.client.force_authenticate(user=teammate.user)
        accept_response = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "accept_invitation", "invitation_id": invitation.id},
            format="json",
        )
        self.assertEqual(accept_response.status_code, 200, accept_response.json())

        non_leader_delete = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "delete_group"},
            format="json",
        )
        self.assertEqual(non_leader_delete.status_code, 400, non_leader_delete.json())

        non_leader_remove = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "remove_member", "student_id": self.student.id},
            format="json",
        )
        self.assertEqual(non_leader_remove.status_code, 400, non_leader_remove.json())

        self.client.force_authenticate(user=self.student.user)
        remove_response = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "remove_member", "student_id": teammate.id},
            format="json",
        )
        self.assertEqual(remove_response.status_code, 200, remove_response.json())
        self.assertFalse(
            AssignmentGroupMembership.objects.filter(group=group, student=teammate).exists()
        )

        delete_response = self.client.post(
            f"/student/assignments/{assignment.id}",
            {"action": "delete_group"},
            format="json",
        )
        self.assertEqual(delete_response.status_code, 200, delete_response.json())
        self.assertFalse(AssignmentGroup.objects.filter(pk=group.pk).exists())
        self.assertFalse(AssignmentGroupMembership.objects.filter(group_id=group.pk).exists())

    def test_lab_activity_requires_lab_section_and_enforces_format_count_size_and_late_rules(self):
        lab_section = CourseSection.objects.create(
            offering=self.offering,
            title="Lab 1",
            section_type=CourseSection.TYPE_LAB_WORK,
            is_published=True,
        )
        assignment = Assignment.objects.create(
            offering=self.offering,
            section=lab_section,
            activity_kind=Assignment.ACTIVITY_LAB,
            title="Database lab",
            due_date=timezone.now() - timezone.timedelta(hours=1),
            submission_type=Assignment.SUBMISSION_FILE,
            accepted_file_type=Assignment.FILE_ZIP,
            accepted_file_types=[Assignment.FILE_ZIP, Assignment.FILE_PDF],
            max_files=2,
            max_file_size_mb=1,
            allow_late_submissions=True,
            status=Assignment.STATUS_PUBLISHED,
            created_by=self.teacher,
        )

        valid_zip = SimpleUploadedFile("source.zip", b"zip", content_type="application/zip")
        valid_pdf = SimpleUploadedFile("report.pdf", b"pdf", content_type="application/pdf")
        invalid_doc = SimpleUploadedFile("notes.docx", b"doc", content_type="application/octet-stream")
        oversized_pdf = SimpleUploadedFile(
            "large.pdf",
            b"x" * (1024 * 1024 + 1),
            content_type="application/pdf",
        )

        self.assertIsNone(validate_submission_files(assignment, [valid_zip, valid_pdf]))
        self.assertIn("up to 2 file", validate_submission_files(assignment, [valid_zip, valid_pdf, valid_pdf]))
        self.assertIn("not allowed", validate_submission_files(assignment, [invalid_doc]))
        self.assertIn("1 MB per-file limit", validate_submission_files(assignment, [oversized_pdf]))
        self.assertIsNone(can_submit_assignment(assignment))

        assignment.allow_late_submissions = False
        assignment.save(update_fields=["allow_late_submissions"])
        self.assertIn("Late submissions are not allowed", can_submit_assignment(assignment))

        self.client.force_authenticate(user=self.teacher.user)
        response = self.client.get("/teacher/assignments/create")
        lab_option = next(
            offering
            for offering in response.json()["offerings"]
            if offering["id"] == self.offering.id
        )
        self.assertEqual(lab_option["sections"][0]["section_type"], "lab_work")
        self.assertIn(
            {"value": "lab_activity", "label": "Lab activity"},
            response.json()["activity_types"],
        )
        create_response = self.client.post(
            "/teacher/assignments/create",
            {
                "offering_id": self.offering.id,
                "section_id": lab_section.id,
                "activity_kind": "lab_activity",
                "title": "API lab activity",
                "due_date": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
                "submission_type": "file",
                "accepted_file_types": ["zip", "pdf"],
                "max_files": 2,
                "max_file_size_mb": 8,
                "allow_late_submissions": False,
                "status": "published",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.json())
        self.assertEqual(create_response.json()["assignment"]["activity_kind"], "lab_activity")
        self.assertEqual(create_response.json()["assignment"]["accepted_file_types"], ["zip", "pdf"])
        self.assertEqual(create_response.json()["assignment"]["max_file_size_mb"], 8)

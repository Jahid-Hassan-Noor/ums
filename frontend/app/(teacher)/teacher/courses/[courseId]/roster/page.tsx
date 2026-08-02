import { PlannedWorkflowPage } from "@/components/role-zone/planned-workflow-page"

export default function TeacherCourseRosterPage() {
  return (
    <PlannedWorkflowPage
      role="teacher"
      title="Course Roster"
      description="Placeholder for enrolled students, groups, attendance status, and exports."
      path="/teacher/courses/[courseId]/roster"
    />
  )
}

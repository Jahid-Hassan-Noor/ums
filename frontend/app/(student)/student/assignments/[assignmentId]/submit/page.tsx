import { StudentAssignmentSubmitPage } from "@/components/student/student-assignments-page"

export default async function StudentAssignmentSubmitRoute({
  params,
}: {
  params: Promise<{ assignmentId: string }>
}) {
  const { assignmentId } = await params
  return <StudentAssignmentSubmitPage assignmentId={assignmentId} />
}

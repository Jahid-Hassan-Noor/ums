import { StudentAssignmentDetailPage } from "@/components/student/student-assignments-page"

export default async function StudentAssignmentDetailRoute({
  params,
}: {
  params: Promise<{ assignmentId: string }>
}) {
  const { assignmentId } = await params
  return <StudentAssignmentDetailPage assignmentId={assignmentId} />
}

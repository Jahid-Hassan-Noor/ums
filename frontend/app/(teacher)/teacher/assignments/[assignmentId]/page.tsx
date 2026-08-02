import { TeacherAssignmentDetailPage } from "@/components/teacher/teacher-assignments-page"

export default async function Page({ params }: { params: Promise<{ assignmentId: string }> }) {
  const { assignmentId } = await params
  return <TeacherAssignmentDetailPage assignmentId={assignmentId} />
}

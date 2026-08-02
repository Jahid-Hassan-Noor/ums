import { AdminManageStudentDetailPage } from "@/components/admin/admin-manage-student-detail-page"

export default async function AdminManageStudentDetailRoute({
  params,
}: {
  params: Promise<{ studentId: string }>
}) {
  const { studentId } = await params
  return <AdminManageStudentDetailPage studentId={studentId} />
}

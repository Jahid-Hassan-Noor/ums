import { AdminManageStaffDetailPage } from "@/components/admin/admin-manage-staff-detail-page"

export default async function AdminManageTeacherDetailRoute({
  params,
}: {
  params: Promise<{ teacherId: string }>
}) {
  const { teacherId } = await params
  return <AdminManageStaffDetailPage kind="teachers" profileId={teacherId} />
}

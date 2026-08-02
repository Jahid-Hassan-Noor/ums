import { AdminManageStaffDetailPage } from "@/components/admin/admin-manage-staff-detail-page"

export default async function AdminManageExecutiveDetailRoute({
  params,
}: {
  params: Promise<{ executiveId: string }>
}) {
  const { executiveId } = await params
  return <AdminManageStaffDetailPage kind="executives" profileId={executiveId} />
}

import { AdminManageApplicantDetailPage } from "@/components/admin/admin-manage-applicant-detail-page"

export default async function AdminManageApplicantDetailRoute({
  params,
}: {
  params: Promise<{ applicantId: string }>
}) {
  const { applicantId } = await params
  return <AdminManageApplicantDetailPage applicantId={applicantId} />
}

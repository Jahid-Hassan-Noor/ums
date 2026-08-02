import { TeacherAssignmentCreatePage } from "@/components/teacher/teacher-assignments-page"

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ offering_id?: string }>
}) {
  const { offering_id = "" } = await searchParams
  return <TeacherAssignmentCreatePage offeringId={offering_id} />
}

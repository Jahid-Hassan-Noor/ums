import { TeacherCourseAttendancePage } from "@/components/teacher/teacher-attendance-page"

export default async function Page({
  params,
}: {
  params: Promise<{ courseId: string }>
}) {
  const { courseId } = await params
  return <TeacherCourseAttendancePage courseId={courseId} />
}

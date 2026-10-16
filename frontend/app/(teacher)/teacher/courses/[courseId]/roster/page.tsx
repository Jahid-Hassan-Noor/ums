import { TeacherCourseRosterPage } from "@/components/teacher/teacher-course-roster-page"

export default async function Page({
  params,
}: {
  params: Promise<{ courseId: string }>
}) {
  const { courseId } = await params
  return <TeacherCourseRosterPage courseId={courseId} />
}

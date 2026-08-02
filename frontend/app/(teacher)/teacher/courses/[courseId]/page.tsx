import { TeacherCourseWorkspacePage } from "@/components/teacher/teacher-courses-page"

export default async function Page({ params }: { params: Promise<{ courseId: string }> }) {
  const { courseId } = await params
  return <TeacherCourseWorkspacePage courseId={courseId} />
}

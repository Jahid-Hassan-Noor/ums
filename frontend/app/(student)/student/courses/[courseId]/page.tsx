import { StudentCourseDetailPage } from "@/components/student/student-course-detail-page"

export default async function Page({ params }: { params: Promise<{ courseId: string }> }) {
  const { courseId } = await params
  return <StudentCourseDetailPage courseId={courseId} />
}

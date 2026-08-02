import { TeacherQuizDetailPage } from "@/components/quiz/teacher-quizzes-page"

export default async function Page({ params }: { params: Promise<{ quizId: string }> }) {
  const { quizId } = await params
  return <TeacherQuizDetailPage quizId={quizId} />
}

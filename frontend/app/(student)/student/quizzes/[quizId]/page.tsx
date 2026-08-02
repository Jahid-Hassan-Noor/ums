import { StudentQuizDetailPage } from "@/components/quiz/student-quizzes-page"

export default async function Page({ params }: { params: Promise<{ quizId: string }> }) {
  const { quizId } = await params
  return <StudentQuizDetailPage quizId={quizId} />
}

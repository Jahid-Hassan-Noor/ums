"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  Loader2,
  Play,
  RefreshCw,
  Save,
  Send,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type QuizOffering = {
  id: number
  course_code: string
  course_title: string
  section: string
  semester: string
}

type QuizChoice = {
  id: number
  label: string
  text: string
}

type QuizQuestion = {
  id: number
  question_type: "multiple_choice" | "true_false" | "short_answer" | "fill_blank" | "numerical" | "matching" | "ordering" | "essay"
  question_type_label: string
  question_text: string
  choices: QuizChoice[]
  settings?: {
    prompts?: string[]
    answers?: string[]
    items?: string[]
  }
}

type QuestionResponse = {
  choice_ids?: number[]
  answer?: string
  matching?: Record<string, string>
  order?: string[]
}

type AttemptQuestion = {
  id: number
  slot_number: number
  max_mark: string
  response: QuestionResponse
  response_summary: string
  awarded_mark: string | null
  requires_manual_grading: boolean
  feedback: string
  right_answer_summary: string
  question: QuizQuestion
}

type QuizAttempt = {
  id: number
  quiz_id: number
  quiz_title: string
  attempt_number: number
  state: string
  state_label: string
  started_at: string | null
  due_at: string | null
  submitted_at: string | null
  score: string | null
  needs_manual_grading: boolean
  review_allowed: boolean
  questions?: AttemptQuestion[]
}

type QuizRecord = {
  id: number
  title: string
  description: string
  instructions: string
  status_label: string
  opens_at: string | null
  closes_at: string | null
  time_limit_minutes: number
  max_attempts: number
  total_marks: string
  pass_mark: string
  offering: QuizOffering
  student_attempts: QuizAttempt[]
  access: {
    can_start: boolean
    reason: string
    password_required: boolean
  }
}

type QuizListResponse = {
  quizzes: QuizRecord[]
}

type QuizDetailResponse = {
  quiz: QuizRecord
}

type AttemptResponse = {
  attempt: QuizAttempt
  message?: string
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not set"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not set"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function nativeSelectClass() {
  return "h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
}

function Notice({ error, success }: { error: string; success: string }) {
  if (!error && !success) return null
  return (
    <div
      className={`flex gap-2 rounded-lg border p-3 text-sm ${
        error ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"
      }`}
    >
      {error ? <AlertCircle className="mt-0.5 size-4" /> : <CheckCircle2 className="mt-0.5 size-4" />}
      {error || success}
    </div>
  )
}

function responseFromAttempt(attempt: QuizAttempt | null) {
  const responses: Record<number, QuestionResponse> = {}
  attempt?.questions?.forEach((question) => {
    responses[question.id] = question.response || {}
  })
  return responses
}

export function StudentQuizzesPage() {
  const [quizzes, setQuizzes] = useState<QuizRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadQuizzes = useCallback(async () => {
    const data = await apiFetch<QuizListResponse>("/quiz/student/quizzes")
    setQuizzes(data.quizzes)
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQuizzes()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load quizzes."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQuizzes])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/quizzes", title: "Quizzes" },
        ]}
      />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Quizzes</h1>
            <p className="text-sm text-muted-foreground">Open quizzes for your enrolled courses.</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => void loadQuizzes()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </div>
        <Notice error={error} success="" />
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading quizzes...
          </div>
        ) : (
          <div className="grid gap-3">
            {quizzes.map((quiz) => (
              <Card key={quiz.id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-lg">{quiz.title}</CardTitle>
                      <CardDescription>
                        {quiz.offering.course_code} {quiz.offering.section} - {quiz.offering.semester}
                      </CardDescription>
                    </div>
                    <Badge variant={quiz.access.can_start ? "default" : "secondary"}>
                      {quiz.access.reason || "Available"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-wrap items-center justify-between gap-3 text-sm">
                  <div className="flex flex-wrap gap-3 text-muted-foreground">
                    <span>Closes {formatDateTime(quiz.closes_at)}</span>
                    <span>{quiz.time_limit_minutes || "No"} min limit</span>
                    <span>{quiz.student_attempts.length}/{quiz.max_attempts || "unlimited"} attempts</span>
                    <span>{quiz.total_marks} marks</span>
                  </div>
                  <Button size="sm" render={<Link href={`/student/quizzes/${quiz.id}`} />}>
                    <ClipboardList className="size-4" />
                    Open
                  </Button>
                </CardContent>
              </Card>
            ))}
            {!quizzes.length && <p className="text-sm text-muted-foreground">No quizzes are currently available.</p>}
          </div>
        )}
      </main>
    </div>
  )
}

export function StudentQuizDetailPage({ quizId }: { quizId: string }) {
  const [quiz, setQuiz] = useState<QuizRecord | null>(null)
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null)
  const [responses, setResponses] = useState<Record<number, QuestionResponse>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const inProgressAttempt = useMemo(
    () => quiz?.student_attempts.find((item) => item.state === "in_progress") || null,
    [quiz],
  )

  const loadQuiz = useCallback(async () => {
    const data = await apiFetch<QuizDetailResponse>(`/quiz/student/quizzes/${quizId}`)
    setQuiz(data.quiz)
  }, [quizId])

  const loadAttempt = useCallback(async (attemptId: number, review = false) => {
    const data = await apiFetch<AttemptResponse>(`/quiz/student/attempts/${attemptId}${review ? "?review=1" : ""}`)
    setAttempt(data.attempt)
    setResponses(responseFromAttempt(data.attempt))
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQuiz()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load quiz."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQuiz])

  async function handleStart(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      const data = await apiFetch<AttemptResponse>(`/quiz/student/quizzes/${quizId}/start`, {
        method: "POST",
        body: JSON.stringify({ password }),
      })
      setAttempt(data.attempt)
      setResponses(responseFromAttempt(data.attempt))
      setSuccess("Attempt started.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to start quiz.")
    } finally {
      setSubmitting(false)
    }
  }

  function updateResponse(questionId: number, response: QuestionResponse) {
    setResponses((current) => ({ ...current, [questionId]: response }))
  }

  async function saveAnswer(question: AttemptQuestion) {
    if (!attempt) return
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      const data = await apiFetch<AttemptResponse>(`/quiz/student/attempts/${attempt.id}/answer`, {
        method: "POST",
        body: JSON.stringify({
          question_attempt_id: question.id,
          response: responses[question.id] || {},
        }),
      })
      setAttempt(data.attempt)
      setResponses(responseFromAttempt(data.attempt))
      setSuccess("Answer saved.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save answer.")
    } finally {
      setSubmitting(false)
    }
  }

  async function submitQuiz() {
    if (!attempt) return
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      const data = await apiFetch<AttemptResponse>(`/quiz/student/attempts/${attempt.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ responses }),
      })
      setAttempt(data.attempt)
      setResponses(responseFromAttempt(data.attempt))
      setSuccess("Quiz submitted.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit quiz.")
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-svh flex-col bg-muted/25">
        <Header breadcrumbItems={[{ href: "/student", title: "Student" }, { href: "/student/quizzes", title: "Quizzes" }]} />
        <main className="mx-auto flex w-full max-w-6xl flex-1 items-center gap-2 p-6 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading quiz...
        </main>
      </div>
    )
  }

  if (!quiz) {
    return (
      <div className="flex min-h-svh flex-col bg-muted/25">
        <Header breadcrumbItems={[{ href: "/student", title: "Student" }, { href: "/student/quizzes", title: "Quizzes" }]} />
        <main className="mx-auto w-full max-w-6xl flex-1 p-6">
          <Notice error={error || "Quiz not found."} success="" />
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/quizzes", title: "Quizzes" },
          { href: `/student/quizzes/${quiz.id}`, title: quiz.title },
        ]}
      />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 p-4 md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">{quiz.title}</h1>
            <p className="text-sm text-muted-foreground">
              {quiz.offering.course_code} {quiz.offering.section} - closes {formatDateTime(quiz.closes_at)}
            </p>
          </div>
          <Badge>{quiz.total_marks} marks</Badge>
        </div>

        <Notice error={error} success={success} />

        {!attempt && (
          <Card>
            <CardHeader>
              <CardTitle>Start quiz</CardTitle>
              <CardDescription>{quiz.instructions || quiz.description || "Complete the quiz within the available window."}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              {inProgressAttempt && (
                <Button onClick={() => void loadAttempt(inProgressAttempt.id)} className="w-fit">
                  <Play className="size-4" />
                  Resume attempt {inProgressAttempt.attempt_number}
                </Button>
              )}
              <form className="flex flex-wrap items-end gap-3" onSubmit={handleStart}>
                {quiz.access.password_required && (
                  <div className="grid gap-2">
                    <Label htmlFor="password">Password</Label>
                    <Input id="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                  </div>
                )}
                <Button type="submit" disabled={submitting || (!quiz.access.can_start && quiz.access.reason !== "Password required.")}>
                  {submitting ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
                  Start new attempt
                </Button>
              </form>
              <div className="grid gap-2 text-sm">
                {quiz.student_attempts.map((item) => (
                  <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-background p-3">
                    <span>
                      Attempt {item.attempt_number} - {item.state_label} - {item.score || "Pending"}
                    </span>
                    {item.review_allowed && (
                      <Button variant="outline" size="sm" onClick={() => void loadAttempt(item.id, true)}>
                        Review
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {attempt && (
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle>Attempt {attempt.attempt_number}</CardTitle>
                  <CardDescription>
                    {attempt.state_label} - Due {formatDateTime(attempt.due_at)}
                  </CardDescription>
                </div>
                <Badge variant={attempt.state === "in_progress" ? "default" : "secondary"}>
                  Score {attempt.score || "Pending"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4">
              {attempt.questions?.map((question) => (
                <div key={question.id} className="rounded-lg border bg-background p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="text-sm text-muted-foreground">Question {question.slot_number}</div>
                      <div className="font-medium">{question.question.question_text}</div>
                    </div>
                    <Badge variant="secondary">{question.max_mark} marks</Badge>
                  </div>
                  <QuestionInput
                    question={question}
                    disabled={attempt.state !== "in_progress"}
                    response={responses[question.id] || {}}
                    onChange={(response) => updateResponse(question.id, response)}
                  />
                  {attempt.state === "in_progress" ? (
                    <Button className="mt-3" variant="outline" size="sm" onClick={() => void saveAnswer(question)} disabled={submitting}>
                      <Save className="size-4" />
                      Save answer
                    </Button>
                  ) : (
                    <div className="mt-3 grid gap-1 text-sm text-muted-foreground">
                      <span>Your response: {question.response_summary || "No response"}</span>
                      {question.awarded_mark !== null && (
                        <span>
                          Mark: {question.awarded_mark} / {question.max_mark}
                        </span>
                      )}
                      {question.right_answer_summary && <span>Right answer: {question.right_answer_summary}</span>}
                      {question.feedback && <span>Feedback: {question.feedback}</span>}
                      {question.requires_manual_grading && <span>Manual grading pending.</span>}
                    </div>
                  )}
                </div>
              ))}
              {attempt.state === "in_progress" && (
                <Button className="w-fit" onClick={() => void submitQuiz()} disabled={submitting}>
                  {submitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Submit quiz
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}

function QuestionInput({
  question,
  response,
  disabled,
  onChange,
}: {
  question: AttemptQuestion
  response: QuestionResponse
  disabled: boolean
  onChange: (response: QuestionResponse) => void
}) {
  if (question.question.question_type === "multiple_choice") {
    const selected = new Set(response.choice_ids || [])
    return (
      <div className="mt-3 grid gap-2">
        {question.question.choices.map((choice) => (
          <label key={choice.id} className="flex items-center gap-2 rounded-md border p-2 text-sm">
            <input
              type="checkbox"
              checked={selected.has(choice.id)}
              disabled={disabled}
              onChange={(event) => {
                const next = new Set(selected)
                if (event.target.checked) next.add(choice.id)
                else next.delete(choice.id)
                onChange({ choice_ids: Array.from(next) })
              }}
            />
            <span className="font-medium">{choice.label}</span>
            <span>{choice.text}</span>
          </label>
        ))}
      </div>
    )
  }

  if (question.question.question_type === "true_false") {
    return (
      <div className="mt-3 grid gap-2">
        <Label htmlFor={`answer-${question.id}`}>Answer</Label>
        <select
          id={`answer-${question.id}`}
          className={nativeSelectClass()}
          value={response.answer || ""}
          disabled={disabled}
          onChange={(event) => onChange({ answer: event.target.value })}
        >
          <option value="">Select answer</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      </div>
    )
  }

  if (question.question.question_type === "matching") {
    const prompts = question.question.settings?.prompts || []
    const answers = question.question.settings?.answers || []
    const matching = response.matching || {}
    return (
      <div className="mt-3 grid gap-2">
        {prompts.map((prompt) => (
          <div key={prompt} className="grid gap-1 rounded-md border p-2">
            <Label htmlFor={`matching-${question.id}-${prompt}`}>{prompt}</Label>
            <select
              id={`matching-${question.id}-${prompt}`}
              className={nativeSelectClass()}
              value={matching[prompt] || ""}
              disabled={disabled}
              onChange={(event) =>
                onChange({
                  matching: {
                    ...matching,
                    [prompt]: event.target.value,
                  },
                })
              }
            >
              <option value="">Select match</option>
              {answers.map((answer) => (
                <option key={answer} value={answer}>
                  {answer}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    )
  }

  if (question.question.question_type === "ordering") {
    const items = question.question.settings?.items || []
    const order = response.order || items
    return (
      <div className="mt-3 grid gap-2">
        {items.map((item, index) => (
          <div key={`${item}-${index}`} className="grid gap-1 rounded-md border p-2">
            <Label htmlFor={`ordering-${question.id}-${index}`}>Position {index + 1}</Label>
            <select
              id={`ordering-${question.id}-${index}`}
              className={nativeSelectClass()}
              value={order[index] || ""}
              disabled={disabled}
              onChange={(event) => {
                const next = [...order]
                next[index] = event.target.value
                onChange({ order: next })
              }}
            >
              <option value="">Select item</option>
              {items.map((candidate) => (
                <option key={candidate} value={candidate}>
                  {candidate}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="mt-3 grid gap-2">
      <Label htmlFor={`answer-${question.id}`}>Answer</Label>
      <Textarea
        id={`answer-${question.id}`}
        value={response.answer || ""}
        disabled={disabled}
        rows={question.question.question_type === "essay" ? 6 : 2}
        onChange={(event) => onChange({ answer: event.target.value })}
      />
    </div>
  )
}

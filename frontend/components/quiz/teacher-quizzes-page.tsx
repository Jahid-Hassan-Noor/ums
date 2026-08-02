"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  Loader2,
  Plus,
  RefreshCw,
  Save,
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

type QuizQuestionChoice = {
  id: number
  label: string
  text: string
  is_correct?: boolean
}

type QuizQuestion = {
  id: number
  question_type: "multiple_choice" | "true_false" | "short_answer" | "fill_blank" | "numerical" | "matching" | "ordering" | "essay"
  question_type_label: string
  question_text: string
  choices: QuizQuestionChoice[]
  settings?: Record<string, unknown>
}

type QuizSlot = {
  id: number
  max_mark: string
  sort_order: number
  question_version: QuizQuestion
}

type QuizRandomRule = {
  id: number
  category: string
  question_type: string
  count: number
  max_mark: string
}

type QuizAttemptQuestion = {
  id: number
  slot_number: number
  max_mark: string
  response_summary: string
  awarded_mark: string | null
  requires_manual_grading: boolean
  feedback: string
  question: QuizQuestion
}

type QuizAttempt = {
  id: number
  student: string
  attempt_number: number
  state_label: string
  score: string | null
  needs_manual_grading: boolean
  submitted_at: string | null
  questions?: QuizAttemptQuestion[]
}

type QuizStatistics = {
  attempts_total: number
  attempts_submitted: number
  attempts_in_progress: number
  manual_pending: number
  average_score: string | null
  highest_score: string | null
  lowest_score: string | null
  questions: Array<{
    question_version_id: number
    question_text: string
    attempts: number
    answered: number
    manual_pending: number
    full_mark: number
    average_mark: string | null
    max_mark: string
  }>
}

type QuizRecord = {
  id: number
  title: string
  description: string
  instructions: string
  status: string
  status_label: string
  opens_at: string | null
  closes_at: string | null
  time_limit_minutes: number
  max_attempts: number
  total_marks: string
  pass_mark: string
  attempt_count: number
  password_required: boolean
  ip_allowlist?: string
  require_safe_exam_browser: boolean
  safe_exam_browser_config_key?: string
  offering: QuizOffering
  slots?: QuizSlot[]
  random_rules?: QuizRandomRule[]
  attempts?: QuizAttempt[]
  statistics?: QuizStatistics
}

type QuizOptions = {
  offerings: QuizOffering[]
  question_types: Array<{ value: QuizQuestion["question_type"]; label: string }>
  grade_methods: Array<{ value: string; label: string }>
}

type BankQuestionOption = {
  id: number
  version_id: number
  title: string
  question_type_label: string
  default_mark: string
}

type QuizListResponse = {
  options: QuizOptions
  quizzes: QuizRecord[]
}

type QuizDetailResponse = {
  quiz: QuizRecord
  options?: {
    question_bank_questions: BankQuestionOption[]
  }
}

const QUESTION_TYPES: QuizOptions["question_types"] = [
  { value: "multiple_choice", label: "Multiple choice" },
  { value: "true_false", label: "True/False" },
  { value: "short_answer", label: "Short answer" },
  { value: "fill_blank", label: "Fill in the blank" },
  { value: "numerical", label: "Numerical" },
  { value: "matching", label: "Matching" },
  { value: "ordering", label: "Ordering" },
  { value: "essay", label: "Essay" },
]

function nativeSelectClass() {
  return "h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
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

function choicesFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [label, text, correct] = line.split("|").map((part) => part.trim())
      return {
        label: label || String.fromCharCode(65 + index),
        text: text || label || `Choice ${index + 1}`,
        is_correct: ["1", "true", "yes", "correct"].includes((correct || "").toLowerCase()),
      }
    })
}

function matchingPairsFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [prompt, answer] = line.split("|").map((part) => part.trim())
      return { prompt: prompt || answer || "", answer: answer || "" }
    })
}

function orderedItemsFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
}

function questionPayload(form: HTMLFormElement) {
  const data = new FormData(form)
  const questionType = String(data.get("question_type") || "multiple_choice")
  return {
    title: String(data.get("question_title") || "Question"),
    question_type: questionType,
    question_text: String(data.get("question_text") || ""),
    correct_answer: String(data.get("correct_answer") || ""),
    max_mark: String(data.get("max_mark") || "1"),
    default_mark: String(data.get("max_mark") || "1"),
    choices: questionType === "multiple_choice" ? choicesFromText(String(data.get("choices") || "")) : [],
    tolerance: String(data.get("tolerance") || "0"),
    matching_pairs: matchingPairsFromText(String(data.get("matching_pairs") || "")),
    ordering_items: orderedItemsFromText(String(data.get("ordering_items") || "")),
  }
}

export function TeacherQuizzesPage() {
  const [quizzes, setQuizzes] = useState<QuizRecord[]>([])
  const [options, setOptions] = useState<QuizOptions>({ offerings: [], question_types: QUESTION_TYPES, grade_methods: [] })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadQuizzes = useCallback(async () => {
    const data = await apiFetch<QuizListResponse>("/quiz/teacher/quizzes")
    setQuizzes(data.quizzes)
    setOptions({
      offerings: data.options.offerings,
      question_types: data.options.question_types.length ? data.options.question_types : QUESTION_TYPES,
      grade_methods: data.options.grade_methods,
    })
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQuizzes()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load quizzes."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQuizzes])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    const form = event.currentTarget
    const data = new FormData(form)
    try {
      const payload = {
        offering_id: Number(data.get("offering_id")),
        title: String(data.get("title") || ""),
        description: String(data.get("description") || ""),
        instructions: String(data.get("instructions") || ""),
        status: String(data.get("status") || "draft"),
        opens_at: String(data.get("opens_at") || ""),
        closes_at: String(data.get("closes_at") || ""),
        time_limit_minutes: Number(data.get("time_limit_minutes") || 0),
        max_attempts: Number(data.get("max_attempts") || 1),
        password: String(data.get("password") || ""),
        ip_allowlist: String(data.get("ip_allowlist") || ""),
        require_safe_exam_browser: data.get("require_safe_exam_browser") === "on",
        safe_exam_browser_config_key: String(data.get("safe_exam_browser_config_key") || ""),
        pass_mark: String(data.get("pass_mark") || "0"),
        review_show_marks: true,
        review_show_feedback: true,
        questions: [questionPayload(form)],
      }
      await apiFetch<{ quiz: QuizRecord }>("/quiz/teacher/quizzes", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      form.reset()
      setSuccess("Quiz saved.")
      await loadQuizzes()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save quiz.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/quizzes", title: "Quizzes" },
        ]}
      />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Quizzes</h1>
            <p className="text-sm text-muted-foreground">Create online quizzes and review attempts.</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => void loadQuizzes()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </div>

        <Notice error={error} success={success} />

        <Card>
          <CardHeader>
            <CardTitle>Create quiz</CardTitle>
            <CardDescription>Start with one question, then add more from the quiz detail page.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleCreate}>
              <div className="grid gap-2">
                <Label htmlFor="offering_id">Course offering</Label>
                <select id="offering_id" name="offering_id" className={nativeSelectClass()} required>
                  <option value="">Select offering</option>
                  {options.offerings.map((offering) => (
                    <option key={offering.id} value={offering.id}>
                      {offering.course_code} {offering.section} - {offering.semester}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="title">Quiz title</Label>
                <Input id="title" name="title" required />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <select id="status" name="status" className={nativeSelectClass()} defaultValue="draft">
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="time_limit_minutes">Time limit minutes</Label>
                <Input id="time_limit_minutes" name="time_limit_minutes" type="number" min="0" defaultValue="30" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="opens_at">Opens at</Label>
                <Input id="opens_at" name="opens_at" type="datetime-local" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="closes_at">Closes at</Label>
                <Input id="closes_at" name="closes_at" type="datetime-local" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="max_attempts">Max attempts</Label>
                <Input id="max_attempts" name="max_attempts" type="number" min="0" defaultValue="1" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="pass_mark">Pass mark</Label>
                <Input id="pass_mark" name="pass_mark" type="number" min="0" step="0.01" defaultValue="0" />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" name="password" />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="ip_allowlist">Allowed IP addresses</Label>
                <Textarea id="ip_allowlist" name="ip_allowlist" rows={2} placeholder="10.0.0.0/24, 192.168.1.20" />
              </div>
              <label className="flex items-center gap-2 text-sm md:col-span-2">
                <input name="require_safe_exam_browser" type="checkbox" className="size-4 rounded border-input" />
                Require Safe Exam Browser
              </label>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="safe_exam_browser_config_key">Safe Exam Browser config key</Label>
                <Input id="safe_exam_browser_config_key" name="safe_exam_browser_config_key" />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="description">Description</Label>
                <Textarea id="description" name="description" rows={2} />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="instructions">Instructions</Label>
                <Textarea id="instructions" name="instructions" rows={2} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="question_type">First question type</Label>
                <select id="question_type" name="question_type" className={nativeSelectClass()} defaultValue="multiple_choice">
                  {options.question_types.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="max_mark">Question mark</Label>
                <Input id="max_mark" name="max_mark" type="number" min="0" step="0.01" defaultValue="1" />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="question_title">Question title</Label>
                <Input id="question_title" name="question_title" required />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="question_text">Question text</Label>
                <Textarea id="question_text" name="question_text" rows={2} required />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="choices">Choices</Label>
                <Textarea id="choices" name="choices" rows={4} placeholder={"A|First option|false\nB|Second option|true"} />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="correct_answer">Correct answer</Label>
                <Input id="correct_answer" name="correct_answer" placeholder="Use for true/false or short answer" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="tolerance">Numerical tolerance</Label>
                <Input id="tolerance" name="tolerance" type="number" min="0" step="0.01" defaultValue="0" />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="matching_pairs">Matching pairs</Label>
                <Textarea id="matching_pairs" name="matching_pairs" rows={3} placeholder={"Prompt|Answer\nAnother prompt|Another answer"} />
              </div>
              <div className="grid gap-2 md:col-span-2">
                <Label htmlFor="ordering_items">Ordering items</Label>
                <Textarea id="ordering_items" name="ordering_items" rows={3} placeholder={"First item\nSecond item\nThird item"} />
              </div>
              <div className="md:col-span-2">
                <Button type="submit" disabled={submitting}>
                  {submitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                  Save quiz
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading quizzes...
          </div>
        ) : (
          <div className="grid gap-3">
            {quizzes.map((quiz) => (
              <Card key={quiz.id}>
                <CardHeader className="gap-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle className="text-lg">{quiz.title}</CardTitle>
                      <CardDescription>
                        {quiz.offering.course_code} {quiz.offering.section} - {quiz.offering.semester}
                      </CardDescription>
                    </div>
                    <Badge variant={quiz.status === "published" ? "default" : "secondary"}>{quiz.status_label}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-wrap items-center justify-between gap-3 text-sm">
                  <div className="flex flex-wrap gap-3 text-muted-foreground">
                    <span>Opens {formatDateTime(quiz.opens_at)}</span>
                    <span>Closes {formatDateTime(quiz.closes_at)}</span>
                    <span>{quiz.attempt_count} attempts</span>
                    <span>{quiz.total_marks} marks</span>
                  </div>
                  <Button size="sm" render={<Link href={`/teacher/quizzes/${quiz.id}`} />}>
                    <ClipboardCheck className="size-4" />
                    Manage
                  </Button>
                </CardContent>
              </Card>
            ))}
            {!quizzes.length && <p className="text-sm text-muted-foreground">No quizzes yet.</p>}
          </div>
        )}
      </main>
    </div>
  )
}

export function TeacherQuizDetailPage({ quizId }: { quizId: string }) {
  const [quiz, setQuiz] = useState<QuizRecord | null>(null)
  const [bankQuestions, setBankQuestions] = useState<BankQuestionOption[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadQuiz = useCallback(async () => {
    const data = await apiFetch<QuizDetailResponse>(`/quiz/teacher/quizzes/${quizId}`)
    setQuiz(data.quiz)
    setBankQuestions(data.options?.question_bank_questions || [])
  }, [quizId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadQuiz()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load quiz."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadQuiz])

  async function handleAddQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch<QuizDetailResponse>(`/quiz/teacher/quizzes/${quizId}/questions`, {
        method: "POST",
        body: JSON.stringify(questionPayload(event.currentTarget)),
      })
      event.currentTarget.reset()
      setSuccess("Question added.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add question.")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleAddExistingQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    const data = new FormData(event.currentTarget)
    try {
      await apiFetch<QuizDetailResponse>(`/quiz/teacher/quizzes/${quizId}/questions`, {
        method: "POST",
        body: JSON.stringify({
          question_id: Number(data.get("question_id")),
          max_mark: String(data.get("max_mark") || "1"),
        }),
      })
      event.currentTarget.reset()
      setSuccess("Question added from bank.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add bank question.")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleAddRandomRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    const data = new FormData(event.currentTarget)
    try {
      await apiFetch<QuizDetailResponse>(`/quiz/teacher/quizzes/${quizId}/random-rules`, {
        method: "POST",
        body: JSON.stringify({
          question_type: String(data.get("question_type") || ""),
          count: Number(data.get("count") || 1),
          max_mark: String(data.get("max_mark") || "1"),
        }),
      })
      event.currentTarget.reset()
      setSuccess("Random question rule added.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add random rule.")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGrade(event: FormEvent<HTMLFormElement>, attemptId: number, questionAttemptId: number) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    const data = new FormData(event.currentTarget)
    try {
      await apiFetch(`/quiz/teacher/quizzes/${quizId}/attempts/${attemptId}/grade`, {
        method: "POST",
        body: JSON.stringify({
          question_attempt_id: questionAttemptId,
          awarded_mark: String(data.get("awarded_mark") || "0"),
          feedback: String(data.get("feedback") || ""),
        }),
      })
      setSuccess("Manual grade saved.")
      await loadQuiz()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save grade.")
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-svh flex-col bg-muted/25">
        <Header breadcrumbItems={[{ href: "/teacher", title: "Teacher" }, { href: "/teacher/quizzes", title: "Quizzes" }]} />
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
        <Header breadcrumbItems={[{ href: "/teacher", title: "Teacher" }, { href: "/teacher/quizzes", title: "Quizzes" }]} />
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
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/quizzes", title: "Quizzes" },
          { href: `/teacher/quizzes/${quiz.id}`, title: quiz.title },
        ]}
      />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 p-4 md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">{quiz.title}</h1>
            <p className="text-sm text-muted-foreground">
              {quiz.offering.course_code} {quiz.offering.section} - {quiz.total_marks} marks
            </p>
          </div>
          <Badge variant={quiz.status === "published" ? "default" : "secondary"}>{quiz.status_label}</Badge>
        </div>

        <Notice error={error} success={success} />

        {quiz.statistics && (
          <div className="grid gap-3 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Attempts</CardDescription>
                <CardTitle>{quiz.statistics.attempts_total}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Submitted</CardDescription>
                <CardTitle>{quiz.statistics.attempts_submitted}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Average score</CardDescription>
                <CardTitle>{quiz.statistics.average_score ?? "Pending"}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Manual queue</CardDescription>
                <CardTitle>{quiz.statistics.manual_pending}</CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Questions</CardTitle>
                <CardDescription>{quiz.slots?.length || 0} questions in this quiz.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                {quiz.slots?.map((slot) => (
                  <div key={slot.id} className="rounded-lg border bg-background p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="font-medium">{slot.question_version.question_text}</div>
                      <Badge variant="secondary">{slot.max_mark} marks</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{slot.question_version.question_type_label}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Random question rules</CardTitle>
                <CardDescription>{quiz.random_rules?.length || 0} rules configured for this quiz.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                {quiz.random_rules?.map((rule) => (
                  <div key={rule.id} className="rounded-lg border bg-background p-3 text-sm">
                    <div className="font-medium">
                      {rule.count} random {rule.question_type || "any type"} question{rule.count === 1 ? "" : "s"}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {rule.max_mark} marks each{rule.category ? ` - ${rule.category}` : ""}
                    </div>
                  </div>
                ))}
                {!quiz.random_rules?.length && <p className="text-sm text-muted-foreground">No random rules yet.</p>}
              </CardContent>
            </Card>

            {quiz.statistics?.questions.length ? (
              <Card>
                <CardHeader>
                  <CardTitle>Question statistics</CardTitle>
                  <CardDescription>Response and score distribution by question.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {quiz.statistics.questions.map((question) => (
                    <div key={question.question_version_id} className="rounded-lg border bg-background p-3 text-sm">
                      <div className="font-medium">{question.question_text}</div>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>{question.answered}/{question.attempts} answered</span>
                        <span>Average {question.average_mark ?? "Pending"} / {question.max_mark}</span>
                        <span>{question.full_mark} full mark</span>
                        <span>{question.manual_pending} manual</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle>Attempts</CardTitle>
                <CardDescription>Review submissions and complete manual grading.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                {quiz.attempts?.map((attempt) => (
                  <div key={attempt.id} className="rounded-lg border bg-background p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="font-medium">{attempt.student}</div>
                        <div className="text-xs text-muted-foreground">
                          Attempt {attempt.attempt_number} - {attempt.state_label} - Score {attempt.score || "Pending"}
                        </div>
                      </div>
                      {attempt.needs_manual_grading && <Badge variant="secondary">Manual grading</Badge>}
                    </div>
                    <div className="mt-3 grid gap-3">
                      {attempt.questions?.map((question) => (
                        <div key={question.id} className="rounded-md border p-3">
                          <div className="text-sm font-medium">{question.question.question_text}</div>
                          <div className="mt-1 text-xs text-muted-foreground">Response: {question.response_summary || "No response"}</div>
                          <div className="mt-1 text-xs text-muted-foreground">
                            Mark: {question.awarded_mark ?? "Pending"} / {question.max_mark}
                          </div>
                          {question.requires_manual_grading && (
                            <form className="mt-3 grid gap-2 md:grid-cols-[120px_1fr_auto]" onSubmit={(event) => handleGrade(event, attempt.id, question.id)}>
                              <Input name="awarded_mark" type="number" min="0" max={question.max_mark} step="0.01" required />
                              <Input name="feedback" placeholder="Feedback" />
                              <Button type="submit" size="sm" disabled={submitting}>
                                <Save className="size-4" />
                                Save
                              </Button>
                            </form>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {!quiz.attempts?.length && <p className="text-sm text-muted-foreground">No attempts yet.</p>}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Add from bank</CardTitle>
                <CardDescription>Reuse a ready question version from this teacher question bank.</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3" onSubmit={handleAddExistingQuestion}>
                  <div className="grid gap-2">
                    <Label htmlFor="bank_question_id">Question</Label>
                    <select id="bank_question_id" name="question_id" className={nativeSelectClass()} required>
                      <option value="">Select question</option>
                      {bankQuestions.map((question) => (
                        <option key={question.id} value={question.id}>
                          {question.title} - {question.question_type_label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="bank_max_mark">Mark</Label>
                    <Input id="bank_max_mark" name="max_mark" type="number" min="0" step="0.01" defaultValue="1" />
                  </div>
                  <Button type="submit" disabled={submitting || !bankQuestions.length}>
                    {submitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    Add bank question
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Add question</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3" onSubmit={handleAddQuestion}>
                <div className="grid gap-2">
                  <Label htmlFor="question_type">Question type</Label>
                  <select id="question_type" name="question_type" className={nativeSelectClass()} defaultValue="multiple_choice">
                    {QUESTION_TYPES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="question_title">Title</Label>
                  <Input id="question_title" name="question_title" required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="question_text">Question</Label>
                  <Textarea id="question_text" name="question_text" rows={3} required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="max_mark">Mark</Label>
                  <Input id="max_mark" name="max_mark" type="number" step="0.01" min="0" defaultValue="1" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="choices">Choices</Label>
                  <Textarea id="choices" name="choices" rows={4} placeholder={"A|First option|false\nB|Second option|true"} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="correct_answer">Correct answer</Label>
                  <Input id="correct_answer" name="correct_answer" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="tolerance">Numerical tolerance</Label>
                  <Input id="tolerance" name="tolerance" type="number" min="0" step="0.01" defaultValue="0" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="matching_pairs">Matching pairs</Label>
                  <Textarea id="matching_pairs" name="matching_pairs" rows={3} placeholder={"Prompt|Answer\nAnother prompt|Another answer"} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="ordering_items">Ordering items</Label>
                  <Textarea id="ordering_items" name="ordering_items" rows={3} placeholder={"First item\nSecond item\nThird item"} />
                </div>
                <Button type="submit" disabled={submitting}>
                    {submitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    Add question
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Add random rule</CardTitle>
                <CardDescription>Pull random ready questions from this offering bank during each attempt.</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3" onSubmit={handleAddRandomRule}>
                <div className="grid gap-2">
                  <Label htmlFor="random_question_type">Question type</Label>
                  <select id="random_question_type" name="question_type" className={nativeSelectClass()} defaultValue="">
                    <option value="">Any type</option>
                    {QUESTION_TYPES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="random_count">Count</Label>
                  <Input id="random_count" name="count" type="number" min="1" defaultValue="1" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="random_max_mark">Marks each</Label>
                  <Input id="random_max_mark" name="max_mark" type="number" min="0" step="0.01" defaultValue="1" />
                </div>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    Add random rule
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

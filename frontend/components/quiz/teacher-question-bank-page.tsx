"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Loader2, Plus, RefreshCw, Save } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type QuestionTypeValue =
  | "multiple_choice"
  | "true_false"
  | "short_answer"
  | "fill_blank"
  | "numerical"
  | "matching"
  | "ordering"
  | "essay"

type Bank = {
  id: number
  title: string
  question_count: number
  offering: {
    course_code: string
    section: string
    semester: string
  } | null
}

type Category = {
  id: number
  bank_id: number
  title: string
}

type QuestionVersion = {
  id: number
  version: number
  question_text: string
  default_mark: string
  correct_answer?: string
}

type BankQuestion = {
  id: number
  bank_id: number
  bank_title: string
  category: Category | null
  title: string
  question_type: QuestionTypeValue
  question_type_label: string
  latest_version: QuestionVersion | null
  version_count: number
}

type QuestionType = {
  value: QuestionTypeValue
  label: string
}

type BankResponse = {
  banks: Bank[]
  categories: Category[]
  questions: BankQuestion[]
  question_types: QuestionType[]
}

const fallbackQuestionTypes: QuestionType[] = [
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

function pairsFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [prompt, answer] = line.split("|").map((part) => part.trim())
      return { prompt: prompt || answer || "", answer: answer || "" }
    })
}

function itemsFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
}

function questionPayload(form: HTMLFormElement) {
  const data = new FormData(form)
  const questionType = String(data.get("question_type") || "multiple_choice")
  return {
    bank_id: Number(data.get("bank_id")),
    category_id: data.get("category_id") ? Number(data.get("category_id")) : undefined,
    title: String(data.get("question_title") || "Question"),
    question_type: questionType,
    question_text: String(data.get("question_text") || ""),
    correct_answer: String(data.get("correct_answer") || ""),
    default_mark: String(data.get("default_mark") || "1"),
    choices: questionType === "multiple_choice" ? choicesFromText(String(data.get("choices") || "")) : [],
    tolerance: String(data.get("tolerance") || "0"),
    matching_pairs: pairsFromText(String(data.get("matching_pairs") || "")),
    ordering_items: itemsFromText(String(data.get("ordering_items") || "")),
  }
}

export function TeacherQuestionBankPage() {
  const [data, setData] = useState<BankResponse>({ banks: [], categories: [], questions: [], question_types: fallbackQuestionTypes })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const questionTypes = data.question_types.length ? data.question_types : fallbackQuestionTypes
  const categoriesByBank = useMemo(() => {
    const grouped = new Map<number, Category[]>()
    data.categories.forEach((category) => {
      grouped.set(category.bank_id, [...(grouped.get(category.bank_id) || []), category])
    })
    return grouped
  }, [data.categories])

  const loadBank = useCallback(async () => {
    const response = await apiFetch<BankResponse>("/quiz/teacher/question-bank")
    setData({
      banks: response.banks,
      categories: response.categories,
      questions: response.questions,
      question_types: response.question_types.length ? response.question_types : fallbackQuestionTypes,
    })
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadBank()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load question bank."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadBank])

  async function submitForm(event: FormEvent<HTMLFormElement>, path: string, message: string, body: unknown) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(path, {
        method: "POST",
        body: JSON.stringify(body),
      })
      event.currentTarget.reset()
      setSuccess(message)
      await loadBank()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save question bank changes.")
    } finally {
      setSubmitting(false)
    }
  }

  function handleCategory(event: FormEvent<HTMLFormElement>) {
    const form = event.currentTarget
    const formData = new FormData(form)
    void submitForm(event, "/quiz/teacher/question-bank/categories", "Category saved.", {
      bank_id: Number(formData.get("bank_id")),
      title: String(formData.get("title") || ""),
      description: String(formData.get("description") || ""),
    })
  }

  function handleQuestion(event: FormEvent<HTMLFormElement>) {
    void submitForm(event, "/quiz/teacher/question-bank/questions", "Question saved.", questionPayload(event.currentTarget))
  }

  function handleVersion(event: FormEvent<HTMLFormElement>) {
    const form = event.currentTarget
    const formData = new FormData(form)
    const questionId = Number(formData.get("question_id"))
    void submitForm(event, `/quiz/teacher/question-bank/questions/${questionId}/versions`, "Question version saved.", questionPayload(form))
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/quizzes", title: "Quizzes" },
          { href: "/teacher/quizzes/question-bank", title: "Question Bank" },
        ]}
      />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Question Bank</h1>
            <p className="text-sm text-muted-foreground">Reusable questions, categories, and versions for assigned offerings.</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => void loadBank()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </div>

        <Notice error={error} success={success} />

        <div className="grid gap-3 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Banks</CardDescription>
              <CardTitle>{data.banks.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Categories</CardDescription>
              <CardTitle>{data.categories.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Questions</CardDescription>
              <CardTitle>{data.questions.length}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Create category</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3" onSubmit={handleCategory}>
                  <div className="grid gap-2">
                    <Label htmlFor="category_bank_id">Bank</Label>
                    <select id="category_bank_id" name="bank_id" className={nativeSelectClass()} required>
                      <option value="">Select bank</option>
                      {data.banks.map((bank) => (
                        <option key={bank.id} value={bank.id}>
                          {bank.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="category_title">Title</Label>
                    <Input id="category_title" name="title" required />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="category_description">Description</Label>
                    <Textarea id="category_description" name="description" rows={2} />
                  </div>
                  <Button type="submit" disabled={submitting || !data.banks.length}>
                    {submitting ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    Save category
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Create version</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3" onSubmit={handleVersion}>
                  <QuestionAuthorFields
                    banks={data.banks}
                    questions={data.questions}
                    questionTypes={questionTypes}
                    categoriesByBank={categoriesByBank}
                    includeQuestionSelect
                    submitting={submitting}
                    submitLabel="Save version"
                    submitIcon="save"
                  />
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Create question</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="grid gap-3 md:grid-cols-2" onSubmit={handleQuestion}>
                  <QuestionAuthorFields
                    banks={data.banks}
                    questions={data.questions}
                    questionTypes={questionTypes}
                    categoriesByBank={categoriesByBank}
                    submitting={submitting}
                    submitLabel="Save question"
                  />
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Questions</CardTitle>
                <CardDescription>{loading ? "Loading..." : `${data.questions.length} reusable questions`}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                {data.questions.map((question) => (
                  <div key={question.id} className="rounded-lg border bg-background p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="font-medium">{question.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {question.bank_title}
                          {question.category ? ` - ${question.category.title}` : ""}
                        </div>
                      </div>
                      <Badge variant="secondary">{question.question_type_label}</Badge>
                    </div>
                    <p className="mt-2 text-sm">{question.latest_version?.question_text}</p>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                      <span>{question.version_count} versions</span>
                      <span>{question.latest_version?.default_mark || "0"} default marks</span>
                    </div>
                  </div>
                ))}
                {!loading && !data.questions.length && <p className="text-sm text-muted-foreground">No questions yet.</p>}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

function QuestionAuthorFields({
  banks,
  questions,
  questionTypes,
  categoriesByBank,
  includeQuestionSelect = false,
  submitting,
  submitLabel,
  submitIcon = "plus",
}: {
  banks: Bank[]
  questions: BankQuestion[]
  questionTypes: QuestionType[]
  categoriesByBank: Map<number, Category[]>
  includeQuestionSelect?: boolean
  submitting: boolean
  submitLabel: string
  submitIcon?: "plus" | "save"
}) {
  const allCategories = Array.from(categoriesByBank.values()).flat()
  return (
    <>
      {includeQuestionSelect ? (
        <div className="grid gap-2">
          <Label htmlFor="version_question_id">Question</Label>
          <select id="version_question_id" name="question_id" className={nativeSelectClass()} required>
            <option value="">Select question</option>
            {questions.map((question) => (
              <option key={question.id} value={question.id}>
                {question.title}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="grid gap-2">
          <Label htmlFor="bank_id">Bank</Label>
          <select id="bank_id" name="bank_id" className={nativeSelectClass()} required>
            <option value="">Select bank</option>
            {banks.map((bank) => (
              <option key={bank.id} value={bank.id}>
                {bank.title}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="grid gap-2">
        <Label htmlFor="category_id">Category</Label>
        <select id="category_id" name="category_id" className={nativeSelectClass()}>
          <option value="">No category</option>
          {allCategories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.title}
            </option>
          ))}
        </select>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="question_type">Question type</Label>
        <select id="question_type" name="question_type" className={nativeSelectClass()} defaultValue="multiple_choice" disabled={includeQuestionSelect}>
          {questionTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="default_mark">Default mark</Label>
        <Input id="default_mark" name="default_mark" type="number" min="0" step="0.01" defaultValue="1" />
      </div>
      <div className="grid gap-2 md:col-span-2">
        <Label htmlFor="question_title">Title</Label>
        <Input id="question_title" name="question_title" required={!includeQuestionSelect} />
      </div>
      <div className="grid gap-2 md:col-span-2">
        <Label htmlFor="question_text">Question text</Label>
        <Textarea id="question_text" name="question_text" rows={3} required />
      </div>
      <div className="grid gap-2 md:col-span-2">
        <Label htmlFor="choices">Choices</Label>
        <Textarea id="choices" name="choices" rows={3} placeholder={"A|First option|false\nB|Second option|true"} />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="correct_answer">Correct answer</Label>
        <Input id="correct_answer" name="correct_answer" />
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
          {submitting ? <Loader2 className="size-4 animate-spin" /> : submitIcon === "save" ? <Save className="size-4" /> : <Plus className="size-4" />}
          {submitLabel}
        </Button>
      </div>
    </>
  )
}

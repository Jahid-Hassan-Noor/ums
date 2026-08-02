"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Loader2, Send } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import type { EvaluationQuestion, LikertOption } from "@/lib/course-evaluations"

type SurveyDetail = {
  id: number
  title: string
  instructions: string
  offering: {
    course: { code: string; title: string }
    semester: { name: string; academic_session: string }
    section: string
    instructor: { name: string } | null
  }
  state: string
  is_required: boolean
  submitted: boolean
  submitted_at: string | null
  questions: EvaluationQuestion[]
  likert_options: LikertOption[]
  answers: Record<string, string> | null
}

export default function StudentEvaluationFormPage() {
  const params = useParams<{ surveyId: string }>()
  const surveyId = Number(params.surveyId)
  const [survey, setSurvey] = useState<SurveyDetail | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadSurvey() {
    const payload = await apiFetch<SurveyDetail>(`/student/evaluations/${surveyId}`)
    setSurvey(payload)
    setAnswers(payload.answers ?? {})
  }

  useEffect(() => {
    let active = true
    apiFetch<SurveyDetail>(`/student/evaluations/${surveyId}`)
      .then((payload) => {
        if (!active) return
        setSurvey(payload)
        setAnswers(payload.answers ?? {})
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to load evaluation.")
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [surveyId])

  const sections = useMemo(() => {
    if (!survey) return []
    const map = new Map<string, EvaluationQuestion[]>()
    survey.questions.forEach((question) => {
      map.set(question.section, [...(map.get(question.section) ?? []), question])
    })
    return Array.from(map.entries())
  }, [survey])

  async function submitEvaluation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError("")
    try {
      const response = await apiFetch<{ message: string }>(`/student/evaluations/${surveyId}`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      })
      setSuccess(response.message)
      await loadSurvey()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit evaluation.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/evaluations", title: "Course Evaluations" },
          { href: `/student/evaluations/${surveyId}`, title: survey?.offering.course.code ?? "Evaluation" },
        ]}
      />
      <main className="mx-auto w-full max-w-4xl flex-1 space-y-6 px-4 pb-10 pt-4 sm:px-6">
        {error ? <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="size-4" />{error}</div> : null}
        {success ? <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</div> : null}
        {isLoading ? (
          <div className="flex h-64 items-center justify-center"><Loader2 className="size-8 animate-spin text-muted-foreground" /></div>
        ) : survey ? (
          <>
            <Card className="border-t-4 border-t-blue-500">
              <CardHeader>
                <div className="flex flex-wrap items-center gap-2">
                  <CardTitle className="text-2xl">{survey.title}</CardTitle>
                  {survey.is_required ? <Badge variant="outline">Required</Badge> : null}
                  {survey.submitted ? <Badge className="bg-emerald-600">Submitted</Badge> : null}
                </div>
                <CardDescription className="leading-6">
                  {survey.offering.course.code} - {survey.offering.course.title}<br />
                  {survey.offering.semester.name} / Lecturer: {survey.offering.instructor?.name || "Not assigned"}
                </CardDescription>
              </CardHeader>
              <CardContent><p className="text-sm leading-6 text-muted-foreground">{survey.instructions}</p></CardContent>
            </Card>

            {survey.submitted ? (
              <Card>
                <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
                  <CheckCircle2 className="size-10 text-emerald-600" />
                  <div><p className="font-semibold">Evaluation submitted</p><p className="mt-1 text-sm text-muted-foreground">Thank you for helping improve course content and teaching quality.</p></div>
                  <Button variant="outline" render={<Link href="/student/evaluations" />}>Back to evaluations</Button>
                </CardContent>
              </Card>
            ) : survey.state !== "open" ? (
              <Card><CardContent className="flex gap-3 p-5 text-sm"><AlertCircle className="size-5 shrink-0 text-amber-600" /><p>This evaluation is currently <strong>{survey.state}</strong>. Contact your school executive if a required activity needs to be reopened.</p></CardContent></Card>
            ) : (
              <form className="space-y-6" onSubmit={submitEvaluation}>
                {sections.map(([section, questions]) => (
                  <Card key={section}>
                    <CardHeader><CardTitle>{section}</CardTitle><CardDescription>Select the response that best reflects your experience.</CardDescription></CardHeader>
                    <CardContent className="space-y-5">
                      {questions.map((question) => (
                        <div key={question.id} className="space-y-2 rounded-lg border border-border bg-background p-4">
                          <Label className="text-sm leading-6">{question.text}{question.required ? <span className="ml-1 text-red-500">*</span> : null}</Label>
                          {question.type === "likert" ? (
                            <select
                              required={question.required}
                              value={answers[question.id] ?? ""}
                              onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
                            >
                              <option value="">Choose</option>
                              {survey.likert_options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                            </select>
                          ) : (
                            <Textarea
                              required={question.required}
                              value={answers[question.id] ?? ""}
                              onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                              placeholder="Your answer"
                              rows={4}
                            />
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))}
                <div className="flex justify-end"><Button size="lg" disabled={isSubmitting}>{isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />} Submit evaluation</Button></div>
              </form>
            )}
          </>
        ) : null}
      </main>
    </div>
  )
}

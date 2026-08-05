"use client"

import { useParams } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Download, Loader2, RefreshCw, Save, Users } from "lucide-react"
import { useTheme } from "next-themes"

import { ValueBarChart } from "@/components/charts/value-bar-chart"
import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import { exportCourseEvaluation, type EvaluationQuestion, type LikertOption } from "@/lib/course-evaluations"

type Respondent = {
  id: number
  name: string
  student_id: string
  email: string
  submitted: boolean
  submitted_at: string | null
}

type LikertAnalytics = {
  id: string
  section: string
  text: string
  type: "likert"
  counts: Array<LikertOption & { count: number }>
  answered: number
  average: number
}

type TextAnalytics = {
  id: string
  section: string
  text: string
  type: "text"
  comments: string[]
  answered: number
}

type SurveyDetail = {
  id: number
  title: string
  evaluation_label?: string
  instructions: string
  offering: {
    id: number
    course: { id: number; code: string; title: string }
    semester: { id: number; name: string; academic_session: string }
    section: string
    instructor: { id: number; name: string } | null
  }
  opens_at: string | null
  closes_at: string | null
  is_published: boolean
  is_required: boolean
  state: string
  eligible_count: number
  response_count: number
  pending_count: number
  completion_rate: number
  questions: EvaluationQuestion[]
  likert_options: LikertOption[]
  respondents: Respondent[]
  analytics: Array<LikertAnalytics | TextAnalytics>
}

function formatDateTime(value: string | null) {
  if (!value) return "No limit"
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? "Not set" : parsed.toLocaleString()
}

function stateClass(state: string) {
  if (state === "open") return "border-emerald-200 bg-emerald-50 text-emerald-700"
  if (state === "upcoming") return "border-blue-200 bg-blue-50 text-blue-700"
  if (state === "closed") return "border-slate-200 bg-slate-100 text-slate-700"
  return "border-amber-200 bg-amber-50 text-amber-700"
}

function localDateTimeValue(value: string | null) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export default function ExecutiveEvaluationDetailPage() {
  const params = useParams<{ surveyId: string }>()
  const surveyId = Number(params.surveyId)
  const { resolvedTheme } = useTheme()
  const [survey, setSurvey] = useState<SurveyDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [controls, setControls] = useState({
    opensAt: "",
    closesAt: "",
    isPublished: false,
    isRequired: true,
  })
  const evaluationLabel = survey?.evaluation_label ?? "Course Evaluation"

  function applySurvey(payload: SurveyDetail) {
    setSurvey(payload)
    setControls({
      opensAt: localDateTimeValue(payload.opens_at),
      closesAt: localDateTimeValue(payload.closes_at),
      isPublished: payload.is_published,
      isRequired: payload.is_required,
    })
  }

  async function loadSurvey() {
    setIsLoading(true)
    try {
      applySurvey(await apiFetch<SurveyDetail>(`/executive/evaluations/surveys/${surveyId}`))
      setError("")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load evaluation analytics.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!Number.isFinite(surveyId)) return
    let active = true
    apiFetch<SurveyDetail>(`/executive/evaluations/surveys/${surveyId}`)
      .then((payload) => {
        if (active) {
          applySurvey(payload)
          setError("")
        }
      })
      .catch((caught) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load evaluation analytics.")
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [surveyId])

  const distribution = useMemo(() => {
    if (!survey) return []
    const totals = Object.fromEntries(survey.likert_options.map((option) => [option.value, 0]))
    survey.analytics.forEach((item) => {
      if (item.type !== "likert") return
      item.counts.forEach((count) => {
        totals[count.value] = (totals[count.value] ?? 0) + count.count
      })
    })
    return survey.likert_options.map((option) => ({
      label: option.label.replace("Strongly ", "S. "),
      value: totals[option.value] ?? 0,
    }))
  }, [survey])

  async function exportReport() {
    if (!survey) return
    setIsExporting(true)
    setError("")
    try {
      await exportCourseEvaluation(survey.id, survey.offering.course.code)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to export evaluation.")
    } finally {
      setIsExporting(false)
    }
  }

  async function saveControls() {
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ survey: SurveyDetail; message: string }>(
        `/executive/evaluations/surveys/${surveyId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            opens_at: controls.opensAt ? new Date(controls.opensAt).toISOString() : null,
            closes_at: controls.closesAt ? new Date(controls.closesAt).toISOString() : null,
            is_published: controls.isPublished,
            is_required: controls.isRequired,
          }),
        }
      )
      applySurvey(response.survey)
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update survey controls.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/evaluations", title: `${evaluationLabel}s` },
          { href: `/executive/evaluations/${surveyId}`, title: survey?.offering.course.code ?? "Survey" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" /> {error}
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" /> {success}
          </div>
        ) : null}
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : survey ? (
          <>
            <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{survey.offering.course.code} {evaluationLabel}</h1>
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${stateClass(survey.state)}`}>{survey.state}</span>
                  {survey.is_required ? <Badge variant="outline">Registration requirement</Badge> : null}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {survey.offering.course.title} / {survey.offering.semester.name} / Section {survey.offering.section || "Main"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {formatDateTime(survey.opens_at)} - {formatDateTime(survey.closes_at)}
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => void loadSurvey()}><RefreshCw className="size-4" /> Refresh</Button>
                <Button onClick={() => void exportReport()} disabled={isExporting}>
                  {isExporting ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />} Export XLSX
                </Button>
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-4">
              {[
                ["Eligible students", survey.eligible_count],
                ["Submitted", survey.response_count],
                ["Pending", survey.pending_count],
                ["Completion", `${survey.completion_rate}%`],
              ].map(([label, value]) => (
                <Card key={label}>
                  <CardContent className="p-5"><p className="text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-semibold">{value}</p></CardContent>
                </Card>
              ))}
            </section>

            <Card>
              <CardHeader>
                <CardTitle>Survey controls</CardTitle>
                <CardDescription>
                  Publish, pause, reopen, or extend the activity window. Required surveys place a
                  hold on future course registration until submission.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
                <div className="space-y-1.5">
                  <Label>Opens</Label>
                  <Input
                    type="datetime-local"
                    value={controls.opensAt}
                    onChange={(event) =>
                      setControls((current) => ({ ...current, opensAt: event.target.value }))
                    }
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Closes</Label>
                  <Input
                    type="datetime-local"
                    value={controls.closesAt}
                    onChange={(event) =>
                      setControls((current) => ({ ...current, closesAt: event.target.value }))
                    }
                  />
                </div>
                <Button onClick={() => void saveControls()} disabled={isSaving}>
                  {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                  Save controls
                </Button>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={controls.isPublished}
                    onChange={(event) =>
                      setControls((current) => ({
                        ...current,
                        isPublished: event.target.checked,
                      }))
                    }
                  />
                  Published to enrolled students
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={controls.isRequired}
                    onChange={(event) =>
                      setControls((current) => ({
                        ...current,
                        isRequired: event.target.checked,
                      }))
                    }
                  />
                  Required for next-semester registration
                </label>
              </CardContent>
            </Card>

            <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(22rem,0.8fr)]">
              <ValueBarChart
                title="Overall response distribution"
                subtitle="Combined answers across all agreement-scale questions."
                labels={distribution.map((item) => item.label)}
                values={distribution.map((item) => item.value)}
                isDark={resolvedTheme === "dark"}
                formatter={(value) => Math.round(value).toString()}
                gradientId={`sec-set-${survey.id}`}
                startColor="#2563eb"
                endColor="#60a5fa"
                totalLabel="Scale answers"
                peakLabel="Largest category"
                leftPadding={44}
              />

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Users className="size-5" /> Student completion</CardTitle>
                  <CardDescription>Executives can identify who has or has not completed the activity.</CardDescription>
                </CardHeader>
                <CardContent className="max-h-[30rem] space-y-2 overflow-y-auto">
                  {survey.respondents.map((student) => (
                    <div key={student.id} className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{student.name}</p>
                        <p className="truncate text-xs text-muted-foreground">{student.student_id || student.email}</p>
                      </div>
                      <span className={student.submitted ? "flex items-center gap-1 text-xs font-medium text-emerald-700" : "text-xs font-medium text-amber-700"}>
                        {student.submitted ? <CheckCircle2 className="size-4" /> : <AlertCircle className="size-4" />}
                        {student.submitted ? "Submitted" : "Pending"}
                      </span>
                    </div>
                  ))}
                  {!survey.respondents.length ? <p className="text-sm text-muted-foreground">No enrolled students were found for this offering.</p> : null}
                </CardContent>
              </Card>
            </section>

            <Card>
              <CardHeader>
                <CardTitle>Question-by-question analysis</CardTitle>
                <CardDescription>Average scores use a four-point scale: 4 for Strongly Agree and 1 for Strongly Disagree.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {survey.analytics.filter((item): item is LikertAnalytics => item.type === "likert").map((item) => (
                  <div key={item.id} className="space-y-3 rounded-lg border border-border p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div><p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{item.section}</p><p className="mt-1 text-sm font-medium">{item.text}</p></div>
                      <Badge variant="secondary">Average {item.average.toFixed(2)} / 4</Badge>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-4">
                      {item.counts.map((count) => {
                        const percentage = item.answered ? (count.count / item.answered) * 100 : 0
                        return (
                          <div key={count.value} className="rounded-md bg-muted/50 p-3">
                            <p className="text-xs text-muted-foreground">{count.label}</p>
                            <p className="mt-1 text-lg font-semibold">{count.count}</p>
                            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border"><div className="h-full rounded-full bg-blue-600" style={{ width: `${percentage}%` }} /></div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Written comments</CardTitle><CardDescription>Comments are grouped by question for qualitative review.</CardDescription></CardHeader>
              <CardContent className="grid gap-5 lg:grid-cols-2">
                {survey.analytics.filter((item): item is TextAnalytics => item.type === "text").map((item) => (
                  <div key={item.id} className="rounded-lg border border-border p-4">
                    <p className="text-sm font-semibold">{item.text}</p>
                    <div className="mt-3 space-y-2">
                      {item.comments.map((comment, index) => <blockquote key={`${item.id}-${index}`} className="rounded-md bg-muted/50 p-3 text-sm leading-6">“{comment}”</blockquote>)}
                      {!item.comments.length ? <p className="text-sm text-muted-foreground">No comments submitted yet.</p> : null}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  )
}

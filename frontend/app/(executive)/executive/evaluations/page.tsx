"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ClipboardList,
  FilePlus2,
  Loader2,
  Plus,
  Save,
  Trash2,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import type { EvaluationQuestion } from "@/lib/course-evaluations"
import { statusClassName } from "@/lib/status-utils"

type Template = {
  id: number
  name: string
  description: string
  questions: EvaluationQuestion[]
  question_count: number
}

type Offering = {
  id: number
  course: { id: number; code: string; title: string }
  semester: { id: number; name: string; academic_session: string }
  section: string
  instructor: { id: number; name: string } | null
  has_survey: boolean
}

type Survey = {
  id: number
  title: string
  offering: Offering
  opens_at: string | null
  closes_at: string | null
  is_published: boolean
  is_required: boolean
  state: string
  eligible_count: number
  response_count: number
  pending_count: number
  completion_rate: number
}

type TemplatesResponse = {
  evaluation_label?: string
  templates: Template[]
}

type SurveysResponse = {
  evaluation_label?: string
  offerings: Offering[]
  surveys: Survey[]
}

const inputClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"

function localDateTime(hoursFromNow: number) {
  const date = new Date(Date.now() + hoursFromNow * 60 * 60 * 1000)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

function formatDateTime(value: string | null) {
  if (!value) return "No limit"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "Not set" : date.toLocaleString()
}

function uniqueQuestionId() {
  return `question_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

export default function ExecutiveEvaluationsPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [offerings, setOfferings] = useState<Offering[]>([])
  const [surveys, setSurveys] = useState<Survey[]>([])
  const [evaluationLabel, setEvaluationLabel] = useState("Course Evaluation")
  const [selectedTemplateId, setSelectedTemplateId] = useState("")
  const [templateName, setTemplateName] = useState("")
  const [templateDescription, setTemplateDescription] = useState("")
  const [templateQuestions, setTemplateQuestions] = useState<
    EvaluationQuestion[]
  >([])
  const [launchQuestions, setLaunchQuestions] = useState<EvaluationQuestion[]>(
    []
  )
  const [launch, setLaunch] = useState({
    offeringId: "",
    templateId: "",
    title: "",
    instructions:
      "Please evaluate the course content and teaching honestly. Your feedback supports continuous improvement.",
    opensAt: localDateTime(0),
    closesAt: localDateTime(24 * 14),
    isPublished: true,
    isRequired: true,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [busy, setBusy] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async (preferredTemplateId = "") => {
    const [templateData, surveyData] = await Promise.all([
      apiFetch<TemplatesResponse>("/executive/evaluations/templates"),
      apiFetch<SurveysResponse>("/executive/evaluations/surveys"),
    ])
    setTemplates(templateData.templates ?? [])
    setOfferings(surveyData.offerings ?? [])
    setSurveys(surveyData.surveys ?? [])
    setEvaluationLabel(
      surveyData.evaluation_label ??
        templateData.evaluation_label ??
        "Course Evaluation"
    )
    const selectedTemplate =
      templateData.templates?.find(
        (template) => String(template.id) === preferredTemplateId
      ) ?? templateData.templates?.[0]
    if (selectedTemplate) {
      setSelectedTemplateId(String(selectedTemplate.id))
      setTemplateName(selectedTemplate.name)
      setTemplateDescription(selectedTemplate.description)
      setTemplateQuestions(
        selectedTemplate.questions.map((question) => ({ ...question }))
      )
      setLaunchQuestions(
        selectedTemplate.questions.map((question) => ({ ...question }))
      )
      setLaunch((current) => ({
        ...current,
        templateId: current.templateId || String(selectedTemplate.id),
      }))
    }
    const firstAvailable = surveyData.offerings?.find(
      (offering) => !offering.has_survey
    )
    if (firstAvailable) {
      setLaunch((current) => ({
        ...current,
        offeringId: current.offeringId || String(firstAvailable.id),
      }))
    }
  }, [])

  useEffect(() => {
    let active = true
    async function hydrate() {
      try {
        await loadData()
      } catch (caught) {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load evaluations."
          )
      } finally {
        if (active) setIsLoading(false)
      }
    }
    void hydrate()
    return () => {
      active = false
    }
  }, [loadData])

  function selectTemplate(template: Template) {
    setSelectedTemplateId(String(template.id))
    setTemplateName(template.name)
    setTemplateDescription(template.description)
    setTemplateQuestions(
      template.questions.map((question) => ({ ...question }))
    )
  }

  const availableOfferings = useMemo(
    () => offerings.filter((offering) => !offering.has_survey),
    [offerings]
  )

  function updateQuestion(index: number, changes: Partial<EvaluationQuestion>) {
    setTemplateQuestions((current) =>
      current.map((question, questionIndex) =>
        questionIndex === index ? { ...question, ...changes } : question
      )
    )
  }

  function updateLaunchQuestion(
    index: number,
    changes: Partial<EvaluationQuestion>
  ) {
    setLaunchQuestions((current) =>
      current.map((question, questionIndex) =>
        questionIndex === index ? { ...question, ...changes } : question
      )
    )
  }

  async function saveTemplate() {
    if (!selectedTemplateId) return
    setBusy("template")
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/evaluations/templates/${selectedTemplateId}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: templateName,
          description: templateDescription,
          questions: templateQuestions,
        }),
      })
      setSuccess(
        "Template saved. Future course surveys can reuse these questions."
      )
      await loadData(selectedTemplateId)
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to save template."
      )
    } finally {
      setBusy("")
    }
  }

  async function createTemplate() {
    setBusy("new-template")
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ template: Template }>(
        "/executive/evaluations/templates",
        {
          method: "POST",
          body: JSON.stringify({
            name: `${templateName || `${evaluationLabel} Template`} Copy`,
            description: templateDescription,
            questions: templateQuestions,
          }),
        }
      )
      await loadData(String(response.template.id))
      setSelectedTemplateId(String(response.template.id))
      setSuccess("A reusable template copy was created.")
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to create template."
      )
    } finally {
      setBusy("")
    }
  }

  async function launchSurvey(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy("launch")
    setError("")
    setSuccess("")
    try {
      await apiFetch("/executive/evaluations/surveys", {
        method: "POST",
        body: JSON.stringify({
          offering_id: Number(launch.offeringId),
          template_id: Number(launch.templateId),
          questions: launchQuestions,
          title: launch.title,
          instructions: launch.instructions,
          opens_at: launch.opensAt
            ? new Date(launch.opensAt).toISOString()
            : null,
          closes_at: launch.closesAt
            ? new Date(launch.closesAt).toISOString()
            : null,
          is_published: launch.isPublished,
          is_required: launch.isRequired,
        }),
      })
      setSuccess(`${evaluationLabel} activity launched for the selected course.`)
      const selectedTemplate = templates.find(
        (template) => String(template.id) === launch.templateId
      )
      setLaunch((current) => ({ ...current, title: "" }))
      if (selectedTemplate) {
        setLaunchQuestions(
          selectedTemplate.questions.map((question) => ({ ...question }))
        )
      }
      await loadData(selectedTemplateId)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to launch evaluation."
      )
    } finally {
      setBusy("")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/evaluations", title: `${evaluationLabel}s` },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {evaluationLabel}s
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Maintain reusable questionnaires, launch one evaluation for each
            course offering, monitor completion, and analyze student feedback.
          </p>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            {error}
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            {success}
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <section className="grid gap-4 lg:grid-cols-3">
              <Card>
                <CardContent className="flex items-center justify-between p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Course surveys
                    </p>
                    <p className="text-3xl font-semibold">{surveys.length}</p>
                  </div>
                  <ClipboardList className="size-6 text-blue-600" />
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex items-center justify-between p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">Responses</p>
                    <p className="text-3xl font-semibold">
                      {surveys.reduce(
                        (sum, survey) => sum + survey.response_count,
                        0
                      )}
                    </p>
                  </div>
                  <BarChart3 className="size-6 text-emerald-600" />
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex items-center justify-between p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Pending students
                    </p>
                    <p className="text-3xl font-semibold">
                      {surveys.reduce(
                        (sum, survey) => sum + survey.pending_count,
                        0
                      )}
                    </p>
                  </div>
                  <AlertCircle className="size-6 text-amber-600" />
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(22rem,0.85fr)]">
              <Card>
                <CardHeader>
                  <CardTitle>Reusable questionnaire template</CardTitle>
                  <CardDescription>
                    Edit the standard form once, then reuse it for each offered
                    course.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label>Template</Label>
                      <select
                        className={inputClass}
                        value={selectedTemplateId}
                        onChange={(event) => {
                          const template = templates.find(
                            (item) => String(item.id) === event.target.value
                          )
                          if (template) selectTemplate(template)
                        }}
                      >
                        {templates.map((template) => (
                          <option key={template.id} value={template.id}>
                            {template.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Template name</Label>
                      <Input
                        value={templateName}
                        onChange={(event) =>
                          setTemplateName(event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Description</Label>
                    <Textarea
                      value={templateDescription}
                      onChange={(event) =>
                        setTemplateDescription(event.target.value)
                      }
                    />
                  </div>
                  <div className="space-y-3">
                    {templateQuestions.map((question, index) => (
                      <div
                        key={question.id}
                        className="space-y-3 rounded-lg border border-border bg-background p-3"
                      >
                        <div className="grid gap-3 md:grid-cols-[1fr_10rem_auto]">
                          <Input
                            value={question.section}
                            onChange={(event) =>
                              updateQuestion(index, {
                                section: event.target.value,
                              })
                            }
                            placeholder="Section"
                          />
                          <select
                            className={inputClass}
                            value={question.type}
                            onChange={(event) =>
                              updateQuestion(index, {
                                type: event.target
                                  .value as EvaluationQuestion["type"],
                              })
                            }
                          >
                            <option value="likert">Agreement scale</option>
                            <option value="text">Written response</option>
                          </select>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Remove question"
                            onClick={() =>
                              setTemplateQuestions((current) =>
                                current.filter(
                                  (_, itemIndex) => itemIndex !== index
                                )
                              )
                            }
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                        <Textarea
                          value={question.text}
                          onChange={(event) =>
                            updateQuestion(index, { text: event.target.value })
                          }
                        />
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={question.required}
                            onChange={(event) =>
                              updateQuestion(index, {
                                required: event.target.checked,
                              })
                            }
                          />
                          Required question
                        </label>
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        setTemplateQuestions((current) => [
                          ...current,
                          {
                            id: uniqueQuestionId(),
                            section: "General",
                            text: "",
                            type: "likert",
                            required: true,
                          },
                        ])
                      }
                    >
                      <Plus className="size-4" /> Add question
                    </Button>
                    <Button
                      onClick={() => void saveTemplate()}
                      disabled={busy === "template"}
                    >
                      {busy === "template" ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Save className="size-4" />
                      )}{" "}
                      Save template
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => void createTemplate()}
                      disabled={busy === "new-template"}
                    >
                      <FilePlus2 className="size-4" /> Save as new
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="h-fit">
                <CardHeader>
                  <CardTitle>Launch a course evaluation</CardTitle>
                  <CardDescription>
                    The selected template is copied, so this course can be
                    customized independently later.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="space-y-4" onSubmit={launchSurvey}>
                    <div className="space-y-1.5">
                      <Label>Current course offering</Label>
                      <select
                        required
                        className={inputClass}
                        value={launch.offeringId}
                        onChange={(event) =>
                          setLaunch((current) => ({
                            ...current,
                            offeringId: event.target.value,
                          }))
                        }
                      >
                        <option value="">Select a course</option>
                        {availableOfferings.map((offering) => (
                          <option key={offering.id} value={offering.id}>
                            {offering.course.code} - {offering.course.title} (
                            {offering.semester.name})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>Question template</Label>
                      <select
                        required
                        className={inputClass}
                        value={launch.templateId}
                        onChange={(event) => {
                          const template = templates.find(
                            (item) => String(item.id) === event.target.value
                          )
                          setLaunch((current) => ({
                            ...current,
                            templateId: event.target.value,
                          }))
                          if (template) {
                            setLaunchQuestions(
                              template.questions.map((question) => ({
                                ...question,
                              }))
                            )
                          }
                        }}
                      >
                        {templates.map((template) => (
                          <option key={template.id} value={template.id}>
                            {template.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <details className="rounded-lg border border-border bg-muted/20 p-3">
                      <summary className="cursor-pointer text-sm font-medium">
                        Customize this course questionnaire (
                        {launchQuestions.length} questions)
                      </summary>
                      <div className="mt-4 max-h-[32rem] space-y-3 overflow-y-auto pr-1">
                        {launchQuestions.map((question, index) => (
                          <div
                            key={question.id}
                            className="space-y-2 rounded-md border border-border bg-background p-3"
                          >
                            <div className="grid gap-2 sm:grid-cols-[1fr_9rem_auto]">
                              <Input
                                value={question.section}
                                onChange={(event) =>
                                  updateLaunchQuestion(index, {
                                    section: event.target.value,
                                  })
                                }
                                placeholder="Section"
                              />
                              <select
                                className={inputClass}
                                value={question.type}
                                onChange={(event) =>
                                  updateLaunchQuestion(index, {
                                    type: event.target
                                      .value as EvaluationQuestion["type"],
                                  })
                                }
                              >
                                <option value="likert">Scale</option>
                                <option value="text">Text</option>
                              </select>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() =>
                                  setLaunchQuestions((current) =>
                                    current.filter(
                                      (_, itemIndex) => itemIndex !== index
                                    )
                                  )
                                }
                              >
                                <Trash2 className="size-4" />
                              </Button>
                            </div>
                            <Textarea
                              value={question.text}
                              onChange={(event) =>
                                updateLaunchQuestion(index, {
                                  text: event.target.value,
                                })
                              }
                            />
                            <label className="flex items-center gap-2 text-xs">
                              <input
                                type="checkbox"
                                checked={question.required}
                                onChange={(event) =>
                                  updateLaunchQuestion(index, {
                                    required: event.target.checked,
                                  })
                                }
                              />
                              Required
                            </label>
                          </div>
                        ))}
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setLaunchQuestions((current) => [
                              ...current,
                              {
                                id: uniqueQuestionId(),
                                section: "General",
                                text: "",
                                type: "likert",
                                required: true,
                              },
                            ])
                          }
                        >
                          <Plus className="size-4" /> Add course-specific
                          question
                        </Button>
                      </div>
                    </details>
                    <div className="space-y-1.5">
                      <Label>Survey title (optional)</Label>
                      <Input
                        value={launch.title}
                        onChange={(event) =>
                          setLaunch((current) => ({
                            ...current,
                            title: event.target.value,
                          }))
                        }
                        placeholder="Generated from the course if left blank"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Instructions</Label>
                      <Textarea
                        value={launch.instructions}
                        onChange={(event) =>
                          setLaunch((current) => ({
                            ...current,
                            instructions: event.target.value,
                          }))
                        }
                      />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <Label>Opens</Label>
                        <Input
                          type="datetime-local"
                          value={launch.opensAt}
                          onChange={(event) =>
                            setLaunch((current) => ({
                              ...current,
                              opensAt: event.target.value,
                            }))
                          }
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label>Closes</Label>
                        <Input
                          type="datetime-local"
                          value={launch.closesAt}
                          onChange={(event) =>
                            setLaunch((current) => ({
                              ...current,
                              closesAt: event.target.value,
                            }))
                          }
                        />
                      </div>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={launch.isRequired}
                        onChange={(event) =>
                          setLaunch((current) => ({
                            ...current,
                            isRequired: event.target.checked,
                          }))
                        }
                      />{" "}
                      Required before next-semester registration
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={launch.isPublished}
                        onChange={(event) =>
                          setLaunch((current) => ({
                            ...current,
                            isPublished: event.target.checked,
                          }))
                        }
                      />{" "}
                      Publish to enrolled students immediately
                    </label>
                    <Button
                      className="w-full"
                      type="submit"
                      disabled={busy === "launch" || !availableOfferings.length}
                    >
                      {busy === "launch" ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <FilePlus2 className="size-4" />
                      )}{" "}
                      Launch {evaluationLabel} activity
                    </Button>
                    {!availableOfferings.length ? (
                      <p className="text-xs text-muted-foreground">
                        Every course offering in your scope already has a
                        survey.
                      </p>
                    ) : null}
                  </form>
                </CardContent>
              </Card>
            </section>

            <Card>
              <CardHeader>
                <CardTitle>Course evaluation activity</CardTitle>
                <CardDescription>
                  Open a survey to review respondents, charts, comments, and
                  export data.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 lg:grid-cols-2">
                {surveys.map((survey) => (
                  <Link
                    key={survey.id}
                    href={`/executive/evaluations/${survey.id}`}
                    className="rounded-lg border border-border bg-background p-4 transition hover:border-primary/40 hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">
                          {survey.offering.course.code} /{" "}
                          {survey.offering.section || "Main"}
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {survey.offering.course.title}
                        </p>
                      </div>
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${statusClassName(survey.state)}`}
                      >
                        {survey.state}
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
                      <div className="rounded-md bg-muted/50 p-2">
                        <p className="font-semibold">{survey.response_count}</p>
                        <p className="text-xs text-muted-foreground">
                          Submitted
                        </p>
                      </div>
                      <div className="rounded-md bg-muted/50 p-2">
                        <p className="font-semibold">{survey.pending_count}</p>
                        <p className="text-xs text-muted-foreground">Pending</p>
                      </div>
                      <div className="rounded-md bg-muted/50 p-2">
                        <p className="font-semibold">
                          {survey.completion_rate}%
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Complete
                        </p>
                      </div>
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground">
                      {formatDateTime(survey.opens_at)} -{" "}
                      {formatDateTime(survey.closes_at)}
                    </p>
                  </Link>
                ))}
                {!surveys.length ? (
                  <p className="text-sm text-muted-foreground">
                    No course evaluations have been launched yet.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  )
}

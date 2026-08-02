"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  BookOpen,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Edit3,
  GraduationCap,
  Languages,
  Loader2,
  Play,
  Save,
  Square,
  X,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type CalendarGroup = "undergraduate" | "foundation"
type Workspace = CalendarGroup | "language"

type Choice = {
  value: string
  label: string
}

type TeachingPeriod = {
  starts_on: string
  ends_on: string
  weeks: number | string
}

type RegistrationPeriod = {
  id?: number
  title: string
  phase: "course_registration" | "add_drop" | "drop_only"
  opens_at: string
  closes_at: string
}

type Holiday = {
  id?: number
  name: string
  starts_on: string
  ends_on?: string | null
}

type SemesterRecord = {
  id: number
  name: string
  academic_session: string
  semester_type: "long" | "short"
  calendar_group: CalendarGroup
  starting_week: number
  start_date: string
  end_date: string
  teaching_periods: TeachingPeriod[]
  course_offering_opens_at: string | null
  course_offering_closes_at: string | null
  mid_semester_break_starts_on: string | null
  mid_semester_break_ends_on: string | null
  revision_starts_on: string | null
  revision_ends_on: string | null
  examination_starts_on: string | null
  examination_ends_on: string | null
  inter_semester_break_starts_on: string | null
  inter_semester_break_ends_on: string | null
  max_credit_hours: number
  default_classes_per_week: number
  notes: string
  is_active: boolean
  status: "active" | "planned" | "completed"
  expected_weeks: number
  can_start: boolean
  holidays: Holiday[]
  registration_periods: RegistrationPeriod[]
}

type CalendarReference = Omit<Partial<SemesterRecord>, "id" | "status" | "can_start" | "is_active"> & {
  name: string
  notes?: string[]
}

type IeltsSession = {
  id: number
  academic_session: string
  title: string
  center: number | null
  center_detail?: { code: string; name: string } | null
  registration_opens_at: string | null
  registration_closes_at: string | null
  exam_date: string
  capacity: number
  notes: string
  is_active: boolean
}

type SemesterResponse = {
  calendar_reference: CalendarReference[]
  semester_types: Choice[]
  calendar_groups: Choice[]
  semesters: SemesterRecord[]
  ielts_sessions: IeltsSession[]
  academic_centers: Array<{ id: number; code: string; name: string }>
  summary: {
    total: number
    active: number
    undergraduate: number
    foundation: number
  }
}

type SemesterForm = {
  name: string
  academic_session: string
  semester_type: "long" | "short"
  calendar_group: CalendarGroup
  starting_week: string
  start_date: string
  end_date: string
  course_offering_opens_at: string
  course_offering_closes_at: string
  mid_semester_break_starts_on: string
  mid_semester_break_ends_on: string
  revision_starts_on: string
  revision_ends_on: string
  examination_starts_on: string
  examination_ends_on: string
  inter_semester_break_starts_on: string
  inter_semester_break_ends_on: string
  max_credit_hours: string
  default_classes_per_week: string
  notes: string
  holidays: string
  teaching_periods: TeachingPeriod[]
  registration_periods: RegistrationPeriod[]
}

type IeltsForm = {
  academic_session: string
  title: string
  center: string
  registration_opens_at: string
  registration_closes_at: string
  exam_date: string
  capacity: string
  notes: string
}

const selectClass =
  "h-9 w-full rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"

const blankRegistrationPeriods: RegistrationPeriod[] = [
  { title: "Course Pre-Registration", phase: "course_registration", opens_at: "", closes_at: "" },
  { title: "Add and Drop Courses", phase: "add_drop", opens_at: "", closes_at: "" },
  { title: "Drop Courses", phase: "drop_only", opens_at: "", closes_at: "" },
]

const blankTeachingPeriods: TeachingPeriod[] = [
  { starts_on: "", ends_on: "", weeks: "" },
  { starts_on: "", ends_on: "", weeks: "" },
]

function blankSemesterForm(calendarGroup: CalendarGroup): SemesterForm {
  return {
    name: "",
    academic_session: "",
    semester_type: "long",
    calendar_group: calendarGroup,
    starting_week: "1",
    start_date: "",
    end_date: "",
    course_offering_opens_at: "",
    course_offering_closes_at: "",
    mid_semester_break_starts_on: "",
    mid_semester_break_ends_on: "",
    revision_starts_on: "",
    revision_ends_on: "",
    examination_starts_on: "",
    examination_ends_on: "",
    inter_semester_break_starts_on: "",
    inter_semester_break_ends_on: "",
    max_credit_hours: "21",
    default_classes_per_week: "1",
    notes: "",
    holidays: "",
    teaching_periods: blankTeachingPeriods.map((item) => ({ ...item })),
    registration_periods: blankRegistrationPeriods.map((item) => ({ ...item })),
  }
}

const blankIeltsForm: IeltsForm = {
  academic_session: "",
  title: "",
  center: "",
  registration_opens_at: "",
  registration_closes_at: "",
  exam_date: "",
  capacity: "0",
  notes: "",
}

function toDateTimeLocal(value?: string | null) {
  if (!value) return ""
  if (!value.endsWith("Z") && !/[+-]\d{2}:\d{2}$/.test(value)) return value.slice(0, 16)
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

function localDateTimeToIso(value: string) {
  return value ? new Date(value).toISOString() : ""
}

function formatDate(value?: string | null) {
  if (!value) return "Not set"
  return new Intl.DateTimeFormat("en-MY", { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(`${value.slice(0, 10)}T00:00:00`)
  )
}

function formatDateTime(value?: string | null) {
  if (!value) return "Not set"
  return new Intl.DateTimeFormat("en-MY", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value))
}

function holidayLines(holidays?: Holiday[]) {
  return (holidays ?? [])
    .map((holiday) => [holiday.name, holiday.starts_on, holiday.ends_on ?? ""].join(" | "))
    .join("\n")
}

function parseHolidayLines(value: string) {
  return value
    .split("\n")
    .map((line) => line.split("|").map((part) => part.trim()))
    .filter(([name, startsOn]) => Boolean(name && startsOn))
    .map(([name, starts_on, ends_on]) => ({ name, starts_on, ends_on: ends_on || null }))
}

function formFromReference(reference: CalendarReference): SemesterForm {
  return {
    ...blankSemesterForm("undergraduate"),
    name: reference.name,
    academic_session: reference.academic_session ?? "2025/2026",
    semester_type: reference.semester_type ?? "long",
    calendar_group: "undergraduate",
    start_date: reference.start_date ?? "",
    end_date: reference.end_date ?? "",
    mid_semester_break_starts_on: reference.mid_semester_break_starts_on ?? "",
    mid_semester_break_ends_on: reference.mid_semester_break_ends_on ?? "",
    revision_starts_on: reference.revision_starts_on ?? "",
    revision_ends_on: reference.revision_ends_on ?? "",
    examination_starts_on: reference.examination_starts_on ?? "",
    examination_ends_on: reference.examination_ends_on ?? "",
    inter_semester_break_starts_on: reference.inter_semester_break_starts_on ?? "",
    inter_semester_break_ends_on: reference.inter_semester_break_ends_on ?? "",
    notes: reference.notes?.join("\n") ?? "",
    holidays: holidayLines(reference.holidays),
    teaching_periods: reference.teaching_periods?.map((item) => ({ ...item })) ?? blankTeachingPeriods,
    registration_periods:
      reference.registration_periods?.map((item) => ({
        ...item,
        opens_at: toDateTimeLocal(item.opens_at),
        closes_at: toDateTimeLocal(item.closes_at),
      })) ?? blankRegistrationPeriods,
  }
}

function formFromSemester(semester: SemesterRecord): SemesterForm {
  const teachingPeriods = semester.teaching_periods.map((item) => ({ ...item }))
  while (teachingPeriods.length < 2) teachingPeriods.push({ starts_on: "", ends_on: "", weeks: "" })
  return {
    ...blankSemesterForm(semester.calendar_group),
    name: semester.name,
    academic_session: semester.academic_session,
    semester_type: semester.semester_type,
    calendar_group: semester.calendar_group,
    starting_week: String(semester.starting_week),
    start_date: semester.start_date,
    end_date: semester.end_date,
    course_offering_opens_at: toDateTimeLocal(semester.course_offering_opens_at),
    course_offering_closes_at: toDateTimeLocal(semester.course_offering_closes_at),
    mid_semester_break_starts_on: semester.mid_semester_break_starts_on ?? "",
    mid_semester_break_ends_on: semester.mid_semester_break_ends_on ?? "",
    revision_starts_on: semester.revision_starts_on ?? "",
    revision_ends_on: semester.revision_ends_on ?? "",
    examination_starts_on: semester.examination_starts_on ?? "",
    examination_ends_on: semester.examination_ends_on ?? "",
    inter_semester_break_starts_on: semester.inter_semester_break_starts_on ?? "",
    inter_semester_break_ends_on: semester.inter_semester_break_ends_on ?? "",
    max_credit_hours: String(semester.max_credit_hours),
    default_classes_per_week: String(semester.default_classes_per_week),
    notes: semester.notes,
    holidays: holidayLines(semester.holidays),
    teaching_periods: teachingPeriods,
    registration_periods: semester.registration_periods.map((period) => ({
      ...period,
      opens_at: toDateTimeLocal(period.opens_at),
      closes_at: toDateTimeLocal(period.closes_at),
    })),
  }
}

function statusBadge(status: SemesterRecord["status"]) {
  if (status === "active") return "border-emerald-300 bg-emerald-50 text-emerald-700"
  if (status === "completed") return "border-slate-300 bg-slate-50 text-slate-700"
  return "border-amber-300 bg-amber-50 text-amber-700"
}

function TimelinePair({
  label,
  startsOn,
  endsOn,
}: {
  label: string
  startsOn?: string | null
  endsOn?: string | null
}) {
  return (
    <div className="rounded-lg border border-border/70 bg-muted/20 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{startsOn ? `${formatDate(startsOn)} - ${formatDate(endsOn)}` : "Not configured"}</p>
    </div>
  )
}

export function AdminSemestersPage() {
  const [data, setData] = useState<SemesterResponse | null>(null)
  const [workspace, setWorkspace] = useState<Workspace>("undergraduate")
  const [form, setForm] = useState<SemesterForm>(blankSemesterForm("undergraduate"))
  const [editingSemester, setEditingSemester] = useState<SemesterRecord | null>(null)
  const [ieltsForm, setIeltsForm] = useState<IeltsForm>(blankIeltsForm)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const response = await apiFetch<SemesterResponse>("/admin/semesters")
    setData(response)
    if (response.academic_centers.length) {
      const languageCenter =
        response.academic_centers.find((center) => center.code.toLowerCase() === "lc") ??
        response.academic_centers[0]
      setIeltsForm((current) => current.center ? current : { ...current, center: String(languageCenter.id) })
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load academic calendars."))
        .finally(() => setIsLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  const visibleSemesters = useMemo(
    () => data?.semesters.filter((semester) => semester.calendar_group === workspace) ?? [],
    [data?.semesters, workspace]
  )

  function switchWorkspace(next: Workspace) {
    setWorkspace(next)
    setError("")
    setSuccess("")
    if (next !== "language") {
      setForm(blankSemesterForm(next))
    }
    setEditingSemester(null)
  }

  function updateForm(field: keyof SemesterForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function updateTeachingPeriod(index: number, field: keyof TeachingPeriod, value: string) {
    setForm((current) => ({
      ...current,
      teaching_periods: current.teaching_periods.map((period, periodIndex) =>
        periodIndex === index ? { ...period, [field]: value } : period
      ),
    }))
  }

  function updateRegistrationPeriod(index: number, field: "opens_at" | "closes_at", value: string) {
    setForm((current) => ({
      ...current,
      registration_periods: current.registration_periods.map((period, periodIndex) =>
        periodIndex === index ? { ...period, [field]: value } : period
      ),
    }))
  }

  async function submitSemester(event: FormEvent) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const incompleteTeaching = form.teaching_periods.some(
        (period) => Boolean(period.starts_on) !== Boolean(period.ends_on)
      )
      const incompleteRegistration = form.registration_periods.some(
        (period) => Boolean(period.opens_at) !== Boolean(period.closes_at)
      )
      if (incompleteTeaching || incompleteRegistration) {
        throw new Error("Complete both dates for every teaching or registration period you started.")
      }
      const registrationPeriods = form.registration_periods.filter(
        (period) => period.opens_at && period.closes_at
      ).map((period) => ({
        ...period,
        opens_at: localDateTimeToIso(period.opens_at),
        closes_at: localDateTimeToIso(period.closes_at),
      }))
      const teachingPeriods = form.teaching_periods.filter((period) => period.starts_on && period.ends_on)
      const response = await apiFetch<{ message: string }>("/admin/semesters", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          action: editingSemester ? "update_semester" : "create_semester",
          semester_id: editingSemester?.id,
          semester_type: form.calendar_group === "foundation" ? "long" : form.semester_type,
          course_offering_opens_at: localDateTimeToIso(form.course_offering_opens_at),
          course_offering_closes_at: localDateTimeToIso(form.course_offering_closes_at),
          teaching_periods: teachingPeriods,
          registration_periods: registrationPeriods.length ? registrationPeriods : undefined,
          holidays: parseHolidayLines(form.holidays),
        }),
      })
      setSuccess(response.message)
      setForm(blankSemesterForm(form.calendar_group))
      setEditingSemester(null)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create semester plan.")
    } finally {
      setIsSaving(false)
    }
  }

  async function semesterAction(action: "start_semester" | "close_semester", semester: SemesterRecord) {
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>("/admin/semesters", {
        method: "POST",
        body: JSON.stringify({ action, semester_id: semester.id }),
      })
      setSuccess(response.message)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update semester.")
    } finally {
      setIsSaving(false)
    }
  }

  async function submitIelts(event: FormEvent) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>("/admin/semesters", {
        method: "POST",
        body: JSON.stringify({
          ...ieltsForm,
          action: "create_ielts_session",
          registration_opens_at: localDateTimeToIso(ieltsForm.registration_opens_at),
          registration_closes_at: localDateTimeToIso(ieltsForm.registration_closes_at),
        }),
      })
      setSuccess(response.message)
      setIeltsForm((current) => ({ ...blankIeltsForm, center: current.center }))
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create IELTS session.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/admin", title: "Admin" }, { href: "/admin/semesters", title: "Academic Calendar" }]} />
      <main className="flex-1 space-y-6 px-4 pb-10 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Academic Calendar</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              Plan school and CFGS semesters independently, control registration and course-offering windows, and schedule LC IELTS sessions.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {([
              ["undergraduate", "Schools", GraduationCap],
              ["foundation", "CFGS", BookOpen],
              ["language", "Language Centre", Languages],
            ] as const).map(([value, label, Icon]) => (
              <Button
                key={value}
                type="button"
                variant={workspace === value ? "default" : "outline"}
                onClick={() => switchWorkspace(value)}
              >
                <Icon className="size-4" />
                {label}
              </Button>
            ))}
          </div>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {isLoading || !data ? (
          <div className="flex min-h-72 items-center justify-center"><Loader2 className="size-8 animate-spin text-muted-foreground" /></div>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["All semester plans", data.summary.total],
                ["Running calendars", data.summary.active],
                ["School semesters", data.summary.undergraduate],
                ["CFGS semesters", data.summary.foundation],
              ].map(([label, value]) => (
                <Card key={label}>
                  <CardHeader>
                    <CardDescription>{label}</CardDescription>
                    <CardTitle className="text-3xl">{value}</CardTitle>
                  </CardHeader>
                </Card>
              ))}
            </section>

            {workspace === "language" ? (
              <section className="grid gap-5 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
                <Card>
                  <form onSubmit={submitIelts}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2"><Languages className="size-5" /> Add IELTS Exam Session</CardTitle>
                      <CardDescription>LC does not use semesters. Schedule up to two IELTS exam sessions per academic year.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Field label="Academic session"><Input required value={ieltsForm.academic_session} placeholder="2026/2027" onChange={(event) => setIeltsForm((current) => ({ ...current, academic_session: event.target.value }))} /></Field>
                        <Field label="Session title"><Input required value={ieltsForm.title} placeholder="IELTS Session 1" onChange={(event) => setIeltsForm((current) => ({ ...current, title: event.target.value }))} /></Field>
                      </div>
                      <Field label="Language centre">
                        <select className={selectClass} value={ieltsForm.center} onChange={(event) => setIeltsForm((current) => ({ ...current, center: event.target.value }))}>
                          <option value="">No centre selected</option>
                          {data.academic_centers.map((center) => <option key={center.id} value={center.id}>{center.code} - {center.name}</option>)}
                        </select>
                      </Field>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Field label="Registration opens"><Input type="datetime-local" value={ieltsForm.registration_opens_at} onChange={(event) => setIeltsForm((current) => ({ ...current, registration_opens_at: event.target.value }))} /></Field>
                        <Field label="Registration closes"><Input type="datetime-local" value={ieltsForm.registration_closes_at} onChange={(event) => setIeltsForm((current) => ({ ...current, registration_closes_at: event.target.value }))} /></Field>
                        <Field label="Exam date"><Input required type="date" value={ieltsForm.exam_date} onChange={(event) => setIeltsForm((current) => ({ ...current, exam_date: event.target.value }))} /></Field>
                        <Field label="Capacity"><Input type="number" min="0" value={ieltsForm.capacity} onChange={(event) => setIeltsForm((current) => ({ ...current, capacity: event.target.value }))} /></Field>
                      </div>
                      <Field label="Notes"><Textarea value={ieltsForm.notes} onChange={(event) => setIeltsForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
                      <Button className="w-full" disabled={isSaving} type="submit">{isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save IELTS Session</Button>
                    </CardContent>
                  </form>
                </Card>
                <Card>
                  <CardHeader><CardTitle>IELTS Session Calendar</CardTitle><CardDescription>{data.ielts_sessions.length} sessions configured across all academic years</CardDescription></CardHeader>
                  <CardContent className="space-y-3">
                    {data.ielts_sessions.length ? data.ielts_sessions.map((session) => (
                      <div key={session.id} className="rounded-lg border border-border bg-background p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div><p className="font-semibold">{session.title}</p><p className="text-sm text-muted-foreground">{session.academic_session} / {session.center_detail?.name ?? "Language Centre"}</p></div>
                          <Badge variant="outline">{formatDate(session.exam_date)}</Badge>
                        </div>
                        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                          <p><span className="text-muted-foreground">Registration: </span>{formatDateTime(session.registration_opens_at)} - {formatDateTime(session.registration_closes_at)}</p>
                          <p><span className="text-muted-foreground">Capacity: </span>{session.capacity || "Open"}</p>
                        </div>
                      </div>
                    )) : <p className="text-sm text-muted-foreground">No IELTS sessions configured yet.</p>}
                  </CardContent>
                </Card>
              </section>
            ) : (
              <>
                {workspace === "undergraduate" ? (
                  <Card className="border-primary/20 bg-primary/5">
                    <CardHeader>
                      <CardTitle className="text-base">UGP Academic Calendar 2025/2026 Reference</CardTitle>
                      <CardDescription>Load a semester from the supplied calendar, review it, then save it as a plan.</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-wrap gap-2">
                      {data.calendar_reference.map((reference) => (
                        <Button key={reference.name} type="button" variant="outline" onClick={() => { setEditingSemester(null); setForm(formFromReference(reference)) }}>
                          <CalendarClock className="size-4" /> Load {reference.name.split(",")[0]}
                        </Button>
                      ))}
                    </CardContent>
                  </Card>
                ) : null}

                <section className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                  <Card>
                    <form onSubmit={submitSemester}>
                      <CardHeader>
                        <CardTitle>Create {workspace === "foundation" ? "CFGS" : "School"} Semester Plan</CardTitle>
                        <CardDescription>
                          Saving lists the semester without starting it. A running semester in the same calendar group must be closed before another can start.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        <FormSection title="Semester identity">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <Field label="Semester name"><Input required value={form.name} placeholder="Semester 1, Session 2026/2027" onChange={(event) => updateForm("name", event.target.value)} /></Field>
                            <Field label="Academic session"><Input required value={form.academic_session} placeholder="2026/2027" onChange={(event) => updateForm("academic_session", event.target.value)} /></Field>
                            <Field label="Semester type">
                              <select className={selectClass} disabled={workspace === "foundation"} value={workspace === "foundation" ? "long" : form.semester_type} onChange={(event) => updateForm("semester_type", event.target.value)}>
                                {data.semester_types.map((choice) => <option key={choice.value} value={choice.value}>{choice.label}</option>)}
                              </select>
                            </Field>
                            <Field label="Maximum credit hours"><Input required type="number" min="1" value={form.max_credit_hours} onChange={(event) => updateForm("max_credit_hours", event.target.value)} /></Field>
                            <Field label="Semester starts"><Input required type="date" value={form.start_date} onChange={(event) => updateForm("start_date", event.target.value)} /></Field>
                            <Field label="Semester ends"><Input required type="date" value={form.end_date} onChange={(event) => updateForm("end_date", event.target.value)} /></Field>
                          </div>
                        </FormSection>

                        <FormSection title="Executive course-offering window">
                          <div className="grid gap-3 sm:grid-cols-2">
                            <Field label="Offering opens"><Input type="datetime-local" value={form.course_offering_opens_at} onChange={(event) => updateForm("course_offering_opens_at", event.target.value)} /></Field>
                            <Field label="Offering closes"><Input type="datetime-local" value={form.course_offering_closes_at} onChange={(event) => updateForm("course_offering_closes_at", event.target.value)} /></Field>
                          </div>
                          <p className="text-xs text-muted-foreground">The course-offering window must close before student pre-registration opens.</p>
                        </FormSection>

                        <FormSection title="Student registration phases">
                          <div className="space-y-3">
                            {form.registration_periods.map((period, index) => (
                              <div key={period.phase} className="rounded-lg border border-border/70 p-3">
                                <p className="mb-3 text-sm font-medium">{period.title}</p>
                                <div className="grid gap-3 sm:grid-cols-2">
                                  <Field label="Opens"><Input type="datetime-local" value={period.opens_at} onChange={(event) => updateRegistrationPeriod(index, "opens_at", event.target.value)} /></Field>
                                  <Field label="Closes"><Input type="datetime-local" value={period.closes_at} onChange={(event) => updateRegistrationPeriod(index, "closes_at", event.target.value)} /></Field>
                                </div>
                              </div>
                            ))}
                          </div>
                        </FormSection>

                        <FormSection title="Teaching periods">
                          <div className="space-y-3">
                            {form.teaching_periods.map((period, index) => (
                              <div key={index} className="grid gap-3 rounded-lg border border-border/70 p-3 sm:grid-cols-[1fr_1fr_90px]">
                                <Field label={`Block ${index + 1} starts`}><Input type="date" value={period.starts_on} onChange={(event) => updateTeachingPeriod(index, "starts_on", event.target.value)} /></Field>
                                <Field label="Ends"><Input type="date" value={period.ends_on} onChange={(event) => updateTeachingPeriod(index, "ends_on", event.target.value)} /></Field>
                                <Field label="Weeks"><Input type="number" min="1" value={period.weeks} onChange={(event) => updateTeachingPeriod(index, "weeks", event.target.value)} /></Field>
                              </div>
                            ))}
                          </div>
                        </FormSection>

                        <FormSection title="Breaks, revision, and examinations">
                          <div className="grid gap-3 sm:grid-cols-2">
                            {([
                              ["Mid-semester break starts", "mid_semester_break_starts_on"],
                              ["Mid-semester break ends", "mid_semester_break_ends_on"],
                              ["Revision starts", "revision_starts_on"],
                              ["Revision ends", "revision_ends_on"],
                              ["Examinations start", "examination_starts_on"],
                              ["Examinations end", "examination_ends_on"],
                              ["Inter-semester break starts", "inter_semester_break_starts_on"],
                              ["Inter-semester break ends", "inter_semester_break_ends_on"],
                            ] as const).map(([label, field]) => (
                              <Field key={field} label={label}><Input type="date" value={form[field]} onChange={(event) => updateForm(field, event.target.value)} /></Field>
                            ))}
                          </div>
                        </FormSection>

                        <FormSection title="Holidays and notes">
                          <Field label="Holidays">
                            <Textarea rows={5} value={form.holidays} placeholder={"Christmas | 2026-12-25 |\nChinese New Year | 2027-02-06 | 2027-02-07"} onChange={(event) => updateForm("holidays", event.target.value)} />
                            <p className="text-xs text-muted-foreground">One holiday per line: name | start date | optional end date.</p>
                          </Field>
                          <Field label="Administrative notes"><Textarea rows={4} value={form.notes} onChange={(event) => updateForm("notes", event.target.value)} /></Field>
                        </FormSection>

                        <div className="flex gap-2">
                          <Button className="flex-1" disabled={isSaving} type="submit">{isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} {editingSemester ? "Update Semester Plan" : "Save Semester Plan"}</Button>
                          {editingSemester ? (
                            <Button type="button" variant="outline" onClick={() => { setEditingSemester(null); setForm(blankSemesterForm(form.calendar_group)) }}><X className="size-4" /> Cancel</Button>
                          ) : null}
                        </div>
                      </CardContent>
                    </form>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>{workspace === "foundation" ? "CFGS" : "School"} Semester Plans</CardTitle>
                      <CardDescription>{visibleSemesters.length} plans configured for this calendar group</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {visibleSemesters.length ? visibleSemesters.map((semester) => (
                        <div key={semester.id} className="rounded-xl border border-border bg-background p-4">
                          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                            <div className="space-y-2">
                              <div className="flex flex-wrap items-center gap-2">
                                <h3 className="font-semibold">{semester.name}</h3>
                                <Badge className={statusBadge(semester.status)} variant="outline">{semester.status}</Badge>
                                <Badge variant="outline">{semester.semester_type} / expected {semester.expected_weeks} weeks</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{semester.academic_session} / {formatDate(semester.start_date)} - {formatDate(semester.end_date)} / max {semester.max_credit_hours} credits</p>
                            </div>
                            <div className="flex shrink-0 gap-2">
                              {semester.is_active ? (
                                <Button type="button" variant="outline" disabled={isSaving} onClick={() => void semesterAction("close_semester", semester)}><Square className="size-4" /> Close</Button>
                              ) : (
                                <>
                                  <Button type="button" variant="outline" disabled={isSaving} onClick={() => { setEditingSemester(semester); setForm(formFromSemester(semester)); setError(""); setSuccess("") }}><Edit3 className="size-4" /> Edit</Button>
                                  <Button type="button" disabled={isSaving || !semester.can_start} onClick={() => void semesterAction("start_semester", semester)}><Play className="size-4" /> Start</Button>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="mt-4 grid gap-2 sm:grid-cols-2">
                            <TimelinePair label="Mid-semester break" startsOn={semester.mid_semester_break_starts_on} endsOn={semester.mid_semester_break_ends_on} />
                            <TimelinePair label="Revision" startsOn={semester.revision_starts_on} endsOn={semester.revision_ends_on} />
                            <TimelinePair label="Examinations" startsOn={semester.examination_starts_on} endsOn={semester.examination_ends_on} />
                            <TimelinePair label="Inter-semester break" startsOn={semester.inter_semester_break_starts_on} endsOn={semester.inter_semester_break_ends_on} />
                          </div>
                          <div className="mt-3 rounded-lg border border-border/70 p-3 text-sm">
                            <p className="font-medium">Registration controls</p>
                            <div className="mt-2 space-y-1 text-muted-foreground">
                              <p>Course offering: {formatDateTime(semester.course_offering_opens_at)} - {formatDateTime(semester.course_offering_closes_at)}</p>
                              {semester.registration_periods.map((period) => <p key={period.phase}>{period.title}: {formatDateTime(period.opens_at)} - {formatDateTime(period.closes_at)}</p>)}
                            </div>
                          </div>
                          {semester.holidays.length ? <p className="mt-3 text-sm text-muted-foreground">Holidays: {semester.holidays.map((holiday) => holiday.name).join(", ")}</p> : null}
                        </div>
                      )) : <p className="text-sm text-muted-foreground">No semester plans configured for this calendar group.</p>}
                    </CardContent>
                  </Card>
                </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2 border-b border-border/70 pb-2">
        <Clock3 className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </section>
  )
}

"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Download,
  Loader2,
  MapPin,
  Plus,
  Save,
  Search,
  Trash2,
  User,
  X,
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
import { apiFetch, apiRequest } from "@/lib/auth"
import { triggerBlobDownload } from "@/lib/fetch-utils"

type Scope = {
  kind: "school" | "center" | null
  id: number | null
  code: string
  name: string
}

type Course = {
  id: number
  code: string
  title: string
}

type Semester = {
  id: number
  name: string
  academic_session: string
}

type Teacher = {
  id: number
  name: string
  staff_id: string
}

type Venue = {
  id: number
  code: string
  name: string
  floor: string
  capacity: number | null
  building_detail: {
    id: number
    name: string
    code: string
  }
}

type ClassType = {
  value: string
  label: string
}

type ScheduleMeeting = {
  id: number
  offering_id: number
  course: Course
  semester: Semester
  section: string
  day_of_week: number
  day_label: string
  meeting_date: string | null
  start_time: string
  end_time: string
  lecturer: number | null
  lecturer_detail?: {
    id: number
    name: string
  } | null
  venue: number | null
  venue_detail?: Venue | null
  class_type: string
  class_type_label: string
  recurring_meeting: number | null
  is_single_week_adjustment: boolean
}

type ScheduleResponse = {
  title: string
  section: string
  scope: Scope
  scope_error?: string | null
  teachers: Teacher[]
  venues: Venue[]
  class_types: ClassType[]
  meetings: ScheduleMeeting[]
  exam_offerings: ExamOffering[]
  final_exams: FinalExam[]
}

type ExamOffering = {
  id: number
  course: Course
  section: string
  semester: Semester & {
    start_date: string | null
    examination_starts_on: string | null
    examination_ends_on: string | null
  }
  enrollment_count: number
  edit_window_error: string | null
}

type FinalExam = {
  id: number
  offering_id: number
  course: Course
  section: string
  semester: Semester & {
    examination_starts_on: string | null
    examination_ends_on: string | null
  }
  title: string
  exam_date: string
  start_time: string
  end_time: string
  instructions: string
  enrollment_count: number
  edit_window_error: string | null
  venue_allocations: {
    id: number
    venue_id: number
    seats: number
    venue: {
      id: number
      code: string
      name: string
      capacity: number | null
      building: string
    }
  }[]
}

type ExamForm = {
  exam_id: number | null
  offering_id: string
  exam_date: string
  start_time: string
  end_time: string
  instructions: string
  venue_allocations: {
    venue_id: string
    seats: string
  }[]
}

function pad(value: number) {
  return String(value).padStart(2, "0")
}

function formatDateInput(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function nextDateForDay(dayOfWeek: number) {
  const today = new Date()
  const todayIsoDay = today.getDay() === 0 ? 7 : today.getDay()
  const offset = (dayOfWeek - todayIsoDay + 7) % 7
  const date = new Date(today)
  date.setDate(today.getDate() + offset)
  return formatDateInput(date)
}

function adjustmentForm(meeting: ScheduleMeeting) {
  return {
    meeting_date: meeting.meeting_date ?? nextDateForDay(meeting.day_of_week),
    start_time: meeting.start_time.slice(0, 5),
    end_time: meeting.end_time.slice(0, 5),
    venue_id: meeting.venue ? String(meeting.venue) : "",
    lecturer_id: meeting.lecturer ? String(meeting.lecturer) : "",
    class_type: meeting.class_type,
  }
}

function emptyExamForm(): ExamForm {
  return {
    exam_id: null,
    offering_id: "",
    exam_date: "",
    start_time: "09:30",
    end_time: "12:30",
    instructions: "",
    venue_allocations: [{ venue_id: "", seats: "" }],
  }
}

function examForm(exam: FinalExam): ExamForm {
  return {
    exam_id: exam.id,
    offering_id: String(exam.offering_id),
    exam_date: exam.exam_date,
    start_time: exam.start_time,
    end_time: exam.end_time,
    instructions: exam.instructions,
    venue_allocations: exam.venue_allocations.map((allocation) => ({
      venue_id: String(allocation.venue_id),
      seats: String(allocation.seats),
    })),
  }
}

async function downloadScheduleXlsx() {
  const response = await apiRequest("/executive/manage/schedule?export=xlsx")
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || "Unable to export schedule.")
  }

  const blob = await response.blob()
  triggerBlobDownload(blob, "executive-schedule.xlsx")
}

export default function ExecutiveSchedulePage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [scopeError, setScopeError] = useState("")
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [venues, setVenues] = useState<Venue[]>([])
  const [classTypes, setClassTypes] = useState<ClassType[]>([])
  const [meetings, setMeetings] = useState<ScheduleMeeting[]>([])
  const [examOfferings, setExamOfferings] = useState<ExamOffering[]>([])
  const [finalExams, setFinalExams] = useState<FinalExam[]>([])
  const [finalExamForm, setFinalExamForm] = useState<ExamForm>(emptyExamForm)
  const [selectedMeeting, setSelectedMeeting] =
    useState<ScheduleMeeting | null>(null)
  const [form, setForm] = useState<ReturnType<typeof adjustmentForm> | null>(
    null
  )
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    try {
      setIsLoading(true)
      const data = await apiFetch<ScheduleResponse>(
        "/executive/manage/schedule"
      )
      setScope(data.scope)
      setScopeError(data.scope_error ?? "")
      setTeachers(data.teachers ?? [])
      setVenues(data.venues ?? [])
      setClassTypes(data.class_types ?? [])
      setMeetings(data.meetings ?? [])
      setExamOfferings(data.exam_offerings ?? [])
      setFinalExams(data.final_exams ?? [])
      setError("")
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load schedule."
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial data hydration needs to sync state after the API response arrives.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData()
  }, [])

  const filteredMeetings = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return meetings
    return meetings.filter((meeting) =>
      [
        meeting.course.code,
        meeting.course.title,
        meeting.section,
        meeting.day_label,
        meeting.venue_detail?.name,
        meeting.lecturer_detail?.name,
        meeting.class_type_label,
      ]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    )
  }, [meetings, query])

  const selectedExamOffering = useMemo(
    () =>
      examOfferings.find(
        (offering) => String(offering.id) === finalExamForm.offering_id
      ) ?? null,
    [examOfferings, finalExamForm.offering_id]
  )

  function updateExamField(
    field: keyof Omit<ExamForm, "venue_allocations">,
    value: string
  ) {
    setFinalExamForm((current) => {
      if (field !== "offering_id") return { ...current, [field]: value }
      const offering = examOfferings.find((item) => String(item.id) === value)
      return {
        ...current,
        offering_id: value,
        exam_date:
          current.exam_date || offering?.semester.examination_starts_on || "",
        venue_allocations: current.venue_allocations.map(
          (allocation, index) => ({
            ...allocation,
            seats:
              index === 0 && !allocation.seats && offering?.enrollment_count
                ? String(offering.enrollment_count)
                : allocation.seats,
          })
        ),
      }
    })
  }

  function updateExamAllocation(
    index: number,
    field: "venue_id" | "seats",
    value: string
  ) {
    setFinalExamForm((current) => ({
      ...current,
      venue_allocations: current.venue_allocations.map(
        (allocation, allocationIndex) =>
          allocationIndex === index
            ? { ...allocation, [field]: value }
            : allocation
      ),
    }))
  }

  function addExamAllocation() {
    setFinalExamForm((current) => ({
      ...current,
      venue_allocations: [
        ...current.venue_allocations,
        { venue_id: "", seats: "" },
      ],
    }))
  }

  function removeExamAllocation(index: number) {
    setFinalExamForm((current) => ({
      ...current,
      venue_allocations: current.venue_allocations.filter(
        (_, allocationIndex) => allocationIndex !== index
      ),
    }))
  }

  async function saveFinalExam(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/executive/manage/schedule", {
        method: "POST",
        body: JSON.stringify({
          schedule_kind: "final_exam",
          exam_id: finalExamForm.exam_id,
          offering_id: Number(finalExamForm.offering_id),
          exam_date: finalExamForm.exam_date,
          start_time: finalExamForm.start_time,
          end_time: finalExamForm.end_time,
          instructions: finalExamForm.instructions,
          venue_allocations: finalExamForm.venue_allocations.map(
            (allocation) => ({
              venue_id: Number(allocation.venue_id),
              seats: Number(allocation.seats),
            })
          ),
        }),
      })
      setSuccess("Final exam schedule saved successfully.")
      setFinalExamForm(emptyExamForm())
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to save this final exam."
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function removeFinalExam(exam: FinalExam) {
    if (!confirm(`Remove the final exam schedule for ${exam.course.code}?`))
      return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/manage/schedule?exam_id=${exam.id}`, {
        method: "DELETE",
      })
      setSuccess("Final exam schedule removed.")
      if (finalExamForm.exam_id === exam.id) setFinalExamForm(emptyExamForm())
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to remove this final exam."
      )
    }
  }

  function startAdjustment(meeting: ScheduleMeeting) {
    const baseMeeting = meeting.is_single_week_adjustment
      ? meetings.find((item) => item.id === meeting.recurring_meeting)
      : meeting
    if (!baseMeeting) return
    setSelectedMeeting(baseMeeting)
    setForm(adjustmentForm(meeting))
    setError("")
    setSuccess("")
  }

  function updateField(
    field: keyof ReturnType<typeof adjustmentForm>,
    value: string
  ) {
    setForm((current) => (current ? { ...current, [field]: value } : current))
  }

  async function saveAdjustment(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedMeeting || !form) return

    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/executive/manage/schedule", {
        method: "POST",
        body: JSON.stringify({
          recurring_meeting_id: selectedMeeting.id,
          meeting_date: form.meeting_date,
          start_time: form.start_time,
          end_time: form.end_time,
          venue_id: Number(form.venue_id),
          lecturer_id: Number(form.lecturer_id),
          class_type: form.class_type,
        }),
      })
      setSuccess("Single-week class updated successfully.")
      setSelectedMeeting(null)
      setForm(null)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to update this class."
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function removeAdjustment(meeting: ScheduleMeeting) {
    if (!meeting.is_single_week_adjustment) return
    if (!confirm("Remove this single-week adjustment?")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/manage/schedule?adjustment_id=${meeting.id}`, {
        method: "DELETE",
      })
      setSuccess("Single-week adjustment removed.")
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to remove adjustment."
      )
    }
  }

  async function handleExport() {
    setIsExporting(true)
    setError("")
    try {
      await downloadScheduleXlsx()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to export schedule."
      )
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/manage", title: "Manage" },
          { href: "/executive/manage/schedule", title: "Schedule" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Schedule
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Schedule final examinations, review class schedules, and adjust an
              individual class for one week.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleExport}
            disabled={isExporting}
          >
            {isExporting ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Download className="size-4" />
            )}
            {isExporting ? "Exporting..." : "Export Excel"}
          </Button>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        ) : null}
        {scopeError ? (
          <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-800">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{scopeError}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_28rem]">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">
                    Final Examination Schedule
                  </CardTitle>
                  <CardDescription>
                    Exams may share a venue only while their combined reserved
                    seats stay within its capacity.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {finalExams.length === 0 ? (
                    <p className="py-8 text-center text-sm text-muted-foreground">
                      No final exams have been scheduled for{" "}
                      {scope?.name ?? "this scope"}.
                    </p>
                  ) : (
                    finalExams.map((exam) => (
                      <div
                        key={exam.id}
                        className="rounded-lg border border-border bg-background p-4 shadow-sm"
                      >
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div className="min-w-0 space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono text-sm font-semibold text-primary">
                                {exam.course.code}
                              </span>
                              <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                                Sec {exam.section || "-"}
                              </span>
                              <span className="rounded-md bg-rose-50 px-2 py-0.5 text-xs text-rose-700">
                                {exam.enrollment_count} enrolled
                              </span>
                            </div>
                            <h2 className="text-base font-semibold">
                              {exam.course.title}
                            </h2>
                            <p className="flex items-center gap-2 text-sm text-muted-foreground">
                              <CalendarClock className="size-4" />
                              {exam.exam_date} {exam.start_time} -{" "}
                              {exam.end_time}
                            </p>
                            <div className="space-y-1 text-sm text-muted-foreground">
                              {exam.venue_allocations.map((allocation) => (
                                <p
                                  key={allocation.id}
                                  className="flex items-center gap-2"
                                >
                                  <MapPin className="size-4" />
                                  {allocation.venue.building} -{" "}
                                  {allocation.venue.name}: {allocation.seats}{" "}
                                  seats
                                </p>
                              ))}
                            </div>
                            {exam.edit_window_error ? (
                              <p className="text-xs font-medium text-amber-700">
                                {exam.edit_window_error}
                              </p>
                            ) : null}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={Boolean(exam.edit_window_error)}
                              onClick={() => setFinalExamForm(examForm(exam))}
                            >
                              <CalendarClock className="size-4" />
                              Edit
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={Boolean(exam.edit_window_error)}
                              onClick={() => removeFinalExam(exam)}
                            >
                              <Trash2 className="size-4" />
                              Remove
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base">
                    {finalExamForm.exam_id
                      ? "Edit Final Exam"
                      : "Schedule Final Exam"}
                  </CardTitle>
                  <CardDescription>
                    Admin controls the examination period and venue capacities.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="space-y-4" onSubmit={saveFinalExam}>
                    <div className="space-y-2">
                      <Label htmlFor="exam-offering">Course Offering</Label>
                      <select
                        id="exam-offering"
                        value={finalExamForm.offering_id}
                        onChange={(event) =>
                          updateExamField("offering_id", event.target.value)
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        required
                      >
                        <option value="">Select offering</option>
                        {examOfferings.map((offering) => (
                          <option key={offering.id} value={offering.id}>
                            {offering.course.code}{" "}
                            {offering.section ? `Sec ${offering.section}` : ""}{" "}
                            - {offering.enrollment_count} students
                          </option>
                        ))}
                      </select>
                      {selectedExamOffering?.edit_window_error ? (
                        <p className="text-xs font-medium text-amber-700">
                          {selectedExamOffering.edit_window_error}
                        </p>
                      ) : null}
                    </div>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="space-y-2 sm:col-span-3">
                        <Label htmlFor="exam-date">Exam Date</Label>
                        <Input
                          id="exam-date"
                          type="date"
                          min={
                            selectedExamOffering?.semester
                              .examination_starts_on ?? undefined
                          }
                          max={
                            selectedExamOffering?.semester
                              .examination_ends_on ?? undefined
                          }
                          value={finalExamForm.exam_date}
                          onChange={(event) =>
                            updateExamField("exam_date", event.target.value)
                          }
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="exam-start">Start</Label>
                        <Input
                          id="exam-start"
                          type="time"
                          value={finalExamForm.start_time}
                          onChange={(event) =>
                            updateExamField("start_time", event.target.value)
                          }
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="exam-end">End</Label>
                        <Input
                          id="exam-end"
                          type="time"
                          value={finalExamForm.end_time}
                          onChange={(event) =>
                            updateExamField("end_time", event.target.value)
                          }
                          required
                        />
                      </div>
                      <div className="space-y-2 sm:col-span-3">
                        <Label htmlFor="exam-instructions">Instructions</Label>
                        <Input
                          id="exam-instructions"
                          value={finalExamForm.instructions}
                          onChange={(event) =>
                            updateExamField("instructions", event.target.value)
                          }
                          placeholder="Optional student instructions"
                        />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label>Venue Seat Allocations</Label>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={addExamAllocation}
                        >
                          <Plus className="size-4" />
                          Add Venue
                        </Button>
                      </div>
                      {finalExamForm.venue_allocations.map(
                        (allocation, index) => (
                          <div
                            key={index}
                            className="grid gap-2 rounded-lg border border-border p-3 sm:grid-cols-[minmax(0,1fr)_7rem_auto]"
                          >
                            <select
                              value={allocation.venue_id}
                              onChange={(event) =>
                                updateExamAllocation(
                                  index,
                                  "venue_id",
                                  event.target.value
                                )
                              }
                              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                              required
                            >
                              <option value="">Select venue</option>
                              {venues.map((venue) => (
                                <option key={venue.id} value={venue.id}>
                                  {venue.building_detail.name} - {venue.name} (
                                  {venue.capacity ?? "no capacity"})
                                </option>
                              ))}
                            </select>
                            <Input
                              type="number"
                              min="1"
                              value={allocation.seats}
                              onChange={(event) =>
                                updateExamAllocation(
                                  index,
                                  "seats",
                                  event.target.value
                                )
                              }
                              placeholder="Seats"
                              required
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              disabled={
                                finalExamForm.venue_allocations.length === 1
                              }
                              onClick={() => removeExamAllocation(index)}
                            >
                              <X className="size-4" />
                            </Button>
                          </div>
                        )
                      )}
                    </div>
                    <div className="flex justify-end gap-2">
                      {finalExamForm.exam_id ? (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setFinalExamForm(emptyExamForm())}
                        >
                          <X className="size-4" />
                          Cancel Edit
                        </Button>
                      ) : null}
                      <Button
                        type="submit"
                        disabled={
                          isSaving ||
                          Boolean(selectedExamOffering?.edit_window_error)
                        }
                      >
                        {isSaving ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <Save className="size-4" />
                        )}
                        {isSaving ? "Saving..." : "Save Final Exam"}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader className="gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      {scope?.name ?? "Unassigned"}
                    </CardTitle>
                    <CardDescription>
                      {filteredMeetings.length} of {meetings.length} class
                      entries shown.
                    </CardDescription>
                  </div>
                  <div className="relative w-full lg:w-80">
                    <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search schedule..."
                      className="pl-9"
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {filteredMeetings.length === 0 ? (
                    <p className="py-10 text-center text-sm text-muted-foreground">
                      No classes found.
                    </p>
                  ) : (
                    filteredMeetings.map((meeting) => (
                      <div
                        key={meeting.id}
                        className="rounded-lg border border-border bg-background p-4 shadow-sm"
                      >
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div className="min-w-0 space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono text-sm font-semibold text-primary">
                                {meeting.course.code}
                              </span>
                              <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                                Sec {meeting.section || "-"}
                              </span>
                              <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                                {meeting.class_type_label}
                              </span>
                              {meeting.is_single_week_adjustment ? (
                                <span className="rounded-md border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
                                  Single week
                                </span>
                              ) : null}
                            </div>
                            <h2 className="text-base font-semibold">
                              {meeting.course.title}
                            </h2>
                            <div className="grid gap-2 text-sm text-muted-foreground md:grid-cols-3">
                              <p className="flex items-center gap-2">
                                <CalendarClock className="size-4" />
                                {meeting.meeting_date ?? meeting.day_label}{" "}
                                {meeting.start_time} - {meeting.end_time}
                              </p>
                              <p className="flex items-center gap-2">
                                <MapPin className="size-4" />
                                {meeting.venue_detail
                                  ? `${meeting.venue_detail.building_detail.name} - ${meeting.venue_detail.name}`
                                  : "Venue missing"}
                              </p>
                              <p className="flex items-center gap-2">
                                <User className="size-4" />
                                {meeting.lecturer_detail?.name ??
                                  "Lecturer missing"}
                              </p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => startAdjustment(meeting)}
                            >
                              <CalendarClock className="size-4" />
                              Edit Week
                            </Button>
                            {meeting.is_single_week_adjustment ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => removeAdjustment(meeting)}
                              >
                                <Trash2 className="size-4" />
                                Remove
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base">
                    Single-Week Class Edit
                  </CardTitle>
                  <CardDescription>
                    Semester-wide changes stay in Offered Courses.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedMeeting && form ? (
                    <form className="space-y-4" onSubmit={saveAdjustment}>
                      <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                        <p className="font-medium">
                          {selectedMeeting.course.code}
                        </p>
                        <p className="mt-1 text-muted-foreground">
                          {selectedMeeting.course.title}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="meeting-date">Class Date</Label>
                        <Input
                          id="meeting-date"
                          type="date"
                          value={form.meeting_date}
                          onChange={(event) =>
                            updateField("meeting_date", event.target.value)
                          }
                          required
                        />
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="week-start">Start</Label>
                          <Input
                            id="week-start"
                            type="time"
                            value={form.start_time}
                            onChange={(event) =>
                              updateField("start_time", event.target.value)
                            }
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="week-end">End</Label>
                          <Input
                            id="week-end"
                            type="time"
                            value={form.end_time}
                            onChange={(event) =>
                              updateField("end_time", event.target.value)
                            }
                            required
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="week-venue">Venue</Label>
                        <select
                          id="week-venue"
                          value={form.venue_id}
                          onChange={(event) =>
                            updateField("venue_id", event.target.value)
                          }
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          required
                        >
                          <option value="">Select venue</option>
                          {venues.map((venue) => (
                            <option key={venue.id} value={venue.id}>
                              {venue.building_detail.name} - {venue.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="week-lecturer">Lecturer</Label>
                        <select
                          id="week-lecturer"
                          value={form.lecturer_id}
                          onChange={(event) =>
                            updateField("lecturer_id", event.target.value)
                          }
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          required
                        >
                          <option value="">Select lecturer</option>
                          {teachers.map((teacher) => (
                            <option key={teacher.id} value={teacher.id}>
                              {teacher.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="week-type">Type</Label>
                        <select
                          id="week-type"
                          value={form.class_type}
                          onChange={(event) =>
                            updateField("class_type", event.target.value)
                          }
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          required
                        >
                          {classTypes.map((classType) => (
                            <option
                              key={classType.value}
                              value={classType.value}
                            >
                              {classType.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="flex justify-end gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setSelectedMeeting(null)
                            setForm(null)
                          }}
                        >
                          <X className="size-4" />
                          Cancel
                        </Button>
                        <Button type="submit" disabled={isSaving}>
                          {isSaving ? (
                            <Loader2 className="size-4 animate-spin" />
                          ) : (
                            <Save className="size-4" />
                          )}
                          {isSaving ? "Saving..." : "Save"}
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <p className="text-sm leading-6 text-muted-foreground">
                      Select a class entry to adjust one week only.
                    </p>
                  )}
                </CardContent>
              </Card>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

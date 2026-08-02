"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Clock,
  Edit3,
  Loader2,
  MapPin,
  Save,
  Trash2,
  User,
  X,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

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
  credits: number
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

type ClassMeeting = {
  id: number
  day_of_week: number
  day_label: string
  start_time: string
  end_time: string
  lecturer: number | null
  venue: number | null
  class_type: string
  class_type_label: string
  lecturer_detail?: {
    id: number
    name: string
  } | null
  venue_detail?: Venue | null
}

type Offering = {
  id: number
  course: Course
  semester: Semester
  instructor: {
    id: number
    name: string
  } | null
  section: string
  capacity: number
  is_active: boolean
  meetings: ClassMeeting[]
}

type OfferedResponse = {
  title: string
  section: string
  scope: Scope
  scope_error?: string | null
  teachers: Teacher[]
  venues: Venue[]
  class_types: ClassType[]
  offerings: Offering[]
}

const DAY_LABELS: Record<number, string> = {
  1: "Monday",
  2: "Tuesday",
  3: "Wednesday",
  4: "Thursday",
  5: "Friday",
  6: "Saturday",
  7: "Sunday",
}

function meetingForm(meeting: ClassMeeting) {
  return {
    day_of_week: String(meeting.day_of_week),
    start_time: meeting.start_time.slice(0, 5),
    end_time: meeting.end_time.slice(0, 5),
    venue_id: meeting.venue ? String(meeting.venue) : "",
    lecturer_id: meeting.lecturer ? String(meeting.lecturer) : "",
    class_type: meeting.class_type,
  }
}

export default function ExecutiveOfferedCoursesPage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [scopeError, setScopeError] = useState("")
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [venues, setVenues] = useState<Venue[]>([])
  const [classTypes, setClassTypes] = useState<ClassType[]>([])
  const [offerings, setOfferings] = useState<Offering[]>([])
  const [selectedMeeting, setSelectedMeeting] = useState<ClassMeeting | null>(null)
  const [form, setForm] = useState<ReturnType<typeof meetingForm> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    try {
      setIsLoading(true)
      const data = await apiFetch<OfferedResponse>("/executive/courses/offered")
      setScope(data.scope)
      setScopeError(data.scope_error ?? "")
      setTeachers(data.teachers ?? [])
      setVenues(data.venues ?? [])
      setClassTypes(data.class_types ?? [])
      setOfferings(data.offerings ?? [])
      setError("")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load offered courses.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial data hydration needs to sync state after the API response arrives.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData()
  }, [])

  const totals = useMemo(() => {
    const classes = offerings.reduce((count, offering) => count + offering.meetings.length, 0)
    return { offerings: offerings.length, classes }
  }, [offerings])

  function startEditing(meeting: ClassMeeting) {
    setSelectedMeeting(meeting)
    setForm(meetingForm(meeting))
    setError("")
    setSuccess("")
  }

  function updateField(field: keyof ReturnType<typeof meetingForm>, value: string) {
    setForm((current) => (current ? { ...current, [field]: value } : current))
  }

  async function saveMeeting(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedMeeting || !form) return

    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/courses/offered?meeting_id=${selectedMeeting.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          day_of_week: Number(form.day_of_week),
          start_time: form.start_time,
          end_time: form.end_time,
          venue_id: Number(form.venue_id),
          lecturer_id: Number(form.lecturer_id),
          class_type: form.class_type,
        }),
      })
      setSuccess("Semester class schedule updated successfully.")
      setSelectedMeeting(null)
      setForm(null)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update schedule.")
    } finally {
      setIsSaving(false)
    }
  }

  async function removeOffering(offering: Offering) {
    if (!confirm(`Remove offering ${offering.course.code} ${offering.section}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/courses/offered?offering_id=${offering.id}`, {
        method: "DELETE",
      })
      setSuccess("Course offering removed successfully.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to remove offering.")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/courses", title: "Courses" },
          { href: "/executive/courses/offered", title: "Offered Courses" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Offered Courses
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Manage semester-wide class times, venues, and lecturers after conflict checks.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm sm:w-80">
            <div className="rounded-lg border border-border bg-background p-3">
              <p className="text-xs text-muted-foreground">Offerings</p>
              <p className="text-xl font-semibold">{totals.offerings}</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <p className="text-xs text-muted-foreground">Classes</p>
              <p className="text-xl font-semibold">{totals.classes}</p>
            </div>
          </div>
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
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-background px-4 py-3 text-sm">
                <span className="font-medium">{scope?.name ?? "Unassigned"}</span>
              </div>
              {offerings.length === 0 ? (
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardContent className="py-12 text-center text-sm text-muted-foreground">
                    No offered courses found.
                  </CardContent>
                </Card>
              ) : (
                offerings.map((offering) => (
                  <Card key={offering.id} className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-primary">
                            {offering.course.code}
                          </span>
                          <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            Sec {offering.section || "-"}
                          </span>
                          <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {offering.capacity} seats
                          </span>
                        </div>
                        <CardTitle className="mt-2 text-lg">{offering.course.title}</CardTitle>
                        <CardDescription>
                          {offering.semester.name}
                          {offering.semester.academic_session ? ` - ${offering.semester.academic_session}` : ""}
                        </CardDescription>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => removeOffering(offering)}>
                        <Trash2 className="size-4" />
                        Remove
                      </Button>
                    </CardHeader>
                    <CardContent className="grid gap-3 md:grid-cols-2">
                      {offering.meetings.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No semester classes scheduled.</p>
                      ) : (
                        offering.meetings.map((meeting) => (
                          <div key={meeting.id} className="rounded-lg border border-border bg-background p-3 text-sm">
                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-2">
                                <p className="font-medium">{meeting.class_type_label}</p>
                                <p className="flex items-center gap-2 text-muted-foreground">
                                  <Clock className="size-4" />
                                  {meeting.day_label}: {meeting.start_time} - {meeting.end_time}
                                </p>
                                <p className="flex items-center gap-2 text-muted-foreground">
                                  <MapPin className="size-4" />
                                  {meeting.venue_detail
                                    ? `${meeting.venue_detail.building_detail.name} - ${meeting.venue_detail.name}`
                                    : "Venue missing"}
                                </p>
                                <p className="flex items-center gap-2 text-muted-foreground">
                                  <User className="size-4" />
                                  {meeting.lecturer_detail?.name ?? "Lecturer missing"}
                                </p>
                              </div>
                              <Button variant="ghost" size="icon" onClick={() => startEditing(meeting)}>
                                <Edit3 className="size-4" />
                              </Button>
                            </div>
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CalendarClock className="size-5 text-primary" />
                  Semester Class Edit
                </CardTitle>
                <CardDescription>
                  Changes here apply to the semester class pattern.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedMeeting && form ? (
                  <form className="space-y-4" onSubmit={saveMeeting}>
                    <div className="space-y-2">
                      <Label htmlFor="edit-day">Day</Label>
                      <select
                        id="edit-day"
                        value={form.day_of_week}
                        onChange={(event) => updateField("day_of_week", event.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        {Object.entries(DAY_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="edit-start">Start</Label>
                        <Input
                          id="edit-start"
                          type="time"
                          value={form.start_time}
                          onChange={(event) => updateField("start_time", event.target.value)}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="edit-end">End</Label>
                        <Input
                          id="edit-end"
                          type="time"
                          value={form.end_time}
                          onChange={(event) => updateField("end_time", event.target.value)}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-venue">Venue</Label>
                      <select
                        id="edit-venue"
                        value={form.venue_id}
                        onChange={(event) => updateField("venue_id", event.target.value)}
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
                      <Label htmlFor="edit-lecturer">Lecturer</Label>
                      <select
                        id="edit-lecturer"
                        value={form.lecturer_id}
                        onChange={(event) => updateField("lecturer_id", event.target.value)}
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
                      <Label htmlFor="edit-type">Type</Label>
                      <select
                        id="edit-type"
                        value={form.class_type}
                        onChange={(event) => updateField("class_type", event.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        required
                      >
                        {classTypes.map((classType) => (
                          <option key={classType.value} value={classType.value}>
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
                        {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                        {isSaving ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </form>
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    Choose a class meeting to adjust the semester-wide schedule.
                  </p>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}

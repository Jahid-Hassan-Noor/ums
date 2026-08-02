"use client"

import { useEffect, useState } from "react"
import {
  AlertCircle,
  Armchair,
  Calendar,
  CheckCircle2,
  Clock,
  GraduationCap,
  Loader2,
  MapPin,
  Plus,
  Trash2,
  User,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type Course = {
  id: number
  code: string
  title: string
  credits: number
}

type School = {
  id: number
  code: string
  name: string
}

type Semester = {
  id: number
  name: string
  academic_session: string
  start_date: string
  end_date: string
}

type Teacher = {
  id: number
  name: string
  staff_id: string
  designation: string
}

type Building = {
  id: number
  code: string
  name: string
}

type Venue = {
  id: number
  building: number
  building_detail: Building
  code: string
  name: string
  floor: string
  capacity: number | null
}

type ClassType = {
  value: string
  label: string
}

type ClassMeeting = {
  id: number
  day_of_week: number
  start_time: string
  end_time: string
  lecturer: number | null
  venue: number | null
  class_type: string
  class_type_label: string
  venue_detail?: Venue
  lecturer_detail?: {
    id: number
    name: string
  }
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

type OfferResponse = {
  title: string
  section: string
  courses: Course[]
  schools: School[]
  semesters: Semester[]
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

function timeToMinutes(value: string): number {
  const [hours, minutes] = value.split(":").map(Number)
  return hours * 60 + minutes
}

export default function ExecutiveOfferCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [schools, setSchools] = useState<School[]>([])
  const [semesters, setSemesters] = useState<Semester[]>([])
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [venues, setVenues] = useState<Venue[]>([])
  const [classTypes, setClassTypes] = useState<ClassType[]>([])
  const [offerings, setOfferings] = useState<Offering[]>([])

  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  // Form State
  const [courseId, setCourseId] = useState("")
  const [semesterId, setSemesterId] = useState("")
  const [instructorId, setInstructorId] = useState("")
  const [section, setSection] = useState("A")
  const [capacity, setCapacity] = useState("40")
  const [eligibleSchoolIds, setEligibleSchoolIds] = useState<number[]>([])
  const [meetings, setMeetings] = useState<Array<{
    day_of_week: number
    start_time: string
    end_time: string
    venue_id: string
    lecturer_id: string
    class_type: string
  }>>([])

  // Current adding meeting state
  const [newMeeting, setNewMeeting] = useState({
    day_of_week: 1,
    start_time: "09:00",
    end_time: "10:30",
    venue_id: "",
    lecturer_id: "",
    class_type: "lecture",
  })

  const loadData = async () => {
    try {
      setIsLoading(true)
      const data = await apiFetch<OfferResponse>("/executive/courses/offer")
      setCourses(data.courses || [])
      setSchools(data.schools || [])
      setSemesters(data.semesters || [])
      setTeachers(data.teachers || [])
      setVenues(data.venues || [])
      setClassTypes(data.class_types || [])
      setOfferings(data.offerings || [])

      if (data.semesters && data.semesters.length > 0) {
        setSemesterId(String(data.semesters[0].id))
      }
      if (data.venues && data.venues.length > 0) {
        setNewMeeting((m) => ({ ...m, venue_id: String(data.venues[0].id) }))
      }
      if (data.teachers && data.teachers.length > 0 && !newMeeting.lecturer_id) {
        setNewMeeting((m) => ({ ...m, lecturer_id: String(data.teachers[0].id) }))
      }
      if (data.class_types && data.class_types.length > 0) {
        setNewMeeting((m) => ({ ...m, class_type: data.class_types[0].value }))
      }
      setError("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load academic data.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial data hydration needs to sync state after the API response arrives.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleAddMeetingSlot = () => {
    if (!newMeeting.venue_id) {
      setError("Please select a venue for this meeting slot.")
      return
    }
    if (!newMeeting.lecturer_id) {
      setError("Please select a lecturer for this meeting slot.")
      return
    }
    if (!newMeeting.class_type) {
      setError("Please select lecture class or lab class.")
      return
    }

    const startMinutes = timeToMinutes(newMeeting.start_time)
    const endMinutes = timeToMinutes(newMeeting.end_time)
    if (startMinutes >= endMinutes) {
      setError("Meeting end time must be after the start time.")
      return
    }

    const hasConflict = meetings.some((meeting) => {
      if (meeting.day_of_week !== newMeeting.day_of_week) return false
      const meetingStart = timeToMinutes(meeting.start_time)
      const meetingEnd = timeToMinutes(meeting.end_time)
      const overlaps = startMinutes < meetingEnd && endMinutes > meetingStart
      if (!overlaps) return false
      return (
        meeting.venue_id === newMeeting.venue_id ||
        meeting.lecturer_id === newMeeting.lecturer_id
      )
    })

    if (hasConflict) {
      setError("This venue or lecturer already has an overlapping meeting slot.")
      return
    }

    setError("")
    setMeetings((m) => [...m, { ...newMeeting }])
  }

  const handleRemoveMeetingSlot = (idx: number) => {
    setMeetings((m) => m.filter((_, i) => i !== idx))
  }

  const handleOfferCourse = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")

    if (!courseId) {
      setError("Please select a course.")
      return
    }
    if (!semesterId) {
      setError("Please select a semester.")
      return
    }
    if (meetings.length === 0) {
      setError("Add at least one lecture or lab class.")
      return
    }

    try {
      setIsSubmitting(true)
      const payload = {
        course_id: parseInt(courseId),
        semester_id: parseInt(semesterId),
        instructor_id: instructorId ? parseInt(instructorId) : null,
        section,
        capacity: parseInt(capacity),
        eligible_school_ids: eligibleSchoolIds,
        meetings,
      }

      await apiFetch("/executive/courses/offer", {
        method: "POST",
        body: JSON.stringify(payload),
      })

      setSuccess("Course offering created and classes scheduled in venues successfully.")
      // Reset form
      setCourseId("")
      setInstructorId("")
      setSection("A")
      setCapacity("40")
      setEligibleSchoolIds([])
      setMeetings([])
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error offering course.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteOffering = async (id: number) => {
    if (!confirm("Are you sure you want to cancel this course offering? All scheduled classes will be removed.")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/courses/offer?offering_id=${id}`, {
        method: "DELETE",
      })
      setSuccess("Offering canceled successfully.")
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error canceling offering.")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/courses/offer", title: "Offer Courses" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              Executive Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Offer Courses & Class Scheduler
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Publish semester offerings for academic courses, assign lecturers, and schedule class meetings in physical venues.
              </p>
            </div>
          </div>
        </section>

        {/* Feedback Banners */}
        {error && (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}
        {success && (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        )}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1.2fr_1.8fr]">
            {/* Offer Course Form Panel */}
            <Card className="border-border/70 bg-card/95 shadow-sm h-fit">
              <CardHeader>
                <CardTitle className="text-lg">Offer New Course</CardTitle>
                <CardDescription>Setup details and allocate physical venue timeslots.</CardDescription>
              </CardHeader>
              <form onSubmit={handleOfferCourse}>
                <CardContent className="space-y-4">
                  {/* Select Semester */}
                  <div className="grid gap-2">
                    <Label htmlFor="sem-select">Academic Semester</Label>
                    <select
                      id="sem-select"
                      required
                      value={semesterId}
                      onChange={(e) => setSemesterId(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background"
                    >
                      {semesters.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                          {s.academic_session ? ` (${s.academic_session})` : ""}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Select Course */}
                  <div className="grid gap-2">
                    <Label htmlFor="course-select">Academic Course</Label>
                    <select
                      id="course-select"
                      required
                      value={courseId}
                      onChange={(e) => setCourseId(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background"
                    >
                      <option value="">-- Choose Course --</option>
                      {courses.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.code} - {c.title} ({c.credits} CH)
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Instructor & Details */}
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="sm:col-span-2 grid gap-2">
                      <Label htmlFor="teacher-select">Primary Instructor</Label>
                      <select
                        id="teacher-select"
                        value={instructorId}
                        onChange={(e) => {
                          const value = e.target.value
                          setInstructorId(value)
                          setNewMeeting((m) => ({ ...m, lecturer_id: value }))
                        }}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background"
                      >
                        <option value="">-- Assign Instructor (Optional) --</option>
                        {teachers.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="section-input">Section</Label>
                      <Input
                        id="section-input"
                        placeholder="e.g. A"
                        required
                        value={section}
                        onChange={(e) => setSection(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="cap-input">Class Seating Capacity</Label>
                    <Input
                      id="cap-input"
                      type="number"
                      min="1"
                      required
                      value={capacity}
                      onChange={(e) => setCapacity(e.target.value)}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label>Other Eligible Schools</Label>
                    <p className="text-xs leading-5 text-muted-foreground">
                      Students from this course&apos;s own school are eligible automatically. Select any
                      additional schools whose students may register.
                    </p>
                    {schools.length ? (
                      <div className="grid gap-2 rounded-md border border-border bg-background p-3 sm:grid-cols-2">
                        {schools.map((school) => (
                          <label key={school.id} className="flex items-start gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={eligibleSchoolIds.includes(school.id)}
                              onChange={(event) =>
                                setEligibleSchoolIds((current) =>
                                  event.target.checked
                                    ? [...current, school.id]
                                    : current.filter((id) => id !== school.id)
                                )
                              }
                              className="mt-1"
                            />
                            <span>
                              <span className="font-medium">{school.code}</span>
                              <span className="block text-xs text-muted-foreground">{school.name}</span>
                            </span>
                          </label>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No other active schools are available.</p>
                    )}
                  </div>

                  {/* Schedule Meeting Allocation (Sub-form) */}
                  <div className="rounded-lg border bg-muted/20 p-4 space-y-4">
                    <div className="flex items-center gap-1.5 font-semibold text-foreground text-sm">
                      <Calendar className="size-4 text-primary" />
                      <span>Class Schedule Slot</span>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="grid gap-1.5">
                        <Label htmlFor="meet-day" className="text-xs">Day</Label>
                        <select
                          id="meet-day"
                          value={newMeeting.day_of_week}
                          onChange={(e) => setNewMeeting({ ...newMeeting, day_of_week: parseInt(e.target.value) })}
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-xs shadow-sm"
                        >
                          {Object.entries(DAY_LABELS).map(([val, label]) => (
                            <option key={val} value={val}>{label}</option>
                          ))}
                        </select>
                      </div>
                      <div className="grid gap-1.5">
                        <Label htmlFor="meet-start" className="text-xs">Start Time</Label>
                        <Input
                          id="meet-start"
                          type="time"
                          className="h-8 text-xs"
                          value={newMeeting.start_time}
                          onChange={(e) => setNewMeeting({ ...newMeeting, start_time: e.target.value })}
                        />
                      </div>
                      <div className="grid gap-1.5">
                        <Label htmlFor="meet-end" className="text-xs">End Time</Label>
                        <Input
                          id="meet-end"
                          type="time"
                          className="h-8 text-xs"
                          value={newMeeting.end_time}
                          onChange={(e) => setNewMeeting({ ...newMeeting, end_time: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="grid gap-1.5">
                        <Label htmlFor="meet-venue" className="text-xs">Venue</Label>
                        <select
                          id="meet-venue"
                          value={newMeeting.venue_id}
                          onChange={(e) => setNewMeeting({ ...newMeeting, venue_id: e.target.value })}
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-xs shadow-sm"
                        >
                          <option value="">Select venue</option>
                          {venues.map((v) => (
                            <option key={v.id} value={v.id}>
                              {v.building_detail.name} - {v.name} ({v.capacity ?? "-"} seats)
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="grid gap-1.5">
                        <Label htmlFor="meet-lecturer" className="text-xs">Lecturer</Label>
                        <select
                          id="meet-lecturer"
                          value={newMeeting.lecturer_id}
                          onChange={(e) => setNewMeeting({ ...newMeeting, lecturer_id: e.target.value })}
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-xs shadow-sm"
                        >
                          <option value="">Select lecturer</option>
                          {teachers.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid gap-1.5">
                      <Label htmlFor="meet-type" className="text-xs">Class Type</Label>
                      <select
                        id="meet-type"
                        value={newMeeting.class_type}
                        onChange={(e) => setNewMeeting({ ...newMeeting, class_type: e.target.value })}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-xs shadow-sm"
                      >
                        {classTypes.map((classType) => (
                          <option key={classType.value} value={classType.value}>
                            {classType.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex justify-end pt-1">
                      <Button type="button" size="sm" variant="secondary" onClick={handleAddMeetingSlot}>
                        <Plus className="mr-1 size-3.5" />
                        Add Meeting Slot
                      </Button>
                    </div>
                  </div>

                  {/* Scheduled Slots Review */}
                  {meetings.length > 0 && (
                    <div className="space-y-2 border-t pt-3">
                      <Label className="text-xs font-semibold">Allocated Slots Checklist</Label>
                      <div className="space-y-1.5">
                        {meetings.map((m, idx) => {
                          const matchingVenue = venues.find((v) => String(v.id) === m.venue_id)
                          const matchingLecturer = teachers.find((t) => String(t.id) === m.lecturer_id)
                          const matchingClassType = classTypes.find((type) => type.value === m.class_type)
                          return (
                            <div key={idx} className="flex items-center justify-between gap-3 bg-muted/40 p-2.5 rounded-lg border text-xs">
                              <div className="space-y-1">
                                <div className="font-medium text-foreground">
                                  {matchingClassType?.label ?? m.class_type}
                                </div>
                                <div className="flex items-center gap-1.5 font-medium text-foreground">
                                  <Clock className="size-3.5 text-muted-foreground" />
                                  <span>{DAY_LABELS[m.day_of_week]}: {m.start_time} - {m.end_time}</span>
                                </div>
                                <div className="flex items-center gap-1.5 text-muted-foreground">
                                  <MapPin className="size-3" />
                                  <span>{matchingVenue ? `${matchingVenue.building_detail.name} - ${matchingVenue.name}` : "Unknown"}</span>
                                </div>
                                {matchingLecturer && (
                                  <div className="flex items-center gap-1.5 text-muted-foreground">
                                    <User className="size-3" />
                                    <span>{matchingLecturer.name}</span>
                                  </div>
                                )}
                              </div>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="size-6 text-destructive hover:bg-destructive/10"
                                onClick={() => handleRemoveMeetingSlot(idx)}
                              >
                                <Trash2 className="size-3.5" />
                              </Button>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </CardContent>
                <div className="border-t p-4 flex justify-end">
                  <Button type="submit" disabled={isSubmitting || !courseId || meetings.length === 0}>
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-1.5 size-4 animate-spin" />
                        Offering...
                      </>
                    ) : (
                      "Publish Course Offering"
                    )}
                  </Button>
                </div>
              </form>
            </Card>

            {/* Current Offered Courses Grid */}
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Offered Semestral Courses</CardTitle>
                <CardDescription>Academic listings currently active on scheduling slots.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {offerings.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">No active course offerings found.</p>
                ) : (
                  offerings.map((off) => (
                    <div
                      key={off.id}
                      className="rounded-lg border border-border bg-background p-5 shadow-sm space-y-4 transition-colors hover:border-primary/20"
                    >
                      <div className="flex items-start justify-between gap-4 border-b pb-3">
                        <div className="space-y-1.5 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-foreground text-base">{off.course.title}</span>
                            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-mono font-bold text-primary">
                              {off.course.code}
                            </span>
                            <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                              Sec {off.section}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1 font-medium">
                              <GraduationCap className="size-3.5" />
                              {off.semester.name}
                              {off.semester.academic_session ? ` - ${off.semester.academic_session}` : ""}
                            </span>
                            {off.instructor && (
                              <span className="flex items-center gap-1">
                                <User className="size-3.5" />
                                {off.instructor.name}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Armchair className="size-3.5" />
                              {off.capacity} Cap
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive hover:bg-destructive/10 h-8 px-2"
                          onClick={() => handleDeleteOffering(off.id)}
                        >
                          <Trash2 className="size-3.5 mr-1" />
                          Cancel
                        </Button>
                      </div>

                      {/* Scheduled meetings */}
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Scheduled Slots</p>
                        {off.meetings && off.meetings.length > 0 ? (
                          <div className="grid gap-2 sm:grid-cols-2">
                            {off.meetings.map((m) => (
                              <div key={m.id} className="rounded border bg-muted/30 p-3 text-xs flex flex-col justify-between">
                                <div className="space-y-1">
                                  <div className="font-semibold text-foreground">
                                    {m.class_type_label}
                                  </div>
                                  <div className="flex items-center gap-1.5 font-medium text-foreground">
                                    <Clock className="size-3.5 text-primary shrink-0" />
                                    <span>{DAY_LABELS[m.day_of_week]}: {m.start_time.slice(0, 5)} - {m.end_time.slice(0, 5)}</span>
                                  </div>
                                  {m.venue_detail && (
                                    <div className="flex items-start gap-1.5 text-muted-foreground">
                                      <MapPin className="size-3.5 text-success shrink-0 mt-0.5" />
                                      <span>
                                        {m.venue_detail.building_detail.name} - {m.venue_detail.name} (Fl {m.venue_detail.floor})
                                      </span>
                                    </div>
                                  )}
                                  {m.lecturer_detail && (
                                    <div className="flex items-center gap-1.5 text-muted-foreground pl-5">
                                      <span>Lec: {m.lecturer_detail.name}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-amber-600 italic">No scheduled class slots for this offering.</p>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}

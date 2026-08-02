"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useRef, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileText,
  FolderOpen,
  Loader2,
  Megaphone,
  Paperclip,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
  Users,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type CourseListView = "all" | "current" | "previous"
type WorkspaceView = "overview" | "resources" | "assignments"
type ContentAction =
  | "create_section"
  | "create_folder"
  | "create_resource"
  | "create_announcement"
  | "create_activity"
  | "update_assessment"

type Choice = { value: string; label: string }

type AssessmentPlan = {
  has_final_exam: boolean
  coursework_percentage: string
  final_exam_percentage: string
  assessment_overview: string
  study_guide: string | null
  study_guide_name: string
}

type TeacherCourse = {
  id: number
  code: string
  title: string
  section: string
  semester: string
  semester_active: boolean
  has_lab: boolean
  is_active: boolean
  assessment: AssessmentPlan
  has_study_guide: boolean
  assignment_count: number
  section_count: number
  resource_count: number
  student_count: number
}

type Resource = {
  id: number
  resource_type: string
  title: string
  description: string
  file: string | null
  url: string
  content: string
  visible_from: string | null
  section_id: number | null
  folder_id: number | null
  is_published: boolean
}

type Assignment = {
  id: number
  title: string
  description: string
  due_date: string | null
  max_score: string
  status: string
}

type Activity = {
  id: number
  title: string
  activity_type: string
  due_at: string | null
  completion_policy: string
  is_required: boolean
}

type Section = {
  id: number
  title: string
  summary: string
  section_type: string
  week_number: number | null
  starts_on: string | null
  ends_on: string | null
  is_published: boolean
  resources: Resource[]
  assignments: Assignment[]
  activities: Activity[]
}

type Folder = {
  id: number
  parent_id: number | null
  title: string
  description: string
  is_published: boolean
  resources: Resource[]
}

type Announcement = {
  id: number
  title: string
  body: string
  announcement_type: string
  assignment_id: number | null
  assignment_title: string
  assignment_collaboration_mode: "" | "individual" | "group"
  scheduled_for: string | null
  visible_from: string | null
  is_published: boolean
  created_at: string | null
  slots: AnnouncementSlot[]
}

type AnnouncementSlot = {
  id: number
  label: string
  starts_at: string
  ends_at: string | null
  capacity: number
  selection_type: "individual" | "group"
  selection_type_label: string
  selected_count: number
  remaining: number
  selections?: Array<{
    id: number
    student: string
    group_name: string
  }>
}

type AnnouncementSlotDraft = {
  key: string
  label: string
  starts_at: string
  ends_at: string
  capacity: number
  selection_type: "individual" | "group"
  instructions: string
}

type CourseContent = {
  course: {
    id: number
    code: string
    title: string
    section: string
    has_lab: boolean
    semester: string
  }
  assessment: AssessmentPlan
  section_types: Choice[]
  announcement_types: Choice[]
  resource_types: Choice[]
  activity_types: Choice[]
  completion_policies: Choice[]
  sections: Section[]
  folders: Folder[]
  resources: Resource[]
  announcements: Announcement[]
  assignments: Assignment[]
  activities: Activity[]
  meetings?: Array<{ id: number }>
}

function endpointForCourses(view: CourseListView) {
  if (view === "current") return "/teacher/courses/current"
  if (view === "previous") return "/teacher/courses/previous"
  return "/teacher/courses"
}

function titleForCourses(view: CourseListView) {
  if (view === "current") return "Current Courses"
  if (view === "previous") return "Previous Courses"
  return "Teaching Courses"
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "No deadline"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "No deadline"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function assessmentSummary(assessment: AssessmentPlan) {
  if (!assessment.has_final_exam) return "Coursework only"
  return `${assessment.coursework_percentage}% coursework / ${assessment.final_exam_percentage}% final`
}

function SelectField({
  label,
  name,
  options,
  placeholder,
  required,
}: {
  label: string
  name: string
  options: Choice[]
  placeholder?: string
  required?: boolean
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <select
        id={name}
        name={name}
        required={required}
        className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
      >
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

function ResourceLink({ resource }: { resource: Resource }) {
  const destination = resource.file || resource.url
  const body = (
    <div className="flex items-start gap-3">
      <Paperclip className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <p className="font-medium">{resource.title}</p>
        {resource.description ? <p className="mt-1 text-sm text-muted-foreground">{resource.description}</p> : null}
        {resource.content ? <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{resource.content}</p> : null}
      </div>
    </div>
  )
  return destination ? (
    <a
      href={destination}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border bg-background p-3 transition hover:bg-muted/40"
    >
      {body}
    </a>
  ) : (
    <div className="rounded-lg border bg-background p-3">{body}</div>
  )
}

export function TeacherCoursesPage({ view = "all" }: { view?: CourseListView }) {
  const [courses, setCourses] = useState<TeacherCourse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadCourses = useCallback(async () => {
    const response = await apiFetch<{ courses: TeacherCourse[] }>(endpointForCourses(view))
    setCourses(response.courses)
  }, [view])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCourses()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load courses."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadCourses])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/courses", title: "Courses" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{titleForCourses(view)}</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Open a course workspace to publish learning materials, announcements, activities, and assignments.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant={view === "current" ? "default" : "outline"} render={<Link href="/teacher/courses/current" />}>
              Current
            </Button>
            <Button variant={view === "previous" ? "default" : "outline"} render={<Link href="/teacher/courses/previous" />}>
              Previous
            </Button>
            <Button variant="outline" onClick={() => void loadCourses()}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 size-4" />
            {error}
          </div>
        ) : null}
        {loading ? (
          <div className="flex h-56 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : courses.length ? (
          <section className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
            {courses.map((course) => (
              <Card key={course.id} className="border-border/70 shadow-sm">
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardDescription>
                        {course.code} / Section {course.section}
                      </CardDescription>
                      <CardTitle className="mt-1">{course.title}</CardTitle>
                    </div>
                    <Badge variant="outline">{course.semester_active ? "Current" : "Previous"}</Badge>
                  </div>
                  <CardDescription>{course.semester}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <p><Users className="mr-2 inline size-4" />{course.student_count} students</p>
                    <p><FolderOpen className="mr-2 inline size-4" />{course.section_count} sections</p>
                    <p><Paperclip className="mr-2 inline size-4" />{course.resource_count} resources</p>
                    <p><FileText className="mr-2 inline size-4" />{course.assignment_count} assignments</p>
                  </div>
                  <div className="rounded-lg border bg-background p-3 text-sm">
                    <p className="font-medium"><ClipboardList className="mr-2 inline size-4" />{assessmentSummary(course.assessment)}</p>
                    <p className="mt-1 text-muted-foreground">
                      {course.has_study_guide ? "Study guide uploaded" : "Study guide pending"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button render={<Link href={`/teacher/courses/${course.id}`} />}>Open workspace</Button>
                    <Button variant="outline" render={<Link href={`/teacher/courses/${course.id}/resources`} />}>
                      Resources
                    </Button>
                    <Button variant="outline" render={<Link href={`/teacher/courses/${course.id}/assignments`} />}>
                      Assignments
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </section>
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              No courses are assigned to this teacher for the selected period.
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}

export function TeacherCourseWorkspacePage({
  courseId,
  view = "overview",
}: {
  courseId: string
  view?: WorkspaceView
}) {
  const [data, setData] = useState<CourseContent | null>(null)
  const [action, setAction] = useState<ContentAction>("create_section")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [announcementSlots, setAnnouncementSlots] = useState<AnnouncementSlotDraft[]>([])
  const formRef = useRef<HTMLFormElement>(null)

  const loadWorkspace = useCallback(async () => {
    const response = await apiFetch<CourseContent>(`/teacher/courses/${courseId}`)
    setData(response)
  }, [courseId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadWorkspace()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load course workspace."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadWorkspace])

  async function saveContent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const formData = new FormData(event.currentTarget)
      formData.set("action", action)
      if (action === "create_announcement") {
        formData.set(
          "slots",
          JSON.stringify(
            announcementSlots.map((slot) => ({
              label: slot.label,
              starts_at: slot.starts_at,
              ends_at: slot.ends_at,
              capacity: slot.capacity,
              selection_type: slot.selection_type,
              instructions: slot.instructions,
            }))
          )
        )
      }
      const response = await apiFetch<{ message: string }>(`/teacher/courses/${courseId}/resources`, {
        method: "POST",
        body: formData,
      })
      setSuccess(response.message)
      formRef.current?.reset()
      setAnnouncementSlots([])
      await loadWorkspace()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save course content.")
    } finally {
      setSaving(false)
    }
  }

  const sectionOptions = data?.sections.map((section) => ({ value: String(section.id), label: section.title })) ?? []
  const folderOptions = data?.folders.map((folder) => ({ value: String(folder.id), label: folder.title })) ?? []
  const assignmentOptions = data?.assignments.map((assignment) => ({ value: String(assignment.id), label: assignment.title })) ?? []
  const resourceOptions = [
    ...(data?.resources ?? []),
    ...(data?.sections.flatMap((section) => section.resources) ?? []),
    ...(data?.folders.flatMap((folder) => folder.resources) ?? []),
  ].map((resource) => ({ value: String(resource.id), label: resource.title }))

  function addAnnouncementSlot() {
    setAnnouncementSlots((current) => [
      ...current,
      {
        key: `${Date.now()}-${current.length}`,
        label: "",
        starts_at: "",
        ends_at: "",
        capacity: 1,
        selection_type: "individual",
        instructions: "",
      },
    ])
  }

  function updateAnnouncementSlot(
    key: string,
    field: keyof Omit<AnnouncementSlotDraft, "key">,
    value: string | number
  ) {
    setAnnouncementSlots((current) =>
      current.map((slot) => (slot.key === key ? { ...slot, [field]: value } : slot))
    )
  }

  function removeAnnouncementSlot(key: string) {
    setAnnouncementSlots((current) => current.filter((slot) => slot.key !== key))
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/courses", title: "Courses" },
          { href: `/teacher/courses/${courseId}`, title: data?.course.code ?? "Course" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 size-4" />
            {error}
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4" />
            {success}
          </div>
        ) : null}

        {loading ? (
          <div className="flex h-56 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : data ? (
          <>
            <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-medium text-primary">{data.course.code} / Section {data.course.section}</p>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{data.course.title}</h1>
                <p className="mt-2 text-sm text-muted-foreground">{data.course.semester}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant={view === "overview" ? "default" : "outline"} render={<Link href={`/teacher/courses/${courseId}`} />}>
                  Overview
                </Button>
                <Button variant={view === "resources" ? "default" : "outline"} render={<Link href={`/teacher/courses/${courseId}/resources`} />}>
                  Resources
                </Button>
                <Button variant={view === "assignments" ? "default" : "outline"} render={<Link href={`/teacher/courses/${courseId}/assignments`} />}>
                  Assignments
                </Button>
                <Button variant="outline" render={<Link href={`/teacher/assignments/create?offering_id=${courseId}`} />}>
                  <Plus className="size-4" />
                  New assignment
                </Button>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <div className="space-y-5">
                {view !== "assignments" && data.announcements.length ? (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2"><Megaphone className="size-5" />Announcements</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {data.announcements.map((announcement) => (
                        <div key={announcement.id} className="rounded-lg border bg-background p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-medium">{announcement.title}</p>
                            <Badge variant="outline">{announcement.announcement_type}</Badge>
                          </div>
                          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{announcement.body}</p>
                          {announcement.slots.length ? (
                            <div className="mt-4 space-y-2 border-t pt-4">
                              {announcement.slots.map((slot) => (
                                <div key={slot.id} className="rounded-lg border p-3 text-sm">
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <p className="font-medium">{slot.label || formatDateTime(slot.starts_at)}</p>
                                    <Badge variant="outline">
                                      {slot.selected_count}/{slot.capacity} {slot.selection_type_label.toLowerCase()}
                                    </Badge>
                                  </div>
                                  <p className="mt-1 text-muted-foreground">
                                    {formatDateTime(slot.starts_at)}
                                    {slot.ends_at ? ` – ${formatDateTime(slot.ends_at)}` : ""}
                                  </p>
                                  {slot.selections?.length ? (
                                    <p className="mt-2 text-xs text-muted-foreground">
                                      Selected: {slot.selections.map((selection) =>
                                        selection.group_name
                                          ? `${selection.group_name} (${selection.student})`
                                          : selection.student
                                      ).join(", ")}
                                    </p>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ) : null}

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2"><ClipboardList className="size-5" />Assessment plan</CardTitle>
                    <CardDescription>{assessmentSummary(data.assessment)}</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-lg border bg-background p-3">
                      <p className="text-xs text-muted-foreground">Coursework</p>
                      <p className="mt-1 text-xl font-semibold">{data.assessment.coursework_percentage}%</p>
                    </div>
                    <div className="rounded-lg border bg-background p-3">
                      <p className="text-xs text-muted-foreground">Final Exam</p>
                      <p className="mt-1 text-xl font-semibold">
                        {data.assessment.has_final_exam ? `${data.assessment.final_exam_percentage}%` : "None"}
                      </p>
                    </div>
                    <div className="rounded-lg border bg-background p-3">
                      <p className="text-xs text-muted-foreground">Study Guide</p>
                      {data.assessment.study_guide ? (
                        <Button className="mt-2" size="sm" variant="outline" render={<a href={data.assessment.study_guide} target="_blank" rel="noreferrer" />}>
                          <FileText className="size-4" />
                          Open
                        </Button>
                      ) : (
                        <p className="mt-1 text-sm font-medium">Pending</p>
                      )}
                    </div>
                    {data.assessment.assessment_overview ? (
                      <p className="whitespace-pre-wrap rounded-lg border bg-background p-3 text-sm leading-6 text-muted-foreground sm:col-span-3">
                        {data.assessment.assessment_overview}
                      </p>
                    ) : null}
                  </CardContent>
                </Card>

                {view === "assignments" ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Course Assignments</CardTitle>
                      <CardDescription>Publication, deadlines, submissions, rubrics, and feedback.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {data.assignments.length ? data.assignments.map((assignment) => (
                        <div key={assignment.id} className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="font-medium">{assignment.title}</p>
                              <Badge variant="outline">{assignment.status}</Badge>
                            </div>
                            <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(assignment.due_date)} / {assignment.max_score} marks</p>
                          </div>
                          <Button variant="outline" render={<Link href={`/teacher/assignments/${assignment.id}`} />}>
                            Review
                          </Button>
                        </div>
                      )) : <p className="py-8 text-center text-sm text-muted-foreground">No assignments created yet.</p>}
                    </CardContent>
                  </Card>
                ) : (
                  <>
                    {data.folders.length ? (
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2"><FolderOpen className="size-5" />Resource folders</CardTitle>
                        </CardHeader>
                        <CardContent className="grid gap-4 md:grid-cols-2">
                          {data.folders.map((folder) => (
                            <div key={folder.id} className="rounded-lg border bg-background p-4">
                              <p className="font-medium">{folder.title}</p>
                              {folder.description ? <p className="mt-1 text-sm text-muted-foreground">{folder.description}</p> : null}
                              <div className="mt-3 space-y-2">
                                {folder.resources.map((resource) => <ResourceLink key={resource.id} resource={resource} />)}
                              </div>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    ) : null}

                    {data.sections.map((section) => (
                      <Card key={section.id}>
                        <CardHeader>
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <CardDescription>{section.week_number ? `Week ${section.week_number}` : section.section_type}</CardDescription>
                              <CardTitle>{section.title}</CardTitle>
                            </div>
                            <Badge variant="outline">{section.is_published ? "Published" : "Draft"}</Badge>
                          </div>
                          {section.summary ? <CardDescription>{section.summary}</CardDescription> : null}
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {section.resources.map((resource) => <ResourceLink key={resource.id} resource={resource} />)}
                          {section.assignments.map((assignment) => (
                            <Link key={assignment.id} href={`/teacher/assignments/${assignment.id}`} className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/40">
                              <span><FileText className="mr-2 inline size-4" />{assignment.title}</span>
                              <span className="text-sm text-muted-foreground">{formatDateTime(assignment.due_date)}</span>
                            </Link>
                          ))}
                          {section.activities.map((activity) => (
                            <div key={activity.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                              <span><CalendarClock className="mr-2 inline size-4" />{activity.title}</span>
                              <span className="text-muted-foreground">{formatDateTime(activity.due_at)}</span>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    ))}
                  </>
                )}
              </div>

              <Card className="h-fit">
                <CardHeader>
                  <CardTitle>Add learning content</CardTitle>
                  <CardDescription>Create a section, folder, resource, announcement, or deadline activity.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form
                    key={`${action}-${data.assessment.coursework_percentage}-${data.assessment.final_exam_percentage}-${data.assessment.study_guide_name}`}
                    ref={formRef}
                    className="space-y-4"
                    onSubmit={saveContent}
                  >
                    <div className="space-y-2">
                      <Label htmlFor="content-action">Content type</Label>
                      <select
                      id="content-action"
                      value={action}
                      onChange={(event) => setAction(event.target.value as ContentAction)}
                      className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
                    >
                        <option value="create_section">Course section</option>
                        <option value="create_folder">Resource folder</option>
                        <option value="create_resource">Resource</option>
                        <option value="create_announcement">Announcement</option>
                        <option value="create_activity">Activity deadline</option>
                        <option value="update_assessment">Assessment plan & study guide</option>
                      </select>
                    </div>
                    {action !== "update_assessment" ? (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="content-title">Title</Label>
                          <Input id="content-title" name="title" required />
                        </div>
                        {action !== "create_activity" ? (
                          <div className="space-y-2">
                            <Label htmlFor="content-description">{action === "create_announcement" ? "Message" : "Description"}</Label>
                            <Textarea
                              id="content-description"
                              name={action === "create_announcement" ? "body" : action === "create_section" ? "summary" : "description"}
                            />
                          </div>
                        ) : null}
                      </>
                    ) : null}

                    {action === "create_section" ? (
                      <>
                        <SelectField label="Section type" name="section_type" options={data.section_types} />
                        <div className="space-y-2"><Label htmlFor="week_number">Week number</Label><Input id="week_number" name="week_number" type="number" min="1" /></div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-2"><Label htmlFor="starts_on">Starts</Label><Input id="starts_on" name="starts_on" type="date" /></div>
                          <div className="space-y-2"><Label htmlFor="ends_on">Ends</Label><Input id="ends_on" name="ends_on" type="date" /></div>
                        </div>
                      </>
                    ) : null}

                    {action === "create_folder" ? (
                      <SelectField label="Parent folder" name="parent_id" options={folderOptions} placeholder="Top-level folder" />
                    ) : null}

                    {action === "create_resource" ? (
                      <>
                        <SelectField label="Section" name="section_id" options={sectionOptions} placeholder="Uncategorized" />
                        <SelectField label="Folder" name="folder_id" options={folderOptions} placeholder="No folder" />
                        <SelectField label="Resource type" name="resource_type" options={data.resource_types} />
                        <div className="space-y-2"><Label htmlFor="resource-file">PDF or PowerPoint file</Label><Input id="resource-file" name="file" type="file" accept=".pdf,.ppt,.pptx" /></div>
                        <div className="space-y-2"><Label htmlFor="resource-url">External URL</Label><Input id="resource-url" name="url" type="url" /></div>
                        <div className="space-y-2"><Label htmlFor="resource-content">Page content</Label><Textarea id="resource-content" name="content" /></div>
                        <div className="space-y-2"><Label htmlFor="visible_from">Visible from</Label><Input id="visible_from" name="visible_from" type="datetime-local" /></div>
                      </>
                    ) : null}

                    {action === "create_announcement" ? (
                      <>
                        <SelectField label="Announcement type" name="announcement_type" options={data.announcement_types} />
                        <SelectField
                          label="Linked assignment or project"
                          name="assignment_id"
                          options={assignmentOptions}
                          placeholder="No linked assignment"
                        />
                        <div className="space-y-2"><Label htmlFor="scheduled_for">Scheduled for</Label><Input id="scheduled_for" name="scheduled_for" type="datetime-local" /></div>
                        <div className="space-y-3 border-t pt-4">
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <p className="text-sm font-medium">Selectable time slots</p>
                              <p className="text-xs text-muted-foreground">Optional for tests and presentations.</p>
                            </div>
                            <Button type="button" variant="outline" onClick={addAnnouncementSlot}>
                              <Plus className="size-4" />
                              Add slot
                            </Button>
                          </div>
                          {announcementSlots.map((slot, index) => (
                            <div key={slot.key} className="space-y-3 rounded-lg border p-3">
                              <div className="flex items-center justify-between">
                                <p className="text-sm font-medium">Slot {index + 1}</p>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  onClick={() => removeAnnouncementSlot(slot.key)}
                                  aria-label={`Remove slot ${index + 1}`}
                                >
                                  <Trash2 className="size-4" />
                                </Button>
                              </div>
                              <Input
                                value={slot.label}
                                placeholder="Label, room, or presentation order"
                                onChange={(event) => updateAnnouncementSlot(slot.key, "label", event.target.value)}
                              />
                              <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-2">
                                  <Label>Starts</Label>
                                  <Input
                                    type="datetime-local"
                                    value={slot.starts_at}
                                    required
                                    onChange={(event) => updateAnnouncementSlot(slot.key, "starts_at", event.target.value)}
                                  />
                                </div>
                                <div className="space-y-2">
                                  <Label>Ends</Label>
                                  <Input
                                    type="datetime-local"
                                    value={slot.ends_at}
                                    onChange={(event) => updateAnnouncementSlot(slot.key, "ends_at", event.target.value)}
                                  />
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-2">
                                  <Label>Selection type</Label>
                                  <select
                                    value={slot.selection_type}
                                    className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                                    onChange={(event) =>
                                      updateAnnouncementSlot(
                                        slot.key,
                                        "selection_type",
                                        event.target.value as "individual" | "group"
                                      )
                                    }
                                  >
                                    <option value="individual">Individual</option>
                                    <option value="group">Group</option>
                                  </select>
                                </div>
                                <div className="space-y-2">
                                  <Label>Slot limit</Label>
                                  <Input
                                    type="number"
                                    min="1"
                                    max="100"
                                    value={slot.capacity}
                                    onChange={(event) =>
                                      updateAnnouncementSlot(slot.key, "capacity", Number(event.target.value))
                                    }
                                  />
                                </div>
                              </div>
                              <Textarea
                                value={slot.instructions}
                                placeholder="Optional slot instructions"
                                onChange={(event) => updateAnnouncementSlot(slot.key, "instructions", event.target.value)}
                              />
                            </div>
                          ))}
                        </div>
                      </>
                    ) : null}

                    {action === "create_activity" ? (
                      <>
                        <SelectField label="Activity type" name="activity_type" options={data.activity_types} />
                        <SelectField label="Section" name="section_id" options={sectionOptions} placeholder="No section" />
                        <SelectField label="Linked assignment" name="assignment_id" options={assignmentOptions} placeholder="No assignment" />
                        <SelectField label="Linked resource" name="resource_id" options={resourceOptions} placeholder="No resource" />
                        <SelectField label="Completion policy" name="completion_policy" options={data.completion_policies} />
                        <div className="space-y-2"><Label htmlFor="due_at">Due date</Label><Input id="due_at" name="due_at" type="datetime-local" /></div>
                      </>
                    ) : null}

                    {action === "update_assessment" ? (
                      <>
                        <label className="flex items-center gap-2 text-sm">
                          <input type="hidden" name="has_final_exam" value="false" />
                          <input type="checkbox" name="has_final_exam" value="true" defaultChecked={data.assessment.has_final_exam} />
                          Final exam
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-2">
                            <Label htmlFor="coursework_percentage">Coursework %</Label>
                            <Input
                              id="coursework_percentage"
                              name="coursework_percentage"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              defaultValue={data.assessment.coursework_percentage}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="final_exam_percentage">Final exam %</Label>
                            <Input
                              id="final_exam_percentage"
                              name="final_exam_percentage"
                              type="number"
                              min="0"
                              max="100"
                              step="0.01"
                              defaultValue={data.assessment.final_exam_percentage}
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="assessment_overview">Assessment notes</Label>
                          <Textarea
                            id="assessment_overview"
                            name="assessment_overview"
                            defaultValue={data.assessment.assessment_overview}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="study_guide">Study guide PDF</Label>
                          <Input id="study_guide" name="study_guide" type="file" accept=".pdf,application/pdf" />
                        </div>
                        {data.assessment.study_guide ? (
                          <div className="space-y-3 rounded-lg border bg-background p-3">
                            <Button type="button" variant="outline" render={<a href={data.assessment.study_guide} target="_blank" rel="noreferrer" />}>
                              <FileText className="size-4" />
                              Current guide
                            </Button>
                            <label className="flex items-center gap-2 text-sm font-medium">
                              <input type="checkbox" name="clear_study_guide" value="true" />
                              <Trash2 className="size-4 text-muted-foreground" />
                              Remove current guide
                            </label>
                          </div>
                        ) : null}
                      </>
                    ) : (
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" name={action === "create_activity" ? "is_required" : "is_published"} defaultChecked />
                        {action === "create_activity" ? "Required activity" : "Publish immediately"}
                      </label>
                    )}
                    <Button className="w-full" type="submit" disabled={saving}>
                      {saving ? <Loader2 className="size-4 animate-spin" /> : action === "update_assessment" ? <Upload className="size-4" /> : <Plus className="size-4" />}
                      Save
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </section>
          </>
        ) : null}
      </main>
    </div>
  )
}

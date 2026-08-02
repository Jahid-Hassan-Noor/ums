"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  BookOpen,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileText,
  FolderOpen,
  Loader2,
  Megaphone,
  Paperclip,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type Resource = {
  id: number
  title: string
  description: string
  file: string | null
  url: string
  content: string
  resource_type: string
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
  resources: Resource[]
  assignments: Assignment[]
  activities: Activity[]
}

type Folder = {
  id: number
  title: string
  description: string
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
  instructions: string
  selected_count: number
  remaining: number
  is_full: boolean
  is_selected: boolean
  can_manage_selection: boolean
  can_select: boolean
  selection_block_reason: string
  own_selection: {
    id: number
    group_name: string
  } | null
}

type AssessmentPlan = {
  has_final_exam: boolean
  coursework_percentage: string
  final_exam_percentage: string
  assessment_overview: string
  study_guide: string | null
  study_guide_name: string
}

type CourseDetailResponse = {
  course: {
    id: number
    code: string
    title: string
    section: string
    has_lab: boolean
    semester: string
  }
  assessment: AssessmentPlan
  enrollment: {
    id: number
    tutorial_group: string
    lab_group: string
    enrolled_at: string | null
  }
  sections: Section[]
  folders: Folder[]
  resources: Resource[]
  announcements: Announcement[]
  assignments: Assignment[]
  activities: Activity[]
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

function StudentResource({ resource }: { resource: Resource }) {
  const destination = resource.file || resource.url
  const content = (
    <div className="flex items-start gap-3">
      <Paperclip className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div>
        <p className="font-medium">{resource.title}</p>
        {resource.description ? <p className="mt-1 text-sm text-muted-foreground">{resource.description}</p> : null}
        {resource.content ? <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{resource.content}</p> : null}
      </div>
    </div>
  )
  return destination ? (
    <a href={destination} target="_blank" rel="noreferrer" className="block rounded-lg border bg-background p-3 hover:bg-muted/40">
      {content}
    </a>
  ) : (
    <div className="rounded-lg border bg-background p-3">{content}</div>
  )
}

function AnnouncementCard({
  announcement,
  busySlot,
  onSelect,
  onCancel,
}: {
  announcement: Announcement
  busySlot: string
  onSelect: (announcementId: number, slotId: number, groupName: string) => Promise<void>
  onCancel: (announcementId: number) => Promise<void>
}) {
  const [groupNames, setGroupNames] = useState<Record<number, string>>({})
  const selectedSlot = announcement.slots.find((slot) => slot.is_selected)

  return (
    <div className="rounded-lg border bg-background p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium">{announcement.title}</p>
        <Badge variant="outline">{announcement.announcement_type}</Badge>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{announcement.body}</p>
      {announcement.slots.length ? (
        <div className="mt-4 space-y-3 border-t pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium">Select a time slot</p>
            {selectedSlot?.can_manage_selection ? (
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busySlot === `cancel-${announcement.id}`}
                onClick={() => void onCancel(announcement.id)}
              >
                Cancel selection
              </Button>
            ) : null}
          </div>
          {announcement.slots.map((slot) => {
            const isLinkedGroup = announcement.assignment_collaboration_mode === "group"
            const groupName = groupNames[slot.id] ?? slot.own_selection?.group_name ?? ""
            const isBusy = busySlot === `${announcement.id}-${slot.id}`
            return (
              <div
                key={slot.id}
                className={`rounded-lg border p-3 text-sm ${
                  slot.is_selected ? "border-emerald-300 bg-emerald-50" : ""
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{slot.label || formatDateTime(slot.starts_at)}</p>
                    <p className="mt-1 text-muted-foreground">
                      {formatDateTime(slot.starts_at)}
                      {slot.ends_at ? ` – ${formatDateTime(slot.ends_at)}` : ""}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {slot.selection_type_label} / {slot.remaining} of {slot.capacity} place
                      {slot.capacity === 1 ? "" : "s"} remaining
                    </p>
                  </div>
                  {slot.is_selected ? (
                    <Badge className="bg-emerald-600">
                      <CheckCircle2 className="size-3" />
                      Selected
                    </Badge>
                  ) : null}
                </div>
                {slot.instructions ? <p className="mt-2 text-xs text-muted-foreground">{slot.instructions}</p> : null}
                {slot.selection_block_reason ? (
                  <p className="mt-2 text-xs text-amber-700">{slot.selection_block_reason}</p>
                ) : null}
                {slot.selection_type === "group" && !isLinkedGroup ? (
                  <div className="mt-3 space-y-2">
                    <label className="text-xs font-medium" htmlFor={`group-${slot.id}`}>Group name</label>
                    <input
                      id={`group-${slot.id}`}
                      value={groupName}
                      onChange={(event) =>
                        setGroupNames((current) => ({ ...current, [slot.id]: event.target.value }))
                      }
                      placeholder="Enter your group name"
                      className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                    />
                  </div>
                ) : null}
                <Button
                  className="mt-3 w-full"
                  type="button"
                  variant={slot.is_selected ? "outline" : "default"}
                  disabled={
                    isBusy ||
                    !slot.can_select ||
                    (slot.is_full && !slot.is_selected) ||
                    (isLinkedGroup && Boolean(selectedSlot) && !selectedSlot?.can_manage_selection) ||
                    (slot.selection_type === "group" && !isLinkedGroup && !groupName.trim())
                  }
                  onClick={() => void onSelect(announcement.id, slot.id, groupName)}
                >
                  {isBusy ? <Loader2 className="size-4 animate-spin" /> : <CalendarClock className="size-4" />}
                  {slot.is_selected
                    ? (slot.can_manage_selection ? "Update selection" : "Selected by group leader")
                    : selectedSlot
                      ? "Change to this slot"
                      : "Select slot"}
                </Button>
              </div>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}

export function StudentCourseDetailPage({ courseId }: { courseId: string }) {
  const [data, setData] = useState<CourseDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [busySlot, setBusySlot] = useState("")

  const loadCourse = useCallback(async () => {
    setData(await apiFetch<CourseDetailResponse>(`/student/courses/${courseId}`))
  }, [courseId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCourse()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load course."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadCourse])

  function replaceAnnouncement(announcement: Announcement) {
    setData((current) =>
      current
        ? {
            ...current,
            announcements: current.announcements.map((item) =>
              item.id === announcement.id ? announcement : item
            ),
          }
        : current
    )
  }

  async function selectSlot(announcementId: number, slotId: number, groupName: string) {
    setBusySlot(`${announcementId}-${slotId}`)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string; announcement: Announcement }>(
        `/student/courses/${courseId}`,
        {
          method: "POST",
          body: JSON.stringify({
            action: "select_slot",
            announcement_id: announcementId,
            slot_id: slotId,
            group_name: groupName,
          }),
        }
      )
      replaceAnnouncement(response.announcement)
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to select this slot.")
    } finally {
      setBusySlot("")
    }
  }

  async function cancelSlot(announcementId: number) {
    setBusySlot(`cancel-${announcementId}`)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string; announcement: Announcement }>(
        `/student/courses/${courseId}`,
        {
          method: "POST",
          body: JSON.stringify({
            action: "cancel_slot",
            announcement_id: announcementId,
          }),
        }
      )
      replaceAnnouncement(response.announcement)
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to cancel this selection.")
    } finally {
      setBusySlot("")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/courses/current", title: "Current Courses" },
          { href: `/student/courses/${courseId}`, title: data?.course.code ?? "Course" },
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
          <div className="flex h-56 items-center justify-center"><Loader2 className="size-7 animate-spin text-muted-foreground" /></div>
        ) : data ? (
          <>
            <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-medium text-primary">{data.course.code} / Section {data.course.section}</p>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{data.course.title}</h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  {data.course.semester}
                  {data.enrollment.tutorial_group ? ` / Tutorial ${data.enrollment.tutorial_group}` : ""}
                  {data.enrollment.lab_group ? ` / Lab ${data.enrollment.lab_group}` : ""}
                </p>
              </div>
              <Button variant="outline" render={<Link href="/student/assignments" />}>
                <FileText className="size-4" />
                All assignments
              </Button>
            </section>

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

            {data.announcements.length ? (
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Megaphone className="size-5" />Announcements</CardTitle></CardHeader>
                <CardContent className="grid gap-3 lg:grid-cols-2">
                  {data.announcements.map((announcement) => (
                    <AnnouncementCard
                      key={announcement.id}
                      announcement={announcement}
                      busySlot={busySlot}
                      onSelect={selectSlot}
                      onCancel={cancelSlot}
                    />
                  ))}
                </CardContent>
              </Card>
            ) : null}

            <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <div className="space-y-5">
                {data.folders.length ? (
                  <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><FolderOpen className="size-5" />Resource folders</CardTitle></CardHeader>
                    <CardContent className="grid gap-4 md:grid-cols-2">
                      {data.folders.map((folder) => (
                        <div key={folder.id} className="rounded-lg border bg-background p-4">
                          <p className="font-medium">{folder.title}</p>
                          {folder.description ? <p className="mt-1 text-sm text-muted-foreground">{folder.description}</p> : null}
                          <div className="mt-3 space-y-2">{folder.resources.map((resource) => <StudentResource key={resource.id} resource={resource} />)}</div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ) : null}

                {data.resources.length ? (
                  <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><BookOpen className="size-5" />Course resources</CardTitle></CardHeader>
                    <CardContent className="space-y-3">{data.resources.map((resource) => <StudentResource key={resource.id} resource={resource} />)}</CardContent>
                  </Card>
                ) : null}

                {data.sections.map((section) => (
                  <Card key={section.id}>
                    <CardHeader>
                      <CardDescription>{section.week_number ? `Week ${section.week_number}` : section.section_type}</CardDescription>
                      <CardTitle>{section.title}</CardTitle>
                      {section.summary ? <CardDescription>{section.summary}</CardDescription> : null}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {section.resources.map((resource) => <StudentResource key={resource.id} resource={resource} />)}
                      {section.assignments.map((assignment) => (
                        <Link key={assignment.id} href={`/student/assignments/${assignment.id}`} className="flex flex-col gap-2 rounded-lg border p-4 hover:bg-muted/40 sm:flex-row sm:items-center sm:justify-between">
                          <span><FileText className="mr-2 inline size-4" />{assignment.title}</span>
                          <span className="text-sm text-muted-foreground">{formatDateTime(assignment.due_date)}</span>
                        </Link>
                      ))}
                      {section.activities.map((activity) => (
                        <div key={activity.id} className="flex flex-col gap-2 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">
                          <span><CalendarClock className="mr-2 inline size-4" />{activity.title}</span>
                          <span className="text-sm text-muted-foreground">{formatDateTime(activity.due_at)}</span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="space-y-5">
                <Card>
                  <CardHeader><CardTitle>Upcoming activities</CardTitle><CardDescription>Required work and course deadlines.</CardDescription></CardHeader>
                  <CardContent className="space-y-3">
                    {data.activities.length ? data.activities.map((activity) => (
                      <div key={activity.id} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium">{activity.title}</p>
                          {activity.is_required ? <Badge variant="outline">Required</Badge> : null}
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(activity.due_at)}</p>
                      </div>
                    )) : <p className="text-sm text-muted-foreground">No activity deadlines have been published.</p>}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>Assignments</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {data.assignments.length ? data.assignments.map((assignment) => (
                      <Link key={assignment.id} href={`/student/assignments/${assignment.id}`} className="block rounded-lg border p-3 hover:bg-muted/40">
                        <p className="font-medium">{assignment.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(assignment.due_date)} / {assignment.max_score} marks</p>
                      </Link>
                    )) : <p className="text-sm text-muted-foreground">No assignments have been published.</p>}
                  </CardContent>
                </Card>
              </div>
            </section>
          </>
        ) : null}
      </main>
    </div>
  )
}

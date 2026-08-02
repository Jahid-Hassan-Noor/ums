"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileText,
  GraduationCap,
  Loader2,
  Paperclip,
  Plus,
  RefreshCw,
  Send,
  Upload,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
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
import { statusClassName } from "@/lib/status-utils"

type AssignmentStatus = "all" | "upcoming" | "overdue" | "submitted" | "graded"

type AssignmentOffering = {
  id: number
  course_code: string
  course_title: string
  section: string
  semester: string
}

type AssignmentAttachment = {
  id: number
  file: string
  name: string
  uploaded_at: string | null
}

type AssignmentSubmission = {
  id: number
  content: string
  attempt_count: number
  status: string
  status_label?: string
  grade: string | null
  feedback: string
  submitted_at: string
  last_modified_at: string
  graded_at: string | null
  attachments?: AssignmentAttachment[]
  assignment_group?: {
    id: number
    name: string
    leader_id: number
  } | null
}

type AssignmentRubric = {
  id: number
  title: string
  criteria: Array<{
    title?: string
    description?: string
    max_score?: number | string
  }>
  max_score: string
}

type AssignmentComment = {
  id: number
  body: string
  author: string
  author_role: string
  created_at: string | null
}

type AssignmentRecord = {
  id: number
  title: string
  description: string
  instructions: string
  file_instructions: string
  opens_at: string | null
  due_date: string | null
  cutoff_at: string | null
  max_score: string
  activity_kind: "assignment" | "lab_activity"
  activity_kind_label: string
  collaboration_mode: "individual" | "group"
  collaboration_mode_label: string
  max_group_members: number
  require_same_tutorial_group: boolean
  require_same_lab_group: boolean
  min_distinct_countries: number
  group_rules: string
  submission_type: "text" | "file" | "both"
  accepted_file_type: string
  accepted_file_types: string[]
  accepted_extensions: string[]
  max_files: number
  max_file_size_mb: number
  allow_multiple_submissions: boolean
  allow_late_submissions: boolean
  status: string
  created_by: string
  offering: AssignmentOffering
  submission: AssignmentSubmission | null
  student_status: Exclude<AssignmentStatus, "all">
  student_status_label: string
  can_submit: boolean
  submission_error: string | null
  is_overdue: boolean
}

type AssignmentsResponse = {
  title: string
  filter: AssignmentStatus
  counts: Record<AssignmentStatus, number>
  assignments: AssignmentRecord[]
}

type AssignmentDetailResponse = {
  title: string
  assignment: AssignmentRecord
  submission: AssignmentSubmission | null
  rubrics: AssignmentRubric[]
  comments: AssignmentComment[]
  group_workspace: GroupWorkspace | null
  message?: string
}

type GroupMember = {
  id: number
  name: string
  username: string
  tutorial_group: string
  lab_group: string
  country: string
  is_leader: boolean
}

type GroupWorkspace = {
  config: {
    max_members: number
    require_same_tutorial_group: boolean
    require_same_lab_group: boolean
    min_distinct_countries: number
    extra_rules: string
  }
  current_group: {
    id: number
    name: string
    leader_id: number
    leader: string
    is_leader: boolean
    members: GroupMember[]
    rule_status: {
      member_count: number
      max_members: number
      countries: string[]
      country_count: number
      required_country_count: number
      violations: string[]
      is_ready: boolean
    }
  } | null
  invitations: Array<{
    id: number
    group_id: number
    group_name: string
    leader: string
    status: string
    created_at: string | null
  }>
  eligible_students: Array<{
    id: number
    name: string
    username: string
    tutorial_group: string
    lab_group: string
    country: string
    eligibility_error: string | null
    invitation_status: string
  }>
}

type SubmitResponse = {
  message: string
  assignment: AssignmentRecord
  submission: AssignmentSubmission
}

const STATUS_OPTIONS: Array<{
  value: AssignmentStatus
  label: string
  href: string
  icon: typeof ClipboardList
}> = [
  {
    value: "all",
    label: "All",
    href: "/student/assignments",
    icon: ClipboardList,
  },
  {
    value: "upcoming",
    label: "Upcoming",
    href: "/student/assignments/upcoming",
    icon: CalendarClock,
  },
  {
    value: "overdue",
    label: "Overdue",
    href: "/student/assignments/overdue",
    icon: AlertCircle,
  },
  {
    value: "submitted",
    label: "Submitted",
    href: "/student/assignments/submitted",
    icon: Send,
  },
  {
    value: "graded",
    label: "Graded",
    href: "/student/assignments/graded",
    icon: GraduationCap,
  },
]

function endpointForStatus(status: AssignmentStatus) {
  return status === "all"
    ? "/student/assignments"
    : `/student/assignments/${status}`
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not set"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not set"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatScore(value: string | null | undefined) {
  if (value === null || value === undefined || value === "") return "Not graded"
  return Number(value).toFixed(2)
}

function attachmentName(attachment: AssignmentAttachment) {
  return attachment.name || attachment.file.split("/").pop() || "Attachment"
}

function SummaryCards({
  counts,
}: {
  counts: Record<AssignmentStatus, number>
}) {
  return (
    <section className="grid gap-3 md:grid-cols-4">
      {STATUS_OPTIONS.slice(1).map((option) => {
        const Icon = option.icon
        return (
          <Card key={option.value} className="border-border/70 shadow-sm">
            <CardContent className="flex items-center justify-between gap-3 p-4">
              <div>
                <p className="text-sm text-muted-foreground">{option.label}</p>
                <p className="mt-1 text-2xl font-semibold">
                  {counts[option.value] ?? 0}
                </p>
              </div>
              <Icon className="size-5 text-muted-foreground" />
            </CardContent>
          </Card>
        )
      })}
    </section>
  )
}

function StatusNav({
  active,
  counts,
}: {
  active: AssignmentStatus
  counts: Record<AssignmentStatus, number>
}) {
  return (
    <nav className="flex gap-2 overflow-x-auto pb-1">
      {STATUS_OPTIONS.map((option) => {
        const Icon = option.icon
        const isActive = option.value === active
        return (
          <Link
            key={option.value}
            href={option.href}
            className={`inline-flex h-9 shrink-0 items-center gap-2 rounded-lg border px-3 text-sm font-medium transition ${
              isActive
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background hover:bg-muted"
            }`}
          >
            <Icon className="size-4" />
            {option.label}
            <span
              className={`rounded-full px-1.5 text-xs ${isActive ? "bg-primary-foreground/20" : "bg-muted"}`}
            >
              {counts[option.value] ?? 0}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}

function AssignmentMeta({ assignment }: { assignment: AssignmentRecord }) {
  return (
    <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-2 xl:grid-cols-4">
      <p>
        <span className="block font-medium text-foreground">Course</span>
        {assignment.offering.course_code} / {assignment.offering.section}
      </p>
      <p>
        <span className="block font-medium text-foreground">Due</span>
        {formatDateTime(assignment.due_date)}
      </p>
      <p>
        <span className="block font-medium text-foreground">Submission</span>
        {assignment.submission_type === "both"
          ? "Text and file"
          : assignment.submission_type}
      </p>
      <p>
        <span className="block font-medium text-foreground">Score</span>
        {assignment.max_score} marks
      </p>
    </div>
  )
}

function AssignmentCard({ assignment }: { assignment: AssignmentRecord }) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 space-y-1">
            <CardDescription>
              {assignment.offering.course_code} /{" "}
              {assignment.offering.course_title}
            </CardDescription>
            <CardTitle className="text-xl">{assignment.title}</CardTitle>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{assignment.activity_kind_label}</Badge>
            <Badge
              variant="outline"
              className={statusClassName(assignment.student_status)}
            >
              {assignment.student_status_label}
            </Badge>
          </div>
        </div>
        <AssignmentMeta assignment={assignment} />
      </CardHeader>
      <CardContent className="space-y-4">
        {assignment.description ? (
          <p className="text-sm leading-6 text-muted-foreground">
            {assignment.description}
          </p>
        ) : null}
        {assignment.submission ? (
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="font-medium">Last submission</p>
            <p className="mt-1 text-muted-foreground">
              {assignment.submission.status_label ??
                assignment.submission.status}{" "}
              / attempt {assignment.submission.attempt_count} /{" "}
              {formatDateTime(assignment.submission.last_modified_at)}
            </p>
          </div>
        ) : assignment.submission_error ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            {assignment.submission_error}
          </div>
        ) : null}
        <div className="flex flex-wrap justify-end gap-2">
          <Button
            variant="outline"
            render={<Link href={`/student/assignments/${assignment.id}`} />}
          >
            <FileText className="size-4" />
            Details
          </Button>
          {assignment.can_submit ? (
            <Button
              render={
                <Link href={`/student/assignments/${assignment.id}/submit`} />
              }
            >
              <Upload className="size-4" />
              Submit
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState({ status }: { status: AssignmentStatus }) {
  const option =
    STATUS_OPTIONS.find((item) => item.value === status) ?? STATUS_OPTIONS[0]
  const Icon = option.icon
  const label =
    status === "all"
      ? "assignments"
      : `${option.label.toLowerCase()} assignments`
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <Icon className="size-8 text-muted-foreground" />
        <p className="font-medium">No {label}</p>
        <p className="max-w-md text-sm text-muted-foreground">
          Assignments from enrolled course offerings will appear here once they
          match this view.
        </p>
      </CardContent>
    </Card>
  )
}

export function StudentAssignmentsPage({
  status = "all",
}: {
  status?: AssignmentStatus
}) {
  const [response, setResponse] = useState<AssignmentsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadAssignments = useCallback(async () => {
    const data = await apiFetch<AssignmentsResponse>(endpointForStatus(status))
    setResponse(data)
  }, [status])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError("")
      void loadAssignments()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load assignments."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAssignments])

  const counts = response?.counts ?? {
    all: 0,
    upcoming: 0,
    overdue: 0,
    submitted: 0,
    graded: 0,
  }
  const assignments = response?.assignments ?? []
  const activeTitle =
    STATUS_OPTIONS.find((option) => option.value === status)?.label ??
    "Assignments"

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/assignments", title: "Assignments" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold sm:text-3xl">
              {activeTitle} Assignments
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Track due work, submitted attempts, grades, feedback, and accepted
              files for your enrolled courses.
            </p>
          </div>
          <Button
            variant="outline"
            disabled={loading}
            onClick={() => {
              setLoading(true)
              setError("")
              void loadAssignments()
                .catch((caught) =>
                  setError(
                    caught instanceof Error
                      ? caught.message
                      : "Unable to refresh assignments."
                  )
                )
                .finally(() => setLoading(false))
            }}
          >
            {loading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Refresh
          </Button>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        <SummaryCards counts={counts} />
        <StatusNav active={status} counts={counts} />

        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : assignments.length ? (
          <section className="space-y-4">
            {assignments.map((assignment) => (
              <AssignmentCard key={assignment.id} assignment={assignment} />
            ))}
          </section>
        ) : (
          <EmptyState status={status} />
        )}
      </main>
    </div>
  )
}

function SubmissionPanel({
  submission,
  maxScore,
}: {
  submission: AssignmentSubmission | null
  maxScore: string
}) {
  if (!submission) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <Send className="size-8 text-muted-foreground" />
          <p className="font-medium">No submission yet</p>
          <p className="text-sm text-muted-foreground">
            Your submitted text, files, grade, and feedback will appear here.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardDescription>
              Attempt {submission.attempt_count}
            </CardDescription>
            <CardTitle>Submission Status</CardTitle>
          </div>
          <Badge variant="outline">
            {submission.status_label ?? submission.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <p>
            <span className="block font-medium">Submitted</span>
            <span className="text-muted-foreground">
              {formatDateTime(submission.submitted_at)}
            </span>
          </p>
          <p>
            <span className="block font-medium">Last updated</span>
            <span className="text-muted-foreground">
              {formatDateTime(submission.last_modified_at)}
            </span>
          </p>
          <p>
            <span className="block font-medium">Grade</span>
            <span className="text-muted-foreground">
              {formatScore(submission.grade)}{" "}
              {submission.grade ? `/ ${maxScore}` : ""}
            </span>
          </p>
          <p>
            <span className="block font-medium">Graded at</span>
            <span className="text-muted-foreground">
              {formatDateTime(submission.graded_at)}
            </span>
          </p>
        </div>
        {submission.content ? (
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="font-medium">Submitted Text</p>
            <p className="mt-2 text-sm leading-6 whitespace-pre-wrap text-muted-foreground">
              {submission.content}
            </p>
          </div>
        ) : null}
        {submission.attachments?.length ? (
          <div className="space-y-2">
            <p className="font-medium">Files</p>
            {submission.attachments.map((attachment) => (
              <a
                key={attachment.id}
                href={attachment.file}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-3 rounded-lg border p-3 text-sm hover:bg-muted/40"
              >
                <span className="flex min-w-0 items-center gap-2">
                  <Paperclip className="size-4 shrink-0 text-muted-foreground" />
                  <span className="truncate">{attachmentName(attachment)}</span>
                </span>
                <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
              </a>
            ))}
          </div>
        ) : null}
        {submission.feedback ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
            <p className="font-medium">Feedback</p>
            <p className="mt-2 text-sm leading-6 whitespace-pre-wrap">
              {submission.feedback}
            </p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

function AssignmentDetailLayout({
  assignment,
  submission,
  rubrics,
  comments,
  onComment,
  commenting,
  groupWorkspace,
  onGroupAction,
  groupBusy,
}: {
  assignment: AssignmentRecord
  submission: AssignmentSubmission | null
  rubrics: AssignmentRubric[]
  comments: AssignmentComment[]
  onComment: (event: FormEvent<HTMLFormElement>) => void
  commenting: boolean
  groupWorkspace: GroupWorkspace | null
  onGroupAction: (payload: Record<string, unknown>) => Promise<void>
  groupBusy: boolean
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,26rem)]">
      <div className="space-y-5">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardDescription>
                  {assignment.offering.course_code} /{" "}
                  {assignment.offering.course_title}
                </CardDescription>
                <CardTitle className="text-2xl">{assignment.title}</CardTitle>
              </div>
              <Badge
                variant="outline"
                className={statusClassName(assignment.student_status)}
              >
                {assignment.student_status_label}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <AssignmentMeta assignment={assignment} />
            {assignment.description ? (
              <div>
                <p className="font-medium">Description</p>
                <p className="mt-2 text-sm leading-6 whitespace-pre-wrap text-muted-foreground">
                  {assignment.description}
                </p>
              </div>
            ) : null}
            {assignment.instructions ? (
              <div>
                <p className="font-medium">Instructions</p>
                <p className="mt-2 text-sm leading-6 whitespace-pre-wrap text-muted-foreground">
                  {assignment.instructions}
                </p>
              </div>
            ) : null}
            {assignment.file_instructions ? (
              <div>
                <p className="font-medium">File Instructions</p>
                <p className="mt-2 text-sm leading-6 whitespace-pre-wrap text-muted-foreground">
                  {assignment.file_instructions}
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>
        {groupWorkspace ? (
          <GroupWorkspacePanel
            workspace={groupWorkspace}
            onAction={onGroupAction}
            busy={groupBusy}
          />
        ) : null}
        <SubmissionPanel
          submission={submission}
          maxScore={assignment.max_score}
        />
        {rubrics.length ? (
          <Card>
            <CardHeader>
              <CardTitle>Grading Rubric</CardTitle>
              <CardDescription>
                Criteria the lecturer will use when reviewing this assignment.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {rubrics.map((rubric) => (
                <div key={rubric.id} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium">{rubric.title}</p>
                    <Badge variant="outline">{rubric.max_score} marks</Badge>
                  </div>
                  <div className="mt-3 space-y-2">
                    {rubric.criteria.map((criterion, index) => (
                      <div
                        key={`${rubric.id}-${index}`}
                        className="rounded-lg bg-muted/40 p-3 text-sm"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-medium">
                            {criterion.title || `Criterion ${index + 1}`}
                          </p>
                          <span className="text-muted-foreground">
                            {criterion.max_score ?? 0} marks
                          </span>
                        </div>
                        {criterion.description ? (
                          <p className="mt-1 text-muted-foreground">
                            {criterion.description}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : null}
        <Card>
          <CardHeader>
            <CardTitle>Questions & Comments</CardTitle>
            <CardDescription>
              Clarifications shared between students and the lecturer.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {comments.map((comment) => (
              <div key={comment.id} className="rounded-lg border p-3 text-sm">
                <p className="font-medium">{comment.author}</p>
                <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
                  {comment.body}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {formatDateTime(comment.created_at)}
                </p>
              </div>
            ))}
            <form className="space-y-3 border-t pt-4" onSubmit={onComment}>
              <Textarea
                name="body"
                placeholder="Ask a question about this assignment"
                required
              />
              <Button type="submit" variant="outline" disabled={commenting}>
                {commenting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Send className="size-4" />
                )}
                Post comment
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>Submission Window</CardTitle>
          <CardDescription>{assignment.offering.semester}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="space-y-3">
            <p>
              <span className="block font-medium">Opens</span>
              <span className="text-muted-foreground">
                {formatDateTime(assignment.opens_at)}
              </span>
            </p>
            <p>
              <span className="block font-medium">Due</span>
              <span className="text-muted-foreground">
                {formatDateTime(assignment.due_date)}
              </span>
            </p>
            <p>
              <span className="block font-medium">Cutoff</span>
              <span className="text-muted-foreground">
                {formatDateTime(assignment.cutoff_at)}
              </span>
            </p>
            <p>
              <span className="block font-medium">Accepted files</span>
              <span className="text-muted-foreground">
                {assignment.accepted_extensions.length
                  ? assignment.accepted_extensions.join(", ")
                  : "No file upload required"}
              </span>
            </p>
            <p>
              <span className="block font-medium">Maximum files</span>
              <span className="text-muted-foreground">
                {assignment.max_files}
              </span>
            </p>
            <p>
              <span className="block font-medium">Maximum size per file</span>
              <span className="text-muted-foreground">
                {assignment.max_file_size_mb} MB
              </span>
            </p>
          </div>
          {assignment.submission_error ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800">
              {assignment.submission_error}
            </div>
          ) : null}
          <Button
            className="w-full"
            disabled={!assignment.can_submit}
            render={
              assignment.can_submit ? (
                <Link href={`/student/assignments/${assignment.id}/submit`} />
              ) : undefined
            }
          >
            <Upload className="size-4" />
            Submit Assignment
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

function GroupWorkspacePanel({
  workspace,
  onAction,
  busy,
}: {
  workspace: GroupWorkspace
  onAction: (payload: Record<string, unknown>) => Promise<void>
  busy: boolean
}) {
  const group = workspace.current_group

  async function createGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await onAction({ action: "create_group", name: form.get("name") })
  }

  async function removeMember(member: GroupMember) {
    if (
      !window.confirm(
        `Remove ${member.name} from ${group?.name ?? "this group"}?`
      )
    )
      return
    await onAction({ action: "remove_member", student_id: member.id })
  }

  async function leaveOrDeleteGroup() {
    const action = group?.is_leader ? "delete_group" : "leave_group"
    const message = group?.is_leader
      ? `Delete ${group.name}? This removes the group and all memberships.`
      : `Leave ${group?.name}?`
    if (!window.confirm(message)) return
    await onAction({ action })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Group</CardTitle>
        <CardDescription>
          Maximum {workspace.config.max_members} members.
          {workspace.config.require_same_tutorial_group
            ? " Same tutorial group required."
            : ""}
          {workspace.config.require_same_lab_group
            ? " Same lab group required."
            : ""}
          {workspace.config.min_distinct_countries
            ? ` At least ${workspace.config.min_distinct_countries} countries required.`
            : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {workspace.config.extra_rules ? (
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="font-medium">Additional criteria</p>
            <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
              {workspace.config.extra_rules}
            </p>
          </div>
        ) : null}

        {!group ? (
          <>
            {workspace.invitations.length ? (
              <div className="space-y-2">
                <p className="font-medium">Group invitations</p>
                {workspace.invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="flex flex-col gap-3 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="font-medium">{invitation.group_name}</p>
                      <p className="text-sm text-muted-foreground">
                        Leader: {invitation.leader}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void onAction({
                            action: "accept_invitation",
                            invitation_id: invitation.id,
                          })
                        }
                      >
                        Accept
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={busy}
                        onClick={() =>
                          void onAction({
                            action: "decline_invitation",
                            invitation_id: invitation.id,
                          })
                        }
                      >
                        Decline
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            <form
              className="space-y-3 rounded-lg border p-4"
              onSubmit={createGroup}
            >
              <div>
                <p className="font-medium">Create a new group</p>
                <p className="text-sm text-muted-foreground">
                  You will become the group leader.
                </p>
              </div>
              <Input name="name" placeholder="Group name" required />
              <Button type="submit" disabled={busy}>
                {busy ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Plus className="size-4" />
                )}
                Create group
              </Button>
            </form>
          </>
        ) : (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-lg font-semibold">{group.name}</p>
                <p className="text-sm text-muted-foreground">
                  Leader: {group.leader}
                </p>
              </div>
              <Badge variant="outline">
                {group.rule_status.member_count}/{group.rule_status.max_members}{" "}
                members
              </Badge>
            </div>
            <div className="space-y-2">
              {group.members.map((member) => (
                <div
                  key={member.id}
                  className="flex flex-col gap-2 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">
                      {member.name}
                      {member.is_leader ? " / Leader" : ""}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {member.tutorial_group
                        ? `Tutorial ${member.tutorial_group}`
                        : "No tutorial group"}
                      {" / "}
                      {member.lab_group
                        ? `Lab ${member.lab_group}`
                        : "No lab group"}
                      {member.country ? ` / ${member.country}` : ""}
                    </p>
                  </div>
                  {group.is_leader && !member.is_leader ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={busy}
                      onClick={() => void removeMember(member)}
                    >
                      Remove
                    </Button>
                  ) : null}
                </div>
              ))}
            </div>
            {group.rule_status.violations.length ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {group.rule_status.violations.join(" ")}
              </div>
            ) : (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                Group criteria satisfied. The leader can submit final work and
                select group presentation slots.
              </div>
            )}
            {group.is_leader ? (
              <div className="space-y-2 border-t pt-4">
                <p className="font-medium">Invite enrolled students</p>
                {workspace.eligible_students.length ? (
                  workspace.eligible_students.map((candidate) => (
                    <div
                      key={candidate.id}
                      className="flex flex-col gap-2 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="font-medium">{candidate.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {candidate.tutorial_group
                            ? `Tutorial ${candidate.tutorial_group}`
                            : "No tutorial group"}
                          {" / "}
                          {candidate.lab_group
                            ? `Lab ${candidate.lab_group}`
                            : "No lab group"}
                          {candidate.country ? ` / ${candidate.country}` : ""}
                        </p>
                        {candidate.eligibility_error ? (
                          <p className="mt-1 text-xs text-amber-700">
                            {candidate.eligibility_error}
                          </p>
                        ) : null}
                      </div>
                      <Button
                        type="button"
                        size="sm"
                        disabled={
                          busy ||
                          Boolean(candidate.eligibility_error) ||
                          candidate.invitation_status === "pending"
                        }
                        onClick={() =>
                          void onAction({
                            action: "invite_member",
                            student_id: candidate.id,
                          })
                        }
                      >
                        {candidate.invitation_status === "pending"
                          ? "Invited"
                          : "Invite"}
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No other eligible students are available.
                  </p>
                )}
              </div>
            ) : null}
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => void leaveOrDeleteGroup()}
            >
              {group.is_leader ? "Delete group" : "Leave group"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function StudentAssignmentDetailPage({
  assignmentId,
}: {
  assignmentId: string
}) {
  const [assignment, setAssignment] = useState<AssignmentRecord | null>(null)
  const [submission, setSubmission] = useState<AssignmentSubmission | null>(
    null
  )
  const [rubrics, setRubrics] = useState<AssignmentRubric[]>([])
  const [comments, setComments] = useState<AssignmentComment[]>([])
  const [groupWorkspace, setGroupWorkspace] = useState<GroupWorkspace | null>(
    null
  )
  const [loading, setLoading] = useState(true)
  const [commenting, setCommenting] = useState(false)
  const [groupBusy, setGroupBusy] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadAssignment = useCallback(async () => {
    const data = await apiFetch<AssignmentDetailResponse>(
      `/student/assignments/${assignmentId}`
    )
    setAssignment(data.assignment)
    setSubmission(data.submission)
    setRubrics(data.rubrics ?? [])
    setComments(data.comments ?? [])
    setGroupWorkspace(data.group_workspace ?? null)
  }, [assignmentId])

  function applyDetailResponse(data: AssignmentDetailResponse) {
    setAssignment(data.assignment)
    setSubmission(data.submission)
    setRubrics(data.rubrics ?? [])
    setComments(data.comments ?? [])
    setGroupWorkspace(data.group_workspace ?? null)
  }

  async function groupAction(payload: Record<string, unknown>) {
    setGroupBusy(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<AssignmentDetailResponse>(
        `/student/assignments/${assignmentId}`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      )
      applyDetailResponse(response)
      setSuccess(response.message ?? "Group updated.")
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to update the group."
      )
    } finally {
      setGroupBusy(false)
    }
  }

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCommenting(true)
    setError("")
    setSuccess("")
    try {
      const form = new FormData(event.currentTarget)
      const response = await apiFetch<AssignmentDetailResponse>(
        `/student/assignments/${assignmentId}`,
        {
          method: "POST",
          body: JSON.stringify({
            action: "add_comment",
            body: form.get("body"),
          }),
        }
      )
      applyDetailResponse(response)
      setSuccess(response.message ?? "Comment added.")
      event.currentTarget.reset()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to post comment."
      )
    } finally {
      setCommenting(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError("")
      void loadAssignment()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load assignment."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAssignment])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/assignments", title: "Assignments" },
          { href: `/student/assignments/${assignmentId}`, title: "Detail" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
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
        {loading ? (
          <div className="flex h-56 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : assignment ? (
          <AssignmentDetailLayout
            assignment={assignment}
            submission={submission}
            rubrics={rubrics}
            comments={comments}
            onComment={addComment}
            commenting={commenting}
            groupWorkspace={groupWorkspace}
            onGroupAction={groupAction}
            groupBusy={groupBusy}
          />
        ) : null}
      </main>
    </div>
  )
}

export function StudentAssignmentSubmitPage({
  assignmentId,
}: {
  assignmentId: string
}) {
  const [assignment, setAssignment] = useState<AssignmentRecord | null>(null)
  const [submission, setSubmission] = useState<AssignmentSubmission | null>(
    null
  )
  const [content, setContent] = useState("")
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadAssignment = useCallback(async () => {
    const data = await apiFetch<AssignmentDetailResponse>(
      `/student/assignments/${assignmentId}/submit`
    )
    setAssignment(data.assignment)
    setSubmission(data.submission)
    setContent(data.submission?.content ?? "")
  }, [assignmentId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError("")
      void loadAssignment()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load assignment."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAssignment])

  const acceptsText =
    assignment?.submission_type === "text" ||
    assignment?.submission_type === "both"
  const acceptsFiles =
    assignment?.submission_type === "file" ||
    assignment?.submission_type === "both"
  const allowedFiles = useMemo(
    () => assignment?.accepted_extensions.join(",") ?? "",
    [assignment]
  )
  const missingText = Boolean(acceptsText && !content.trim())
  const missingFile = Boolean(acceptsFiles && selectedFiles.length === 0)
  const tooManyFiles = Boolean(
    assignment && selectedFiles.length > assignment.max_files
  )
  const oversizedFiles = assignment
    ? selectedFiles.filter(
        (file) => file.size > assignment.max_file_size_mb * 1024 * 1024
      )
    : []
  const canSubmit = Boolean(
    assignment?.can_submit &&
    !missingText &&
    !missingFile &&
    !tooManyFiles &&
    !oversizedFiles.length &&
    !saving
  )

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!assignment) return

    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const formData = new FormData()
      formData.append("content", content)
      selectedFiles.forEach((file) => formData.append("files", file))
      const response = await apiFetch<SubmitResponse>(
        `/student/assignments/${assignment.id}/submit`,
        {
          method: "POST",
          body: formData,
        }
      )
      setAssignment(response.assignment)
      setSubmission(response.submission)
      setSelectedFiles([])
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to submit assignment."
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/assignments", title: "Assignments" },
          { href: `/student/assignments/${assignmentId}`, title: "Detail" },
          {
            href: `/student/assignments/${assignmentId}/submit`,
            title: "Submit",
          },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
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

        {loading ? (
          <div className="flex h-56 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : assignment ? (
          <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,26rem)]">
            <Card>
              <CardHeader>
                <CardDescription>
                  {assignment.offering.course_code} /{" "}
                  {assignment.offering.course_title}
                </CardDescription>
                <CardTitle className="text-2xl">{assignment.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-5" onSubmit={submitAssignment}>
                  {acceptsText ? (
                    <div className="space-y-2">
                      <Label htmlFor="assignment-content">
                        Submission text
                      </Label>
                      <Textarea
                        id="assignment-content"
                        className="min-h-40"
                        value={content}
                        onChange={(event) => setContent(event.target.value)}
                        disabled={!assignment.can_submit || saving}
                      />
                    </div>
                  ) : null}

                  {acceptsFiles ? (
                    <div className="space-y-2">
                      <Label htmlFor="assignment-files">Files</Label>
                      <input
                        id="assignment-files"
                        type="file"
                        multiple={assignment.max_files > 1}
                        accept={allowedFiles}
                        disabled={!assignment.can_submit || saving}
                        className="block w-full rounded-lg border bg-background px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-sm file:font-medium"
                        onChange={(event) =>
                          setSelectedFiles(Array.from(event.target.files ?? []))
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        {assignment.accepted_extensions.join(", ")} / maximum{" "}
                        {assignment.max_files} file
                        {assignment.max_files === 1 ? "" : "s"} /{" "}
                        {assignment.max_file_size_mb} MB each
                      </p>
                    </div>
                  ) : null}

                  {assignment.submission_error ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                      {assignment.submission_error}
                    </div>
                  ) : null}

                  {missingText || missingFile ? (
                    <div className="rounded-lg border bg-muted/40 p-3 text-sm text-muted-foreground">
                      {missingText ? "Submission text is required. " : ""}
                      {missingFile
                        ? "Select the required file before submitting."
                        : ""}
                    </div>
                  ) : null}
                  {tooManyFiles || oversizedFiles.length ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                      {tooManyFiles
                        ? `Select no more than ${assignment.max_files} file(s). `
                        : ""}
                      {oversizedFiles.length
                        ? `${oversizedFiles.map((file) => file.name).join(", ")} exceed the ${assignment.max_file_size_mb} MB per-file limit.`
                        : ""}
                    </div>
                  ) : null}

                  <div className="flex flex-wrap justify-between gap-2">
                    <Button
                      variant="outline"
                      render={
                        <Link href={`/student/assignments/${assignment.id}`} />
                      }
                    >
                      <FileText className="size-4" />
                      Assignment Detail
                    </Button>
                    <Button type="submit" disabled={!canSubmit}>
                      {saving ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Send className="size-4" />
                      )}
                      Submit
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <div className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle>Requirements</CardTitle>
                  <CardDescription>
                    {assignment.offering.semester}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <p>
                    <span className="block font-medium">Due</span>
                    <span className="text-muted-foreground">
                      {formatDateTime(assignment.due_date)}
                    </span>
                  </p>
                  <p>
                    <span className="block font-medium">Cutoff</span>
                    <span className="text-muted-foreground">
                      {formatDateTime(assignment.cutoff_at)}
                    </span>
                  </p>
                  <p>
                    <span className="block font-medium">
                      Multiple submissions
                    </span>
                    <span className="text-muted-foreground">
                      {assignment.allow_multiple_submissions
                        ? "Allowed"
                        : "Not allowed"}
                    </span>
                  </p>
                  <p>
                    <span className="block font-medium">Late submissions</span>
                    <span className="text-muted-foreground">
                      {assignment.allow_late_submissions
                        ? "Allowed"
                        : "Not allowed"}
                    </span>
                  </p>
                  <p>
                    <span className="block font-medium">Maximum file size</span>
                    <span className="text-muted-foreground">
                      {assignment.max_file_size_mb} MB per file
                    </span>
                  </p>
                </CardContent>
              </Card>
              <SubmissionPanel
                submission={submission}
                maxScore={assignment.max_score}
              />
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}

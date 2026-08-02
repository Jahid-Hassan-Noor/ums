"use client"

import Link from "next/link"
import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Loader2,
  MessageSquare,
  Paperclip,
  Plus,
  RefreshCw,
  Send,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type AssignmentListMode = "all" | "submissions" | "feedback"

type Offering = {
  id: number
  course_code: string
  course_title: string
  section: string
  semester: string
  sections: Array<{
    id: number
    title: string
    section_type: string
    section_type_label: string
  }>
}

type Assignment = {
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
  submission_type: string
  accepted_file_type: string
  accepted_file_types: string[]
  max_files: number
  max_file_size_mb: number
  allow_multiple_submissions: boolean
  allow_late_submissions: boolean
  status: string
  created_by: string
  submission_count: number | null
  graded_count: number | null
  offering: Offering
}

type RubricCriterion = {
  title?: string
  description?: string
  max_score?: number | string
}

type Rubric = {
  id: number
  title: string
  criteria: RubricCriterion[]
  max_score: string
  is_active: boolean
}

type Comment = {
  id: number
  body: string
  is_private: boolean
  author: string
  author_role: string
  submission_id: number | null
  created_at: string | null
}

type Attachment = {
  id: number
  file: string
  name: string
  uploaded_at: string | null
}

type FeedbackEntry = {
  id: number
  reviewer: string
  rubric_id: number | null
  rubric_scores: Record<string, number>
  comments: string
  created_at: string | null
}

type Submission = {
  id: number
  student: { id: number; name: string; username: string }
  content: string
  attempt_count: number
  status: string
  status_label: string
  grade: string | null
  feedback: string
  submitted_at: string | null
  last_modified_at: string | null
  graded_by: string
  graded_at: string | null
  attachments: Attachment[]
  feedback_entries: FeedbackEntry[]
  comments: Comment[]
}

type AssignmentGroupOverview = {
  id: number
  name: string
  leader_id: number
  leader: string
  members: Array<{
    id: number
    name: string
    username: string
    tutorial_group: string
    lab_group: string
    country: string
    is_leader: boolean
  }>
  rule_status: {
    member_count: number
    max_members: number
    countries: string[]
    country_count: number
    required_country_count: number
    violations: string[]
    is_ready: boolean
  }
}

type AssignmentDetailResponse = {
  title: string
  assignment: Assignment
  rubrics: Rubric[]
  comments: Comment[]
  groups: AssignmentGroupOverview[]
  submissions: Submission[]
  message?: string
}

type CreateOptions = {
  offerings: Offering[]
  activity_types: Array<{ value: string; label: string }>
  collaboration_modes: Array<{ value: string; label: string }>
  submission_types: Array<{ value: string; label: string }>
  file_types: Array<{ value: string; label: string }>
  max_file_limit: number
  max_file_size_limit_mb: number
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

function rubricCriteriaFromText(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [title, score, description] = line.split("|").map((part) => part.trim())
      return {
        title,
        max_score: Number(score) || 0,
        description: description || "",
      }
    })
}

function nativeSelectClass() {
  return "h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
}

function Notice({ error, success }: { error: string; success: string }) {
  if (!error && !success) return null
  return (
    <div
      className={`flex gap-2 rounded-lg border p-3 text-sm ${
        error ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"
      }`}
    >
      {error ? <AlertCircle className="mt-0.5 size-4" /> : <CheckCircle2 className="mt-0.5 size-4" />}
      {error || success}
    </div>
  )
}

export function TeacherAssignmentsPage({ mode = "all" }: { mode?: AssignmentListMode }) {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadAssignments = useCallback(async () => {
    const response = await apiFetch<{ assignments: Assignment[] }>("/teacher/assignments")
    setAssignments(response.assignments)
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAssignments()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load assignments."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAssignments])

  const visibleAssignments = assignments.filter((assignment) => {
    if (mode === "submissions") return (assignment.submission_count ?? 0) > 0
    if (mode === "feedback") return (assignment.graded_count ?? 0) > 0
    return true
  })

  const pageTitle = mode === "submissions" ? "Assignment Submissions" : mode === "feedback" ? "Grading & Feedback" : "Assignments"

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/assignments", title: "Assignments" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{pageTitle}</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Create assignments, monitor submissions, apply rubrics, and return grades and feedback.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant={mode === "all" ? "default" : "outline"} render={<Link href="/teacher/assignments" />}>All</Button>
            <Button variant={mode === "submissions" ? "default" : "outline"} render={<Link href="/teacher/assignments/submissions" />}>Submissions</Button>
            <Button variant={mode === "feedback" ? "default" : "outline"} render={<Link href="/teacher/assignments/feedback" />}>Feedback</Button>
            <Button render={<Link href="/teacher/assignments/create" />}><Plus className="size-4" />Create</Button>
            <Button variant="outline" onClick={() => void loadAssignments()}><RefreshCw className="size-4" />Refresh</Button>
          </div>
        </section>

        <Notice error={error} success="" />
        {loading ? (
          <div className="flex h-56 items-center justify-center"><Loader2 className="size-7 animate-spin text-muted-foreground" /></div>
        ) : visibleAssignments.length ? (
          <section className="grid gap-4 lg:grid-cols-2">
            {visibleAssignments.map((assignment) => (
              <Card key={assignment.id} className="border-border/70 shadow-sm">
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardDescription>{assignment.offering.course_code} / {assignment.offering.section}</CardDescription>
                      <CardTitle className="mt-1">{assignment.title}</CardTitle>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">{assignment.activity_kind_label}</Badge>
                      <Badge variant="outline">{assignment.status}</Badge>
                    </div>
                  </div>
                  <CardDescription>{assignment.offering.semester}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {assignment.description ? <p className="text-sm leading-6 text-muted-foreground">{assignment.description}</p> : null}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <p><span className="block font-medium">Due</span><span className="text-muted-foreground">{formatDateTime(assignment.due_date)}</span></p>
                    <p><span className="block font-medium">Maximum score</span><span className="text-muted-foreground">{assignment.max_score}</span></p>
                    <p><span className="block font-medium">Submissions</span><span className="text-muted-foreground">{assignment.submission_count ?? 0}</span></p>
                    <p><span className="block font-medium">Graded</span><span className="text-muted-foreground">{assignment.graded_count ?? 0}</span></p>
                  </div>
                  <Button render={<Link href={`/teacher/assignments/${assignment.id}`} />}>
                    <ClipboardCheck className="size-4" />
                    Open assignment
                  </Button>
                </CardContent>
              </Card>
            ))}
          </section>
        ) : (
          <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No assignments match this view.</CardContent></Card>
        )}
      </main>
    </div>
  )
}

export function TeacherAssignmentCreatePage({ offeringId = "" }: { offeringId?: string }) {
  const [options, setOptions] = useState<CreateOptions | null>(null)
  const [selectedOfferingId, setSelectedOfferingId] = useState(offeringId)
  const [activityKind, setActivityKind] = useState<"assignment" | "lab_activity">("assignment")
  const [collaborationMode, setCollaborationMode] = useState<"individual" | "group">("individual")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [createdId, setCreatedId] = useState<number | null>(null)

  useEffect(() => {
    void apiFetch<CreateOptions>("/teacher/assignments/create")
      .then(setOptions)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load assignment options."))
  }, [])

  async function createAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const form = new FormData(event.currentTarget)
      const response = await apiFetch<{ message: string; assignment: Assignment }>("/teacher/assignments/create", {
        method: "POST",
        body: JSON.stringify({
          offering_id: Number(form.get("offering_id")),
          section_id: form.get("section_id") ? Number(form.get("section_id")) : null,
          activity_kind: form.get("activity_kind"),
          collaboration_mode: form.get("collaboration_mode"),
          max_group_members: collaborationMode === "group" ? Number(form.get("max_group_members") || 2) : 1,
          require_same_tutorial_group: form.get("require_same_tutorial_group") === "on",
          require_same_lab_group: form.get("require_same_lab_group") === "on",
          min_distinct_countries: collaborationMode === "group" ? Number(form.get("min_distinct_countries") || 0) : 0,
          group_rules: form.get("group_rules"),
          title: form.get("title"),
          description: form.get("description"),
          instructions: form.get("instructions"),
          file_instructions: form.get("file_instructions"),
          opens_at: form.get("opens_at") || null,
          due_date: form.get("due_date") || null,
          cutoff_at: form.get("cutoff_at") || null,
          max_score: Number(form.get("max_score") || 100),
          submission_type: form.get("submission_type"),
          accepted_file_types: form.getAll("accepted_file_types"),
          max_files: Number(form.get("max_files") || 1),
          max_file_size_mb: Number(form.get("max_file_size_mb") || 10),
          allow_multiple_submissions: form.get("allow_multiple_submissions") === "on",
          allow_late_submissions: form.get("allow_late_submissions") === "on",
          status: form.get("status"),
          rubric_title: form.get("rubric_title"),
          rubric_criteria: rubricCriteriaFromText(String(form.get("rubric_criteria") || "")),
        }),
      })
      setCreatedId(response.assignment.id)
      setSuccess(response.message)
      event.currentTarget.reset()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create assignment.")
    } finally {
      setSaving(false)
    }
  }

  const selectedOffering = options?.offerings.find((offering) => String(offering.id) === selectedOfferingId)
  const availableSections =
    activityKind === "lab_activity"
      ? selectedOffering?.sections.filter((section) => section.section_type === "lab_work") ?? []
      : selectedOffering?.sections ?? []

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/assignments", title: "Assignments" },
          { href: "/teacher/assignments/create", title: "Create" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Create Assignment</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure publication, submission rules, deadlines, accepted files, and an optional grading rubric.
          </p>
        </section>
        <Notice error={error} success={success} />
        {createdId ? (
          <Button render={<Link href={`/teacher/assignments/${createdId}`} />}>Open created assignment</Button>
        ) : null}
        {!options ? (
          <div className="flex h-56 items-center justify-center"><Loader2 className="size-7 animate-spin text-muted-foreground" /></div>
        ) : (
          <form className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]" onSubmit={createAssignment}>
            <Card>
              <CardHeader><CardTitle>Assignment details</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="offering_id">Course</Label>
                  <select
                    id="offering_id"
                    name="offering_id"
                    value={selectedOfferingId}
                    required
                    className={nativeSelectClass()}
                    onChange={(event) => setSelectedOfferingId(event.target.value)}
                  >
                    <option value="">Select a course</option>
                    {options.offerings.map((offering) => (
                      <option key={offering.id} value={offering.id}>{offering.course_code} / {offering.section} / {offering.semester}</option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="activity_kind">Activity type</Label>
                    <select
                      id="activity_kind"
                      name="activity_kind"
                      value={activityKind}
                      className={nativeSelectClass()}
                      onChange={(event) => setActivityKind(event.target.value as "assignment" | "lab_activity")}
                    >
                      {options.activity_types.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="section_id">{activityKind === "lab_activity" ? "Lab-work section" : "Course section"}</Label>
                    <select
                      id="section_id"
                      name="section_id"
                      required={activityKind === "lab_activity"}
                      className={nativeSelectClass()}
                    >
                      <option value="">{activityKind === "lab_activity" ? "Select a lab-work section" : "No section"}</option>
                      {availableSections.map((section) => (
                        <option key={section.id} value={section.id}>{section.title} / {section.section_type_label}</option>
                      ))}
                    </select>
                    {activityKind === "lab_activity" && !availableSections.length ? (
                      <p className="text-xs text-amber-700">
                        Create a Lab work section in the course workspace before publishing this activity.
                      </p>
                    ) : null}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="collaboration_mode">Work mode</Label>
                  <select
                    id="collaboration_mode"
                    name="collaboration_mode"
                    value={collaborationMode}
                    className={nativeSelectClass()}
                    onChange={(event) => setCollaborationMode(event.target.value as "individual" | "group")}
                  >
                    {options.collaboration_modes.map((item) => (
                      <option key={item.value} value={item.value}>{item.label}</option>
                    ))}
                  </select>
                </div>
                {collaborationMode === "group" ? (
                  <div className="space-y-4 rounded-lg border bg-muted/20 p-4">
                    <div>
                      <p className="font-medium">Group formation rules</p>
                      <p className="text-sm text-muted-foreground">
                        The creator becomes leader. Only the leader submits final work and books group presentation slots.
                      </p>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="max_group_members">Maximum members</Label>
                        <Input id="max_group_members" name="max_group_members" type="number" min="2" max="20" defaultValue="4" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="min_distinct_countries">Minimum countries</Label>
                        <Input id="min_distinct_countries" name="min_distinct_countries" type="number" min="0" max="20" defaultValue="0" />
                      </div>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" name="require_same_tutorial_group" />
                      Members must be from the same tutorial group
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" name="require_same_lab_group" />
                      Members must be from the same lab group
                    </label>
                    <div className="space-y-2">
                      <Label htmlFor="group_rules">Additional group criteria</Label>
                      <Textarea
                        id="group_rules"
                        name="group_rules"
                        placeholder="Example: Groups should combine technical and presentation roles."
                      />
                    </div>
                  </div>
                ) : null}
                <div className="space-y-2"><Label htmlFor="title">Title</Label><Input id="title" name="title" required /></div>
                <div className="space-y-2"><Label htmlFor="description">Description</Label><Textarea id="description" name="description" /></div>
                <div className="space-y-2"><Label htmlFor="instructions">Instructions</Label><Textarea id="instructions" name="instructions" className="min-h-32" /></div>
                <div className="space-y-2"><Label htmlFor="file_instructions">File instructions</Label><Textarea id="file_instructions" name="file_instructions" /></div>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2"><Label htmlFor="opens_at">Opens</Label><Input id="opens_at" name="opens_at" type="datetime-local" /></div>
                  <div className="space-y-2"><Label htmlFor="due_date">Due</Label><Input id="due_date" name="due_date" type="datetime-local" required /></div>
                  <div className="space-y-2"><Label htmlFor="cutoff_at">Cutoff</Label><Input id="cutoff_at" name="cutoff_at" type="datetime-local" /></div>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-5">
              <Card>
                <CardHeader><CardTitle>Submission settings</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2"><Label htmlFor="max_score">Maximum score</Label><Input id="max_score" name="max_score" type="number" min="1" step="0.01" defaultValue="100" /></div>
                  <div className="space-y-2"><Label htmlFor="submission_type">Submission type</Label><select id="submission_type" name="submission_type" className={nativeSelectClass()}>{options.submission_types.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
                  <div className="space-y-2">
                    <Label>Accepted file formats</Label>
                    <div className="grid grid-cols-2 gap-2 rounded-lg border p-3">
                      {options.file_types.map((item) => (
                        <label key={item.value} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            name="accepted_file_types"
                            value={item.value}
                            defaultChecked={item.value === "pdf"}
                          />
                          {item.label}
                        </label>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">Select one or more formats students may upload.</p>
                  </div>
                  <div className="space-y-2"><Label htmlFor="max_files">Maximum files</Label><Input id="max_files" name="max_files" type="number" min="1" max={options.max_file_limit} defaultValue="1" /></div>
                  <div className="space-y-2">
                    <Label htmlFor="max_file_size_mb">Maximum size of each file (MB)</Label>
                    <Input
                      id="max_file_size_mb"
                      name="max_file_size_mb"
                      type="number"
                      min="1"
                      max={options.max_file_size_limit_mb}
                      defaultValue="10"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="allow_multiple_submissions" />Allow multiple submissions</label>
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="allow_late_submissions" />Allow late submissions</label>
                  <div className="space-y-2"><Label htmlFor="status">Publication status</Label><select id="status" name="status" defaultValue="published" className={nativeSelectClass()}><option value="draft">Draft</option><option value="published">Published</option></select></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Optional rubric</CardTitle>
                  <CardDescription>One criterion per line: title | score | description</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2"><Label htmlFor="rubric_title">Rubric title</Label><Input id="rubric_title" name="rubric_title" /></div>
                  <div className="space-y-2"><Label htmlFor="rubric_criteria">Criteria</Label><Textarea id="rubric_criteria" name="rubric_criteria" className="min-h-32" placeholder={"Design | 40 | Interface quality\nImplementation | 60 | Working solution"} /></div>
                  <Button className="w-full" type="submit" disabled={saving}>
                    {saving ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    Create assignment
                  </Button>
                </CardContent>
              </Card>
            </div>
          </form>
        )}
      </main>
    </div>
  )
}

function SubmissionReviewCard({
  submission,
  assignment,
  rubrics,
  onMutate,
  saving,
}: {
  submission: Submission
  assignment: Assignment
  rubrics: Rubric[]
  onMutate: (payload: Record<string, unknown>) => Promise<void>
  saving: boolean
}) {
  async function grade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await onMutate({
      action: "grade_submission",
      submission_id: submission.id,
      grade: Number(form.get("grade")),
      feedback: form.get("feedback"),
      rubric_id: form.get("rubric_id") || null,
      rubric_scores: {},
    })
  }

  async function comment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await onMutate({
      action: "add_comment",
      submission_id: submission.id,
      body: form.get("body"),
      is_private: form.get("is_private") === "on",
    })
    event.currentTarget.reset()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardDescription>@{submission.student.username} / Attempt {submission.attempt_count}</CardDescription>
            <CardTitle>{submission.student.name}</CardTitle>
          </div>
          <Badge variant="outline">{submission.status_label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-4">
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            <p><span className="block font-medium">Submitted</span><span className="text-muted-foreground">{formatDateTime(submission.submitted_at)}</span></p>
            <p><span className="block font-medium">Grade</span><span className="text-muted-foreground">{submission.grade ?? "Not graded"} / {assignment.max_score}</span></p>
          </div>
          {submission.content ? <div className="rounded-lg border bg-muted/30 p-4"><p className="font-medium">Submission text</p><p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{submission.content}</p></div> : null}
          {submission.attachments.map((attachment) => (
            <a key={attachment.id} href={attachment.file} target="_blank" rel="noreferrer" className="flex items-center gap-2 rounded-lg border p-3 text-sm hover:bg-muted/40">
              <Paperclip className="size-4" />{attachment.name}
            </a>
          ))}
          {submission.feedback_entries.map((entry) => (
            <div key={entry.id} className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
              <p className="font-medium">{entry.reviewer} / {formatDateTime(entry.created_at)}</p>
              <p className="mt-2 whitespace-pre-wrap">{entry.comments}</p>
            </div>
          ))}
          {submission.comments.map((entry) => (
            <div key={entry.id} className="rounded-lg border p-3 text-sm">
              <p className="font-medium">{entry.author}{entry.is_private ? " / Private note" : ""}</p>
              <p className="mt-1 text-muted-foreground">{entry.body}</p>
            </div>
          ))}
        </div>
        <div className="space-y-4">
          <form className="space-y-3 rounded-lg border p-4" onSubmit={grade}>
            <p className="font-medium">Grade and return feedback</p>
            <div className="space-y-2"><Label htmlFor={`grade-${submission.id}`}>Grade</Label><Input id={`grade-${submission.id}`} name="grade" type="number" min="0" max={assignment.max_score} step="0.01" defaultValue={submission.grade ?? ""} required /></div>
            <div className="space-y-2"><Label htmlFor={`rubric-${submission.id}`}>Rubric</Label><select id={`rubric-${submission.id}`} name="rubric_id" className={nativeSelectClass()}><option value="">No rubric</option>{rubrics.map((rubric) => <option key={rubric.id} value={rubric.id}>{rubric.title}</option>)}</select></div>
            <div className="space-y-2"><Label htmlFor={`feedback-${submission.id}`}>Feedback</Label><Textarea id={`feedback-${submission.id}`} name="feedback" defaultValue={submission.feedback} /></div>
            <Button className="w-full" type="submit" disabled={saving}><GraduationCap className="size-4" />Save grade</Button>
          </form>
          <form className="space-y-3 rounded-lg border p-4" onSubmit={comment}>
            <p className="font-medium">Submission comment</p>
            <Textarea name="body" required />
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_private" />Private teacher note</label>
            <Button className="w-full" variant="outline" type="submit" disabled={saving}><MessageSquare className="size-4" />Add comment</Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}

export function TeacherAssignmentDetailPage({
  assignmentId,
  submissionsOnly = false,
}: {
  assignmentId: string
  submissionsOnly?: boolean
}) {
  const [data, setData] = useState<AssignmentDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadDetail = useCallback(async () => {
    setData(await apiFetch<AssignmentDetailResponse>(`/teacher/assignments/${assignmentId}`))
  }, [assignmentId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDetail()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load assignment."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadDetail])

  async function mutate(payload: Record<string, unknown>) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<AssignmentDetailResponse>(`/teacher/assignments/${assignmentId}`, {
        method: "POST",
        body: JSON.stringify(payload),
      })
      setData(response)
      setSuccess(response.message ?? "Assignment updated.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update assignment.")
    } finally {
      setSaving(false)
    }
  }

  async function addRubric(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await mutate({
      action: "save_rubric",
      title: form.get("title"),
      max_score: data?.assignment.max_score,
      criteria: rubricCriteriaFromText(String(form.get("criteria") || "")),
      is_active: true,
    })
    event.currentTarget.reset()
  }

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await mutate({ action: "add_comment", body: form.get("body"), is_private: false })
    event.currentTarget.reset()
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/assignments", title: "Assignments" },
          { href: `/teacher/assignments/${assignmentId}`, title: "Detail" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <Notice error={error} success={success} />
        {loading ? (
          <div className="flex h-56 items-center justify-center"><Loader2 className="size-7 animate-spin text-muted-foreground" /></div>
        ) : data ? (
          <>
            <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-medium text-primary">{data.assignment.offering.course_code} / {data.assignment.offering.section}</p>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{data.assignment.title}</h1>
                <p className="mt-2 text-sm text-muted-foreground">Due {formatDateTime(data.assignment.due_date)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{data.assignment.status}</Badge>
                <Button variant="outline" render={<Link href={`/teacher/courses/${data.assignment.offering.id}/assignments`} />}>Course assignments</Button>
              </div>
            </section>

            {!submissionsOnly ? (
              <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_24rem]">
                <Card>
                  <CardHeader><CardTitle>Assignment brief</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    {data.assignment.description ? <div><p className="font-medium">Description</p><p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{data.assignment.description}</p></div> : null}
                    {data.assignment.instructions ? <div><p className="font-medium">Instructions</p><p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{data.assignment.instructions}</p></div> : null}
                    <div className="grid gap-3 text-sm sm:grid-cols-3">
                      <p><span className="block font-medium">Maximum score</span>{data.assignment.max_score}</p>
                      <p><span className="block font-medium">Submission type</span>{data.assignment.submission_type}</p>
                      <p><span className="block font-medium">Cutoff</span>{formatDateTime(data.assignment.cutoff_at)}</p>
                    </div>
                  </CardContent>
                </Card>
                {data.assignment.collaboration_mode === "group" ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Project Groups</CardTitle>
                      <CardDescription>
                        {data.assignment.max_group_members} members maximum
                        {data.assignment.min_distinct_countries
                          ? ` / ${data.assignment.min_distinct_countries} countries minimum`
                          : ""}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {data.groups.length ? data.groups.map((group) => (
                        <div key={group.id} className="rounded-lg border p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="font-medium">{group.name}</p>
                              <p className="text-sm text-muted-foreground">Leader: {group.leader}</p>
                            </div>
                            <Badge variant="outline">
                              {group.rule_status.member_count}/{group.rule_status.max_members} members
                            </Badge>
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {group.members.map((member) => (
                              <Badge key={member.id} variant="secondary">
                                {member.name}{member.is_leader ? " / Leader" : ""}
                              </Badge>
                            ))}
                          </div>
                          {group.rule_status.violations.length ? (
                            <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                              {group.rule_status.violations.join(" ")}
                            </div>
                          ) : (
                            <p className="mt-3 text-sm text-emerald-700">All configured group criteria are satisfied.</p>
                          )}
                        </div>
                      )) : (
                        <p className="py-6 text-center text-sm text-muted-foreground">No student groups have been created yet.</p>
                      )}
                    </CardContent>
                  </Card>
                ) : null}
                <div className="space-y-5">
                  <Card>
                    <CardHeader><CardTitle>Rubrics</CardTitle></CardHeader>
                    <CardContent className="space-y-3">
                      {data.rubrics.map((rubric) => (
                        <div key={rubric.id} className="rounded-lg border p-3">
                          <p className="font-medium">{rubric.title}</p>
                          <p className="text-sm text-muted-foreground">{rubric.max_score} marks</p>
                          <ul className="mt-2 space-y-1 text-sm">
                            {rubric.criteria.map((criterion, index) => <li key={`${rubric.id}-${index}`}>{criterion.title} / {criterion.max_score}</li>)}
                          </ul>
                        </div>
                      ))}
                      <form className="space-y-3 border-t pt-4" onSubmit={addRubric}>
                        <Input name="title" placeholder="Rubric title" required />
                        <Textarea name="criteria" placeholder={"Design | 40 | Interface quality\nImplementation | 60 | Working solution"} required />
                        <Button className="w-full" variant="outline" type="submit" disabled={saving}><Plus className="size-4" />Add rubric</Button>
                      </form>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader><CardTitle>Assignment comments</CardTitle></CardHeader>
                    <CardContent className="space-y-3">
                      {data.comments.map((comment) => <div key={comment.id} className="rounded-lg border p-3 text-sm"><p className="font-medium">{comment.author}</p><p className="mt-1 text-muted-foreground">{comment.body}</p></div>)}
                      <form className="space-y-3" onSubmit={addComment}>
                        <Textarea name="body" placeholder="Post a clarification for students" required />
                        <Button className="w-full" variant="outline" type="submit" disabled={saving}><Send className="size-4" />Post comment</Button>
                      </form>
                    </CardContent>
                  </Card>
                </div>
              </section>
            ) : null}

            <section className="space-y-4">
              <div>
                <h2 className="text-xl font-semibold">Student submissions</h2>
                <p className="mt-1 text-sm text-muted-foreground">{data.submissions.length} submission{data.submissions.length === 1 ? "" : "s"} received.</p>
              </div>
              {data.submissions.length ? data.submissions.map((submission) => (
                <SubmissionReviewCard
                  key={submission.id}
                  submission={submission}
                  assignment={data.assignment}
                  rubrics={data.rubrics}
                  onMutate={mutate}
                  saving={saving}
                />
              )) : (
                <Card><CardContent className="py-12 text-center text-sm text-muted-foreground"><FileText className="mx-auto mb-3 size-8" />No submissions yet.</CardContent></Card>
              )}
            </section>
          </>
        ) : null}
      </main>
    </div>
  )
}

"use client"

import { useEffect, useMemo, useState } from "react"
import {
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Loader2,
  RefreshCw,
  Save,
  Search,
  UserRoundCheck,
  XCircle,
  type LucideIcon,
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
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import { statusBadgeVariant } from "@/lib/status-utils"

type ClassMeeting = {
  id: number
  course_code: string
  course_title: string
  section: string
  class_type_label: string
  day_label: string
  meeting_date: string | null
  start_time: string | null
  end_time: string | null
  room: string
  venue: string
}

type LeaveApproval = {
  id: number
  approver: { id: number; name: string }
  approval_role: "teacher" | "dean"
  class_meeting: ClassMeeting | null
  status: "pending" | "approved" | "rejected"
  note: string
  decided_at: string | null
  created_at: string
  is_current_approver?: boolean
}

type LeaveRequest = {
  id: number
  student: { id: number; name: string; student_id: string }
  start_date: string
  end_date: string
  reason: string
  status: "draft" | "pending" | "approved" | "rejected" | "cancelled"
  review_note: string
  created_at: string
  reviewed_at: string | null
  approval_summary: {
    total: number
    pending: number
    approved: number
    rejected: number
  }
  approvals: LeaveApproval[]
}

type TeacherLeaveResponse = {
  approver_profile_id: number
  leave_requests: LeaveRequest[]
}

function statusLabel(status: string) {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function formatDate(value: string | null) {
  if (!value) return "Not scheduled"
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

function formatDateTime(value: string | null) {
  if (!value) return ""
  return new Date(value).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function dateRangeLabel(request: LeaveRequest) {
  if (request.start_date === request.end_date)
    return formatDate(request.start_date)
  return `${formatDate(request.start_date)} - ${formatDate(request.end_date)}`
}

function classMeetingLabel(meeting: ClassMeeting | null) {
  if (!meeting) return "Dean approval"
  const date = meeting.meeting_date
    ? formatDate(meeting.meeting_date)
    : meeting.day_label
  const time =
    meeting.start_time && meeting.end_time
      ? `${meeting.start_time} - ${meeting.end_time}`
      : ""
  return [meeting.course_code, meeting.section, date, time]
    .filter(Boolean)
    .join(" - ")
}

export function TeacherLeaveRequestsPage() {
  const [requests, setRequests] = useState<LeaveRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<number | null>(null)
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [filter, setFilter] = useState("pending")
  const [query, setQuery] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    const response = await apiFetch<TeacherLeaveResponse>(
      "/teacher/leave-requests"
    )
    setRequests(response.leave_requests ?? [])
    setNotes((current) => {
      const next = { ...current }
      for (const request of response.leave_requests ?? []) {
        for (const approval of request.approvals.filter(
          (item) => item.is_current_approver
        )) {
          next[approval.id] = next[approval.id] ?? approval.note ?? ""
        }
      }
      return next
    })
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load leave requests."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  async function decide(
    approval: LeaveApproval,
    decision: "approved" | "rejected"
  ) {
    setSaving(approval.id)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{
        message: string
        leave_request: LeaveRequest
      }>("/teacher/leave-requests", {
        method: "POST",
        body: JSON.stringify({
          approval_id: approval.id,
          decision,
          note: notes[approval.id] ?? "",
        }),
      })
      setSuccess(response.message)
      setRequests((current) =>
        current.map((request) =>
          request.id === response.leave_request.id
            ? response.leave_request
            : request
        )
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to record leave decision."
      )
    } finally {
      setSaving(null)
    }
  }

  const summary = useMemo(() => {
    const myApprovals = requests.flatMap((request) =>
      request.approvals.filter((approval) => approval.is_current_approver)
    )
    return {
      total: myApprovals.length,
      pending: myApprovals.filter((approval) => approval.status === "pending")
        .length,
      approved: myApprovals.filter((approval) => approval.status === "approved")
        .length,
      rejected: myApprovals.filter((approval) => approval.status === "rejected")
        .length,
    }
  }, [requests])

  const visibleRequests = useMemo(
    () =>
      requests.filter((request) => {
        const myApprovals = request.approvals.filter(
          (approval) => approval.is_current_approver
        )
        const matchesStatus =
          filter === "all" ||
          myApprovals.some((approval) => approval.status === filter)
        const text =
          `${request.student.name} ${request.student.student_id} ${request.reason} ${request.approvals
            .map(
              (approval) =>
                `${approval.approver.name} ${approval.class_meeting?.course_code ?? ""} ${approval.class_meeting?.course_title ?? ""}`
            )
            .join(" ")}`.toLowerCase()
        return matchesStatus && text.includes(query.trim().toLowerCase())
      }),
    [filter, query, requests]
  )

  function updateNote(id: number, value: string) {
    setNotes((current) => ({ ...current, [id]: value }))
  }

  const summaryCards: Array<{
    label: string
    value: number
    icon: LucideIcon
  }> = [
    { label: "Assigned", value: summary.total, icon: ClipboardList },
    { label: "Pending", value: summary.pending, icon: RefreshCw },
    { label: "Approved", value: summary.approved, icon: CheckCircle2 },
    { label: "Rejected", value: summary.rejected, icon: XCircle },
  ]

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/leave-requests", title: "Leave Requests" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Leave Requests
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Approve leave of advance requests assigned to your classes or dean
              designation.
            </p>
          </div>
          <Button variant="outline" onClick={() => void loadData()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </section>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="size-4" />
            {success}
          </p>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {summaryCards.map(({ label, value, icon: Icon }) => (
            <Card key={label}>
              <CardHeader>
                <CardDescription className="flex items-center gap-2">
                  <Icon className="size-4" />
                  {label}
                </CardDescription>
                <CardTitle className="text-3xl">{value}</CardTitle>
              </CardHeader>
            </Card>
          ))}
        </section>

        <section className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute top-3 left-3 size-4 text-muted-foreground" />
            <Input
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search student, course, or reason"
            />
          </div>
          <select
            className="h-10 rounded-lg border bg-background px-3 text-sm"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          >
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="all">All</option>
          </select>
        </section>

        {loading ? (
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        ) : null}
        {!loading && visibleRequests.length ? (
          <section className="grid gap-4 xl:grid-cols-2">
            {visibleRequests.map((request) => {
              const myApprovals = request.approvals.filter(
                (approval) => approval.is_current_approver
              )
              return (
                <Card key={request.id}>
                  <CardHeader>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <CardDescription>
                          {request.student.student_id} - Submitted{" "}
                          {formatDateTime(request.created_at)}
                        </CardDescription>
                        <CardTitle className="flex flex-wrap items-center gap-2">
                          <CalendarDays className="size-5" />
                          {request.student.name} - {dateRangeLabel(request)}
                        </CardTitle>
                      </div>
                      <Badge variant={statusBadgeVariant(request.status)}>
                        {statusLabel(request.status)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm leading-6 text-muted-foreground">
                      {request.reason}
                    </p>
                    <div className="grid gap-3 rounded-lg border bg-muted/25 p-4 text-sm sm:grid-cols-3">
                      <p>
                        <strong>All approvers:</strong>{" "}
                        {request.approval_summary.approved}/
                        {request.approval_summary.total}
                      </p>
                      <p>
                        <strong>Pending:</strong>{" "}
                        {request.approval_summary.pending}
                      </p>
                      <p>
                        <strong>Rejected:</strong>{" "}
                        {request.approval_summary.rejected}
                      </p>
                    </div>
                    <div className="space-y-3 border-t pt-4">
                      <p className="flex items-center gap-2 text-sm font-medium">
                        <UserRoundCheck className="size-4" />
                        Your approvals
                      </p>
                      {myApprovals.map((approval) => (
                        <div
                          key={approval.id}
                          className="rounded-lg border bg-background p-4"
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge
                                  variant={
                                    approval.approval_role === "dean"
                                      ? "outline"
                                      : "secondary"
                                  }
                                >
                                  {approval.approval_role === "dean"
                                    ? "Dean"
                                    : "Teacher"}
                                </Badge>
                                <p className="font-medium">
                                  {classMeetingLabel(approval.class_meeting)}
                                </p>
                              </div>
                              {approval.class_meeting?.course_title ? (
                                <p className="mt-1 text-sm text-muted-foreground">
                                  {approval.class_meeting.course_title}
                                </p>
                              ) : null}
                            </div>
                            <Badge
                              variant={statusBadgeVariant(approval.status)}
                            >
                              {statusLabel(approval.status)}
                            </Badge>
                          </div>
                          {approval.status === "pending" ? (
                            <div className="mt-4 space-y-3">
                              <Textarea
                                value={notes[approval.id] ?? ""}
                                onChange={(event) =>
                                  updateNote(approval.id, event.target.value)
                                }
                                placeholder="Decision note"
                              />
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  onClick={() =>
                                    void decide(approval, "approved")
                                  }
                                  disabled={saving === approval.id}
                                >
                                  {saving === approval.id ? (
                                    <Loader2 className="size-4 animate-spin" />
                                  ) : (
                                    <Save className="size-4" />
                                  )}
                                  Approve
                                </Button>
                                <Button
                                  variant="destructive"
                                  onClick={() =>
                                    void decide(approval, "rejected")
                                  }
                                  disabled={saving === approval.id}
                                >
                                  <XCircle className="size-4" />
                                  Reject
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <div className="mt-3 text-sm text-muted-foreground">
                              {approval.note ? <p>{approval.note}</p> : null}
                              {approval.decided_at ? (
                                <p>
                                  Decided {formatDateTime(approval.decided_at)}
                                </p>
                              ) : null}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </section>
        ) : null}
        {!loading && !visibleRequests.length ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <ClipboardList className="size-9 text-muted-foreground" />
              <p className="font-medium">No leave approvals found</p>
              <p className="max-w-md text-sm text-muted-foreground">
                Assigned leave approvals will appear here.
              </p>
            </CardContent>
          </Card>
        ) : null}
      </main>
    </div>
  )
}

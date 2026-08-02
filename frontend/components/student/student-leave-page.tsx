"use client"

import Link from "next/link"
import { FormEvent, useEffect, useMemo, useState } from "react"
import {
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileUp,
  Loader2,
  RefreshCw,
  Send,
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
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import { statusBadgeVariant } from "@/lib/status-utils"

type StudentLeaveMode = "requests" | "apply" | "history"

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
  topic: string
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
  attachment: string | null
  status: "draft" | "pending" | "approved" | "rejected" | "cancelled"
  review_note: string
  created_at: string
  updated_at: string
  reviewed_at: string | null
  approval_summary: {
    total: number
    pending: number
    approved: number
    rejected: number
  }
  approvals: LeaveApproval[]
}

type LeaveResponse = {
  leave_requests: LeaveRequest[]
}

async function fetchLeaveRequests(endpoint: string) {
  const response = await apiFetch<LeaveResponse>(endpoint)
  return response.leave_requests ?? []
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

function ApprovalTimeline({ approvals }: { approvals: LeaveApproval[] }) {
  if (!approvals.length) {
    return (
      <div className="rounded-lg border bg-muted/25 p-4 text-sm text-muted-foreground">
        No approvers were assigned to this request.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {approvals.map((approval) => (
        <div key={approval.id} className="rounded-lg border bg-background p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant={
                    approval.approval_role === "dean" ? "outline" : "secondary"
                  }
                >
                  {approval.approval_role === "dean" ? "Dean" : "Teacher"}
                </Badge>
                <p className="font-medium">
                  {approval.approver.name || "Assigned approver"}
                </p>
              </div>
              <p className="text-sm text-muted-foreground">
                {classMeetingLabel(approval.class_meeting)}
              </p>
              {approval.class_meeting?.course_title ? (
                <p className="text-sm text-muted-foreground">
                  {approval.class_meeting.course_title}
                </p>
              ) : null}
            </div>
            <Badge variant={statusBadgeVariant(approval.status)}>
              {statusLabel(approval.status)}
            </Badge>
          </div>
          {approval.note ? (
            <p className="mt-3 text-sm text-muted-foreground">
              {approval.note}
            </p>
          ) : null}
          {approval.decided_at ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Decided {formatDateTime(approval.decided_at)}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  )
}

function LeaveRequestCard({ request }: { request: LeaveRequest }) {
  const progress =
    request.approval_summary.total > 0
      ? `${request.approval_summary.approved}/${request.approval_summary.total} approved`
      : "No approvers assigned"

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardDescription>
              Submitted {formatDateTime(request.created_at)}
            </CardDescription>
            <CardTitle className="flex flex-wrap items-center gap-2">
              <CalendarDays className="size-5" />
              {dateRangeLabel(request)}
            </CardTitle>
          </div>
          <Badge variant={statusBadgeVariant(request.status)}>
            {statusLabel(request.status)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 rounded-lg border bg-muted/25 p-4 text-sm sm:grid-cols-3">
          <p>
            <strong>Approval progress:</strong> {progress}
          </p>
          <p>
            <strong>Pending:</strong> {request.approval_summary.pending}
          </p>
          <p>
            <strong>Rejected:</strong> {request.approval_summary.rejected}
          </p>
        </div>
        <div>
          <p className="text-sm font-medium">Reason</p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {request.reason}
          </p>
        </div>
        {request.review_note ? (
          <div className="rounded-lg border bg-muted/25 p-4 text-sm">
            <strong>Review note:</strong> {request.review_note}
          </div>
        ) : null}
        {request.attachment ? (
          <Button
            size="sm"
            variant="outline"
            render={<Link href={request.attachment} target="_blank" />}
          >
            <FileUp className="size-4" />
            Attachment
          </Button>
        ) : null}
        <div className="space-y-3 border-t pt-4">
          <p className="flex items-center gap-2 text-sm font-medium">
            <UserRoundCheck className="size-4" />
            Approval trail
          </p>
          <ApprovalTimeline approvals={request.approvals} />
        </div>
      </CardContent>
    </Card>
  )
}

function EmptyState({ mode }: { mode: StudentLeaveMode }) {
  const copy =
    mode === "history"
      ? "Completed leave applications will appear here."
      : "Your submitted leave applications will appear here."
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <ClipboardList className="size-9 text-muted-foreground" />
        <p className="font-medium">No leave requests found</p>
        <p className="max-w-md text-sm text-muted-foreground">{copy}</p>
        {mode !== "history" ? (
          <Button render={<Link href="/student/leave/apply" />}>
            <Send className="size-4" />
            Apply Leave
          </Button>
        ) : null}
      </CardContent>
    </Card>
  )
}

export function StudentLeavePage({
  mode = "requests",
}: {
  mode?: StudentLeaveMode
}) {
  const [requests, setRequests] = useState<LeaveRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [reason, setReason] = useState("")
  const [attachment, setAttachment] = useState<File | null>(null)

  const endpoint =
    mode === "history" ? "/student/leave/history" : "/student/leave"

  async function loadData() {
    setRequests(await fetchLeaveRequests(endpoint))
  }

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError("")
      void fetchLeaveRequests(endpoint)
        .then((items) => {
          if (active) setRequests(items)
        })
        .catch((caught) => {
          if (active)
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load leave requests."
            )
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [endpoint])

  async function submitLeave(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const formData = new FormData()
      formData.append("start_date", startDate)
      formData.append("end_date", endDate)
      formData.append("reason", reason)
      if (attachment) formData.append("attachment", attachment)
      const response = await apiFetch<{
        message: string
        leave_request: LeaveRequest
      }>("/student/leave/apply", {
        method: "POST",
        body: formData,
      })
      setSuccess(response.message)
      setStartDate("")
      setEndDate("")
      setReason("")
      setAttachment(null)
      if (mode === "history") {
        await loadData()
      } else {
        setRequests((current) => [
          response.leave_request,
          ...current.filter((item) => item.id !== response.leave_request.id),
        ])
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to submit leave request."
      )
    } finally {
      setSaving(false)
    }
  }

  const summary = useMemo(
    () => ({
      total: requests.length,
      pending: requests.filter((request) => request.status === "pending")
        .length,
      approved: requests.filter((request) => request.status === "approved")
        .length,
      rejected: requests.filter((request) => request.status === "rejected")
        .length,
    }),
    [requests]
  )

  const visibleRequests =
    mode === "requests"
      ? requests.filter((request) => request.status === "pending")
      : requests
  const pageTitle =
    mode === "apply"
      ? "Apply Leave"
      : mode === "history"
        ? "Leave History"
        : "Leave Requests"
  const pageDescription =
    mode === "apply"
      ? "Submit a leave of advance request for one day or a date range."
      : mode === "history"
        ? "Review completed leave of advance applications."
        : "Track leave of advance approvals from class teachers and the dean."
  const summaryCards: Array<{
    label: string
    value: number
    icon: LucideIcon
  }> = [
    { label: "Total", value: summary.total, icon: ClipboardList },
    { label: "Pending", value: summary.pending, icon: RefreshCw },
    { label: "Approved", value: summary.approved, icon: CheckCircle2 },
    { label: "Rejected", value: summary.rejected, icon: XCircle },
  ]

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/leave", title: "Leave" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {pageTitle}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {pageDescription}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" render={<Link href="/student/leave" />}>
              Requests
            </Button>
            <Button
              variant="outline"
              render={<Link href="/student/leave/apply" />}
            >
              Apply
            </Button>
            <Button
              variant="outline"
              render={<Link href="/student/leave/history" />}
            >
              History
            </Button>
            <Button variant="outline" onClick={() => void loadData()}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
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

        <section
          className={
            mode === "apply"
              ? "grid gap-5 xl:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]"
              : "space-y-4"
          }
        >
          {mode === "apply" ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="size-5" />
                  Leave of Advance
                </CardTitle>
                <CardDescription>
                  Dates must follow the configured minimum notice period.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={submitLeave}>
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
                    <div className="space-y-2">
                      <Label htmlFor="start_date">Start date</Label>
                      <Input
                        id="start_date"
                        type="date"
                        value={startDate}
                        onChange={(event) => setStartDate(event.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="end_date">End date</Label>
                      <Input
                        id="end_date"
                        type="date"
                        value={endDate}
                        onChange={(event) => setEndDate(event.target.value)}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reason">Reason</Label>
                    <Textarea
                      id="reason"
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                      placeholder="Medical appointment, family matter, official activity"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="attachment">Attachment (optional)</Label>
                    <Input
                      id="attachment"
                      type="file"
                      onChange={(event) =>
                        setAttachment(event.target.files?.[0] ?? null)
                      }
                    />
                  </div>
                  <Button className="w-full" type="submit" disabled={saving}>
                    {saving ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Send className="size-4" />
                    )}
                    Submit Leave
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          <div className="space-y-4">
            {loading ? (
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            ) : null}
            {!loading && visibleRequests.length
              ? visibleRequests.map((request) => (
                  <LeaveRequestCard key={request.id} request={request} />
                ))
              : null}
            {!loading && !visibleRequests.length ? (
              <EmptyState mode={mode} />
            ) : null}
          </div>
        </section>
      </main>
    </div>
  )
}

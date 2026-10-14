"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  ExternalLink,
  Loader2,
  QrCode,
  RefreshCw,
  Save,
  ShieldCheck,
  Users,
  XCircle,
} from "lucide-react"
import { QRCodeSVG } from "qrcode.react"

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
import { apiFetch } from "@/lib/auth"
import { statusBadgeVariant } from "@/lib/status-utils"

type AttendanceWindow = {
  can_open: boolean
  reason: string
  starts_at: string | null
  ends_at: string | null
}

type Meeting = {
  id: number
  offering_id: number
  course_code: string
  course_title: string
  semester: string
  day_of_week: number
  meeting_date: string | null
  start_time: string
  end_time: string
  tutorial_group: string
  lab_group: string
  class_type: string
  status: string
  venue: string
  attendance_window: AttendanceWindow
}

type Session = {
  id: number
  session_date: string
  offering_id: number
  course_code: string
  course_title: string
  class_meeting: Meeting | null
  start_time: string | null
  end_time: string | null
  status: "draft" | "open" | "closed" | "cancelled"
  opens_at: string | null
  closes_at: string | null
  actual_starts_at: string | null
  actual_ends_at: string | null
  schedule_change_reason: string
  cancellation_reason: string
  qr_token?: string
  qr_expires_at?: string | null
  qr_ttl_seconds?: number
  attendance_url_path?: string
}

type TeacherAttendanceResponse = {
  meetings: Meeting[]
  sessions: Session[]
}

type AttendanceRecord = {
  id: number | null
  session_id: number
  class_date: string
  start_time: string | null
  end_time: string | null
  status: string
  session_status: string
  present: boolean
  source: string
  reason: string
  medical_certificate: string
  marked_at: string | null
}

type RosterStudent = {
  student_id: number
  student_name: string
  ums_id: string
  group: string
  record: AttendanceRecord
}

type CorrectionsResponse = {
  sessions: Session[]
  selected_session: Session | null
  students: RosterStudent[]
}

type CourseAttendanceResponse = {
  course: {
    id: number
    code: string
    title: string
    section: string
  }
  sessions: Session[]
  students: Array<{
    student_id: number
    student_name: string
    ums_id: string
    attended: number
    total_classes: number
    attendance_percentage: number
  }>
}

type TeacherAttendanceView = "overview" | "create" | "sessions" | "corrections"

function formatDate(value: string | null | undefined) {
  if (!value) return "Not recorded"
  return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  )
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not recorded"
  return new Date(value).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function groupLabel(meeting: Meeting | null) {
  if (!meeting) return "All enrolled students"
  return meeting.lab_group || meeting.tutorial_group || "Course section"
}

function Alert({
  kind,
  children,
}: {
  kind: "error" | "success"
  children: React.ReactNode
}) {
  const Icon = kind === "error" ? XCircle : CheckCircle2
  return (
    <div
      className={
        kind === "error"
          ? "flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          : "flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"
      }
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      <span>{children}</span>
    </div>
  )
}

function AttendanceHeader({
  title,
  description,
  onRefresh,
  refreshing,
}: {
  title: string
  description: string
  onRefresh?: () => void
  refreshing?: boolean
}) {
  return (
    <>
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/attendance", title: "Attendance" },
          { href: "#", title },
        ]}
      />
      <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {title}
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {description}
          </p>
        </div>
        {onRefresh ? (
          <Button variant="outline" onClick={onRefresh} disabled={refreshing}>
            <RefreshCw
              className={refreshing ? "size-4 animate-spin" : "size-4"}
            />
            Refresh
          </Button>
        ) : null}
      </section>
    </>
  )
}

function QrSessionCard({
  session,
  busy,
  onAction,
}: {
  session: Session
  busy: boolean
  onAction: (
    sessionId: number,
    action: "refresh_qr" | "regenerate_qr" | "close"
  ) => Promise<void>
}) {
  const [now, setNow] = useState(() => Date.now())
  const [origin, setOrigin] = useState("")
  const refreshedToken = useRef("")
  const expiresAt = session.qr_expires_at
    ? new Date(session.qr_expires_at).getTime()
    : now
  const secondsLeft = Math.max(0, Math.ceil((expiresAt - now) / 1000))
  const attendanceUrl =
    origin && session.attendance_url_path
      ? `${origin}${session.attendance_url_path}`
      : ""

  useEffect(() => {
    const originTimer = window.setTimeout(
      () => setOrigin(window.location.origin),
      0
    )
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => {
      window.clearTimeout(originTimer)
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    if (
      session.status === "open" &&
      session.qr_token &&
      secondsLeft === 0 &&
      refreshedToken.current !== session.qr_token &&
      !busy
    ) {
      refreshedToken.current = session.qr_token
      void onAction(session.id, "refresh_qr")
    }
  }, [
    busy,
    onAction,
    secondsLeft,
    session.id,
    session.qr_token,
    session.status,
  ])

  return (
    <Card className="overflow-hidden border-sky-200 shadow-sm">
      <CardHeader className="border-b bg-sky-50/70 text-center">
        <CardTitle>
          {session.course_code} - {session.course_title}
        </CardTitle>
        <CardDescription>
          {formatDate(session.session_date)} ·{" "}
          {session.start_time ?? "Scheduled class"}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4 p-6">
        <p className="text-sm font-medium">
          Students can scan using their phone camera.
        </p>
        <p className="text-sm text-sky-700">
          QR code expires in: <strong>{secondsLeft} seconds</strong>
        </p>
        {attendanceUrl && session.qr_token ? (
          <div className="rounded-2xl border bg-white p-4 shadow-sm">
            <QRCodeSVG
              value={attendanceUrl}
              size={260}
              level="M"
              marginSize={2}
              title={`Attendance QR for ${session.course_code}`}
            />
          </div>
        ) : (
          <div className="grid size-72 place-items-center rounded-2xl border border-dashed">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        )}
        <p className="font-mono text-2xl font-semibold tracking-[0.35em]">
          {session.qr_token || "------"}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <Button
            onClick={() => void onAction(session.id, "regenerate_qr")}
            disabled={busy || session.status !== "open"}
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Regenerate QR
          </Button>
          {attendanceUrl ? (
            <Button
              variant="outline"
              render={
                <a href={attendanceUrl} target="_blank" rel="noreferrer" />
              }
            >
              <ExternalLink className="size-4" />
              Open student link
            </Button>
          ) : null}
          <Button
            variant="destructive"
            onClick={() => void onAction(session.id, "close")}
            disabled={busy || session.status !== "open"}
          >
            Close attendance
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function TeacherSessionWorkspace({
  view,
}: {
  view: Exclude<TeacherAttendanceView, "corrections">
}) {
  const [data, setData] = useState<TeacherAttendanceResponse>({
    meetings: [],
    sessions: [],
  })
  const [activeSession, setActiveSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const endpoint =
      view === "sessions"
        ? "/teacher/attendance/sessions"
        : "/teacher/attendance"
    const response = await apiFetch<TeacherAttendanceResponse>(endpoint)
    setData({
      meetings: response.meetings ?? [],
      sessions: response.sessions ?? [],
    })
    setActiveSession((current) => {
      if (current) {
        return (
          response.sessions?.find((session) => session.id === current.id) ??
          current
        )
      }
      return (
        response.sessions?.find((session) => session.status === "open") ?? null
      )
    })
  }, [view])

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load attendance."
            )
          }
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [loadData])

  async function refresh() {
    setLoading(true)
    setError("")
    try {
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to refresh attendance."
      )
    } finally {
      setLoading(false)
    }
  }

  async function startSession(meeting: Meeting) {
    setBusy(meeting.id)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string; session: Session }>(
        "/teacher/attendance/create",
        {
          method: "POST",
          body: JSON.stringify({ class_meeting_id: meeting.id }),
        }
      )
      setActiveSession(response.session)
      setSuccess(response.message)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to open attendance."
      )
    } finally {
      setBusy(null)
    }
  }

  const sessionAction = useCallback(
    async (
      sessionId: number,
      action: "refresh_qr" | "regenerate_qr" | "close"
    ) => {
      setBusy(sessionId)
      setError("")
      setSuccess("")
      try {
        const response = await apiFetch<{ message: string; session: Session }>(
          "/teacher/attendance/sessions",
          {
            method: "POST",
            body: JSON.stringify({ session_id: sessionId, action }),
          }
        )
        setActiveSession(
          response.session.status === "open" ? response.session : null
        )
        setSuccess(response.message)
        await loadData()
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to update the session."
        )
      } finally {
        setBusy(null)
      }
    },
    [loadData]
  )

  const availableMeetings = useMemo(
    () => data.meetings.filter((meeting) => meeting.attendance_window.can_open),
    [data.meetings]
  )
  const openSessions = data.sessions.filter(
    (session) => session.status === "open"
  )
  const closedSessions = data.sessions.filter(
    (session) => session.status === "closed"
  )
  const title =
    view === "create"
      ? "Open Class Attendance"
      : view === "sessions"
        ? "Attendance Sessions"
        : "Attendance"
  const description =
    view === "create"
      ? "Open a QR attendance window during the scheduled class. A fresh code is generated every 60 seconds."
      : view === "sessions"
        ? "Monitor open and previous class sessions, rotate QR codes, or close attendance."
        : "Manage today’s class QR sessions, review recent attendance, and correct student records."

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <AttendanceHeader
        title={title}
        description={description}
        onRefresh={() => void refresh()}
        refreshing={loading}
      />
      <main className="flex-1 space-y-6 px-4 pt-5 pb-10 sm:px-6">
        {error ? <Alert kind="error">{error}</Alert> : null}
        {success ? <Alert kind="success">{success}</Alert> : null}
        {loading && !data.sessions.length ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading attendance workspace…
          </div>
        ) : null}

        {view === "overview" ? (
          <section className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">Available now</p>
                  <p className="mt-1 text-3xl font-semibold">
                    {availableMeetings.length}
                  </p>
                </div>
                <Clock3 className="size-6 text-sky-600" />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">Open sessions</p>
                  <p className="mt-1 text-3xl font-semibold">
                    {openSessions.length}
                  </p>
                </div>
                <QrCode className="size-6 text-emerald-600" />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Closed sessions
                  </p>
                  <p className="mt-1 text-3xl font-semibold">
                    {closedSessions.length}
                  </p>
                </div>
                <ShieldCheck className="size-6 text-violet-600" />
              </CardContent>
            </Card>
          </section>
        ) : null}

        {activeSession?.status === "open" ? (
          <section className="mx-auto max-w-xl">
            <QrSessionCard
              session={activeSession}
              busy={busy === activeSession.id}
              onAction={sessionAction}
            />
          </section>
        ) : null}

        {view !== "sessions" ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarClock className="size-5" />
                Scheduled classes
              </CardTitle>
              <CardDescription>
                The Open QR button is enabled only while the scheduled class is
                in progress.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 xl:grid-cols-2">
              {data.meetings.map((meeting) => (
                <div
                  key={meeting.id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-background p-4"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">
                        {meeting.course_code} · {meeting.course_title}
                      </p>
                      <Badge
                        variant={
                          meeting.attendance_window.can_open
                            ? "default"
                            : "outline"
                        }
                      >
                        {meeting.attendance_window.can_open
                          ? "Available now"
                          : "Scheduled"}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {meeting.start_time}–{meeting.end_time} ·{" "}
                      {groupLabel(meeting)}
                      {meeting.venue ? ` · ${meeting.venue}` : ""}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {meeting.attendance_window.reason}
                    </p>
                  </div>
                  <Button
                    onClick={() => void startSession(meeting)}
                    disabled={
                      !meeting.attendance_window.can_open || busy === meeting.id
                    }
                  >
                    {busy === meeting.id ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <QrCode className="size-4" />
                    )}
                    Open QR
                  </Button>
                </div>
              ))}
              {!data.meetings.length ? (
                <p className="text-sm text-muted-foreground">
                  No class meetings are assigned to your current course
                  offerings.
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : null}

        {view === "sessions" || view === "overview" ? (
          <Card>
            <CardHeader>
              <CardTitle>Session history</CardTitle>
              <CardDescription>
                Open a session to display its QR, or continue to course
                attendance for the full roster.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.sessions.map((session) => (
                <div
                  key={session.id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-background p-4"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">
                        {session.course_code} · {session.course_title}
                      </p>
                      <Badge variant={statusBadgeVariant(session.status)}>
                        {session.status}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {formatDate(session.session_date)} ·{" "}
                      {groupLabel(session.class_meeting)} · opened{" "}
                      {formatDateTime(session.opens_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {session.status === "open" ? (
                      <Button
                        variant="outline"
                        onClick={() => setActiveSession(session)}
                      >
                        <QrCode className="size-4" />
                        Show QR
                      </Button>
                    ) : null}
                    <Button
                      variant="outline"
                      render={
                        <Link
                          href={`/teacher/courses/${session.offering_id}/attendance`}
                        />
                      }
                    >
                      <Users className="size-4" />
                      Course report
                    </Button>
                  </div>
                </div>
              ))}
              {!data.sessions.length ? (
                <p className="text-sm text-muted-foreground">
                  No attendance sessions have been opened yet.
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </main>
    </div>
  )
}

function TeacherCorrectionsWorkspace() {
  const [data, setData] = useState<CorrectionsResponse>({
    sessions: [],
    selected_session: null,
    students: [],
  })
  const [selectedSession, setSelectedSession] = useState("")
  const [drafts, setDrafts] = useState<
    Record<number, { status: string; reason: string; file?: File }>
  >({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async (sessionId?: string) => {
    const query = sessionId
      ? `?session_id=${encodeURIComponent(sessionId)}`
      : ""
    const response = await apiFetch<CorrectionsResponse>(
      `/teacher/attendance/corrections${query}`
    )
    setData(response)
    setSelectedSession(
      response.selected_session ? String(response.selected_session.id) : ""
    )
    setDrafts(
      Object.fromEntries(
        response.students.map((student) => [
          student.student_id,
          {
            status:
              student.record.status === "absent" ||
              student.record.status === "pending"
                ? "attend"
                : student.record.status,
            reason: student.record.reason ?? "",
          },
        ])
      )
    )
  }, [])

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load corrections."
            )
          }
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [loadData])

  async function chooseSession(sessionId: string) {
    setSelectedSession(sessionId)
    setLoading(true)
    setError("")
    try {
      await loadData(sessionId)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load the session roster."
      )
    } finally {
      setLoading(false)
    }
  }

  async function saveStudent(student: RosterStudent) {
    const draft = drafts[student.student_id]
    if (!draft) return
    setSaving(student.student_id)
    setError("")
    setSuccess("")
    try {
      const body = new FormData()
      body.set("session_id", selectedSession)
      body.set("student_id", String(student.student_id))
      body.set("attendance_status", draft.status)
      body.set("reason", draft.reason)
      if (draft.file) body.set("medical_certificate", draft.file)
      const response = await apiFetch<{ message: string }>(
        "/teacher/attendance/corrections",
        { method: "POST", body }
      )
      setSuccess(`${response.message} ${student.student_name}`)
      await loadData(selectedSession)
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to save correction."
      )
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <AttendanceHeader
        title="Attendance Corrections"
        description="Review a completed or open class roster and record Attend, Late, Absent with reason, or Absent with medical certificate."
        onRefresh={() => void chooseSession(selectedSession)}
        refreshing={loading}
      />
      <main className="flex-1 space-y-6 px-4 pt-5 pb-10 sm:px-6">
        {error ? <Alert kind="error">{error}</Alert> : null}
        {success ? <Alert kind="success">{success}</Alert> : null}
        <Card>
          <CardHeader>
            <CardTitle>Select class session</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              className="h-10 w-full max-w-2xl rounded-lg border border-input bg-background px-3 text-sm"
              value={selectedSession}
              onChange={(event) => void chooseSession(event.target.value)}
            >
              <option value="">Select a session</option>
              {data.sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.course_code} · {formatDate(session.session_date)} ·{" "}
                  {groupLabel(session.class_meeting)} · {session.status}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardCheck className="size-5" />
              Class roster
            </CardTitle>
            <CardDescription>
              Saving creates or updates the student’s attendance record for this
              session.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? <Loader2 className="size-5 animate-spin" /> : null}
            {data.students.map((student) => {
              const draft = drafts[student.student_id] ?? {
                status: "attend",
                reason: "",
              }
              return (
                <div
                  key={student.student_id}
                  className="grid gap-4 rounded-xl border bg-background p-4 lg:grid-cols-[1.2fr_0.8fr_1.4fr_auto] lg:items-end"
                >
                  <div>
                    <p className="font-semibold">{student.student_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {student.ums_id || `Profile ${student.student_id}`} ·{" "}
                      {student.group || "Course section"}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`status-${student.student_id}`}>
                      Status
                    </Label>
                    <select
                      id={`status-${student.student_id}`}
                      className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"
                      value={draft.status}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [student.student_id]: {
                            ...draft,
                            status: event.target.value,
                          },
                        }))
                      }
                    >
                      <option value="attend">Attend</option>
                      <option value="late">Late</option>
                      <option value="absent_reason">Absent with reason</option>
                      <option value="absent_mc">Absent with MC</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`reason-${student.student_id}`}>
                      Reason / note
                    </Label>
                    <Input
                      id={`reason-${student.student_id}`}
                      value={draft.reason}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [student.student_id]: {
                            ...draft,
                            reason: event.target.value,
                          },
                        }))
                      }
                      placeholder="Optional for Attend; required context for absence"
                    />
                    {draft.status === "absent_mc" ? (
                      <Input
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [student.student_id]: {
                              ...draft,
                              file: event.target.files?.[0],
                            },
                          }))
                        }
                      />
                    ) : null}
                  </div>
                  <Button
                    onClick={() => void saveStudent(student)}
                    disabled={saving === student.student_id}
                  >
                    {saving === student.student_id ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Save className="size-4" />
                    )}
                    Save
                  </Button>
                </div>
              )
            })}
            {!loading && !data.students.length ? (
              <p className="text-sm text-muted-foreground">
                Select a session with enrolled students to make corrections.
              </p>
            ) : null}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export function TeacherAttendancePage({
  view = "overview",
}: {
  view?: TeacherAttendanceView
}) {
  if (view === "corrections") return <TeacherCorrectionsWorkspace />
  return <TeacherSessionWorkspace view={view} />
}

export function TeacherCourseAttendancePage({
  courseId,
}: {
  courseId: string
}) {
  const [data, setData] = useState<CourseAttendanceResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    const response = await apiFetch<CourseAttendanceResponse>(
      `/teacher/courses/${encodeURIComponent(courseId)}/attendance`
    )
    setData(response)
  }, [courseId])

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active) {
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load course attendance."
            )
          }
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [loadData])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <AttendanceHeader
        title={data ? `${data.course.code} Attendance` : "Course Attendance"}
        description={
          data
            ? `${data.course.title} · ${data.course.section || "All sections"}`
            : "Review attendance sessions and student percentages for this course."
        }
        onRefresh={() => void loadData()}
        refreshing={loading}
      />
      <main className="flex-1 space-y-6 px-4 pt-5 pb-10 sm:px-6">
        {error ? <Alert kind="error">{error}</Alert> : null}
        {loading && !data ? <Loader2 className="size-6 animate-spin" /> : null}
        {data ? (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Student attendance summary</CardTitle>
                <CardDescription>
                  Attendance includes all non-cancelled sessions created for
                  this offering.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-2xl text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="px-3 py-3 font-medium">Student</th>
                      <th className="px-3 py-3 font-medium">Student ID</th>
                      <th className="px-3 py-3 font-medium">Classes</th>
                      <th className="px-3 py-3 font-medium">Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.students.map((student) => (
                      <tr
                        key={student.student_id}
                        className="border-b last:border-0"
                      >
                        <td className="px-3 py-4 font-medium">
                          {student.student_name}
                        </td>
                        <td className="px-3 py-4">{student.ums_id || "—"}</td>
                        <td className="px-3 py-4">
                          {student.attended}/{student.total_classes}
                        </td>
                        <td className="px-3 py-4">
                          <span
                            className={
                              student.attendance_percentage < 80
                                ? "font-semibold text-red-600"
                                : "font-semibold text-emerald-700"
                            }
                          >
                            {student.attendance_percentage}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Class sessions</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {data.sessions.map((session) => (
                  <div
                    key={session.id}
                    className="rounded-xl border bg-background p-4"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold">
                        {formatDate(session.session_date)}
                      </p>
                      <Badge variant={statusBadgeVariant(session.status)}>
                        {session.status}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {groupLabel(session.class_meeting)} ·{" "}
                      {session.start_time ?? "Time not recorded"}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  )
}

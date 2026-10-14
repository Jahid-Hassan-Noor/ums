"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  BarChart3,
  CalendarCheck2,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Loader2,
  QrCode,
  RefreshCw,
  Search,
  ShieldAlert,
  XCircle,
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
import { apiFetch } from "@/lib/auth"

type Semester = {
  id: number
  name: string
  academic_session: string
  is_active: boolean
  start_date: string | null
  end_date: string | null
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

type CourseAttendance = {
  offering_id: number
  course_code: string
  course_title: string
  semester: string
  semester_id: number
  group: string
  attended: number
  late: number
  absent: number
  total_classes: number
  attendance_percentage: number
  records: AttendanceRecord[]
}

type AttendanceResponse = {
  semester: { id: number; name: string } | null
  semesters: Semester[]
  courses: CourseAttendance[]
}

type SessionPreview = {
  id: number
  session_date: string
  course_code: string
  course_title: string
  status: string
  start_time: string | null
  end_time: string | null
  class_meeting: {
    start_time: string
    end_time: string
    tutorial_group: string
    lab_group: string
    venue: string
  } | null
}

type CodeLookupResponse = {
  session: SessionPreview | null
  code: string
  is_valid: boolean
}

type StudentAttendanceView = "overview" | "code" | "report"

function formatDate(value: string | null | undefined) {
  if (!value) return "Not recorded"
  return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    attend: "Attend",
    late: "Late",
    absent: "Absent",
    absent_reason: "Absent with reason",
    absent_mc: "Absent with MC",
    pending: "In progress",
  }
  return labels[status] ?? status.replaceAll("_", " ")
}

function recordBadgeVariant(status: string) {
  if (status === "attend") return "default" as const
  if (status === "late" || status === "pending") return "secondary" as const
  return "destructive" as const
}

function attendanceTone(percentage: number) {
  if (percentage >= 90) return "text-emerald-700"
  if (percentage >= 80) return "text-amber-700"
  return "text-red-700"
}

function StudentAttendanceHeader({
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
          { href: "/student", title: "Student" },
          { href: "/student/attendance", title: "Attendance" },
          { href: "#", title },
        ]}
      />
      <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {description}
          </p>
        </div>
        {onRefresh ? (
          <Button variant="outline" onClick={onRefresh} disabled={refreshing}>
            <RefreshCw className={refreshing ? "size-4 animate-spin" : "size-4"} />
            Refresh
          </Button>
        ) : null}
      </section>
    </>
  )
}

function Message({
  kind,
  children,
}: {
  kind: "error" | "success"
  children: React.ReactNode
}) {
  const Icon = kind === "success" ? CheckCircle2 : XCircle
  return (
    <div
      className={
        kind === "success"
          ? "flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"
          : "flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      }
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      <span>{children}</span>
    </div>
  )
}

function AttendanceCodeWorkspace({ initialCode = "" }: { initialCode?: string }) {
  const [code, setCode] = useState(initialCode.trim().toLowerCase())
  const [lookup, setLookup] = useState<CodeLookupResponse | null>(null)
  const [loading, setLoading] = useState(Boolean(initialCode))
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const inspectCode = useCallback(async (value: string) => {
    if (!value) {
      setLookup(null)
      return
    }
    const response = await apiFetch<CodeLookupResponse>(
      `/student/attendance/qr?code=${encodeURIComponent(value)}`
    )
    setLookup(response)
  }, [])

  useEffect(() => {
    if (!initialCode) return
    let active = true
    const timer = window.setTimeout(() => {
      void inspectCode(initialCode.trim().toLowerCase())
        .catch((caught) => {
          if (active) {
            setError(caught instanceof Error ? caught.message : "Unable to verify attendance code.")
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
  }, [initialCode, inspectCode])

  async function submitCode(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = code.trim().toLowerCase()
    if (!normalized) {
      setError("Enter the six-character code shown by your teacher.")
      return
    }
    setSubmitting(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>("/student/attendance/code", {
        method: "POST",
        body: JSON.stringify({ code: normalized }),
      })
      setSuccess(response.message)
      await inspectCode(normalized)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit attendance.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <StudentAttendanceHeader
        title="Class Attendance"
        description="Your scanned QR code fills the attendance code automatically. Confirm the class, then submit before the 60-second code expires."
      />
      <main className="flex flex-1 items-start justify-center px-4 pb-10 pt-8 sm:px-6">
        <Card className="w-full max-w-2xl border-sky-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <QrCode className="size-5 text-sky-600" />
              Submit attendance code
            </CardTitle>
            <CardDescription>
              Scan the teacher’s QR with your phone camera, or type the code shown below it.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {error ? <Message kind="error">{error}</Message> : null}
            {success ? <Message kind="success">{success}</Message> : null}
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Checking class code…
              </div>
            ) : null}
            {lookup?.session ? (
              <div className="rounded-xl border bg-sky-50/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">
                      {lookup.session.course_code} · {lookup.session.course_title}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {formatDate(lookup.session.session_date)}
                      {lookup.session.start_time
                        ? ` · ${lookup.session.start_time}–${lookup.session.end_time}`
                        : ""}
                    </p>
                  </div>
                  <Badge variant={lookup.is_valid ? "default" : "destructive"}>
                    {lookup.is_valid ? "Code active" : "Expired"}
                  </Badge>
                </div>
              </div>
            ) : null}
            <form className="space-y-4" onSubmit={submitCode}>
              <div className="space-y-2">
                <Label htmlFor="attendance-code">Attendance code</Label>
                <Input
                  id="attendance-code"
                  value={code}
                  onChange={(event) =>
                    setCode(
                      event.target.value
                        .toLowerCase()
                        .replace(/[^a-z0-9]/g, "")
                        .slice(0, 6)
                    )
                  }
                  placeholder="e.g. 9zmvfa"
                  autoCapitalize="none"
                  autoCorrect="off"
                  inputMode="text"
                  className="h-12 font-mono text-lg tracking-[0.25em]"
                />
              </div>
              <Button type="submit" size="lg" disabled={submitting || code.length !== 6}>
                {submitting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <ClipboardCheck className="size-4" />
                )}
                Submit attendance
              </Button>
            </form>
            <div className="flex items-start gap-2 rounded-lg border border-dashed p-3 text-xs leading-5 text-muted-foreground">
              <ShieldAlert className="mt-0.5 size-4 shrink-0" />
              Attendance is accepted only for students enrolled in the displayed class group.
              Codes are replaced every 60 seconds and cannot be reused.
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

function StudentReportWorkspace({ overview = false }: { overview?: boolean }) {
  const [data, setData] = useState<AttendanceResponse | null>(null)
  const [selectedSemester, setSelectedSemester] = useState("")
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(
    async (semesterId?: string) => {
      const endpoint = overview ? "/student/attendance" : "/student/attendance/report"
      const queryString = semesterId
        ? `?semester_id=${encodeURIComponent(semesterId)}`
        : ""
      const response = await apiFetch<AttendanceResponse>(`${endpoint}${queryString}`)
      setData(response)
      const resolvedSemester = response.semester ? String(response.semester.id) : ""
      setSelectedSemester(resolvedSemester)
      setSelectedCourse((current) => {
        if (current && response.courses.some((course) => course.offering_id === current)) {
          return current
        }
        return overview ? null : (response.courses[0]?.offering_id ?? null)
      })
    },
    [overview]
  )

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active) {
            setError(caught instanceof Error ? caught.message : "Unable to load attendance report.")
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

  async function changeSemester(value: string) {
    setSelectedSemester(value)
    setLoading(true)
    setError("")
    try {
      await loadData(value)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load this semester.")
    } finally {
      setLoading(false)
    }
  }

  async function refresh() {
    setLoading(true)
    setError("")
    try {
      await loadData(selectedSemester)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to refresh attendance.")
    } finally {
      setLoading(false)
    }
  }

  const filteredCourses = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return data?.courses ?? []
    return (data?.courses ?? []).filter((course) =>
      [course.course_code, course.course_title, course.group]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [data?.courses, query])
  const selected =
    data?.courses.find((course) => course.offering_id === selectedCourse) ?? null
  const totals = useMemo(() => {
    const courses = data?.courses ?? []
    const attended = courses.reduce((sum, course) => sum + course.attended, 0)
    const classes = courses.reduce((sum, course) => sum + course.total_classes, 0)
    return {
      courses: courses.length,
      classes,
      percentage: classes ? Math.round((attended / classes) * 100) : 0,
    }
  }, [data?.courses])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <StudentAttendanceHeader
        title={overview ? "Attendance" : "Attendance Report"}
        description={
          overview
            ? "Submit a class code and monitor attendance for your running semester."
            : "Review running and completed semesters, then open any subject for class-by-class attendance."
        }
        onRefresh={() => void refresh()}
        refreshing={loading}
      />
      <main className="flex-1 space-y-6 px-4 pb-10 pt-5 sm:px-6">
        {error ? <Message kind="error">{error}</Message> : null}
        <section className="flex flex-wrap items-end gap-3">
          <label className="space-y-2 text-sm font-medium">
            <span>Semester</span>
            <select
              className="block h-10 min-w-72 rounded-lg border border-input bg-background px-3 text-sm"
              value={selectedSemester}
              onChange={(event) => void changeSemester(event.target.value)}
            >
              {(data?.semesters ?? []).map((semester) => (
                <option key={semester.id} value={semester.id}>
                  {semester.name}
                  {semester.is_active ? " · Running" : ""}
                </option>
              ))}
            </select>
          </label>
          <label className="relative block min-w-64 flex-1">
            <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search course code, subject, or group"
              className="pl-9"
            />
          </label>
          {overview ? (
            <Button render={<Link href="/student/attendance/code" />}>
              <QrCode className="size-4" />
              Enter class code
            </Button>
          ) : null}
        </section>

        {loading && !data ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading attendance…
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">Registered subjects</p>
                <p className="mt-1 text-3xl font-semibold">{totals.courses}</p>
              </div>
              <BarChart3 className="size-6 text-sky-600" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">Recorded classes</p>
                <p className="mt-1 text-3xl font-semibold">{totals.classes}</p>
              </div>
              <CalendarCheck2 className="size-6 text-violet-600" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">Overall attendance</p>
                <p className={`mt-1 text-3xl font-semibold ${attendanceTone(totals.percentage)}`}>
                  {totals.percentage}%
                </p>
              </div>
              <ClipboardCheck className="size-6 text-emerald-600" />
            </CardContent>
          </Card>
        </section>

        <Card>
          <CardHeader>
            <CardTitle>Class Attendance Report</CardTitle>
            <CardDescription>{data?.semester?.name ?? "No semester selected"}</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-3xl text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                  <th className="px-5 py-3 font-medium">Course</th>
                  <th className="px-5 py-3 font-medium">Group</th>
                  <th className="px-5 py-3 font-medium">Classes</th>
                  <th className="px-5 py-3 font-medium">Attendance</th>
                  <th className="px-5 py-3 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCourses.map((course) => (
                  <tr key={course.offering_id} className="border-b last:border-0">
                    <td className="px-5 py-4">
                      <p className="font-semibold">{course.course_code}</p>
                      <p className="mt-1 text-muted-foreground">{course.course_title}</p>
                    </td>
                    <td className="px-5 py-4">{course.group || "—"}</td>
                    <td className="px-5 py-4">
                      {course.attended}/{course.total_classes}
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`font-semibold ${attendanceTone(course.attendance_percentage)}`}
                      >
                        {course.attendance_percentage}%
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Button
                        size="sm"
                        onClick={() => setSelectedCourse(course.offering_id)}
                      >
                        View
                        <ChevronRight className="size-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!filteredCourses.length ? (
              <p className="p-6 text-sm text-muted-foreground">
                No attendance courses match this semester and search.
              </p>
            ) : null}
          </CardContent>
        </Card>

        {selected ? (
          <Card>
            <CardHeader>
              <CardTitle>
                {selected.course_code} · {selected.course_title}
              </CardTitle>
              <CardDescription>
                Group {selected.group || "—"} · {selected.attended} attended ·{" "}
                {selected.late} late · {selected.absent} absent/pending
              </CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <div className="flex min-w-max gap-3 pb-2">
                {selected.records.map((record) => (
                  <div
                    key={record.session_id}
                    className="w-48 shrink-0 rounded-xl border bg-background p-4"
                  >
                    <p className="font-semibold">{formatDate(record.class_date)}</p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock3 className="size-3" />
                      {record.start_time || "Time not recorded"}
                    </p>
                    <Badge className="mt-4" variant={recordBadgeVariant(record.status)}>
                      {statusLabel(record.status)}
                    </Badge>
                    {record.reason ? (
                      <p className="mt-3 text-xs leading-5 text-muted-foreground">
                        {record.reason}
                      </p>
                    ) : null}
                    {record.medical_certificate ? (
                      <a
                        className="mt-3 block text-xs font-medium text-sky-700 underline"
                        href={record.medical_certificate}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Medical certificate
                      </a>
                    ) : null}
                  </div>
                ))}
              </div>
              {!selected.records.length ? (
                <p className="text-sm text-muted-foreground">
                  No attendance sessions have been recorded for this subject.
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </main>
    </div>
  )
}

export function StudentAttendancePage({
  view = "overview",
  initialCode = "",
}: {
  view?: StudentAttendanceView
  initialCode?: string
}) {
  if (view === "code") return <AttendanceCodeWorkspace initialCode={initialCode} />
  return <StudentReportWorkspace overview={view === "overview"} />
}

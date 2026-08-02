"use client"

import Link from "next/link"
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react"
import {
  BarChart3,
  BookOpenCheck,
  CalendarCheck,
  Download,
  FileText,
  GraduationCap,
  Loader2,
  RefreshCw,
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
import { apiFetch, apiRequest } from "@/lib/auth"
import { triggerBlobDownload } from "@/lib/fetch-utils"
import { statusClassName } from "@/lib/status-utils"

type ResultsView = "semester" | "transcript" | "course-works" | "exam-slip"

type StudentInfo = {
  name: string
  student_id: string
  identity_card_no: string
  school: string
  programme: string
  address: string
  intake_session: string
}

type SemesterOption = {
  id: string
  label: string
  name?: string
  academic_session?: string
}

type GradeScaleRow = {
  grade: string
  score: string
  points: string
  assessment: string
}

type ResultRecord = {
  id: number
  semester_id: string
  course_code: string
  course_title: string
  credit_hours: string
  score: string
  grade: string
  grade_points: string
  gpa: string
  cgpa: string
  note: string
  published_at: string | null
}

type ResultGroup = {
  semester: SemesterOption
  records: ResultRecord[]
}

type ResultSummary = {
  include_gpa: boolean
  gpa: string
  cgpa: string
  registered_unit: string
  counted_credit: string
  cumulative_credit_earned: string
  academic_status: string
}

type SemesterResultsResponse = {
  title: string
  student: StudentInfo
  semesters: SemesterOption[]
  selected_semester: string
  groups: ResultGroup[]
  records: ResultRecord[]
  summary: ResultSummary
  grade_scale: GradeScaleRow[]
}

type TranscriptResponse = Omit<SemesterResultsResponse, "selected_semester">

type CourseworkRow = {
  offering_id: number
  course_code: string
  course_title: string
  section: string
  credit_hours: string
  coursework_mark: string
  coursework_weight: string
  final_exam_weight: string
  has_final_exam: boolean
  status: string
  published_at: string | null
  teacher: string
  final_exam_starts_at: string | null
  note: string
}

type CourseworksResponse = {
  title: string
  student: StudentInfo
  semester: SemesterOption | null
  default_coursework_weight: string
  default_final_exam_weight: string
  courseworks: CourseworkRow[]
}

type ExamSlipRow = {
  no: number
  course_code: string
  course_title: string
  credit_hours: string
  exam_date: string
  time: string
  venue: string
  note: string
  table_no: string
}

type ExamSlipResponse = {
  title: string
  student: StudentInfo
  semester: SemesterOption | null
  semesters: SemesterOption[]
  exams: ExamSlipRow[]
  total_credit_hours: string
  can_download: boolean
  generated_at: string
}

const RESULT_TABS: Array<{
  view: ResultsView
  label: string
  href: string
  icon: typeof GraduationCap
}> = [
  {
    view: "semester",
    label: "Semester Results",
    href: "/student/results/semester",
    icon: GraduationCap,
  },
  {
    view: "transcript",
    label: "Transcript",
    href: "/student/results/transcript",
    icon: FileText,
  },
  {
    view: "course-works",
    label: "Course Works",
    href: "/student/results/course-works",
    icon: BookOpenCheck,
  },
  {
    view: "exam-slip",
    label: "Exam Slip",
    href: "/student/results/exam-slip",
    icon: CalendarCheck,
  },
]

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not published"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not published"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

async function downloadPdf(endpoint: string, filename: string) {
  const response = await apiRequest(endpoint)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || "Unable to download PDF.")
  }
  const blob = await response.blob()
  triggerBlobDownload(blob, filename)
}

function ResultsNav({ active }: { active: ResultsView }) {
  return (
    <nav className="flex gap-2 overflow-x-auto pb-1">
      {RESULT_TABS.map((tab) => {
        const Icon = tab.icon
        const isActive = tab.view === active
        return (
          <Link
            key={tab.view}
            href={tab.href}
            className={`inline-flex h-10 shrink-0 items-center gap-2 rounded-lg border px-3 text-sm font-medium transition ${
              isActive
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background hover:bg-muted"
            }`}
          >
            <Icon className="size-4" />
            {tab.label}
          </Link>
        )
      })}
    </nav>
  )
}

function ResultsShell({
  active,
  title,
  description,
  children,
}: {
  active: ResultsView
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/results", title: "Results" },
          {
            href:
              RESULT_TABS.find((tab) => tab.view === active)?.href ??
              "/student/results",
            title,
          },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="space-y-4 border-b border-border/70 pb-5">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {title}
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            </div>
          </div>
          <ResultsNav active={active} />
        </section>
        {children}
      </main>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="size-4 animate-spin" />
      Loading academic records
    </div>
  )
}

function EmptyState({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-border bg-background p-6 text-sm text-muted-foreground">
      {children}
    </p>
  )
}

function ErrorState({ error }: { error: string }) {
  if (!error) return null
  return (
    <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      {error}
    </p>
  )
}

function SummaryCards({
  summary,
  publishedCount,
}: {
  summary: ResultSummary
  publishedCount: number
}) {
  const items = [
    {
      label: "Published Courses",
      value: String(publishedCount),
      icon: GraduationCap,
    },
    {
      label: "Cumulative Credit",
      value: summary.cumulative_credit_earned,
      icon: BarChart3,
    },
    { label: "CGPA", value: summary.cgpa, icon: FileText },
  ]
  if (summary.include_gpa) {
    items.splice(2, 0, { label: "GPA", value: summary.gpa, icon: BarChart3 })
  }
  return (
    <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <Card key={item.label} className="border-border/70 shadow-sm">
            <CardContent className="flex items-center justify-between gap-3 p-4">
              <div>
                <p className="text-sm text-muted-foreground">{item.label}</p>
                <p className="mt-1 text-2xl font-semibold">{item.value}</p>
              </div>
              <Icon className="size-5 text-muted-foreground" />
            </CardContent>
          </Card>
        )
      })}
    </section>
  )
}

function ResultTable({ groups }: { groups: ResultGroup[] }) {
  if (!groups.length)
    return (
      <EmptyState>No published result records are available yet.</EmptyState>
    )
  return (
    <section className="space-y-4">
      {groups.map((group) => (
        <Card key={group.semester.id} className="border-border/70 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">{group.semester.label}</CardTitle>
            <CardDescription>
              {group.records.length} published course result
              {group.records.length === 1 ? "" : "s"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-sm">
                <thead>
                  <tr className="border-b bg-muted/60 text-left">
                    <th className="px-3 py-2 font-medium">No</th>
                    <th className="px-3 py-2 font-medium">Course Code</th>
                    <th className="px-3 py-2 font-medium">Course Name</th>
                    <th className="px-3 py-2 text-center font-medium">Grade</th>
                    <th className="px-3 py-2 text-center font-medium">
                      Credit Hour
                    </th>
                    <th className="px-3 py-2 font-medium">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {group.records.map((record, index) => (
                    <tr key={record.id} className="border-b last:border-0">
                      <td className="px-3 py-2">{index + 1}</td>
                      <td className="px-3 py-2 font-medium">
                        {record.course_code}
                      </td>
                      <td className="px-3 py-2">{record.course_title}</td>
                      <td className="px-3 py-2 text-center font-semibold">
                        {record.grade || "-"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {record.credit_hours}
                      </td>
                      <td className="px-3 py-2">
                        {record.note ? (
                          <Badge variant="outline">{record.note}</Badge>
                        ) : (
                          "-"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ))}
    </section>
  )
}

function GradeScaleTable({ rows }: { rows: GradeScaleRow[] }) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">GPA Calculation</CardTitle>
        <CardDescription>
          AIU grading scale used for GPA and CGPA calculation.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] border-collapse text-sm">
            <thead>
              <tr className="border-b bg-muted/60 text-left">
                <th className="px-3 py-2 font-medium">Grade</th>
                <th className="px-3 py-2 font-medium">Score</th>
                <th className="px-3 py-2 font-medium">Grade Point</th>
                <th className="px-3 py-2 font-medium">
                  Qualitative Assessment
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.grade} className="border-b last:border-0">
                  <td className="px-3 py-2 font-semibold">{row.grade}</td>
                  <td className="px-3 py-2">{row.score}</td>
                  <td className="px-3 py-2">{row.points}</td>
                  <td className="px-3 py-2">{row.assessment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

function SemesterResultsView() {
  const [selectedSemester, setSelectedSemester] = useState("all")
  const [data, setData] = useState<SemesterResultsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    setError("")
    const response = await apiFetch<SemesterResultsResponse>(
      `/student/results/semester?semester=${encodeURIComponent(selectedSemester)}`
    )
    setData(response)
  }, [selectedSemester])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true)
      loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load semester results."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  async function handleDownload() {
    setDownloading(true)
    setError("")
    try {
      await downloadPdf(
        `/student/results/semester/pdf?semester=${encodeURIComponent(data?.selected_semester ?? selectedSemester)}`,
        "semester-results.pdf"
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to download result PDF."
      )
    } finally {
      setDownloading(false)
    }
  }

  return (
    <ResultsShell
      active="semester"
      title="Semester Results"
      description="Filter published completed-semester results, view all results together, and download the official result report."
    >
      <ErrorState error={error} />
      {loading ? <LoadingState /> : null}
      {data && !loading ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm font-medium">
              Semester
              <select
                className="h-10 min-w-60 rounded-lg border border-input bg-background px-3 text-sm"
                value={selectedSemester}
                onChange={(event) => setSelectedSemester(event.target.value)}
              >
                {data.semesters.map((semester) => (
                  <option key={semester.id} value={semester.id}>
                    {semester.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => void loadData()}>
                <RefreshCw className="size-4" />
                Refresh
              </Button>
              <Button
                onClick={() => void handleDownload()}
                disabled={!data.records.length || downloading}
              >
                {downloading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Download className="size-4" />
                )}
                PDF
              </Button>
            </div>
          </div>
          <SummaryCards
            summary={data.summary}
            publishedCount={data.records.length}
          />
          <ResultTable groups={data.groups} />
          <GradeScaleTable rows={data.grade_scale} />
        </>
      ) : null}
    </ResultsShell>
  )
}

function TranscriptView() {
  const [data, setData] = useState<TranscriptResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  async function loadData() {
    setError("")
    const response = await apiFetch<TranscriptResponse>(
      "/student/results/transcript"
    )
    setData(response)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load transcript."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  return (
    <ResultsShell
      active="transcript"
      title="Transcript"
      description="Review published academic records across all semesters with cumulative standing."
    >
      <ErrorState error={error} />
      {loading ? <LoadingState /> : null}
      {data && !loading ? (
        <>
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => void loadData()}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
          <SummaryCards
            summary={data.summary}
            publishedCount={data.records.length}
          />
          <ResultTable groups={data.groups} />
          <GradeScaleTable rows={data.grade_scale} />
        </>
      ) : null}
    </ResultsShell>
  )
}

function CourseWorksView() {
  const [data, setData] = useState<CourseworksResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  async function loadData() {
    setError("")
    const response = await apiFetch<CourseworksResponse>(
      "/student/results/course-works"
    )
    setData(response)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load course works."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const publishedCount = useMemo(
    () =>
      data?.courseworks.filter((row) => row.status === "Published").length ?? 0,
    [data]
  )

  return (
    <ResultsShell
      active="course-works"
      title="Course Works"
      description="View current-semester course work marks published before the final examination period."
    >
      <ErrorState error={error} />
      {loading ? <LoadingState /> : null}
      {data && !loading ? (
        <>
          <section className="grid gap-3 md:grid-cols-3">
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Semester</p>
                <p className="mt-1 font-semibold">
                  {data.semester?.label ?? "No active semester"}
                </p>
              </CardContent>
            </Card>
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Published Marks</p>
                <p className="mt-1 text-2xl font-semibold">{publishedCount}</p>
              </CardContent>
            </Card>
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Default Ratio</p>
                <p className="mt-1 font-semibold">
                  {data.default_coursework_weight}% /{" "}
                  {data.default_final_exam_weight}%
                </p>
              </CardContent>
            </Card>
          </section>
          <Card className="border-border/70 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <div>
                <CardTitle className="text-lg">
                  Current Semester Course Works
                </CardTitle>
                <CardDescription>
                  {data.courseworks.length} enrolled course
                  {data.courseworks.length === 1 ? "" : "s"}
                </CardDescription>
              </div>
              <Button variant="outline" onClick={() => void loadData()}>
                <RefreshCw className="size-4" />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {data.courseworks.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[880px] border-collapse text-sm">
                    <thead>
                      <tr className="border-b bg-muted/60 text-left">
                        <th className="px-3 py-2 font-medium">Course</th>
                        <th className="px-3 py-2 font-medium">Teacher</th>
                        <th className="px-3 py-2 text-center font-medium">
                          Course Work
                        </th>
                        <th className="px-3 py-2 text-center font-medium">
                          Ratio
                        </th>
                        <th className="px-3 py-2 font-medium">Final Exam</th>
                        <th className="px-3 py-2 font-medium">Status</th>
                        <th className="px-3 py-2 font-medium">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.courseworks.map((row) => (
                        <tr
                          key={row.offering_id}
                          className="border-b last:border-0"
                        >
                          <td className="px-3 py-2">
                            <p className="font-medium">{row.course_code}</p>
                            <p className="text-muted-foreground">
                              {row.course_title}
                            </p>
                          </td>
                          <td className="px-3 py-2">{row.teacher || "-"}</td>
                          <td className="px-3 py-2 text-center font-semibold">
                            {row.coursework_mark || "-"}
                          </td>
                          <td className="px-3 py-2 text-center">
                            {row.has_final_exam
                              ? `${row.coursework_weight}% / ${row.final_exam_weight}%`
                              : `${row.coursework_weight}% coursework`}
                          </td>
                          <td className="px-3 py-2">
                            {row.has_final_exam
                              ? formatDateTime(row.final_exam_starts_at)
                              : "No final exam"}
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              className={statusClassName(row.status)}
                              variant="outline"
                            >
                              {row.status}
                            </Badge>
                          </td>
                          <td className="px-3 py-2">{row.note || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState>
                  No current-semester course work marks are available yet.
                </EmptyState>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </ResultsShell>
  )
}

function ExamSlipView() {
  const [data, setData] = useState<ExamSlipResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState("")

  async function loadData() {
    setError("")
    const response = await apiFetch<ExamSlipResponse>(
      "/student/results/exam-slip"
    )
    setData(response)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load exam slip."
          )
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  async function handleDownload() {
    setDownloading(true)
    setError("")
    try {
      await downloadPdf("/student/results/exam-slip/pdf", "exam-slip.pdf")
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to download exam slip."
      )
    } finally {
      setDownloading(false)
    }
  }

  return (
    <ResultsShell
      active="exam-slip"
      title="Exam Slip"
      description="Download the final examination entry slip after the executive publishes the final exam schedule."
    >
      <ErrorState error={error} />
      {loading ? <LoadingState /> : null}
      {data && !loading ? (
        <>
          <section className="grid gap-3 md:grid-cols-3">
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Semester</p>
                <p className="mt-1 font-semibold">
                  {data.semester?.label ?? "No published schedule"}
                </p>
              </CardContent>
            </Card>
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Final Exams</p>
                <p className="mt-1 text-2xl font-semibold">
                  {data.exams.length}
                </p>
              </CardContent>
            </Card>
            <Card className="border-border/70 shadow-sm">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">
                  Total Credit Hours
                </p>
                <p className="mt-1 text-2xl font-semibold">
                  {data.total_credit_hours}
                </p>
              </CardContent>
            </Card>
          </section>
          <Card className="border-border/70 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <div>
                <CardTitle className="text-lg">
                  Final Examination Entry Slip
                </CardTitle>
                <CardDescription>
                  Generated {formatDateTime(data.generated_at)}
                </CardDescription>
              </div>
              <Button
                onClick={() => void handleDownload()}
                disabled={!data.can_download || downloading}
              >
                {downloading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Download className="size-4" />
                )}
                PDF
              </Button>
            </CardHeader>
            <CardContent>
              {data.exams.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[940px] border-collapse text-sm">
                    <thead>
                      <tr className="border-b bg-muted/60 text-left">
                        <th className="px-3 py-2 font-medium">No</th>
                        <th className="px-3 py-2 font-medium">Course</th>
                        <th className="px-3 py-2 text-center font-medium">
                          Unit
                        </th>
                        <th className="px-3 py-2 font-medium">Exam Date</th>
                        <th className="px-3 py-2 font-medium">Time</th>
                        <th className="px-3 py-2 font-medium">Exam Venue</th>
                        <th className="px-3 py-2 font-medium">Note</th>
                        <th className="px-3 py-2 text-center font-medium">
                          Table No
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.exams.map((row) => (
                        <tr
                          key={`${row.course_code}-${row.exam_date}`}
                          className="border-b last:border-0"
                        >
                          <td className="px-3 py-2">{row.no}</td>
                          <td className="px-3 py-2">
                            <p className="font-medium">{row.course_code}</p>
                            <p className="text-muted-foreground">
                              {row.course_title}
                            </p>
                          </td>
                          <td className="px-3 py-2 text-center">
                            {row.credit_hours}
                          </td>
                          <td className="px-3 py-2">{row.exam_date}</td>
                          <td className="px-3 py-2">{row.time}</td>
                          <td className="px-3 py-2">{row.venue}</td>
                          <td className="px-3 py-2">{row.note || "-"}</td>
                          <td className="px-3 py-2 text-center">
                            {row.table_no || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState>
                  No published final examination schedule is available for your
                  current enrollments.
                </EmptyState>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </ResultsShell>
  )
}

export function StudentResultsPage({ view }: { view: ResultsView }) {
  if (view === "transcript") return <TranscriptView />
  if (view === "course-works") return <CourseWorksView />
  if (view === "exam-slip") return <ExamSlipView />
  return <SemesterResultsView />
}

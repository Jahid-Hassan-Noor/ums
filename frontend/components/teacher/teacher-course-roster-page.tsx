"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { Download, Loader2, RefreshCw, Search, Users } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { formatDateTime } from "@/components/utils/format"
import { apiFetch } from "@/lib/auth"
import { triggerBlobDownload } from "@/lib/fetch-utils"

type RosterStudent = {
  profile_id: number
  name: string
  username: string
  email: string
  student_number: string
  tutorial_group: string
  lab_group: string
  enrolled_at: string
  attended: number
  total_classes: number
  attendance_percentage: number
}

type RosterResponse = {
  course: {
    id: number
    code: string
    title: string
    section: string
    semester: string
  }
  summary: {
    students: number
    tutorial_groups: number
    lab_groups: number
    attendance_sessions: number
  }
  students: RosterStudent[]
}

function csvCell(value: unknown) {
  const text = String(value ?? "")
  if (!/[",\n]/.test(text)) return text
  return `"${text.replace(/"/g, '""')}"`
}

function downloadRoster(data: RosterResponse, students: RosterStudent[]) {
  const rows = [
    [
      "student_number",
      "name",
      "username",
      "email",
      "tutorial_group",
      "lab_group",
      "attended",
      "total_classes",
      "attendance_percentage",
      "enrolled_at",
    ],
    ...students.map((student) => [
      student.student_number,
      student.name,
      student.username,
      student.email,
      student.tutorial_group,
      student.lab_group,
      student.attended,
      student.total_classes,
      student.attendance_percentage,
      student.enrolled_at,
    ]),
  ]
  const csv = rows.map((row) => row.map(csvCell).join(",")).join("\n")
  triggerBlobDownload(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
    `${data.course.code}-${data.course.section || "all"}-roster.csv`
  )
}

export function TeacherCourseRosterPage({ courseId }: { courseId: string }) {
  const [data, setData] = useState<RosterResponse | null>(null)
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadRoster = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      setData(
        await apiFetch<RosterResponse>(
          `/teacher/courses/${encodeURIComponent(courseId)}/roster`
        )
      )
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load the course roster."
      )
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadRoster(), 0)
    return () => window.clearTimeout(timer)
  }, [loadRoster])

  const filteredStudents = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return data?.students ?? []
    return (data?.students ?? []).filter((student) =>
      [
        student.name,
        student.student_number,
        student.username,
        student.email,
        student.tutorial_group,
        student.lab_group,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [data?.students, query])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/courses", title: "Courses" },
          {
            href: `/teacher/courses/${courseId}`,
            title: data?.course.code ?? "Course",
          },
          { href: `/teacher/courses/${courseId}/roster`, title: "Roster" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-10 pt-5 sm:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Assigned teaching scope</p>
            <h1 className="text-2xl font-semibold tracking-tight">Course Roster</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {data
                ? `${data.course.code} · ${data.course.title} · ${data.course.semester}${
                    data.course.section ? ` · Section ${data.course.section}` : ""
                  }`
                : "Review enrolled students, teaching groups, and attendance progress."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" render={<Link href={`/teacher/courses/${courseId}`} />}>
              Course workspace
            </Button>
            <Button
              variant="outline"
              disabled={loading}
              onClick={() => void loadRoster()}
            >
              {loading ? <Loader2 className="animate-spin" /> : <RefreshCw />}
              Refresh
            </Button>
            <Button
              disabled={!data || !filteredStudents.length}
              onClick={() => data && downloadRoster(data, filteredStudents)}
            >
              <Download />
              Export CSV
            </Button>
          </div>
        </div>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {data ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ["Enrolled students", data.summary.students],
              ["Tutorial groups", data.summary.tutorial_groups],
              ["Lab groups", data.summary.lab_groups],
              ["Attendance sessions", data.summary.attendance_sessions],
            ].map(([label, value]) => (
              <Card key={label}>
                <CardHeader className="pb-2">
                  <CardDescription>{label}</CardDescription>
                  <CardTitle className="text-2xl">{value}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : null}

        <Card>
          <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="size-5" />
                Enrolled Students
              </CardTitle>
              <CardDescription>
                {data
                  ? `${filteredStudents.length} of ${data.students.length} students shown.`
                  : "Loading the current roster."}
              </CardDescription>
            </div>
            <div className="relative w-full md:max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search name, ID, email, or group"
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent>
            {loading && !data ? (
              <div className="flex min-h-40 items-center justify-center text-muted-foreground">
                <Loader2 className="mr-2 size-5 animate-spin" />
                Loading roster...
              </div>
            ) : !filteredStudents.length ? (
              <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                {query
                  ? "No enrolled students match this search."
                  : "No active enrollments were found for this course offering."}
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[920px] text-sm">
                  <thead>
                    <tr className="border-b bg-muted/60 text-left text-muted-foreground">
                      <th className="px-3 py-3 font-medium">Student</th>
                      <th className="px-3 py-3 font-medium">Student ID</th>
                      <th className="px-3 py-3 font-medium">Tutorial</th>
                      <th className="px-3 py-3 font-medium">Lab</th>
                      <th className="px-3 py-3 font-medium">Attendance</th>
                      <th className="px-3 py-3 font-medium">Enrolled</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStudents.map((student) => (
                      <tr key={student.profile_id} className="border-b last:border-0">
                        <td className="px-3 py-4">
                          <p className="font-medium">{student.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {student.email || student.username}
                          </p>
                        </td>
                        <td className="px-3 py-4">{student.student_number || "—"}</td>
                        <td className="px-3 py-4">{student.tutorial_group || "—"}</td>
                        <td className="px-3 py-4">{student.lab_group || "—"}</td>
                        <td className="px-3 py-4">
                          <p
                            className={
                              student.total_classes && student.attendance_percentage < 80
                                ? "font-semibold text-red-600"
                                : "font-semibold text-emerald-700"
                            }
                          >
                            {student.attendance_percentage}%
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {student.attended}/{student.total_classes} sessions
                          </p>
                        </td>
                        <td className="px-3 py-4">
                          {formatDateTime(student.enrolled_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

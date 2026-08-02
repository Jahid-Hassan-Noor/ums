"use client"

import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Download,
  GraduationCap,
  Loader2,
  RefreshCw,
} from "lucide-react"

import { DataTableToolbar } from "@/components/ui/data-table-controls"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useTableState } from "@/hooks/use-table-state"
import { apiFetch } from "@/lib/auth"
import {
  downloadBlob,
  fetchAdminDirectoryExport,
  type AdminDirectoryOption,
} from "@/lib/admin-directory"

type AdminStudent = {
  id: number
  username: string
  name: string
  email: string
  student_id: string
  phone: string
  country: string
  nationality: string
  intake_id: number | null
  intake: string
  session: string
  session_values: string[]
  school: number | null
  school_code: string
  school_name: string
  program: number | null
  program_code: string
  program_name: string
  admission_number: string
  enrollment_status: string
  status: string
  status_label: string
  room: string
  current_year: number | null
  is_active: boolean
}

type StudentsResponse = {
  summary: {
    total: number
    active: number
    filtered: number
  }
  filters: {
    countries: AdminDirectoryOption[]
    intakes: AdminDirectoryOption[]
    sessions: AdminDirectoryOption[]
    statuses: AdminDirectoryOption[]
    schools: AdminDirectoryOption[]
    programs: AdminDirectoryOption[]
  }
  students: AdminStudent[]
}

const emptyFilters = {
  q: "",
  country: "",
  intake: "",
  session: "",
  status: "",
  school: "",
  program: "",
  sort: "asc",
}

type StudentFilters = typeof emptyFilters

function studentSearchText(student: AdminStudent) {
  return [
    student.name,
    student.username,
    student.email,
    student.student_id,
    student.country,
    student.nationality,
    student.intake,
    student.session,
    student.status_label,
    student.enrollment_status,
    student.school_name,
    student.school_code,
    student.program_name,
    student.program_code,
  ]
    .join(" ")
    .toLowerCase()
}

function matchesFilters(student: AdminStudent, filters: StudentFilters) {
  const query = filters.q.trim().toLowerCase()
  if (query && !studentSearchText(student).includes(query)) return false
  if (
    filters.country &&
    student.country !== filters.country &&
    student.nationality !== filters.country
  ) {
    return false
  }
  if (filters.intake && String(student.intake_id ?? "") !== filters.intake)
    return false
  if (filters.session && !student.session_values.includes(filters.session))
    return false
  if (filters.status && student.status !== filters.status) return false
  if (filters.school && String(student.school ?? "") !== filters.school)
    return false
  if (filters.program && String(student.program ?? "") !== filters.program)
    return false
  return true
}

function statusLabel(student: AdminStudent) {
  if (student.status === "dropout" || student.status === "graduated") {
    return student.status_label
  }
  if (!student.is_active) return "Inactive"
  return student.status_label || student.enrollment_status || "Active"
}

export function AdminManageStudentsPage() {
  const router = useRouter()
  const [students, setStudents] = useState<AdminStudent[]>([])
  const [options, setOptions] = useState<StudentsResponse["filters"]>({
    countries: [],
    intakes: [],
    sessions: [],
    statuses: [],
    schools: [],
    programs: [],
  })
  const [summary, setSummary] = useState<StudentsResponse["summary"]>({
    total: 0,
    active: 0,
    filtered: 0,
  })
  const {
    filters,
    updateFilter: updateTableFilter,
    resetFilters,
  } = useTableState<StudentFilters>({ initialFilters: emptyFilters })
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState<"all" | "filtered" | null>(
    null
  )
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    setIsLoading(true)
    setError("")
    try {
      const data = await apiFetch<StudentsResponse>("/admin/manage/students")
      setStudents(data.students ?? [])
      setOptions(
        data.filters ?? {
          countries: [],
          intakes: [],
          sessions: [],
          statuses: [],
          schools: [],
          programs: [],
        }
      )
      setSummary(
        data.summary ?? {
          total: data.students?.length ?? 0,
          active:
            data.students?.filter((student) => student.is_active).length ?? 0,
          filtered: data.students?.length ?? 0,
        }
      )
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load students."
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const filteredStudents = useMemo(() => {
    const sorted = students
      .filter((student) => matchesFilters(student, filters))
      .sort((a, b) => {
        const result = a.name.localeCompare(b.name, undefined, {
          sensitivity: "base",
        })
        return filters.sort === "desc" ? -result : result
      })
    return sorted
  }, [students, filters])

  function updateFilter(field: keyof StudentFilters, value: string) {
    updateTableFilter(field, value)
  }

  async function exportStudents(kind: "all" | "filtered") {
    setIsExporting(kind)
    setError("")
    setSuccess("")
    try {
      const exportFilters =
        kind === "filtered" ? filters : { sort: filters.sort }
      const { blob, filename } = await fetchAdminDirectoryExport(
        "students",
        exportFilters
      )
      downloadBlob(blob, filename)
      setSuccess(
        kind === "filtered"
          ? "Filtered students exported."
          : "All students exported."
      )
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to export students."
      )
    } finally {
      setIsExporting(null)
    }
  }

  const hasFilters = Object.entries(filters).some(
    ([key, value]) => key !== "sort" && value.trim()
  )

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/students", title: "Students" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Manage Students
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              View student accounts, filter by academic profile, and export
              matching records.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => void loadData()}
              disabled={isLoading}
            >
              <RefreshCw
                className={`size-4 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <Button
              variant="outline"
              onClick={() => void exportStudents("filtered")}
              disabled={isExporting !== null}
            >
              {isExporting === "filtered" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Download className="size-4" />
              )}
              Export Filtered
            </Button>
            <Button
              onClick={() => void exportStudents("all")}
              disabled={isExporting !== null}
            >
              {isExporting === "all" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Download className="size-4" />
              )}
              Export All
            </Button>
          </div>
        </section>

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

        <section className="grid gap-4 sm:grid-cols-3">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Total Students</CardDescription>
              <CardTitle className="text-2xl">{summary.total}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Active Accounts</CardDescription>
              <CardTitle className="text-2xl">{summary.active}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Showing</CardDescription>
              <CardTitle className="text-2xl">
                {filteredStudents.length}
              </CardTitle>
            </CardHeader>
          </Card>
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <DataTableToolbar
            title="Student Directory"
            description={`${filteredStudents.length} of ${students.length} student records`}
            search={{
              id: "student-search",
              value: filters.q,
              onChange: (value) => updateFilter("q", value),
              placeholder: "Name, ID, email",
            }}
            filters={[
              {
                id: "student-country",
                label: "Country",
                value: filters.country,
                onChange: (value) => updateFilter("country", value),
                allLabel: "All countries",
                options: options.countries,
              },
              {
                id: "student-intake",
                label: "Intake",
                value: filters.intake,
                onChange: (value) => updateFilter("intake", value),
                allLabel: "All intakes",
                options: options.intakes,
              },
              {
                id: "student-session",
                label: "Session",
                value: filters.session,
                onChange: (value) => updateFilter("session", value),
                allLabel: "All sessions",
                options: options.sessions,
              },
              {
                id: "student-status",
                label: "Status",
                value: filters.status,
                onChange: (value) => updateFilter("status", value),
                allLabel: "All statuses",
                options: options.statuses,
              },
              {
                id: "student-school",
                label: "School",
                value: filters.school,
                onChange: (value) => updateFilter("school", value),
                allLabel: "All schools",
                options: options.schools,
              },
              {
                id: "student-program",
                label: "Program",
                value: filters.program,
                onChange: (value) => updateFilter("program", value),
                allLabel: "All programs",
                options: options.programs,
              },
            ]}
            sort={{
              id: "student-sort",
              label: "Order",
              value: filters.sort,
              onChange: (value) => updateFilter("sort", value),
              allLabel: "",
              options: [
                { value: "asc", label: "A to Z" },
                { value: "desc", label: "Z to A" },
              ],
            }}
            hasFilters={hasFilters}
            onClear={resetFilters}
            gridClassName="md:grid-cols-2 xl:grid-cols-9"
          >
            {isLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="size-8 animate-spin text-muted-foreground" />
              </div>
            ) : filteredStudents.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No students match the selected filters.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-border bg-background">
                <table className="w-full min-w-[980px] text-sm">
                  <thead className="bg-muted/60 text-left text-xs text-muted-foreground uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium">Student</th>
                      <th className="px-4 py-3 font-medium">Country</th>
                      <th className="px-4 py-3 font-medium">Intake</th>
                      <th className="px-4 py-3 font-medium">Session</th>
                      <th className="px-4 py-3 font-medium">School</th>
                      <th className="px-4 py-3 font-medium">Program</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredStudents.map((student) => (
                      <tr
                        key={student.id}
                        className="cursor-pointer align-top transition-colors hover:bg-muted/40"
                        tabIndex={0}
                        onClick={() =>
                          router.push(`/admin/manage/students/${student.id}`)
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault()
                            router.push(`/admin/manage/students/${student.id}`)
                          }
                        }}
                      >
                        <td className="px-4 py-3">
                          <div className="flex gap-3">
                            <span className="mt-0.5 rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                              <GraduationCap className="size-4" />
                            </span>
                            <div className="min-w-0">
                              <p className="font-medium text-foreground">
                                {student.name}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {student.student_id || student.username}
                              </p>
                              <p className="truncate text-xs text-muted-foreground">
                                {student.email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {student.country || student.nationality || "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {student.intake || "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {student.session || "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {student.school_name ||
                            student.school_code ||
                            "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {student.program_name ||
                            student.program_code ||
                            "Not set"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${
                              student.is_active
                                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                : "border-amber-200 bg-amber-50 text-amber-800"
                            }`}
                          >
                            {statusLabel(student)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </DataTableToolbar>
        </Card>
      </main>
    </div>
  )
}

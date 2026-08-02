"use client"

import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Download,
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

type AdminTeacher = {
  id: number
  username: string
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  school: number | null
  school_code: string
  school_name: string
  center: number | null
  center_code: string
  center_name: string
  unit: number | null
  unit_code: string
  unit_name: string
  department: number | null
  department_code: string
  department_name: string
  academic_rank: string
  specialization: string
  office_location: string
  is_active: boolean
}

type TeachersResponse = {
  summary: {
    total: number
    active: number
    filtered: number
  }
  filters: {
    schools: AdminDirectoryOption[]
    centers: AdminDirectoryOption[]
    units: AdminDirectoryOption[]
    departments: AdminDirectoryOption[]
    designations: AdminDirectoryOption[]
  }
  teachers: AdminTeacher[]
}

const emptyFilters = {
  q: "",
  school: "",
  center: "",
  unit: "",
  department: "",
  designation: "",
  sort: "asc",
}

type TeacherFilters = typeof emptyFilters

function teacherSearchText(teacher: AdminTeacher) {
  return [
    teacher.name,
    teacher.username,
    teacher.email,
    teacher.staff_id,
    teacher.designation,
    teacher.school_name,
    teacher.school_code,
    teacher.center_name,
    teacher.center_code,
    teacher.unit_name,
    teacher.unit_code,
    teacher.department_name,
    teacher.department_code,
    teacher.academic_rank,
    teacher.specialization,
  ]
    .join(" ")
    .toLowerCase()
}

function matchesFilters(teacher: AdminTeacher, filters: TeacherFilters) {
  const query = filters.q.trim().toLowerCase()
  if (query && !teacherSearchText(teacher).includes(query)) return false
  if (filters.school && String(teacher.school ?? "") !== filters.school)
    return false
  if (filters.center && String(teacher.center ?? "") !== filters.center)
    return false
  if (filters.unit && String(teacher.unit ?? "") !== filters.unit) return false
  if (
    filters.department &&
    String(teacher.department ?? "") !== filters.department
  )
    return false
  if (filters.designation && teacher.designation !== filters.designation)
    return false
  return true
}

function scopeLabel(teacher: AdminTeacher) {
  return [
    teacher.school_name || teacher.center_name,
    teacher.department_name,
    teacher.unit_name,
  ]
    .filter(Boolean)
    .join(" / ")
}

export function AdminManageTeachersPage() {
  const router = useRouter()
  const [teachers, setTeachers] = useState<AdminTeacher[]>([])
  const [options, setOptions] = useState<TeachersResponse["filters"]>({
    schools: [],
    centers: [],
    units: [],
    departments: [],
    designations: [],
  })
  const [summary, setSummary] = useState<TeachersResponse["summary"]>({
    total: 0,
    active: 0,
    filtered: 0,
  })
  const {
    filters,
    updateFilter: updateTableFilter,
    resetFilters,
  } = useTableState<TeacherFilters>({ initialFilters: emptyFilters })
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
      const data = await apiFetch<TeachersResponse>("/admin/manage/teachers")
      setTeachers(data.teachers ?? [])
      setOptions(
        data.filters ?? {
          schools: [],
          centers: [],
          units: [],
          departments: [],
          designations: [],
        }
      )
      setSummary(
        data.summary ?? {
          total: data.teachers?.length ?? 0,
          active:
            data.teachers?.filter((teacher) => teacher.is_active).length ?? 0,
          filtered: data.teachers?.length ?? 0,
        }
      )
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load teachers."
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

  const filteredTeachers = useMemo(() => {
    return teachers
      .filter((teacher) => matchesFilters(teacher, filters))
      .sort((a, b) => {
        const result = a.name.localeCompare(b.name, undefined, {
          sensitivity: "base",
        })
        return filters.sort === "desc" ? -result : result
      })
  }, [teachers, filters])

  function updateFilter(field: keyof TeacherFilters, value: string) {
    updateTableFilter(field, value)
  }

  async function exportTeachers(kind: "all" | "filtered") {
    setIsExporting(kind)
    setError("")
    setSuccess("")
    try {
      const exportFilters =
        kind === "filtered" ? filters : { sort: filters.sort }
      const { blob, filename } = await fetchAdminDirectoryExport(
        "teachers",
        exportFilters
      )
      downloadBlob(blob, filename)
      setSuccess(
        kind === "filtered"
          ? "Filtered teachers exported."
          : "All teachers exported."
      )
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to export teachers."
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
          { href: "/admin/manage/teachers", title: "Teachers" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Manage Teachers
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              View teacher accounts, filter by organisation placement and
              designation, and export records.
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
              onClick={() => void exportTeachers("filtered")}
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
              onClick={() => void exportTeachers("all")}
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
              <CardDescription>Total Teachers</CardDescription>
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
                {filteredTeachers.length}
              </CardTitle>
            </CardHeader>
          </Card>
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <DataTableToolbar
            title="Teacher Directory"
            description={`${filteredTeachers.length} of ${teachers.length} teacher records`}
            search={{
              id: "teacher-search",
              value: filters.q,
              onChange: (value) => updateFilter("q", value),
              placeholder: "Name, staff ID, email",
            }}
            filters={[
              {
                id: "teacher-school",
                label: "School",
                value: filters.school,
                onChange: (value) => updateFilter("school", value),
                allLabel: "All schools",
                options: options.schools,
              },
              {
                id: "teacher-center",
                label: "Centre",
                value: filters.center,
                onChange: (value) => updateFilter("center", value),
                allLabel: "All centres",
                options: options.centers,
              },
              {
                id: "teacher-unit",
                label: "Unit",
                value: filters.unit,
                onChange: (value) => updateFilter("unit", value),
                allLabel: "All units",
                options: options.units,
              },
              {
                id: "teacher-department",
                label: "Department",
                value: filters.department,
                onChange: (value) => updateFilter("department", value),
                allLabel: "All departments",
                options: options.departments,
              },
              {
                id: "teacher-designation",
                label: "Designation",
                value: filters.designation,
                onChange: (value) => updateFilter("designation", value),
                allLabel: "All designations",
                options: options.designations,
              },
            ]}
            sort={{
              id: "teacher-sort",
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
          >
            {isLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="size-8 animate-spin text-muted-foreground" />
              </div>
            ) : filteredTeachers.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No teachers match the selected filters.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-border bg-background">
                <table className="w-full min-w-[980px] text-sm">
                  <thead className="bg-muted/60 text-left text-xs text-muted-foreground uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium">Teacher</th>
                      <th className="px-4 py-3 font-medium">Designation</th>
                      <th className="px-4 py-3 font-medium">Scope</th>
                      <th className="px-4 py-3 font-medium">Specialization</th>
                      <th className="px-4 py-3 font-medium">Office</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredTeachers.map((teacher) => (
                      <tr
                        key={teacher.id}
                        className="cursor-pointer align-top transition-colors hover:bg-muted/40"
                        tabIndex={0}
                        onClick={() =>
                          router.push(`/admin/manage/teachers/${teacher.id}`)
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault()
                            router.push(`/admin/manage/teachers/${teacher.id}`)
                          }
                        }}
                      >
                        <td className="px-4 py-3">
                          <div className="flex gap-3">
                            <span className="mt-0.5 rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                              <BookOpen className="size-4" />
                            </span>
                            <div className="min-w-0">
                              <p className="font-medium text-foreground">
                                {teacher.name}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {teacher.staff_id || teacher.username}
                              </p>
                              <p className="truncate text-xs text-muted-foreground">
                                {teacher.email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {teacher.designation ||
                            teacher.academic_rank ||
                            "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {scopeLabel(teacher) || "Unassigned"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {teacher.specialization || "Not set"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {teacher.office_location || "Not set"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-md border px-2 py-0.5 text-xs font-medium ${
                              teacher.is_active
                                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                : "border-amber-200 bg-amber-50 text-amber-800"
                            }`}
                          >
                            {teacher.is_active ? "Active" : "Inactive"}
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

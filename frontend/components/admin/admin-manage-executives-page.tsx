"use client"

import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Download,
  Edit3,
  Loader2,
  RefreshCw,
  Save,
  Users,
  X,
} from "lucide-react"

import { DataTableToolbar } from "@/components/ui/data-table-controls"
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
import { Label } from "@/components/ui/label"
import { useTableState } from "@/hooks/use-table-state"
import { apiFetch } from "@/lib/auth"
import {
  downloadBlob,
  fetchAdminDirectoryExport,
  type AdminDirectoryOption,
} from "@/lib/admin-directory"

type AcademicUnit = {
  id: number
  code: string
  name: string
  school?: number | null
  center?: number | null
}

type Executive = {
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
  office_location: string
  responsibility_area: string
  is_active: boolean
}

type ExecutivesResponse = {
  summary?: {
    total: number
    active: number
    filtered: number
  }
  executives: Executive[]
  schools: AcademicUnit[]
  centers: AcademicUnit[]
  units: AcademicUnit[]
  departments?: AcademicUnit[]
  filters?: {
    schools: AdminDirectoryOption[]
    centers: AdminDirectoryOption[]
    units: AdminDirectoryOption[]
    departments: AdminDirectoryOption[]
    designations: AdminDirectoryOption[]
  }
}

type AssignmentForm = {
  assignment_type: "" | "school" | "center"
  school_id: string
  center_id: string
  unit_id: string
  staff_id: string
  designation: string
  phone: string
  is_active: boolean
}

const emptyForm: AssignmentForm = {
  assignment_type: "",
  school_id: "",
  center_id: "",
  unit_id: "",
  staff_id: "",
  designation: "",
  phone: "",
  is_active: true,
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

type ExecutiveFilters = typeof emptyFilters

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

function formFromExecutive(executive: Executive): AssignmentForm {
  return {
    assignment_type: executive.school
      ? "school"
      : executive.center
        ? "center"
        : "",
    school_id: executive.school ? String(executive.school) : "",
    center_id: executive.center ? String(executive.center) : "",
    unit_id: executive.unit ? String(executive.unit) : "",
    staff_id: executive.staff_id ?? "",
    designation: executive.designation ?? "",
    phone: executive.phone ?? "",
    is_active: executive.is_active,
  }
}

function executiveSearchText(executive: Executive) {
  return [
    executive.name,
    executive.username,
    executive.email,
    executive.staff_id,
    executive.designation,
    executive.school_name,
    executive.school_code,
    executive.center_name,
    executive.center_code,
    executive.unit_name,
    executive.unit_code,
    executive.department_name,
    executive.department_code,
    executive.responsibility_area,
  ]
    .join(" ")
    .toLowerCase()
}

function matchesFilters(executive: Executive, filters: ExecutiveFilters) {
  const query = filters.q.trim().toLowerCase()
  if (query && !executiveSearchText(executive).includes(query)) return false
  if (filters.school && String(executive.school ?? "") !== filters.school)
    return false
  if (filters.center && String(executive.center ?? "") !== filters.center)
    return false
  if (filters.unit && String(executive.unit ?? "") !== filters.unit)
    return false
  if (
    filters.department &&
    String(executive.department ?? "") !== filters.department
  )
    return false
  if (filters.designation && executive.designation !== filters.designation)
    return false
  return true
}

function scopeLabel(executive: Executive) {
  return [
    executive.school_name || executive.center_name,
    executive.department_name,
    executive.unit_name,
  ]
    .filter(Boolean)
    .join(" / ")
}

export function AdminManageExecutivesPage() {
  const router = useRouter()
  const [executives, setExecutives] = useState<Executive[]>([])
  const [schools, setSchools] = useState<AcademicUnit[]>([])
  const [centers, setCenters] = useState<AcademicUnit[]>([])
  const [units, setUnits] = useState<AcademicUnit[]>([])
  const [directoryFilters, setDirectoryFilters] = useState<
    NonNullable<ExecutivesResponse["filters"]>
  >({
    schools: [],
    centers: [],
    units: [],
    departments: [],
    designations: [],
  })
  const [summary, setSummary] = useState({
    total: 0,
    active: 0,
    filtered: 0,
  })
  const [editing, setEditing] = useState<Executive | null>(null)
  const [form, setForm] = useState<AssignmentForm>(emptyForm)
  const {
    filters,
    updateFilter: updateTableFilter,
    resetFilters,
  } = useTableState<ExecutiveFilters>({ initialFilters: emptyFilters })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isExporting, setIsExporting] = useState<"all" | "filtered" | null>(
    null
  )
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    setError("")
    const data = await apiFetch<ExecutivesResponse>("/admin/manage/executives")
    setExecutives(data.executives ?? [])
    setSchools(data.schools ?? [])
    setCenters(data.centers ?? [])
    setUnits(data.units ?? [])
    setDirectoryFilters(
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
        total: data.executives?.length ?? 0,
        active:
          data.executives?.filter((executive) => executive.is_active).length ??
          0,
        filtered: data.executives?.length ?? 0,
      }
    )
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) =>
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load executives."
          )
        )
        .finally(() => setIsLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const filteredExecutives = useMemo(() => {
    return executives
      .filter((executive) => matchesFilters(executive, filters))
      .sort((a, b) => {
        const result = a.name.localeCompare(b.name, undefined, {
          sensitivity: "base",
        })
        return filters.sort === "desc" ? -result : result
      })
  }, [executives, filters])

  function updateField(field: keyof AssignmentForm, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function updateFilter(field: keyof ExecutiveFilters, value: string) {
    updateTableFilter(field, value)
  }

  function startEdit(executive: Executive) {
    setEditing(executive)
    setForm(formFromExecutive(executive))
    setError("")
    setSuccess("")
  }

  function resetForm() {
    setEditing(null)
    setForm(emptyForm)
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editing) return
    setError("")
    setSuccess("")
    setIsSaving(true)

    try {
      await apiFetch(`/admin/manage/executives?profile_id=${editing.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          school_id:
            form.assignment_type === "school" ? Number(form.school_id) : null,
          center_id:
            form.assignment_type === "center" ? Number(form.center_id) : null,
          unit_id: form.unit_id ? Number(form.unit_id) : null,
          staff_id: form.staff_id,
          designation: form.designation,
          phone: form.phone,
          is_active: form.is_active,
        }),
      })
      setSuccess("Executive assignment updated successfully.")
      await loadData()
      resetForm()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to update executive."
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function exportExecutives(kind: "all" | "filtered") {
    setIsExporting(kind)
    setError("")
    setSuccess("")
    try {
      const exportFilters =
        kind === "filtered" ? filters : { sort: filters.sort }
      const { blob, filename } = await fetchAdminDirectoryExport(
        "executives",
        exportFilters
      )
      downloadBlob(blob, filename)
      setSuccess(
        kind === "filtered"
          ? "Filtered executives exported."
          : "All executives exported."
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to export executives."
      )
    } finally {
      setIsExporting(null)
    }
  }

  const scopedUnits = units.filter((unit) =>
    form.assignment_type === "school"
      ? String(unit.school ?? "") === form.school_id
      : form.assignment_type === "center"
        ? String(unit.center ?? "") === form.center_id
        : false
  )

  const hasFilters = Object.entries(filters).some(
    ([key, value]) => key !== "sort" && value.trim()
  )

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/executives", title: "Executives" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Manage Executives
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              View executive accounts, filter organisation assignments, export
              records, and update assignments.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setIsLoading(true)
                loadData()
                  .catch((caught) =>
                    setError(
                      caught instanceof Error
                        ? caught.message
                        : "Unable to load executives."
                    )
                  )
                  .finally(() => setIsLoading(false))
              }}
              disabled={isLoading}
            >
              <RefreshCw
                className={`size-4 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <Button
              variant="outline"
              onClick={() => void exportExecutives("filtered")}
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
              onClick={() => void exportExecutives("all")}
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
              <CardDescription>Total Executives</CardDescription>
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
                {filteredExecutives.length}
              </CardTitle>
            </CardHeader>
          </Card>
        </section>

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <DataTableToolbar
                title="Executive Accounts"
                description={`${filteredExecutives.length} of ${executives.length} executive records`}
                search={{
                  id: "executive-search",
                  value: filters.q,
                  onChange: (value) => updateFilter("q", value),
                  placeholder: "Name, staff ID, email",
                }}
                filters={[
                  {
                    id: "executive-school",
                    label: "School",
                    value: filters.school,
                    onChange: (value) => updateFilter("school", value),
                    allLabel: "All schools",
                    options: directoryFilters.schools,
                  },
                  {
                    id: "executive-center",
                    label: "Centre",
                    value: filters.center,
                    onChange: (value) => updateFilter("center", value),
                    allLabel: "All centres",
                    options: directoryFilters.centers,
                  },
                  {
                    id: "executive-unit",
                    label: "Unit",
                    value: filters.unit,
                    onChange: (value) => updateFilter("unit", value),
                    allLabel: "All units",
                    options: directoryFilters.units,
                  },
                  {
                    id: "executive-department",
                    label: "Department",
                    value: filters.department,
                    onChange: (value) => updateFilter("department", value),
                    allLabel: "All departments",
                    options: directoryFilters.departments,
                  },
                  {
                    id: "executive-designation",
                    label: "Designation",
                    value: filters.designation,
                    onChange: (value) => updateFilter("designation", value),
                    allLabel: "All designations",
                    options: directoryFilters.designations,
                  },
                ]}
                sort={{
                  id: "executive-sort",
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
                gridClassName="md:grid-cols-2 xl:grid-cols-7"
              >
                {filteredExecutives.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                    No executives match the selected filters.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredExecutives.map((executive) => (
                      <div
                        key={executive.id}
                        className="cursor-pointer rounded-lg border border-border bg-background p-4 transition-colors hover:bg-muted/40"
                        tabIndex={0}
                        onClick={() =>
                          router.push(
                            `/admin/manage/executives/${executive.id}`
                          )
                        }
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault()
                            router.push(
                              `/admin/manage/executives/${executive.id}`
                            )
                          }
                        }}
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="font-semibold">{executive.name}</p>
                              <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                                {executive.staff_id || executive.username}
                              </span>
                              {!executive.is_active ? (
                                <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
                                  Inactive
                                </span>
                              ) : null}
                            </div>
                            <p className="mt-2 text-sm text-muted-foreground">
                              {executive.designation || "Executive"}
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {scopeLabel(executive) || "Unassigned"}
                            </p>
                            {executive.email ? (
                              <p className="mt-1 text-xs text-muted-foreground">
                                {executive.email}
                              </p>
                            ) : null}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(event) => {
                              event.stopPropagation()
                              startEdit(executive)
                            }}
                          >
                            <Edit3 className="size-4" />
                            Edit
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </DataTableToolbar>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <Users className="size-5" />
                  </span>
                  <div>
                    <CardTitle className="text-lg">
                      {editing ? "Edit Assignment" : "Select Executive"}
                    </CardTitle>
                    <CardDescription>
                      {editing
                        ? editing.name
                        : "Choose an executive from the list."}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              {editing ? (
                <form onSubmit={handleSubmit}>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="assignment_type">
                        Assigned Unit Type
                      </Label>
                      <select
                        id="assignment_type"
                        value={form.assignment_type}
                        onChange={(event) => {
                          const value = event.target
                            .value as AssignmentForm["assignment_type"]
                          setForm((current) => ({
                            ...current,
                            assignment_type: value,
                            school_id:
                              value === "school" ? current.school_id : "",
                            center_id:
                              value === "center" ? current.center_id : "",
                            unit_id: "",
                          }))
                        }}
                        className={selectClass}
                        required
                      >
                        <option value="">Select assignment</option>
                        <option value="school">School</option>
                        <option value="center">Centre</option>
                      </select>
                    </div>
                    {form.assignment_type === "school" ? (
                      <div className="space-y-2">
                        <Label htmlFor="school_id">School</Label>
                        <select
                          id="school_id"
                          value={form.school_id}
                          onChange={(event) => {
                            updateField("school_id", event.target.value)
                            updateField("unit_id", "")
                          }}
                          className={selectClass}
                          required
                        >
                          <option value="">Select school</option>
                          {schools.map((school) => (
                            <option key={school.id} value={school.id}>
                              {school.code} - {school.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : null}
                    {form.assignment_type === "center" ? (
                      <div className="space-y-2">
                        <Label htmlFor="center_id">Centre</Label>
                        <select
                          id="center_id"
                          value={form.center_id}
                          onChange={(event) => {
                            updateField("center_id", event.target.value)
                            updateField("unit_id", "")
                          }}
                          className={selectClass}
                          required
                        >
                          <option value="">Select centre</option>
                          {centers.map((center) => (
                            <option key={center.id} value={center.id}>
                              {center.code} - {center.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : null}
                    <div className="space-y-2">
                      <Label htmlFor="unit_id">Administrative Unit</Label>
                      <select
                        id="unit_id"
                        value={form.unit_id}
                        onChange={(event) =>
                          updateField("unit_id", event.target.value)
                        }
                        className={selectClass}
                      >
                        <option value="">Direct assignment</option>
                        {scopedUnits.map((unit) => (
                          <option key={unit.id} value={unit.id}>
                            {unit.code} - {unit.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="staff_id">Staff ID</Label>
                      <Input
                        id="staff_id"
                        value={form.staff_id}
                        onChange={(event) =>
                          updateField("staff_id", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="designation">Designation</Label>
                      <Input
                        id="designation"
                        value={form.designation}
                        onChange={(event) =>
                          updateField("designation", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <Input
                        id="phone"
                        value={form.phone}
                        onChange={(event) =>
                          updateField("phone", event.target.value)
                        }
                      />
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(event) =>
                          updateField("is_active", event.target.checked)
                        }
                      />
                      Active
                    </label>
                  </CardContent>
                  <div className="flex justify-between gap-3 border-t p-4">
                    <Button type="button" variant="outline" onClick={resetForm}>
                      <X className="size-4" />
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isSaving}>
                      {isSaving ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Save className="size-4" />
                      )}
                      {isSaving ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </form>
              ) : null}
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}

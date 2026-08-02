"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  Archive,
  CheckCircle2,
  Edit3,
  Loader2,
  Search,
} from "lucide-react"

import { EntityEditorCard } from "@/components/admin/entity-editor-card"
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
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type DirectoryKind = "departments" | "units" | "programmes"

type AcademicUnit = {
  id: number
  code: string
  name: string
}

type Choice = {
  value: string
  label: string
}

type DirectoryRecord = {
  id: number
  code: string
  name?: string
  title?: string
  description?: string
  is_active: boolean
  school?: number | null
  center?: number | null
  department?: number | null
  unit_type?: string
  program_type?: string
  level?: string
  duration_years?: number | null
  school_detail?: AcademicUnit | null
  center_detail?: AcademicUnit | null
  department_detail?: AcademicUnit | null
  assigned_executives?: Array<{
    id: number
    name: string
    designation: string
  }>
}

type DirectoryResponse = {
  schools?: AcademicUnit[]
  centers?: AcademicUnit[]
  departments?: DirectoryRecord[]
  units?: DirectoryRecord[]
  programmes?: DirectoryRecord[]
  unit_types?: Choice[]
  program_types?: Choice[]
}

type FormState = {
  code: string
  name: string
  description: string
  school: string
  center: string
  department: string
  unit_type: string
  program_type: string
  level: string
  duration_years: string
  is_active: boolean
}

const config = {
  departments: {
    title: "Departments",
    description: "Manage departments and offices under a school or centre.",
    endpoint: "/admin/academics/departments",
    collectionKey: "departments",
    itemLabel: "Department",
  },
  units: {
    title: "Units",
    description:
      "Manage administrative units and the executives assigned to them.",
    endpoint: "/admin/academics/units",
    collectionKey: "units",
    itemLabel: "Unit",
  },
  programmes: {
    title: "Programmes",
    description:
      "Manage academic programmes and centre programmes shown on public pages.",
    endpoint: "/admin/academics/programmes",
    collectionKey: "programmes",
    itemLabel: "Programme",
  },
} as const

const emptyForm: FormState = {
  code: "",
  name: "",
  description: "",
  school: "",
  center: "",
  department: "",
  unit_type: "administrative",
  program_type: "academic",
  level: "",
  duration_years: "",
  is_active: true,
}

function formFromRecord(record: DirectoryRecord): FormState {
  return {
    code: record.code ?? "",
    name: record.name ?? record.title ?? "",
    description: record.description ?? "",
    school: record.school ? String(record.school) : "",
    center: record.center ? String(record.center) : "",
    department: record.department ? String(record.department) : "",
    unit_type: record.unit_type ?? "administrative",
    program_type: record.program_type ?? "academic",
    level: record.level ?? "",
    duration_years: record.duration_years ? String(record.duration_years) : "",
    is_active: record.is_active,
  }
}

function maybeNumber(value: string) {
  return value ? Number(value) : null
}

function parentLabel(record: DirectoryRecord) {
  if (record.school_detail) return `School: ${record.school_detail.code}`
  if (record.center_detail) return `Centre: ${record.center_detail.code}`
  return "Unassigned"
}

function departmentLabel(record: DirectoryRecord) {
  if (!record.department_detail) return ""
  return `Department: ${record.department_detail.code}`
}

export function AdminAcademicDirectoryPage({ kind }: { kind: DirectoryKind }) {
  const page = config[kind]
  const [records, setRecords] = useState<DirectoryRecord[]>([])
  const [schools, setSchools] = useState<AcademicUnit[]>([])
  const [centers, setCenters] = useState<AcademicUnit[]>([])
  const [departments, setDepartments] = useState<DirectoryRecord[]>([])
  const [unitTypes, setUnitTypes] = useState<Choice[]>([])
  const [programTypes, setProgramTypes] = useState<Choice[]>([])
  const [form, setForm] = useState<FormState>(emptyForm)
  const [editingRecord, setEditingRecord] = useState<DirectoryRecord | null>(
    null
  )
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const data = await apiFetch<DirectoryResponse>(page.endpoint)
    const items = (data[page.collectionKey] ?? []) as DirectoryRecord[]
    setRecords(items)
    setSchools(data.schools ?? [])
    setCenters(data.centers ?? [])
    setDepartments(data.departments ?? [])
    setUnitTypes(data.unit_types ?? [])
    setProgramTypes(data.program_types ?? [])
  }, [page.collectionKey, page.endpoint])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setIsLoading(true)
      void loadData()
        .catch((caught) => {
          setError(
            caught instanceof Error
              ? caught.message
              : `Unable to load ${page.title.toLowerCase()}.`
          )
        })
        .finally(() => setIsLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData, page.title])

  const filteredRecords = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return records
    return records.filter((record) =>
      [
        record.code,
        record.name,
        record.description,
        record.school_detail?.name,
        record.center_detail?.name,
        record.department_detail?.name,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [query, records])

  const availableDepartments = useMemo(() => {
    if (kind !== "units") return departments
    if (form.school) {
      return departments.filter(
        (department) => String(department.school ?? "") === form.school
      )
    }
    if (form.center) {
      return departments.filter(
        (department) => String(department.center ?? "") === form.center
      )
    }
    return []
  }, [departments, form.center, form.school, kind])

  function updateField(field: keyof FormState, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function updateParentField(field: "school" | "center", value: string) {
    setForm((current) => {
      if (kind !== "units") return { ...current, [field]: value }

      const next = {
        ...current,
        [field]: value,
      }

      if (field === "school" && value) next.center = ""
      if (field === "center" && value) next.school = ""
      if (current[field] !== value) next.department = ""

      return next
    })
  }

  function resetForm() {
    setEditingRecord(null)
    setForm(emptyForm)
  }

  function startEdit(record: DirectoryRecord) {
    setEditingRecord(record)
    setForm(formFromRecord(record))
    setError("")
    setSuccess("")
  }

  function buildPayload() {
    const base = {
      code: form.code.trim().toUpperCase(),
      name: form.name.trim(),
      description: form.description,
      school: maybeNumber(form.school),
      center: maybeNumber(form.center),
      is_active: form.is_active,
    }

    if (kind === "departments") return base
    if (kind === "units") {
      return {
        ...base,
        unit_type: form.unit_type,
        department: maybeNumber(form.department),
      }
    }
    return {
      ...base,
      department: maybeNumber(form.department),
      program_type: form.program_type,
      level: form.level,
      duration_years: maybeNumber(form.duration_years),
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")

    if (kind === "units") {
      if (form.school && form.center) {
        setError("Select either a school or centre for this unit, not both.")
        return
      }
      if (!form.school && !form.center) {
        setError("Select a school or centre for this unit.")
        return
      }
    }

    setIsSaving(true)

    try {
      if (editingRecord) {
        await apiFetch(`${page.endpoint}/${editingRecord.id}`, {
          method: "PUT",
          body: JSON.stringify(buildPayload()),
        })
        setSuccess(`${page.itemLabel} updated successfully.`)
      } else {
        await apiFetch(page.endpoint, {
          method: "POST",
          body: JSON.stringify(buildPayload()),
        })
        setSuccess(`${page.itemLabel} created successfully.`)
      }
      await loadData()
      resetForm()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : `Unable to save ${page.itemLabel.toLowerCase()}.`
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function deleteRecord(record: DirectoryRecord) {
    if (!confirm(`Delete ${record.name ?? record.code}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`${page.endpoint}/${record.id}`, { method: "DELETE" })
      setSuccess(`${page.itemLabel} deleted successfully.`)
      await loadData()
      if (editingRecord?.id === record.id) resetForm()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : `Unable to delete ${page.itemLabel.toLowerCase()}.`
      )
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: `/admin/academics/${kind}`, title: page.title },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {page.title}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {page.description}
            </p>
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

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <CardTitle className="text-lg">{page.title}</CardTitle>
                    <CardDescription>{records.length} records</CardDescription>
                  </div>
                  <div className="relative md:w-72">
                    <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      className="pl-9"
                      placeholder={`Search ${page.title.toLowerCase()}`}
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {filteredRecords.map((record) => (
                  <div
                    key={record.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold">{record.name}</p>
                          <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {record.code}
                          </span>
                          <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {parentLabel(record)}
                          </span>
                          {departmentLabel(record) ? (
                            <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              {departmentLabel(record)}
                            </span>
                          ) : null}
                          {!record.is_active ? (
                            <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
                              Inactive
                            </span>
                          ) : null}
                        </div>
                        {kind === "units" &&
                        record.assigned_executives?.length ? (
                          <p className="mt-2 text-sm text-muted-foreground">
                            {record.assigned_executives.length} assigned
                            executives
                          </p>
                        ) : null}
                        {record.description ? (
                          <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
                            {record.description}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEdit(record)}
                        >
                          <Edit3 className="size-4" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteRecord(record)}
                        >
                          <Archive className="size-4" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredRecords.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                    No records found.
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <EntityEditorCard
              title={
                editingRecord
                  ? `Edit ${page.itemLabel}`
                  : `Add ${page.itemLabel}`
              }
              description={
                kind === "units"
                  ? "Assign each unit to one school or one centre."
                  : "Assign each record to a school or centre."
              }
              isEditing={Boolean(editingRecord)}
              isSaving={isSaving}
              onSubmit={handleSubmit}
              onCancel={resetForm}
            >
              <div className="space-y-2">
                <Label htmlFor="record-code">Code</Label>
                <Input
                  id="record-code"
                  value={form.code}
                  maxLength={20}
                  onChange={(event) =>
                    updateField("code", event.target.value.toUpperCase())
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="record-name">Name</Label>
                <Input
                  id="record-name"
                  value={form.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  required
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="record-school">School</Label>
                  <select
                    id="record-school"
                    value={form.school}
                    onChange={(event) =>
                      updateParentField("school", event.target.value)
                    }
                    disabled={kind === "units" && Boolean(form.center)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    <option value="">None</option>
                    {schools.map((school) => (
                      <option key={school.id} value={school.id}>
                        {school.code}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="record-center">Centre</Label>
                  <select
                    id="record-center"
                    value={form.center}
                    onChange={(event) =>
                      updateParentField("center", event.target.value)
                    }
                    disabled={kind === "units" && Boolean(form.school)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    <option value="">None</option>
                    {centers.map((center) => (
                      <option key={center.id} value={center.id}>
                        {center.code}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {kind !== "departments" ? (
                <div className="space-y-2">
                  <Label htmlFor="record-department">Department</Label>
                  <select
                    id="record-department"
                    value={form.department}
                    onChange={(event) =>
                      updateField("department", event.target.value)
                    }
                    disabled={kind === "units" && !form.school && !form.center}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    <option value="">None</option>
                    {availableDepartments.map((department) => (
                      <option key={department.id} value={department.id}>
                        {department.code} - {department.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}
              {kind === "units" ? (
                <div className="space-y-2">
                  <Label htmlFor="record-unit-type">Unit Type</Label>
                  <select
                    id="record-unit-type"
                    value={form.unit_type}
                    onChange={(event) =>
                      updateField("unit_type", event.target.value)
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {unitTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}
              {kind === "programmes" ? (
                <>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="record-program-type">
                        Programme Type
                      </Label>
                      <select
                        id="record-program-type"
                        value={form.program_type}
                        onChange={(event) =>
                          updateField("program_type", event.target.value)
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        {programTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="record-duration">Years</Label>
                      <Input
                        id="record-duration"
                        type="number"
                        min="1"
                        value={form.duration_years}
                        onChange={(event) =>
                          updateField("duration_years", event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="record-level">Level</Label>
                    <Input
                      id="record-level"
                      value={form.level}
                      onChange={(event) =>
                        updateField("level", event.target.value)
                      }
                    />
                  </div>
                </>
              ) : null}
              <div className="space-y-2">
                <Label htmlFor="record-description">Description</Label>
                <Textarea
                  id="record-description"
                  value={form.description}
                  onChange={(event) =>
                    updateField("description", event.target.value)
                  }
                  rows={5}
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
            </EntityEditorCard>
          </section>
        )}
      </main>
    </div>
  )
}
